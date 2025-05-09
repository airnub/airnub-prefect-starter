# flows/dept_project_alpha/ingestion/tasks/create_ingestion_summary_artifact_task_dept_project_alpha.py
from prefect import task, get_run_logger
from prefect.artifacts import create_markdown_artifact
from typing import Dict, Any, List
from datetime import datetime
from airnub_prefect_starter.common.utils import sanitize_filename

@task(name="Create Ingestion Summary Artifact (Project Alpha)", log_prints=True)
async def create_ingestion_summary_artifact_task(
    flow_name: str,
    subflow_results: Dict[str, Any],
    config_variable_name: str
) -> None:
    logger = get_run_logger() # Moved inside
    logger.info(f"Starting task 'Create Ingestion Summary Artifact' for flow: {flow_name}")

    timestamp_utc_iso = datetime.utcnow().isoformat() + "Z"
    # Sanitize the flow_name part for the artifact key
    sanitized_flow_name_part = sanitize_filename(flow_name.lower(), default_name="flow")
    # Ensure it doesn't create problematic path characters if sanitize_filename also handles paths
    # A simple replace might be safer if sanitize_filename is too aggressive for this key
    # A more targeted sanitization for artifact keys:
    key_flow_name_part = flow_name.lower().replace(' ', '-').replace('(', '').replace(')', '')
    # Remove any remaining non-alphanumeric except dash
    key_flow_name_part = ''.join(c for c in key_flow_name_part if c.isalnum() or c == '-')
    key_flow_name_part = key_flow_name_part.strip('-') # Remove leading/trailing dashes

    artifact_key = f"ingestion-summary-{key_flow_name_part}-{timestamp_utc_iso.split('T')[0]}"
    # Limit key length if necessary, Prefect might have a limit (e.g., 255 chars)
    max_key_length = 200 # Example limit
    if len(artifact_key) > max_key_length:
        artifact_key = artifact_key[:max_key_length]


    markdown_lines = [
        f"## Ingestion Summary: {flow_name}",
        f"- **Overall Status:** `{subflow_results.get('status', 'UNKNOWN')}`",
        f"- **Run Timestamp (UTC):** `{timestamp_utc_iso}`",
        f"- **Configuration Variable Used:** `{config_variable_name}`",
    ]

    details = subflow_results.get("details")
    if isinstance(details, list):
        markdown_lines.append("\n### Category Details:")
        for i, detail_item in enumerate(details): # Renamed detail to detail_item
            if isinstance(detail_item, dict): # Use detail_item
                category_status = detail_item.get('status', 'INFO')
                category_name = "Unknown Category"
                # Attempt to infer category from typical result structures
                if "processed_apis" in detail_item and detail_item["processed_apis"]:
                    category_name = f"Public API Data ({len(detail_item['processed_apis'])} APIs)"
                elif "processed_files" in detail_item and detail_item["processed_files"]:
                    category_name = f"Scheduled File Downloads ({len(detail_item['processed_files'])} files)"
                elif "scraped_pages" in detail_item and detail_item["scraped_pages"]:
                    category_name = f"Web Page Link Scraping ({len(detail_item['scraped_pages'])} pages)"
                elif "category" in detail_item: # Fallback if category flow returns its name
                    category_name = detail_item["category"]
                elif "api_name" in detail_item: # For API polling results if directly appended
                    category_name = f"API: {detail_item['api_name']}"
                elif "file_name" in detail_item: # For file download results if directly appended
                    category_name = f"File: {detail_item['file_name']}"
                elif "page_name" in detail_item: # For web scrape results if directly appended
                    category_name = f"Page: {detail_item['page_name']}"


                markdown_lines.append(f"- **Sub-flow Item {i+1} ({category_name}):** Status `{category_status}`")
                if "error" in detail_item:
                    markdown_lines.append(f"  - Error: `{detail_item['error']}`")
                elif "reason" in detail_item: # Also log reason if status is FAILED/SKIPPED
                    markdown_lines.append(f"  - Reason: `{detail_item['reason']}`")
            else:
                 markdown_lines.append(f"- **Sub-flow Item {i+1}:** `{str(detail_item)}`")

    else:
        markdown_lines.append(f"- No detailed sub-flow results provided or in expected format. Raw details: {details}")


    try:
        logger.info(f"Attempting to create markdown artifact with key: {artifact_key}")
        await create_markdown_artifact(
            key=artifact_key,
            markdown="\n".join(markdown_lines),
            description=f"Summary of the {flow_name} execution."
        )
        logger.info(f"Successfully created ingestion summary artifact: {artifact_key}")
    except Exception as e:
        logger.error(f"Error creating ingestion summary artifact with key '{artifact_key}': {e}", exc_info=True)
        raise # <--- RE-RAISE THE EXCEPTION to fail the task
        # Do not re-raise if artifact creation is non-critical
        # depends on your requirements.

    logger.info(f"Finished task 'Create Ingestion Summary Artifact'.")