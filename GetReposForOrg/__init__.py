import logging
import os

from typing import Dict
from pathlib import Path
from github import Github
from Helpers.SendEmails import sendEmail


def main(orgInfo: Dict) -> Dict:
    """
    Takes in the org info from source.json
    Returns Dict of repos for org after removing the excluded orgs

        Parameters
            orgInfo (Dict) - Single org info from sources.json
            
        Returns
            Dict containing the repos for given org
    """

    try:
        reposToGetStats = []

        orgName = orgInfo["orgName"]

        # Get repos to exclude from source.json for current org
        
        reposToExclude = []
        if "exclude" in orgInfo:
            reposToExclude = orgInfo["exclude"].split(',')

        githubToken = os.environ["Github_Token"]

        # Get orgs by using github rest api and remove the excluded orgs from the list
        # Using rest api we can get all orgs in one call, If using graphql 100 is max

        gh = Github(githubToken)
        org = gh.get_organization(orgName)
        reposInOrg = org.get_repos()
        for repo in reposInOrg:
            if not repo.name in reposToExclude:
                reposToGetStats.append(repo.full_name)

        return reposToGetStats

    except:
        # Log error and send email in case of exception

        logging.error("Error-Unable to get org info for")
        logging.error(orgInfo)

        sendEmail("Error-Unable to get org info for" + str(orgInfo))
        raise
