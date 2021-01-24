import json
import requests
import logging

from typing import Dict, List
from Helpers.SendEmails import sendEmail

def publishEvent(endpoint: str, endpointKey: str, eventGridData: List) -> Dict:

    """
    Takes in subject, eventGridData, eventType to post to event grid
    Returns status of the operation

        Parameters
            endpoint (str) - Event grid topic endpoint
            endpointKey (str) - Event grid topic key
            eventGridData (List) -  List of data to post to event grid
        
        Returns
            Dict containing the status and data posted to event grid
    """
    
    try:
        # Call event grid post api and publish event
        
        headers = {
        'Content-type': 'application/json', 
        'aeg-sas-key': endpointKey
        }
    
        dataToPost = json.dumps(eventGridData)
        response = requests.post(endpoint, data= dataToPost, headers= headers)

        if response.status_code == 200 :
            
            return {
                "success" : True,
                "data" : eventGridData
            }
        
        else :
            
            return {
                "success" : False,
                "data" : eventGridData
            }
            
    
    except:
        # Log error and try to call helper email function in case of exception
        
        logging.error("Error- Unable to post to event grid")
        
        sendEmail("Error- Unable to post to event grid")
        raise