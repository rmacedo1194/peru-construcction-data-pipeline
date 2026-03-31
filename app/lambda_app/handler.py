import asyncio
from typing import Any, Dict
from .config import Settings 

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda entry point.

    this functions is the bridge between AWS Lambda and the asynchronous code in the app. 
    It runs the main function of the app in an event loop and returns the result.
    """
    return asyncio.run(run_pipeline(event, context))

async def run_pipeline(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main pipeline orchestrator function.

    this function will coordinate:
    - Api ingestion
    - Data transformation
    - storage into s3

    """

    settings = Settings.from_env()
    dataset = event.get("dataset","unknown")

    return build_success_response(
        dataset=dataset,
        message=("Lambda handler initialized correctly"
                 f"for bucket '{settings.raw_bucket_name}'"
                 )

    )

def build_success_response(dataset: str, message: str) -> Dict[str, Any]:
    """
    Standard success response builder for the Lambda function.
    """
    return {
        "status": "success",
        "dataset": dataset,
        "message": message
    }