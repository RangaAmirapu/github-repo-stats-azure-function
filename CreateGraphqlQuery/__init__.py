import logging

from typing import List
from Helpers.SendEmails import sendEmail


def main(repos: List) -> str:
    """
    Takes in a list of repos 
    Returns one graphql query for the list of repos

        Parameters
            repos (List) - List containing repos to fetch stats
            
        Returns
            One graphql query for the list of repos obtained
    """
    
    try:
        graphqlQuery = 'query getRepoStats {'


        # Loop through the list of repos and form graphql query
        
        for index, repo in enumerate(repos):
            identifier = 'r' + str(index)
            graphqlQuery += createQueryForRepo(repo, identifier)

        graphqlQuery += '}'
    
        return graphqlQuery
    
    except:
        # Log error and send email in case of exception
        
        logging.error("Error- unable to create graphql query for")
        logging.error(repos)
        
        sendEmail("Error- unable to create graphql query for" + str(repos))
        raise

def createQueryForRepo(repo, identifier):
    """
    Takes in a repo name and its identifier
    Returns graphql query for given repo

        Parameters
            repos (str) - List containing repos to fetch stats
            identifier(str) - Unique identifier for thr repo query
            
        Returns
            Graphql query for the repo
    """
    
    # Split owner, repo name from repo and pass to graphql query
    
    owner = repo.split('/')[0]
    name = repo.split('/')[1]
    
    queryForRepoStats = '$identifier: repository(owner: "$owner", name: "$name") {nameWithOwner,isArchived,isTemplate,updatedAt,Issues: issues{totalCount},openIssues: issues(states: OPEN) {totalCount},closedIssues: issues(states: CLOSED) {totalCount},PRs: issues{totalCount},openPRs: pullRequests(states: OPEN) {totalCount},closedPRs: pullRequests(states: CLOSED) {totalCount},mergedPRs: pullRequests(states: MERGED) {totalCount},stars: stargazers {totalCount}}'.replace("$identifier", identifier).replace("$owner", owner).replace("$name", name)  
    
    return queryForRepoStats
