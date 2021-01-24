import logging
from Helpers.SendEmails import sendEmail


def main(emailData: str) -> str:
    """
    Takes in html string containing email body to send notification
    Returns status of the operation

        Parameters
            emailData (str) - String containing email body to send notification
            
        Returns
            Status of the operation
    """

    try:
        # Call send email function from Helper folder
        
        return sendEmail(emailData)
    
    except:
        # Log error and try to call helper email function in case of exception
        
        logging.error("Error- Unable to send email")
        logging.error(emailData)
        
        sendEmail("Error- Unable to send email")
        raise