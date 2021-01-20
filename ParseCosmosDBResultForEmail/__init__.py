import logging
import functools
import operator

from typing import List
from Helpers.SendEmails import sendEmail


def main(cosmosDBResult: List) -> str:
    """
    Takes in a list of cosmos DB create item results to generate report 
    Returns html string containing the report to send email

        Parameters
            cosmosDBResult (List) - List containing result of cosmos DB create item operation
            
        Returns
            Html string containing the report to send email
    """

    try:
        cosmosDBResults = functools.reduce(operator.iconcat, cosmosDBResult, [])
        
        totalReceived = 0
        totalProcessed = 0
        totalCreatedCount = 0
        totalFailedCount = 0
        failedList = ''
        
        # Parse the incoming list and form html string
        
        for result in cosmosDBResults:
            totalReceived += result["received"]
            totalProcessed += result["processed"]
            totalCreatedCount += result["createdCount"]
            totalFailedCount += result["failedCount"]
            failedList += ", ".join(result["failedList"])
            
        return "<b>Total received: {0} <br>Total processed: {1}<br>Total created: {2}<br>Total failed: {3} <br>Failed List: {4}<br></b>".format(totalReceived, totalProcessed, totalCreatedCount, totalFailedCount, failedList)
        
    except:
        # Log error and send email in case of exception
        
        logging.error("Error- Unable to form email status from cosmos db results")
        
        sendEmail("Error- Unable to form email status from cosmos db results")
        raise
