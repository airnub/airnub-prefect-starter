# flows/dept_project_alpha/ingestion/scheduled_file_downloads/tasks/create_manifest_archive_task_dept_project_alpha.py
from prefect import task, get_run_logger
from typing import Any, Optional, Dict

# Import the core function that creates the artifact AND includes manifest content
from airnub_prefect_starter.core.artifact_creators import core_create_file_download_artifact

@task(name="Create File Download Artifact with Manifest (Project Alpha)", log_prints=True)
async def create_manifest_archive_task(
    processing_result: Dict[str, Any], # This dict comes from download_file_task (core_process_scheduled_file_download)
                                      # and should contain 'worker_manifest_path'
    # config: Optional[Dict[str, Any]] = None # If task-specific config was ever needed
) -> None:
    """
    Prefect task wrapper for creating a Prefect Markdown artifact for a processed file,
    including content from its local JSON manifest.
    Calls core_create_file_download_artifact from artifact_creators.py.
    """
    logger = get_run_logger()
    original_filename = processing_result.get('original_filename', 'N/A')
    logger.info(f"Starting task 'Create File Download Artifact with Manifest' for: {original_filename}")

    if not processing_result or processing_result.get("status") != "SUCCESS":
        logger.warning(f"Skipping artifact creation for '{original_filename}': download processing metadata indicates failure or missing data.")
        # Optionally, you could raise an error here if this is unexpected
        # raise ValueError("Processing result indicates failure, cannot create artifact.")
        return

    if not processing_result.get('worker_manifest_path'):
        logger.error(f"Cannot create artifact for '{original_filename}': 'worker_manifest_path' missing in processing_result.")
        # Decide if this should be a hard failure for the task
        raise ValueError(f"Missing 'worker_manifest_path' for {original_filename}, cannot create artifact with manifest content.")

    try:
        # This core function will now also handle reading the manifest and including its content
        await core_create_file_download_artifact(processing_result=processing_result)
        logger.info(f"Successfully called core function to create artifact for '{original_filename}'.")
    except Exception as e:
        logger.error(f"Task 'Create File Download Artifact with Manifest' failed for '{original_filename}' during core_create_file_download_artifact call: {e}", exc_info=True)
        raise # Re-raise to make this task instance fail

    logger.info(f"Finished task 'Create File Download Artifact with Manifest' for '{original_filename}'.")