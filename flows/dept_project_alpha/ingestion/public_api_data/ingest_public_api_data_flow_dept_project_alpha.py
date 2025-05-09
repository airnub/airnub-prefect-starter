# flows/dept_project_alpha/ingestion/public_api_data/ingest_public_api_data_flow_dept_project_alpha.py
import asyncio
from prefect import flow, get_run_logger, tags
from typing import Dict, Any, Optional, List

# --- Import category-specific tasks ---
# These imports should now succeed if the __init__.py in ./tasks/ is correct
try:
    from .tasks import (
        fetch_data_from_public_api_task,
        parse_api_response_task,
        create_api_data_artifact_task # Ensure this is imported
    )
    TASKS_AVAILABLE = True
except ImportError as e:
    logger = get_run_logger()
    logger.error(f"Failed to import necessary tasks for public_api_data flow: {e}", exc_info=True)
    TASKS_AVAILABLE = False
# --- End Imports ---

@flow(name="Ingest Public API Data (Project Alpha)", log_prints=True)
async def ingest_public_api_data_flow_dept_project_alpha(
    config: Optional[Dict[str, Any]] = None,
):
    """
    Flow for ingesting data related to the 'Public API Data' category
    within Project Alpha. Fetches data from configured APIs, parses responses,
    and potentially creates summary artifacts.

    Typically called by the parent 'Ingestion Flow (Project Alpha)'.
    Receives its specific configuration section from the parent.
    Applies 'dept_project_alpha', 'ingestion', and 'public_api_data' tags to child runs.
    """
    logger = get_run_logger() # logger defined at the start of the flow
    logger.info(f"Starting Ingest Public API Data (Project Alpha)...")

    if not TASKS_AVAILABLE: # Check if all tasks are available
        logger.error("Cannot proceed: Required task modules failed to import.")
        return {"status": "FAILED", "reason": "Missing required tasks"}

    if not config:
        logger.error("No configuration provided to flow. Cannot proceed.")
        return {"status": "FAILED", "reason": "Missing configuration"}

    apis_to_poll = config.get("apis_to_poll", [])
    data_source_name = config.get("data_source_name", "project_alpha_public_apis_demo")

    if not isinstance(apis_to_poll, list) or not apis_to_poll:
        logger.warning("No APIs configured in 'apis_to_poll' list. Exiting.")
        return {"status": "COMPLETED", "message": "No APIs configured to poll"}

    base_tags = ['dept_project_alpha', 'ingestion', 'public_api_data']
    api_results = []
    artifact_creation_tasks = []


    # Wrap the main logic with tags
    with tags(*base_tags):
        logger.info(f"Applying tags to context: {base_tags}")
        logger.info(f"Found {len(apis_to_poll)} API(s) to poll.")

        # Process each API sequentially for simplicity in demo
        # Use asyncio.gather if concurrent processing of multiple APIs is desired
        for api_config in apis_to_poll:
            api_name = api_config.get("name", "Unnamed API")
            api_url = api_config.get("url")
            api_params = api_config.get("params")
            extract_key = api_config.get("extract_key", "fact") # Default relevant for demo APIs

            if not api_url:
                logger.warning(f"Skipping '{api_name}': Missing 'url' in configuration.")
                api_results.append({"api_name": api_name, "status": "SKIPPED", "reason": "Missing URL"})
                continue

            logger.info(f"Processing API: '{api_name}' ({api_url})")
            try:
                # 1. Fetch Data
                # Assuming fetch task takes url and optional params
                raw_data = await fetch_data_from_public_api_task(
                    url=api_url,
                    params=api_params,
                    # Pass task-specific config if needed: config=api_config.get("fetch_task_config")
                )

                if raw_data:
                    # 2. Parse Response
                    # Assuming parse task takes the fetched data and the key to extract
                    parsed_result = await parse_api_response_task(
                        response_data=raw_data,
                        primary_key=extract_key,
                        # Pass task-specific config if needed: config=api_config.get("parse_task_config")
                    )

                    # --- Uncommented and activated artifact creation ---
                    if parsed_result: # Only create artifact if parsing was successful
                        # Use .submit() for non-blocking artifact creation
                        artifact_task_future = create_api_data_artifact_task(
                            api_name=api_name,
                            api_url=api_url,
                            parsed_data=parsed_result,
                            data_source_name=data_source_name
                        )
                        artifact_creation_tasks.append(artifact_task_future)
                        logger.info(f"Submitted artifact creation for '{api_name}'.")
                    # --- End artifact creation ---

                    api_results.append({"api_name": api_name, "status": "SUCCESS", "parsed_data": parsed_result})
                else:
                    logger.warning(f"Fetching data failed for API: '{api_name}'")
                    api_results.append({"api_name": api_name, "status": "FETCH_FAILED"})

            except Exception as e:
                logger.error(f"Error processing API '{api_name}': {e}", exc_info=True)
                api_results.append({"api_name": api_name, "status": "ERROR", "reason": str(e)})
        
        if artifact_creation_tasks:
            logger.info(f"Waiting for {len(artifact_creation_tasks)} API data artifact creation tasks to complete...")
            await asyncio.gather(*artifact_creation_tasks, return_exceptions=True)
            logger.info("API data artifact creation tasks finished.")


    logger.info(f"Finished Ingest Public API Data (Project Alpha).")
    return {"status": "COMPLETED", "processed_apis": api_results}