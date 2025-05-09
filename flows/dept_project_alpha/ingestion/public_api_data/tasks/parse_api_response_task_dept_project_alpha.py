# flows/dept_project_alpha/ingestion/public_api_data/tasks/parse_api_response_task_dept_project_alpha.py
from prefect import task, get_run_logger
from typing import Any, Optional, Dict

from airnub_prefect_starter.core.api_handlers import core_parse_api_response_for_demo

@task(name="Parse API Response (Project Alpha)", log_prints=True)
async def parse_api_response_task(
    response_data: Dict[str, Any],
    primary_key: str = "fact",
    # config: Optional[Dict[str, Any]] = None # Example if task-specific config needed
) -> Optional[Dict[str, Any]]:
    """
    Prefect task wrapper for parsing API JSON responses.
    Calls core_parse_api_response_for_demo from api_handlers.py.
    """
    logger = get_run_logger()
    logger.info(f"Starting task 'Parse API Response'. Primary key to look for: '{primary_key}'.")

    if not response_data or not isinstance(response_data, dict):
        logger.warning("Invalid or empty response_data provided for parsing. Returning None.")
        return None

    parsed_result = None
    try:
        parsed_result = core_parse_api_response_for_demo(response_data=response_data, primary_key=primary_key)
        if parsed_result:
            logger.info(f"Successfully parsed API response. Extracted: {list(parsed_result.keys())}")
        else:
            logger.warning("Parsing API response did not yield a result.")
    except Exception as e:
        logger.error(f"Error during task 'Parse API Response': {e}", exc_info=True)
        raise # Re-raise to fail the task run

    logger.info("Finished task 'Parse API Response'.")
    return parsed_result