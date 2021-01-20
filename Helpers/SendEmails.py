import logging
import os

from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def sendEmail(emailData: str):
    """
    Takes in a email body string and posts to sendgrid api for processing

        Parameters
            emailData (str) - String containing email body
    """
    
    try:
        # Send email using sendgrid
        
        message = Mail(
            from_email= os.environ["SendGrid_VerifiedFromSenderEmail"],
            to_emails= os.environ["SendGrid_ToEmail"], 
            subject='Github stats data sync status -' + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            html_content = emailData)
            
        sg = SendGridAPIClient(os.environ["SendGrid_API_Key"])
        sg.send(message)
        
    except:
        # Log error in case of exception
        
        logging.error("Error- Unable to send email")
        logging.error(emailData)
        
        raise