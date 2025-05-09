# flows/dept_project_alpha/ingestion_flow_dept_project_alpha.py
import asyncio
import json
from prefect import flow, get_run_logger, variables, tags
from typing import List, Dict, Any, Optional, Coroutine

# --- Import category flows ---
# Direct imports - assumes these files/flows exist and are importable.
from .ingestion.public_api_data.ingest_public_api_data_flow_dept_project_alpha import ingest_public_api_data_flow_dept_project_alpha
from .ingestion.scheduled_file_downloads.ingest_scheduled_file_downloads_flow_dept_project_alpha import ingest_scheduled_file_downloads_flow_dept_project_alpha
from .ingestion.web_page_link_scraping.ingest_web_page_link_scraping_flow_dept_project_alpha import ingest_web_page_link_scraping_flow_dept_project_alpha
# --- End Category Imports ---

# --- Import stage-level tasks ---
SUMMARY_TASK_AVAILABLE = False # Default to False
try:
    # This task should reside in flows/dept_project_alpha/ingestion/tasks/
    from .ingestion.tasks import create_ingestion_summary_artifact_task
    SUMMARY_TASK_AVAILABLE = True
except ImportError:
    # get_run_logger might not be available at import time if not in a flow context
    # print("Warning: Summary artifact task not found. Skipping summary artifact creation.")
    pass # We'll log this inside the flow if needed
# --- End Stage Task Imports ---

@flow(name="Ingestion Flow (Project Alpha)", log_prints=True)
async def ingestion_flow_dept_project_alpha(
    config_variable_name: Optional[str] = "dept_project_alpha_ingestion_config",
    # --- Parameters to control category execution ---
    run_public_api_data: bool = True,
    run_scheduled_file_downloads: bool = True,
    run_web_page_link_scraping: bool = True,
):
    """
    Parent orchestrator flow for the ingestion stage for Project Alpha.
    Loads configuration, determines which category flows to run based on parameters,
    executes them concurrently, and creates a summary artifact.
    Applies 'dept_project_alpha' and 'ingestion' tags to child runs.
    """
    logger = get_run_logger()
    logger.info(f"Starting Ingestion Flow (Project Alpha)...")
    logger.info(f"Config Variable targeted: {config_variable_name}")
    base_tags = ['dept_project_alpha', 'ingestion']

    # This will be the overall result of the parent flow
    final_flow_result: Dict[str, Any] = {"status": "INITIATED", "details": []}

    with tags(*base_tags):
        logger.info(f"Applying tags to context: {base_tags}")
        main_config: Dict[str, Any] = {}
        if config_variable_name:
            try:
                config_value = await variables.Variable.get(config_variable_name, default=None)
                if config_value is not None:
                     config_dict = json.loads(config_value)
                     if isinstance(config_dict, dict):
                         main_config = config_dict
                         logger.info(f"Successfully loaded and parsed config Variable '{config_variable_name}'")
                     else:
                         logger.error(f"Config Variable '{config_variable_name}' did not contain a valid JSON dictionary.")
                else:
                     logger.info(f"Config Variable '{config_variable_name}' not found or value is None. Proceeding with empty config.")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from config Variable '{config_variable_name}': {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Failed to load config Variable '{config_variable_name}': {e}", exc_info=True)

        category_coroutines: List[Coroutine] = []

        if run_public_api_data:
            logger.info("Scheduling Public API Data flow...")
            sub_config = main_config.get("public_api_data", {})
            api_coro = ingest_public_api_data_flow_dept_project_alpha(config=sub_config)
            category_coroutines.append(api_coro)
        else:
            logger.info("Skipping Public API Data flow (run_public_api_data=False).")

        if run_scheduled_file_downloads:
            logger.info("Scheduling Scheduled File Downloads flow...")
            sub_config = main_config.get("scheduled_file_downloads", {})
            download_coro = ingest_scheduled_file_downloads_flow_dept_project_alpha(config=sub_config)
            category_coroutines.append(download_coro)
        else:
            logger.info("Skipping Scheduled File Downloads flow (run_scheduled_file_downloads=False).")

        if run_web_page_link_scraping:
            logger.info("Scheduling Web Page Link Scraping flow...")
            sub_config = main_config.get("web_page_link_scraping", {})
            scrape_coro = ingest_web_page_link_scraping_flow_dept_project_alpha(config=sub_config)
            category_coroutines.append(scrape_coro)
        else:
            logger.info("Skipping Web Page Link Scraping flow (run_web_page_link_scraping=False).")

        if not category_coroutines:
            logger.warning("No category flows scheduled to run for ingestion.")
            final_flow_result = {"status": "NO_SUBFLOWS_SCHEDULED", "details": []}
        else:
            logger.info(f"Waiting for {len(category_coroutines)} ingestion category flows...")
            results = await asyncio.gather(*category_coroutines, return_exceptions=True)
            logger.info(f"Ingestion category flows finished.")
            
            processed_results_list = []
            all_successful = True
            for i, res in enumerate(results):
                if isinstance(res, Exception):
                     logger.error(f"Subflow {i+1} failed: {res}", exc_info=res)
                     processed_results_list.append({"subflow_index": i+1, "status": "FAILED", "error": str(res)})
                     all_successful = False
                else:
                     logger.info(f"Subflow {i+1} completed. Result: {res}")
                     processed_results_list.append(res if isinstance(res, dict) else {"subflow_index": i+1, "result": res})
                     if isinstance(res, dict) and res.get("status", "").upper() not in ["COMPLETED", "SUCCESS", "COMPLETED_SUCCESSFULLY"]: # Adjusted status check
                         all_successful = False 

            final_flow_result["details"] = processed_results_list
            final_flow_result["status"] = "COMPLETED_WITH_ERRORS" if not all_successful else "COMPLETED_SUCCESSFULLY"
            

        # --- Call Summary Task/Artifact Creation ---
        if SUMMARY_TASK_AVAILABLE:
            logger.info("Submitting ingestion summary artifact creation...")
            create_ingestion_summary_artifact_task.submit(
                flow_name="Ingestion Flow (Project Alpha)",
                subflow_results=final_flow_result,
                config_variable_name=str(config_variable_name)
            ).wait()
        else:
            logger.warning("Summary artifact task not available (create_ingestion_summary_artifact_task). Skipping summary artifact.")
        # --- End Summary ---

    logger.info(f"Finished Ingestion Flow (Project Alpha). Overall Status: {final_flow_result['status']}")
    return final_flow_result