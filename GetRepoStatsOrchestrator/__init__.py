import logging
import math
import os
import time
import functools
import operator
import azure.durable_functions as df

from github import *

def orchestrator_function(context: df.DurableOrchestrationContext):
    """
    Orchestrator function that handles execution of all other functions
    
    Execution Order:
    1. Create run id and send an email notificataion stating the run has started
    2. Read data from sources.json in Data folder
    3. Get repos for each org in sources.json file and remove the repos mentioned in excluded variable
    4. Append individual repos to the repos obtained for each org and make a final list of repos to obtain stats
    5. Create batches of graphql queries based on 'NumberOfReposToQueryPerCall' setting in config
    6. Execute each batch of graphql queries and collect results
    7. Parse the collected results and make them ready to upload into cosmosdb
    8. Create items cosmosdb based on provisioned throughput capacity and collect the creation status
    9. Parse the collected cosmos db creation statuse and form email report
    10. Send email report about run completion status along with number of repos processed and failure list of repos if any
    """
    
    
    # Create run id and send notification
    
    currentRunId = yield context.call_activity("CreateRunId")
    yield context.call_activity("SendEmailNotifications", "Run Started with run id: " + str(currentRunId))
    
    #-----------------------------------------------------------------
    
    if currentRunId > 0:
        
        # Parse and get data from sources.json in Data folder
        
        sourceData = yield context.call_activity("GetReposFromSource", "sources.json")

        #-----------------------------------------------------------------

        # Get list of repos to get stats for each org
        
        OrgsToGetAllRepoStats = sourceData["fullOrgs"]
        getReposForOrgTasks =[]

        for orgDetails in OrgsToGetAllRepoStats:
            getReposForOrgTasks.append(context.call_activity("GetReposForOrg", orgDetails))

        getReposForOrgTasksResult = yield context.task_all(getReposForOrgTasks)

        #-----------------------------------------------------------------
        
        # Append individual repos to the list of repos fo each org to form a final list of repos to get stats 

        individualRepos = []

        if "individualRepos" in sourceData:
            individualRepos = sourceData["individualRepos"]

        fullReposList = {
            "reposForOrgs" : getReposForOrgTasksResult,
            "individualRepos" : individualRepos
        }

        allReposToGetStats = yield context.call_activity("AppendIndividualRepos", fullReposList)

        #-----------------------------------------------------------------

        # Create batches of graphql queries from the list of repos to get stats based on NumberOfReposToQueryPerCall setting
        # Eg: If NumberOfReposToQueryPerCall = 50 and we have a list of 500 repos to get stats 
        # Then we create 500/50 = 10 batches of queries
        
        createGraphqlQueryTasks =[]

        numberOfReposToQueryPerCall = int(os.environ["NumberOfReposToQueryPerCall"])
        numberOfQueryTasksToCreate =  math.ceil(len(allReposToGetStats)/numberOfReposToQueryPerCall)

        for i in range(numberOfQueryTasksToCreate):
            reposSubset = allReposToGetStats[i*numberOfReposToQueryPerCall : i*numberOfReposToQueryPerCall + numberOfReposToQueryPerCall]
            createGraphqlQueryTasks.append(context.call_activity("CreateGraphqlQuery", reposSubset))


        createGraphqlQueryTasksResult = yield context.task_all(createGraphqlQueryTasks)       

        #-----------------------------------------------------------------

        # Notes: 
        # Github api doesn't allow to send requests parallely against a same org or owner
        # So process one by one and collect those results
        # Don't send a list of all repos to activity function and process
        # Activity function will time out if processing take more than 10 minutes in consumption plans
        # Common github api error is 502 Bad gateway timeout, It can occur itermittently at any point
        # The only fix is to wait sometime and send requests again (30 seconds is enough)
        
        # Below code takes care of following 
        # Execute the batches of queries created and collect results
        # If a query execution fails add it back to the list to re process
        # Wait 60 seconds before going forward in case of failure
        
        
        executeGraphqlQueryTasksResult = []
            
        for query in createGraphqlQueryTasksResult:
                
            queryResult = yield context.call_activity("ExecuteGraphqlQuery", query)
                
            if queryResult["executionFailed"] :
                logging.error("Error- Graphql query execution failed, Appending the query and sleeping 60 seconds")
                createGraphqlQueryTasksResult.append(query)
                time.sleep(60)
                     
            else:
                executeGraphqlQueryTasksResult.append(queryResult["githubStatsData"])

        #-----------------------------------------------------------------

        # Parse the results obtained from executing the graphql queries and create documents for cosmosdb
        
        parseGraphqlQueryTasks =[]

        for result in executeGraphqlQueryTasksResult:

            gqlResult = {
                "currentRunId" : currentRunId,
                "result" : result
            }

            parseGraphqlQueryTasks.append(context.call_activity("ParseGraphqlQueryResult", gqlResult))

        parseGraphqlQueryTasksResult = yield context.task_all(parseGraphqlQueryTasks)

        #-----------------------------------------------------------------
        
        # Create itema is cosmos db based on plan and provisoned throughput
        # If using serverless mode process all data in parallel
        # If using provisioned mode process data one by one not exceeding the available throughput
        # Collect the item creation statuses and form report to send notifications
        
        isCosmoDbInServerlessMode = os.environ["CosmosDB_ServerlessMode"].lower()

        uploadToCosmosDBTasksResult = []

        if isCosmoDbInServerlessMode == "true":
            
            # Process in parallel
            
            uploadToCosmosDBTasks =[]

            for result in parseGraphqlQueryTasksResult:
                uploadToCosmosDBTasks.append(context.call_activity("UploadQueryResultsToCosmosDB", result))

            uploadToCosmosDBTasksResult = yield context.task_all(uploadToCosmosDBTasks)
            
        else:

            #Throttle cosmosdb requests as per provsioned RU
            
            for result in parseGraphqlQueryTasksResult:
                uploadToCosmosDBResult = yield context.call_activity("UploadQueryResultsToCosmosDB", result)
                uploadToCosmosDBTasksResult.append(functools.reduce(operator.iconcat, uploadToCosmosDBResult, []))
                
        #-----------------------------------------------------------------
        
        # Parse the item creation statuses and form report to send notifications

        runCompletionStatus = yield context.call_activity("ParseCosmosDBResults", uploadToCosmosDBTasksResult)
        
        #-----------------------------------------------------------------
        
        # Add run id to the status dict to update the run info container
        
        runStatus = runCompletionStatus["status"]
        runStatus["id"] = currentRunId

        # Update run info container
        
        yield context.call_activity("UpdateRunInfoWithStatus", runStatus)
        
        #-----------------------------------------------------------------
        
        publishToEventGrid = os.environ["PublishToEventGrid"]
        
        notificationText = ""
        
        if publishToEventGrid == "true":
            
            # Publish run info to event grid for any downstream processes

            publishToEventGridStatus = yield context.call_activity("PublishRunInfoToEventGrid", str(currentRunId))

            #-----------------------------------------------------------------

            # Notify the run status

            if publishToEventGridStatus["success"] :
                notificationText = "Run completed and posted to event grid <br><br>" + runCompletionStatus["emailBody"]
            else: 
                notificationText = "Run completed, failed to posted to event grid <br><br>" + runCompletionStatus["emailBody"]

            #-----------------------------------------------------------------
            
        else:
            notificationText = "Run completed <br><br>" + runCompletionStatus["emailBody"]
        
           
        notificationStatus = yield context.call_activity("SendEmailNotifications", notificationText)
        return notificationStatus
        
    else:
        # If unable to create id for current run notify and log error
        
        yield context.call_activity("SendEmailNotifications", "Failed to obtain runId for current run")
        logging.error("Failed to obtain runId for current run")
        
        return "Failed to obtain runId for current run"
    
main = df.Orchestrator.create(orchestrator_function)