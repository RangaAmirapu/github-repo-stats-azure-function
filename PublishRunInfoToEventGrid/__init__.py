import uuid
import os
import logging

from typing import Dict
from datetime import datetime
from Helpers import SendEmails
from Helpers import EventGridClient

def main(runId: str) -> Dict:

    """
    Takes in runId and posts to event grid, for downstream processes
    Returns dict containing status of the operation

        Parameters
            runId (str) - Current run id in run info table
            
        Returns
            Status of the operation
    """
    try:
        # Call event grid post api and publish event
        
        eventGridTopicEndpoint =  os.environ["EventGridEndpoint"]
        eventGridTopicKey =  os.environ["EventGridKey"]
 
        eventGridData = [
            {
                "id": uuid.uuid4().hex,
                "subject": "RunCompleted",
                "data": {
                    "runInfoId": runId,
                    "runInfoDate": datetime.utcnow().strftime("%Y%m%d")
                },
                "eventType": "GithubStats",
                "eventTime": str(datetime.utcnow().isoformat())
            }
        ]
    
        return EventGridClient.publishEvent(eventGridTopicEndpoint, eventGridTopicKey,eventGridData)
    
    except:
        # Log error and try to call helper email function in case of exception
        
        logging.error("Error- Unable to post to event grid for runId: " + runId)

        SendEmails.sendEmail("Error- Unable to post to event grid for runId: " + runId)
        raise