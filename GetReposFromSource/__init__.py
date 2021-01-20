import logging
import json

from typing import Dict, List
from pathlib import Path
from Helpers.SendEmails import sendEmail


def main(sourceDataFile: str) -> Dict:
    
    """
    Takes in source file name
    Returns Dict after parsing the json in source file 

        Parameters
            sourceDataFile (str) - Source json(Eg: souce.json) file name in Data folder
            
        Returns
            Dict after parsing the json in source file 
    """
    
    try:
        repoSources = {}
        
        # Read source file and return
        
        data_path = Path("./Data/" + sourceDataFile)

        with open(data_path) as f:
            repoSources = json.load(f)
            f.close()

        return repoSources
    
    except:
        # Log error and send email in case of exception
        
        logging.error("Error- Unable to read source.json file")
        
        sendEmail("Error- Unable to read source.json file")
        raise