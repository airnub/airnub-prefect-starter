# flows/dept_project_alpha/ingestion/scheduled_file_downloads/tasks/download_file_task_dept_project_alpha.py
from prefect import task, get_run_logger
from typing import Any, Optional, Dict
from pathlib import Path

from airnub_prefect_starter.core.file_handlers import core_process_scheduled_file_download

@task(name="Process Scheduled File Download (Project Alpha)", log_prints=True, retries=1, retry_delay_seconds=30)
async def download_file_task(
    url: str,
    data_source_name: str,
    local_cas_target_base_dir: Path,
    # config: Optional[Dict[str, Any]] = None, # e.g. for file_context
    # file_context: Optional[Dict[str, Any]] = None # To pass original 'name', 'link_title' etc. if core logic is extended
) -> Dict[str, Any]:
    """
    Prefect task wrapper for downloading, hashing, storing a file, and creating its local JSON manifest.
    Calls core_process_scheduled_file_download from file_handlers.py.
    """
    logger = get_run_logger()
    logger.info(f"Starting task 'Process Scheduled File Download' for URL: {url}")
    logger.info(f"Data Source: {data_source_name}, Target Base Dir: {local_cas_target_base_dir}")

    processing_result: Dict[str, Any] = {}
    try:
        processing_result = await core_process_scheduled_file_download(
            url=url,
            data_source_name=data_source_name,
            local_cas_target_base_dir=local_cas_target_base_dir
            # Pass file_context if core logic uses it
        )
        if processing_result.get("status") == "SUCCESS":
            logger.info(f"Successfully processed file download for URL: {url}. Path: {processing_result.get('worker_storage_path')}")
        else:
            logger.warning(f"File download processing failed or did not complete for {url}. Status: {processing_result.get('status')}")

    except Exception as e:
        logger.error(f"Error during task 'Process Scheduled File Download' for {url}: {e}", exc_info=True)
        # Return a failure dictionary consistent with core_process_scheduled_file_download
        return {
            "status": "TASK_EXCEPTION",
            "url": url,
            "data_source_name": data_source_name,
            "error_message": str(e)
        }

    logger.info(f"Finished task 'Process Scheduled File Download' for {url}.")
    return processing_result # This dict contains status, paths, hash, etc.