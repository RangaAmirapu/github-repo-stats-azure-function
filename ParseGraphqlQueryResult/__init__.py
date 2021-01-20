import logging

from typing import Dict, List
from Helpers.SendEmails import sendEmail


def main(gqlResult: Dict) -> List:
    """
    Takes in Dict of executed graphql result 
    Returns parsed list of repo results ready for creating in cosmos db

        Parameters
            gqlResult (Dict) - Dict containing executed graphql results
            
        Returns
            List of repo results ready for creating in cosmos db
    """

    try:
        parsedResults = []
        
        currentRunId = gqlResult["currentRunId"]
        queryResults = gqlResult["result"]["data"]
        numberOfResults = len(queryResults)
        
        # Go through the dict, parse each result and make a list of parsed results for creating in cosmos db
        # Add current run id to repo nameWithOwner property to form unique id
        
        for index in range(numberOfResults):
            currentRepo = "r" + str(index)
            currentRepoStats = queryResults[currentRepo]
            
            stats = {
                "id": currentRepoStats["nameWithOwner"].replace('/', '.') + "." + str(currentRunId),
                "repo": currentRepoStats["nameWithOwner"],
                "isArchived": currentRepoStats["isArchived"],
                "isTemplate": currentRepoStats["isTemplate"],
                "repoUpdatedAt": currentRepoStats["updatedAt"],
                "openIssues": currentRepoStats["openIssues"]["totalCount"],
                "closedIssues": currentRepoStats["closedIssues"]["totalCount"],
                "totalIssues": currentRepoStats["Issues"]["totalCount"],
                "openPRs": currentRepoStats["openPRs"]["totalCount"],
                "closedPRs": currentRepoStats["closedPRs"]["totalCount"],
                "mergedPRs": currentRepoStats["mergedPRs"]["totalCount"],
                "totalPRs": currentRepoStats["PRs"]["totalCount"],
                "stars": currentRepoStats["stars"]["totalCount"]
            }
            parsedResults.append(stats)
            
        return parsedResults
            
    except:
        # Log error and send email in case of exception
        
        logging.error("Parsing failed for")
        logging.error(gqlResult)
        
        sendEmail("Parsing failed for" + str(gqlResult))
        raise