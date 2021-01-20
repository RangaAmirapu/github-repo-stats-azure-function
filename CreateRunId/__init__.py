import logging
import os
import azure.cosmos.cosmos_client as cosmos_client

from datetime import datetime
from Helpers.SendEmails import sendEmail


def main(name: str) -> int:
    
    """
    Returns run id for the current run, which is used for appending to repo names to form unique id.
 
        Returns
            Combined run id
    """
    
    try:
        # Cosmos DB settings from environment
        
        endpoint = os.environ["CosmosDB_Endpoint"]
        key = os.environ["CosmosDB_PrimaryKey"]
        database_name = os.environ["CosmosDB_DBName"]
        container_name = os.environ["CosmosDB_RunInfoContainerName"]

        # Using UTC time as the run happens in UTC time. 
        # Currently there is no option to set timezone is Azure Functions Linux consumption plan
        
        currentUtcDateTime = datetime.utcnow()
        runId = str(currentUtcDateTime.timestamp()).split('.')[0]
        date = currentUtcDateTime.strftime("%Y%m%d")

        runInfo = {
            "id" : runId,
            "date"  : date
        }

        # Create id in Container and return the id if successful else return 0
        
        client = cosmos_client.CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        result = container.create_item(runInfo)
        return int(result["id"])
    
    except:
        # Log error and send email in case of exception

        logging.error("Error- Unable to create id for this run")
        
        sendEmail("Error- Unable to create id for this run")
        return 0