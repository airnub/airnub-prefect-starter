# flows/dept_project_alpha/ingestion/scheduled_file_downloads/ingest_scheduled_file_downloads_flow_dept_project_alpha.py
import asyncio
from prefect import flow, get_run_logger, tags
from typing import Dict, Any, Optional, List
from pathlib import Path # Import Path

# --- Import category-specific tasks ---
try:
    # Assuming download_file_task wraps core_process_scheduled_file_download
    from .tasks.download_file_task_dept_project_alpha import download_file_task
    # Assuming create_manifest_archive_task wraps core_create_file_download_artifact
    from .tasks.create_manifest_archive_task_dept_project_alpha import create_manifest_archive_task
    TASKS_AVAILABLE = True
except ImportError as e:
    logger = get_run_logger()
    logger.error(f"Failed to import necessary tasks for scheduled_file_downloads flow: {e}", exc_info=True)
    TASKS_AVAILABLE = False
# --- End Imports ---


@flow(name="Ingest Scheduled File Downloads (Project Alpha)", log_prints=True)
async def ingest_scheduled_file_downloads_flow_dept_project_alpha(
    config: Optional[Dict[str, Any]] = None,
):
    """
    Flow for ingesting data related to the 'Scheduled File Downloads' category
    within Project Alpha. Downloads files, calculates hashes, stores locally,
    creates local JSON manifests, and creates Prefect UI artifacts.

    Typically called by the parent 'Ingestion Flow (Project Alpha)'.
    Receives its specific configuration section from the parent.
    Applies 'dept_project_alpha', 'ingestion', and 'scheduled_file_downloads' tags to child runs.
    """
    logger = get_run_logger()
    logger.info(f"Starting Ingest Scheduled File Downloads (Project Alpha)...")

    if not TASKS_AVAILABLE:
        logger.error("Cannot proceed: Required task modules failed to import.")
        return {"status": "FAILED", "reason": "Missing required tasks"}

    if not config:
        logger.error("No configuration provided to flow. Cannot proceed.")
        return {"status": "FAILED", "reason": "Missing configuration"}

    # --- Extract Configuration ---
    files_to_acquire = config.get("files_to_acquire", [])
    data_source_name = config.get("data_source_name", "project_alpha_demo_files")
    # Get base path for local CAS storage from config, default if necessary
    local_cas_base_str = config.get("local_artifacts_storage_base", "/app/local_demo_artifacts/downloads")
    local_cas_target_base_dir = Path(local_cas_base_str)
    # ---

    if not isinstance(files_to_acquire, list) or not files_to_acquire:
        logger.warning("No files configured in 'files_to_acquire' list. Exiting.")
        return {"status": "COMPLETED", "message": "No files configured to acquire"}

    base_tags = ['dept_project_alpha', 'ingestion', 'scheduled_file_downloads']
    file_results = []
    artifact_tasks_to_wait = [] # For submitted artifact tasks

    # Wrap the main logic with tags
    with tags(*base_tags):
        logger.info(f"Applying tags to context: {base_tags}")
        logger.info(f"Found {len(files_to_acquire)} file(s) to acquire.")

        # Process each file sequentially for simplicity in demo
        for file_config in files_to_acquire:
            file_name_display = file_config.get("name", "Unnamed File")
            file_url = file_config.get("url")

            if not file_url:
                logger.warning(f"Skipping '{file_name_display}': Missing 'url' in configuration.")
                file_results.append({"file_name": file_name_display, "status": "SKIPPED", "reason": "Missing URL"})
                continue

            logger.info(f"Processing file: '{file_name_display}' from {file_url}")
            try:
                # 1. Process Download (includes download, hash, store, manifest JSON)
                # Assuming download_file_task wraps core_process_scheduled_file_download
                # and takes url, data_source_name, local_cas_target_base_dir as args
                processing_result = await download_file_task(
                    url=file_url,
                    data_source_name=data_source_name,
                    local_cas_target_base_dir=local_cas_target_base_dir,
                    # Optional: pass file_config if task needs more context like link_title
                    # file_context=file_config
                )

                if processing_result and processing_result.get("status") == "SUCCESS":
                    logger.info(f"Successfully processed download for '{file_name_display}'. Result: {processing_result}")
                    file_results.append(processing_result) # Store the full result dict

                    # 2. Create Prefect Artifact
                    # Assuming create_manifest_archive_task wraps core_create_file_download_artifact
                    # Use .submit() for artifact creation as it's often non-critical for main flow path
                    artifact_future = create_manifest_archive_task(
                        processing_result=processing_result
                    )
                    artifact_tasks_to_wait.append(artifact_future) # Collect future if needed

                else:
                    logger.warning(f"Processing download failed for file: '{file_name_display}'. Result: {processing_result}")
                    # Append result even if failed, as it contains status/error info
                    file_results.append(processing_result if processing_result else {"file_name": file_name_display, "url": file_url, "status": "PROCESS_FAILED", "reason": "Task returned None or failure status"})

            except Exception as e:
                logger.error(f"Error processing file '{file_name_display}': {e}", exc_info=True)
                file_results.append({"file_name": file_name_display, "url": file_url, "status": "ERROR", "reason": str(e)})

        # Optionally wait for artifact tasks if their completion is important before flow ends
        if artifact_tasks_to_wait:
            logger.info(f"Waiting for {len(artifact_tasks_to_wait)} artifact creation tasks...")
            # This gather is mainly to ensure they complete before the flow ends,
            # results might not be critical unless error handling is needed.
            await asyncio.gather(*artifact_tasks_to_wait, return_exceptions=True)
            logger.info("Artifact creation tasks finished.")


    logger.info(f"Finished Ingest Scheduled File Downloads (Project Alpha).")
    # Return summary of results for each file attempted
    return {"status": "COMPLETED", "processed_files": file_results}