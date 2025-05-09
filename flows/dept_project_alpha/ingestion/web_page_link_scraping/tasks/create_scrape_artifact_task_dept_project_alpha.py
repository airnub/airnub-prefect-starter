# flows/dept_project_alpha/ingestion/web_page_link_scraping/tasks/create_scrape_artifact_task_dept_project_alpha.py
from prefect import task, get_run_logger
from typing import Any, Optional, Dict
from pathlib import Path

from airnub_prefect_starter.core.artifact_creators import (
    save_scraped_page_manifest_locally,
    core_create_scraped_page_artifact
)

@task(name="Create Scraped Page Manifest and Artifact (Project Alpha)", log_prints=True)
async def create_scrape_artifact_task(
    scrape_result: Dict[str, Any], # Output from extract_links_from_html_content_task
    target_base_dir_for_manifest: Path, # For local JSON manifest, e.g., /app/local_demo_artifacts/web_scrape_manifests
    data_source_id: str, # For manifest path and artifact keying
    # config: Optional[Dict[str, Any]] = None # If task-specific config was ever needed
) -> Optional[Path]: # Returns path to local manifest or None
    """
    Prefect task to:
    1. Save a local JSON manifest for scraped page data.
    2. Create a Prefect Markdown artifact that includes content from this manifest.
    Calls save_scraped_page_manifest_locally and core_create_scraped_page_artifact.
    """
    logger = get_run_logger()
    original_url = scrape_result.get('original_url', 'N/A')
    logger.info(f"Starting task 'Create Scraped Page Manifest and Artifact' for page: {original_url}")

    if not scrape_result or scrape_result.get("status") != "SUCCESS": # Check original scrape status
        logger.warning(f"Skipping manifest/artifact for '{original_url}': initial scrape metadata indicates failure or missing data.")
        # Optionally raise an error if scrape_result must be successful
        # raise ValueError("Scrape result indicates failure, cannot create manifest/artifact.")
        return None

    local_manifest_path: Optional[Path] = None
    try:
        # 1. Save the local JSON manifest first
        logger.info(f"Attempting to save local scrape manifest for '{original_url}' in base directory '{target_base_dir_for_manifest}'.")
        local_manifest_path = save_scraped_page_manifest_locally(
            scrape_result=scrape_result,
            target_base_dir=target_base_dir_for_manifest,
            data_source_id=data_source_id
        )

        if local_manifest_path:
            logger.info(f"Local scrape manifest saved to: {local_manifest_path}")
            # 2. Now, create the Prefect UI Markdown artifact, passing the path to the manifest
            await core_create_scraped_page_artifact(
                scrape_result=scrape_result,
                data_source_name=data_source_id,
                local_manifest_path=local_manifest_path # Pass the path of the just-created manifest
            )
            logger.info(f"Successfully called core function to create scrape artifact for '{original_url}'.")
        else:
            logger.error(f"Failed to save local scrape manifest for '{original_url}'. Cannot proceed to create full artifact.")
            # Decide if this is a critical failure for the task
            raise RuntimeError(f"Failed to save local manifest for {original_url}, artifact creation aborted.")

    except Exception as e:
        logger.error(f"Task 'Create Scraped Page Manifest and Artifact' failed for '{original_url}': {e}", exc_info=True)
        raise # Re-raise to make this task instance fail

    logger.info(f"Finished task 'Create Scraped Page Manifest and Artifact' for {original_url}.")
    return local_manifest_path # Return the path to the manifest file