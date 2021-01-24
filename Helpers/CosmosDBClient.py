import logging
import os
from typing import List
import azure.cosmos.cosmos_client as cosmos_client

from Helpers.SendEmails import sendEmail

def cosmosDbContainer(endPoint: str, key: str, databaseName: str, containerName: str): 
    """
    Takes in a Cosmos DB endpoint, key, database name, container name and returns the container instance to work on it

        Parameters
            endPoint (str) - Cosmos DB endpoint
            key (str) - Cosmos DB key
            databaseName (str) - Cosmos DB database name
            containerName (str) - Cosmos DB container name
            
        Returns
            Container instance to work on it
    """
    try:
        client = cosmos_client.CosmosClient(endPoint, key)
        database = client.get_database_client(databaseName)
        container = database.get_container_client(containerName)

        return container
    
    except:
        logging.error("Error- Unable to get CosmosDB container for " + containerName)
        
        sendEmail("Error- Unable to get CosmosDB container for " + containerName)
        raise
    

def partitionDataForThrottling(data :List) -> List:
    """
    Takes in a list and returns list of data in allowable RU limits

        Parameters
            data (List) - List of all data that need to be created in Cosmos DB
            
        Return
            List of lists, where each list contains data in allowable limit
    """
    
    # Get the provisoned throughput and RU needed for each write
    # Leaving 20 KB as safe buffer limit from max allowable capacity
    
    cosmosDB_ProvisionedThroughput = int(os.environ["CosmosDB_ProvisionedThroughput"])
    cosmosDB_RU_NeededForEachWrite = int(os.environ["CosmosDB_RU_NeededForEachWrite"])
    
    safeCapacityLimitBufferInBytes = 20000
    maxCapacityInBytesPerSecond = ((cosmosDB_ProvisionedThroughput / cosmosDB_RU_NeededForEachWrite)
                                     * 1000
                                     - safeCapacityLimitBufferInBytes)
    
    dataThrottled = []
    currentSet = []
    sizeTracker = 0
 
    for index, repostat in enumerate(data):
    
        # Get the size of current document and upadate sizetracker

        repostatSizeInBytes = len(str(repostat).encode('utf-8'))
        sizeTracker += repostatSizeInBytes

        # If the size of current document fits in the current set add it
        # Else add the the current set to the main list for processing
        # Reset the current set and sizetracker, add the current repo stats back to the list
        # If the loop reaches the last element then add current set to main list

        if maxCapacityInBytesPerSecond - sizeTracker >= 0 :
            currentSet.append(repostat)

            if(len(data)-1 == index):
                dataThrottled.append(currentSet)

        else:
            dataThrottled.append(currentSet)

            sizeTracker = 0
            currentSet = []

            data.append(repostat)
            
    return dataThrottled