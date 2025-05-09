# flows/dept_project_alpha/ingestion/web_page_link_scraping/ingest_web_page_link_scraping_flow_dept_project_alpha.py
import asyncio
from prefect import flow, get_run_logger, tags
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging # For module-level logging

# --- Import category-specific tasks ---
TASKS_AVAILABLE = False
module_level_logger = logging.getLogger(__name__)
try:
    from .tasks import (
        fetch_html_content_of_web_page_task,
        extract_links_from_html_content_task,
        create_scrape_artifact_task
    )
    TASKS_AVAILABLE = True
except ImportError as e:
    module_level_logger.error(f"Failed to import necessary tasks for web_page_link_scraping flow: {e}", exc_info=True)
# --- End Imports ---


@flow(name="Ingest Web Page Link Scraping (Project Alpha)", log_prints=True)
async def ingest_web_page_link_scraping_flow_dept_project_alpha(
    config: Optional[Dict[str, Any]] = None,
):
    logger = get_run_logger()
    logger.info(f"Starting Ingest Web Page Link Scraping (Project Alpha)...")

    if not TASKS_AVAILABLE:
        logger.error("Cannot proceed: Required task modules failed to import.")
        return {"status": "FAILED_IMPORT", "reason": "Missing required tasks"}

    if not config:
        logger.error("No configuration provided to flow. Cannot proceed.")
        return {"status": "FAILED", "reason": "Missing configuration"}

    pages_to_scrape = config.get("pages_to_scrape", [])
    data_source_name = config.get("data_source_name", "project_alpha_web_pages_demo")
    local_manifests_base_str = config.get("local_manifests_storage_base", "/app/local_demo_artifacts/web_scrape_manifests")
    local_manifests_target_base_dir = Path(local_manifests_base_str) # This is correctly a Path object

    if not isinstance(pages_to_scrape, list) or not pages_to_scrape:
        logger.warning("No pages configured in 'pages_to_scrape' list. Exiting.")
        return {"status": "COMPLETED_NO_PAGES", "message": "No pages configured to scrape"}

    base_tags = ['dept_project_alpha', 'ingestion', 'web_page_link_scraping']
    page_results_summary = [] # To store summary of each page processing
    artifact_task_futures = []

    with tags(*base_tags):
        logger.info(f"Applying tags to context: {base_tags}")
        logger.info(f"Found {len(pages_to_scrape)} page(s) to scrape.")

        for page_config in pages_to_scrape:
            page_name_display = page_config.get("name", "Unnamed Page")
            page_url = page_config.get("url")
            current_page_result = {"page_name": page_name_display, "url": page_url}

            if not page_url:
                logger.warning(f"Skipping '{page_name_display}': Missing 'url' in configuration.")
                current_page_result.update({"status": "SKIPPED", "reason": "Missing URL"})
                page_results_summary.append(current_page_result)
                continue

            logger.info(f"Processing page: '{page_name_display}' from {page_url}")
            try:
                html_content = await fetch_html_content_of_web_page_task(url=page_url)
                current_page_result["fetch_status"] = "SUCCESS" if html_content else "FAILED_NO_CONTENT"

                if html_content:
                    scrape_result_dict = await extract_links_from_html_content_task(
                        html_content=html_content,
                        original_page_url=page_url
                    )
                    current_page_result["extract_status"] = scrape_result_dict.get("status", "UNKNOWN")
                    current_page_result["extracted_links_count"] = len(scrape_result_dict.get("extracted_links", []))
                    current_page_result["canonical_url"] = scrape_result_dict.get("canonical_url")


                    if scrape_result_dict and scrape_result_dict.get("status") == "SUCCESS":
                        logger.info(f"Successfully extracted data for '{page_name_display}'. Links: {current_page_result['extracted_links_count']}")
                        
                        # Call the artifact task
                        # Ensure parameter name matches task definition
                        future = create_scrape_artifact_task(
                            scrape_result=scrape_result_dict,
                            target_base_dir_for_manifest=local_manifests_target_base_dir, # <--- CORRECTED PARAMETER NAME
                            data_source_id=data_source_name
                        )
                        artifact_task_futures.append(future)
                        logger.info(f"Submitted scrape artifact/manifest creation for '{page_name_display}'.")
                        current_page_result["artifact_submission_status"] = "SUBMITTED"
                    else:
                        logger.warning(f"Extracting links did not complete successfully for page: '{page_name_display}'. Result: {scrape_result_dict}")
                        current_page_result["artifact_submission_status"] = "SKIPPED_EXTRACT_FAILED"
                else:
                    logger.warning(f"Fetching HTML failed for page: '{page_name_display}' (html_content is None). Skipping extract and artifact.")
                    current_page_result["extract_status"] = "SKIPPED_NO_HTML"
                    current_page_result["artifact_submission_status"] = "SKIPPED_NO_HTML"

                page_results_summary.append(current_page_result)

            except Exception as e:
                logger.error(f"Error processing page '{page_name_display}': {e}", exc_info=True)
                current_page_result.update({"status": "ERROR_IN_PROCESSING", "reason": str(e)})
                page_results_summary.append(current_page_result)


        if artifact_task_futures:
            logger.info(f"Waiting for {len(artifact_task_futures)} scrape artifact creation task(s) to complete...")
            artifact_outcomes = await asyncio.gather(*artifact_task_futures, return_exceptions=True)
            logger.info("Scrape artifact creation task(s) finished.")
            for i, outcome in enumerate(artifact_outcomes):
                if isinstance(outcome, Exception):
                    logger.error(f"Scrape artifact creation task {i+1} resulted in an exception: {outcome}", exc_info=outcome)
                elif outcome is not None: # If task returns manifest path
                    logger.info(f"Scrape artifact task {i+1} completed, local manifest path: {outcome}")


    overall_status = "COMPLETED"
    # Add logic to determine overall_status based on page_results_summary if needed
    has_errors = any(res.get("status") == "ERROR_IN_PROCESSING" for res in page_results_summary)
    if has_errors:
        overall_status = "COMPLETED_WITH_ERRORS"

    logger.info(f"Finished Ingest Web Page Link Scraping (Project Alpha). Overall status: {overall_status}")
    return {"status": overall_status, "scraped_pages_summary": page_results_summary}