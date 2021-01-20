import datetime
import logging
import azure.functions as func
import azure.functions as func
import azure.durable_functions as df

from Helpers.SendEmails import sendEmail


async def main(mytimer: func.TimerRequest ,  starter: str) -> None:
    """
    Time trigger function for starting the durable function orchestrator
    To change the schedule update CRON in function.json file
    """

    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.error('The timer is past due!')

    try:
        client = df.DurableOrchestrationClient(starter)

        instance_id = await client.start_new(orchestration_function_name= "GetRepoStatsOrchestrator", instance_id=None, client_input= None)

        logging.info(f"Started orchestration with ID = '{instance_id}'.")

    except:
        # Log error and send email in case of exception
        
        logging.error("Error- Time trigger starter function failed to run")
        sendEmail("Error- Time trigger starter function failed to run")
    
    
    logging.info("Timer trigger function ran at %s", utc_timestamp)