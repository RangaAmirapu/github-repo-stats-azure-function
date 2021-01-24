import logging
import os
import time
from typing import Dict

from datetime import datetime
from Helpers.SendEmails import sendEmail
from Helpers.CosmosDBClient import cosmosDbContainer, partitionDataForThrottling

def main(runStatus: Dict) -> str:
    """
    Takes in a dict of current run status and updates the run info container with status
    Returns result of the update

        Parameters
            runStatus (Dict) - Status of the current run
            
        Returns
            Result of the update
    """
    
    try:
        
        endpoint = os.environ["CosmosDB_Endpoint"]
        key = os.environ["CosmosDB_PrimaryKey"]
        databaseName = os.environ["CosmosDB_DBName"]
        containerName = os.environ["CosmosDB_RunInfoContainerName"]
        container  = cosmosDbContainer(endpoint, key, databaseName, containerName)
        
        currentUtcDateTime = datetime.utcnow()
        date = currentUtcDateTime.strftime("%Y%m%d")
        
        # Get current run info
        
        itemId = runStatus["id"]
        
        runinfo = container.read_item(item= str(itemId), partition_key= date)
        
        # Update runinfo with status
        
        runinfo["totalReceived"] = runStatus["totalReceived"]
        runinfo["totalProcessed"] = runStatus["totalProcessed"]
        runinfo["totalCreatedCount"] = runStatus["totalCreatedCount"]
        runinfo["totalFailedCount"] = runStatus["totalFailedCount"]
        runinfo["createdList"] = ""
        runinfo["failedList"] = ""
        
        container.replace_item(item=runinfo, body=runinfo)
        
        time.sleep(1)
        
        createdRepos = runStatus["createdList"].split(',')
        createdReposPartitonedForThrottling =  partitionDataForThrottling(createdRepos)
        
        failedRepos = runStatus["failedList"]
        failedReposPartitonedForThrottling =  partitionDataForThrottling(failedRepos)
        
        for createdReposList in createdReposPartitonedForThrottling:
             runinfo["createdList"] += ",".join(createdReposList)
             container.replace_item(item=runinfo, body=runinfo)
             time.sleep(1)
             
               
        for failedReposList in failedReposPartitonedForThrottling:
            runinfo["failedList"] += ",".join(failedReposList)
            container.replace_item(item=runinfo, body=runinfo)
            time.sleep(1)
            
        return "Updated current run info status"
        
    except:
        logging.error("Error- Unable to update run info with run status")
        logging.error(str(runStatus))
        
        sendEmail("Error- Unable to update run info with run status")
        raise
    