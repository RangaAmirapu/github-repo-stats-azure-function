import logging
import os
import time
import azure.cosmos.cosmos_client as cosmos_client

from typing import List
from Helpers.SendEmails import sendEmail
from Helpers.CosmosDBClient import cosmosDbContainer, partitionDataForThrottling

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
            # Partition data for Cosmos DB throttling
            
            ghStatsPartionedForThrottling = partitionDataForThrottling(ghStats)
         
            # Process the data chunks each one by  one
            # Call the create function below and add status to list
            # Cooldown for a second before sending next chunk of data
            
            for ghStats in ghStatsPartionedForThrottling:
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
    
    uploadResults = []
    uploadedCount = 0;
    createdList = []
    failedList = []

    if(len(ghStats) > 0):
        
        # Create an instance of cosmos DB client and create items
        endpoint = os.environ["CosmosDB_Endpoint"]
        key = os.environ["CosmosDB_PrimaryKey"]
        databaseName = os.environ["CosmosDB_DBName"]
        containerName = os.environ["CosmosDB_DataContainerName"]
        container  = cosmosDbContainer(endpoint, key, databaseName, containerName)

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