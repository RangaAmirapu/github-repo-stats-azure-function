import logging
import os

from typing import Dict
from Helpers.SendEmails import sendEmail
from sgqlc.endpoint.http import HTTPEndpoint


def main(graphqlQueryToExecute: str) -> Dict:
    
    """
    Takes in graphql query for a set of repos 
    Returns Dict of result

        Parameters
            graphqlQueryToExecute (str) - Graphql query to execute
            
        Returns
            Dict containing result of executed graphql query and the execution status
    """

    githubStatsData = {}
    executionFailed = False

    try:
        # Set up the graphql client
        
        url = "https://api.github.com/graphql"
        githubToken = os.environ["Github_Token"]

        headers = {
            'Authorization': 'bearer ' + githubToken,
        }
        endpoint = HTTPEndpoint(url, headers)
        
        # Execute query
        
        result = endpoint(graphqlQueryToExecute)

        if "errors" in result:
            logging.error("Error- Graphql query execution has errors")
            logging.error(graphqlQueryToExecute)
            executionFailed = True

        else:
            githubStatsData = result
        
        # Return the result and status
        
        graphqlQueriesExecutionResult = {
            "githubStatsData": githubStatsData,
            "executionFailed": executionFailed
            }

        return graphqlQueriesExecutionResult

    except:
        # Log error and send email in case of exception
        
        logging.error("Error- Unable to execute graphql query")
        logging.error(graphqlQueryToExecute)
        
        sendEmail("Error- Unable to execute graphql query" + str(graphqlQueryToExecute))
        raise


