import logging
import os
import time
import azure.cosmos.cosmos_client as cosmos_client

from typing import List
from Helpers.SendEmails import sendEmail


def main(ghStats: List) -> List:
    """
    Takes in a list of repo stats that come after parsing the graphql results 
    Returns list of dicts containing the status of uploading to cosmos DB

        Parameters
            ghStats (List) - List of repo stats that come after parsing the graphql results 
            
        Returns
            List of dicts containing the status of uploading to cosmos DB
    """

    try:
        # Check if cosnmos db is in serverless mode 
        # so we can process all data at once without worrying about throughput
        
        isCosmoDbInServerlessMode = os.environ["CosmosDB_ServerlessMode"].lower()

        uploadedResults = []
        
        if isCosmoDbInServerlessMode == "true":
            if(len(ghStats) > 0):
                uploadedResults = createCosmosDBItem(ghStats)
                return uploadedResults
            
        # If cosmos DB not in serverless mode make requests as per provisioned throughput
        
        else:
            # Get the provisoned throughput and RU needed for each write
            # Leaving 20 KB as safe buffer limit from max allowable capacity
            
            cosmosDB_ProvisionedThroughput = int(os.environ["CosmosDB_ProvisionedThroughput"])
            cosmosDB_RU_NeededForEachWrite = int(os.environ["CosmosDB_RU_NeededForEachWrite"])
            
            safeCapacityLimitBufferInBytes = 20000
            maxCapacityInBytesPerSecond = ((cosmosDB_ProvisionedThroughput / cosmosDB_RU_NeededForEachWrite)
                                             * 1000
                                             - safeCapacityLimitBufferInBytes)
            
            ghStatsThrottled = []
            currentSet = []
            sizeTracker = 0
            
            # Loop through the list of repo stats obtained ad form data chunks in allowable throughput limit
            
            for index, repostat in enumerate(ghStats):
                
                # Get the size of current document and upadate sizetracker
                
                repostatSizeInBytes = len(str(repostat).encode('utf-8'))
                sizeTracker += repostatSizeInBytes
                
                # If the size of current document fits in the current set add it
                # Else add the the current set to the main list for processing
                # Reset the current set and sizetracker, add the current repo stats back to the list
                # If the loop reaches the last element then add current set to main list
                
                if maxCapacityInBytesPerSecond - sizeTracker >= 0 :
                    currentSet.append(repostat)
                    
                    if(len(ghStats)-1 == index):
                        ghStatsThrottled.append(currentSet)
                
                else:
                    ghStatsThrottled.append(currentSet)
                    
                    sizeTracker = 0
                    currentSet = []
                    
                    ghStats.append(repostat)
                    
            # Process the data chunks each one by  one
            # Call the create function below and add status to list
            # Cooldown for a second before sending next chunk of data
            
            for ghStats in ghStatsThrottled:
                result = createCosmosDBItem(ghStats)
                uploadedResults.append(result)
                
                time.sleep(1)
                
        return uploadedResults

    except:
        # Log error and send email in case of exception
        
        logging.error("Error- Unable to upload to cosmos db")
        logging.error(ghStats)
        
        sendEmail("Error- Unable to upload to cosmos db" + str(ghStats))
        raise


def createCosmosDBItem(ghStats: List) -> List :
    
    endpoint = os.environ["CosmosDB_Endpoint"]
    key = os.environ["CosmosDB_PrimaryKey"]
    database_name = os.environ["CosmosDB_DBName"]
    container_name = os.environ["CosmosDB_DataContainerName"]

    uploadResults = []
    uploadedCount = 0;
    createdList = []
    failedList = []

    if(len(ghStats) > 0):
        
        # Create an instance of cosmos DB client and create items

        client = cosmos_client.CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        # If item is created successfully add it to created list
        # Else add it to failed list in case of exception 
        # Create a dict of status and append to list for sending report
        
        for index, repostat in enumerate(ghStats):
            try:
                result = container.create_item(repostat)
                uploadedCount = index + 1
                createdList.append(result["repo"])

            except:
                failedList.append(repostat["repo"])

        uploadResults.append({
            "success": True if len(ghStats) % len(createdList) == 0 else False,
            "received": len(ghStats),
            "processed": uploadedCount,
            "createdCount": len(createdList),
            "failedCount": len(failedList),
            "createdList": createdList,
            "failedList": failedList
        })

    return uploadResults