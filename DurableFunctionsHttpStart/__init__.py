import logging
import azure.functions as func
import azure.durable_functions as df

from Helpers.SendEmails import sendEmail


async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    """
    HTTP starter function for starting the durble functions orchestrator
    Useful for starting the orchestrator while developing and debugging both locally and in Azure
    Remember to pass the function key if triggering the Azure functions url
    """
    
    try:
        client = df.DurableOrchestrationClient(starter)

        instance_id = await client.start_new(orchestration_function_name= req.route_params["functionName"], instance_id=None, client_input= None)

        logging.info(f"Started orchestration with ID = '{instance_id}'.")

        return client.create_check_status_response(req, instance_id)
    
    except:
        # Log error and send email in case of exception
        
        logging.error("Error- HTTP starter function failed to run")
        sendEmail("Error- HTTP starter function failed to run")