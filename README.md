# Building a data pipeline using Azure Durable Functions 

[Introduction](#introduction)

[Features](#features)

[Project structure explanation](#project-structure-explanation)

[Data source configuration](#data-source-configuration)

[Function configurations](#function-configurations)

[Database design](#database-design)

[Project flow and functions explanation](#project-flow-and-functions-explanation)

[Deployment](#deployment)

[QA and Monitoring](#qa-and-monitoring)

[Next Steps](#next-steps)

[Github Project Board](https://github.com/RangaAmirapu/github-repo-stats-azure-function/projects/1)

## Introduction
github-repo-stats is a data pipeline built using Azure Durable Functions. Posts Github repo stats to Cosmos DB and publish event to Azure Event Grid for starting any downstream processing.

**Example of repo stats obtained :** 

    {
    "repo": "octokit/octokit.rb",
    "isArchived": false,
    "isTemplate": false,
    "repoUpdatedAt": "2021-01-19T20:44:18Z",
    "openIssues": 46,
    "closedIssues": 455,
    "totalIssues": 501,
    "openPRs": 13,
    "closedPRs": 150,
    "mergedPRs": 598,
    "totalPRs": 501,
    "stars": 3378
    }

Harnesses the power of durable functions - Function chaining, Fan out/ Fan in to run tasks in parallel and passing data from one step to other.

**Techstack used**: 

 - Azure durable functions using python 3.8
 - Azure Cosmos DB
 - Azure Event Grid
 - Azure Application Insights
 - Azure Log Analytics
 - SendGrid
 - Github Actions

## Features:

- Easily configure to pull stats for entire org or individual repos through simple json file
- Get stats from multiple orgs at same time or a combination of orgs and individual repos
- Exclude repos that doesn't interest you from full orgs
- Throttle requests to Github GraphQL API using configurable values
- Retry failed requests to Github API after cool down
- Takes Cosmos DB throughput into consideration to prevent request dropping
- Throttle Cosmos DB requests based on RU's configured
- Switch between Cosmos DB serverless and provisioned mode to take full advantage of Cosmos DB infinite scaling
- Send notifications about run start and completion report at end using SendGrid
- Publish event in event grid for starting any down stream process
- Run on schedule using Azure functions time trigger or on demand using HTTP trigger
- Run completely on local machine for development and testing using Azure emulators
- Use Github actions for deploying to Function App

## Project structure explanation

The code for all the functions in a specific function app is located in a root project folder that contains a host configuration file and one or more subfolders. 

Each subfolder contains the code for a separate function. The folder structure is as below

    github-repo-stats-azure-function
     ┣ .github
     ┃ ┗ workflows
     ┃ ┃ ┗ main_githubrepostats.yml
     ┣ AppendIndividualRepos
     ┃ ┣ function.json
     ┃ ┗ __init__.py
     ┣ CreateGraphqlQuery
     ┃ ┣ function.json
     ┃ ┗ __init__.py
     ┣ CreateRunId
     ┃ ┣ function.json
     ┃ ┗ __init__.py
     ┣ Data
     ┃ ┗ sources.json
     ┣ DurableFunctionsHttpStart
     ┃ ┣ function.json
     ┃ ┗ __init__.py
     ┣ ExecuteGraphqlQuery
     ┃ ┣ function.json
     ┃ ┗ __init__.py
     ┣ GetReposForOrg
     ┃ ┣ function.json
     ┃ ┗ __init__.py
     ┣ GetReposFromSource
     ┃ ┣ function.json
     ┃ ┗ __init__.py
     ┣ GetRepoStatsOrchestrator
     ┃ ┣ function.json
     ┃ ┗ __init__.py
     ┣ Helpers
     ┃ ┣ CosmosDBClient.py
     ┃ ┣ EventGridClient.py
     ┃ ┗ SendEmails.py
     ┣ OrchestratorTimeTrigger
     ┃ ┣ function.json
     ┃ ┣ sample.dat
     ┃ ┗ __init__.py
     ┣ ParseCosmosDBResults
     ┃ ┣ function.json
     ┃ ┗ __init__.py
     ┣ ParseGraphqlQueryResult
     ┃ ┣ function.json
     ┃ ┗ __init__.py
     ┣ PublishRunInfoToEventGrid
     ┃ ┣ function.json
     ┃ ┗ __init__.py
     ┣ SendEmailNotifications
     ┃ ┣ function.json
     ┃ ┗ __init__.py
     ┣ UpdateRunInfoWithStatus
     ┃ ┣ function.json
     ┃ ┗ __init__.py
     ┣ UploadQueryResultsToCosmosDB
     ┃ ┣ function.json
     ┃ ┗ __init__.py
     ┣ .funcignore
     ┣ host.json
     ┣ local.settings.json
     ┣ proxies.json
     ┗ requirements.txt

In the above file tree structure apart from folders that hold individual functions there are some configuration files at root level.

 1. **.funcignore** : Contains files that needs to be ignored while deploying app to Azure.
 2. **host.json** : Metadata file that contains global configuration which effects all functions. 
 It contains details about  version, log level, application insights settings and Azure Functions extension bundle version.
 3. **local.settings.json** : Stores app settings, connection strings, Any settings included in this file can be accessed using python OS module. These settings are only used when running locally and these settings need to be exported to your function app configurations. This file is ignored during deployment to prevent any configuration mismatch.
 4. **proxies.json** : Azure functions proxies is a toolkit that allows you to modify the requests and responses of your APIs. You can expose multiple function apps built as a microservice architecture in a single unified endpoint. (Not used in this project)
 5. **requirements.txt** : Used for listing project package dependencies which gets installed when publishing to Azure

## Data source configuration

The repos to pull stats are configured in sources.json file located in Data folder

    {
    "fullOrgs" :[
        {
            "orgName" : "microsoft",
            "exclude" : "FluidExamples,maro"
        },
        {
            "orgName" : "Esri",
            "exclude" : ""
        }
    ],
    "individualRepos" : ["octokit/octokit.rb", "Azure/azure-cli"]
    }

The `fullOrgs` array contains org names that you want get stats for all the repos in an org. Optionally you can provide a CSV list of repos that you want to ignore for the org.

The `individualRepos` array contains a CSV list of repos that you want to get stats


## Function configurations

The `local.settings.json` file has the following settings that are configurable as required.

 - **Github_Token** : Github api key that has access to pull repo stats
 - **NumberOfReposToQueryPerCall** : This setting is used to batch the Github GraphQL query call. 
  
   Eg: If this is set to 65, one GraphQL call will batch 65 repos  and get data for all of them in a single call. Don't increase this number too high as Github API will result in timeout.
 - **CosmosDB_Endpoint** : Cosmos DB account endpoint. Can use local emulator while development
 - **CosmosDB_PrimaryKey**: Cosmos DB account key
 - **CosmosDB_DBName** : Cosmos DB database id
 - **CosmosDB_DataContainerName** : Cosmos DB container which holds stats data
 - **CosmosDB_RunInfoContainerName** : Cosmos DB container which holds run info data 
 - **CosmosDB_ServerlessMode** : Specifies whether Cosmos Db is in serverless mode. If set to "true" create item operations will not throttle and will create items in parallel
 - **CosmosDB_ProvisionedThroughput** : Throughput allowed for this app. Used for throttling requests
 - **CosmosDB_RU_NeededForEachWrite** : Throughput needed for each 1KB write in Cosmos DB
 -  **SendEmailNotifications** : Specifies whether to send email notifocation about run start, end and in error conditions
 - **SendGrid_API_Key** : SendGrid account API key, used for sending emails
 - **SendGrid_VerifiedFromSenderEmail** : Verified email in SendGrid account, used for sending emails
 - **SendGrid_ToEmail** : Email for receiving run notifications
 - **PublishToEventGrid** : Specifies whether to publish events in Azure Event Grid after run completion for starting any other processes
 - **EventGridEndpoint** : Event Grid topic endpoint
 - **EventGridKey** : Event Grid topic key

# Database design

This app uses two Cosmos DB containers which are configurable (In `local.settings.json` during development and in function configuration in Azure)

 1. **CosmosDB_DataContainerName** : Cosmos DB container which holds stats data
 2. **CosmosDB_RunInfoContainerName** : Cosmos DB container which holds run information. 
This container is updated with runId before the run starts and run details after completion. Sample run info document

        {
        "id": "1611127298",
        "date": "20210119",
        "totalReceived": 1,
        "totalProcessed": 1,
        "totalCreatedCount": 1,
        "totalFailedCount": 0,
        "createdList": "octokit/octokit.rb",
        "failedList": ""
        }

The id created in run info container is appended to repo name and used as id in stats table. Sample data container document

    {
        "id": "octokit.octokit.rb.1611127298",
        "repo": "octokit/octokit.rb",
        "isArchived": false,
        "isTemplate": false,
        "repoUpdatedAt": "2021-01-19T20:44:18Z",
        "openIssues": 46,
        "closedIssues": 455,
        "totalIssues": 501,
        "openPRs": 13,
        "closedPRs": 150,
        "mergedPRs": 598,
        "totalPRs": 501,
        "stars": 3378
    }

`repo` is used as partition key for data container. 

After the run is completed run id is published to Event Grid. Using the run id we can get the repos processed for this run from run info container and do a point read by forming id for each repo which is a combination of repo name with owner and run id. 
 
# Project flow and functions explanation

As noted in the function configurations the `NumberOfReposToQueryPerCall` property controls the number of repos to batch in a single GraphQL query.

The `CosmosDB_ServerlessMode` property controls the rate at which items are created in Cosmos DB. If this property is set to "**true**" items are created in Cosmos DB in parallel without taking throughput into consideration. If this property is set to "**false**" the `CosmosDB_ProvisionedThroughput` and `CosmosDB_RU_NeededForEachWrite` are used for throttling the rate at which items are created in Cosmos DB.

###  Sequence diagram for processing 195 repos

![get-repo-stats-Sequence Diagram](https://raw.githubusercontent.com/RangaAmirapu/github-repo-stats-azure-function/documentation/DocumentationAssets/Images/getrepostatsSequenceDiagram.jpg)

 - **GetRepoStatsOrchestrator** : Handles all other function calls is triggered using a timer function for every 6 hours
 
 - **CreateRunId** : Will create id for current run in run info container.
 - **SendEmailNotifications** : Will send notification about run start
 - **GetReposFromSource** : Will parse the sources.json file for processing
 - **GetReposForOrg** : Will get repos for orgs mentioned in `fullOrgs` property in `sources.json` Also filters the orgs in `exclude` property from the list obtained.
 This function is executed in for each org serially. Github API doesn't allow calling a same org in parallel
 - **AppendIndividualRepos** : Will append individual repos in `sources.json` file to the list of repos obtained for orgs. Final list of repos to pull stats are formed in this step.
 - **CreateGraphqlQuery** : Will Create batches of GraphQL queries to execute. Uses `NumberOfReposToQueryPerCall` as batch size. This function is executed in parallel on the list of repos to pull data. The parallel thread count is `TotalNumberOfRepos/BatchSize`
 - **ExecuteGraphqlQuery** : Will execute the batches of  GraphQL queries created in previous step and returns the result. This function in executed serially one batch after other and will retry a query if  it fails execution. A 60 second cool down period is implemented if error occurs.
 - **ParseGraphqlQueryResult** :  Will parse the results of ExecuteGraphqlQuery function. This function is executed in parallel on the results obtained.  The parallel thread count is `TotalNumberOfRepos/BatchSize`
 - **UploadQueryResultsToCosmosDB** : Will upload parsed query results to Cosmos DB. This function is executed in parallel or in serial depending on Cosmos DB configuration.
- **ParseCosmosDBResults** : Will parse Cosmos DB create item operation results to create a report on run status like the number of items processed, number of successful creates, number of failures etc.
- **UpdateRunInfoWithStatus** : Will update the run info container with current run status. This helps the downstream processes to go point reads on data container.
- **PublishRunInfoToEventGrid** :  Will publish a event to Azure Event Grid about run completion status and run details. This helps in starting any downstream processes like analytics and dashboard creation
-  **SendEmailNotifications** : Will send notification about run completion and report on current run

 ###  Gantt chart for processing 195 reports
 
![Gantt chart for processing 195 reports](https://raw.githubusercontent.com/RangaAmirapu/github-repo-stats-azure-function/documentation/DocumentationAssets/Images/getrepostatsGanttChart.jpg)

# Deployment
Github Actions are used on the main branch to deploy code to Azure Functions on push event.

 [Github Actions](https://github.com/RangaAmirapu/github-repo-stats-azure-function/actions)

# QA and Monitoring

 - Tested with 6000 repos scheduled for every 6 hours and had no issues.
 - Exceptions are handled to retry failed GraphQL queries
 - Exceptions are handled on Cosmos DB create and replace item operations to ensure data quality
 - Reports are sent after the run is completed about the run status
 - Notifications are sent on function failures and logging is implemented in functions to log any errors
 - Log Analytics dashboards and alerts are set up for function app and Cosmos DB
 - Will receive notifications on deployment failures from Github actions.  

# Next Steps

 - Develop analytics pipeline to start after data is ingested into Cosmos DB
 - Develop visualization dashboards
 - Develop pipeline to archive data and free space in Cosmos DB after analytics are done so that free tier limit is not crossed
 - Develop unit tests suite and data quality tests
 [Github Project Board](https://github.com/RangaAmirapu/github-repo-stats-azure-function/projects/1)