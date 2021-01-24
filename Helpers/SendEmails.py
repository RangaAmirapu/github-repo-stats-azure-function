import logging
import os

from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def sendEmail(emailData: str) -> str:
    """
    Takes in email body and posts to sendgrid api for processing
    Returns status of the operation

        Parameters
            emailData (str) - String containing email body
            
        Returns
            String containing the status of operation
    """
    
    try:
        # Send email using sendgrid
        
        sendEmailNotifications= os.environ["SendEmailNotifications"]
        
        if sendEmailNotifications == "true":
        
            message = Mail(
                from_email= os.environ["SendGrid_VerifiedFromSenderEmail"],
                to_emails= os.environ["SendGrid_ToEmail"], 
                subject='Github stats data sync status -' + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                html_content = emailData)

            sg = SendGridAPIClient(os.environ["SendGrid_API_Key"])
            sg.send(message)
            return "email sent via sendgrid"
        
        else:
            return "email notifications is set to false in config"
        
    except:
        # Log error in case of exception
        
        logging.error("Error- Unable to send email")
        logging.error(emailData)
        
        raise