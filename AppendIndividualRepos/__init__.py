import logging
import functools
import operator

from typing import Dict, List
from Helpers.SendEmails import sendEmail


def main(repos: Dict) -> List:
    """
    Takes in Dict containing all repos for orgs obtained from github as per source.json and individual repos from source.json
    Returns combined list of all repos and individual repos.

        Parameters
            repos (Dict) - Dict containing all repos and individual repos
            
        Returns
            Combined list of all repos and individual repos
    """

    try:
        # Obtain repos from dict

        reposForOrgs = repos["reposForOrgs"]
        individualRepos = repos["individualRepos"]

        # Flatten the list of repos from all orgs which is a list of lists

        reposForOrgsFlat = functools.reduce(operator.iconcat, reposForOrgs, [])


        # Append the list of all repos and individual repos

        reposToGetStats = reposForOrgsFlat + individualRepos
        return reposToGetStats

    except:
        # Log error and send email in case of exception

        logging.error("Error- Unable to make final list of repos to get orgs")
        logging.error(repos)
        
        sendEmail("Error- Unable to make final list of repos to get orgs" + str(repos))
        raise
