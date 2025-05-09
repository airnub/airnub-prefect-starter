# flows/dept_project_alpha/ingestion/public_api_data/tasks/fetch_data_from_public_api_task_dept_project_alpha.py
from prefect import task, get_run_logger
from typing import Any, Optional, Dict

from airnub_prefect_starter.core.api_handlers import core_fetch_json_from_api

@task(name="Fetch Data From Public API (Project Alpha)", log_prints=True, retries=2, retry_delay_seconds=10)
async def fetch_data_from_public_api_task(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    # config: Optional[Dict[str, Any]] = None # Example if task-specific config needed
) -> Optional[Dict[str, Any]]:
    """
    Prefect task wrapper for fetching JSON data from a public API.
    Calls core_fetch_json_from_api from api_handlers.py.
    """
    logger = get_run_logger()
    logger.info(f"Starting task 'Fetch Data From Public API' for URL: {url} with params: {params}")

    result = None
    try:
        result = await core_fetch_json_from_api(url=url, params=params)
        if result:
            logger.info(f"Successfully fetched data from API: {url}")
        else:
            logger.warning(f"No data returned or failed to fetch from API: {url}")
    except Exception as e:
        logger.error(f"Error during task 'Fetch Data From Public API' for {url}: {e}", exc_info=True)
        raise # Re-raise to fail the task run

    logger.info(f"Finished task 'Fetch Data From Public API' for {url}.")
    return result