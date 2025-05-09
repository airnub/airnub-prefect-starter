# flows/dept_project_alpha/ingestion/public_api_data/tasks/create_api_data_artifact_task_dept_project_alpha.py
from prefect import task, get_run_logger
from prefect.artifacts import create_markdown_artifact
from typing import Any, Optional, Dict
from datetime import datetime
import json

# Import your sanitize_filename utility
from airnub_prefect_starter.common.utils import sanitize_filename # Adjust path if your common utils are elsewhere

@task(name="Create API Data Artifact (Project Alpha)", log_prints=True)
async def create_api_data_artifact_task(
    api_name: str,
    api_url: str,
    parsed_data: Optional[Dict[str, Any]],
    data_source_name: str, # Passed from category flow config
    # config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Prefect task wrapper for creating a markdown artifact for polled API data.
    This task directly uses Prefect's create_markdown_artifact.
    If artifact creation fails, this task will enter a Failed state.
    """
    logger = get_run_logger()
    logger.info(f"Starting task 'Create API Data Artifact' for API: {api_name}")

    if not parsed_data:
        logger.warning(f"No parsed data provided for API '{api_name}'. Skipping artifact creation.")
        return # Successfully did nothing, task completes

    # Sanitize components for the artifact key
    # Prefect artifact keys must only contain lowercase letters, numbers, and dashes.
    safe_data_source_name_part = sanitize_filename(data_source_name.lower(), default_name="datasource")
    safe_api_name_part = sanitize_filename(api_name.lower(), default_name="api")

    # Further ensure only valid characters for artifact keys if sanitize_filename is too broad
    # Example: remove anything not alphanumeric or dash, and ensure no leading/trailing dashes
    def _clean_for_key(name_part: str) -> str:
        # Replace spaces and underscores with dashes first
        cleaned = name_part.replace(' ', '-').replace('_', '-')
        # Keep only lowercase alphanumeric and dashes
        cleaned = ''.join(c for c in cleaned if c.isalnum() or c == '-')
        # Remove consecutive dashes
        while '--' in cleaned:
            cleaned = cleaned.replace('--', '-')
        return cleaned.strip('-')

    key_ds_name = _clean_for_key(safe_data_source_name_part)
    key_api_name = _clean_for_key(safe_api_name_part)

    timestamp_utc_iso_date = datetime.utcnow().isoformat().split('T')[0]
    artifact_key = f"api-poll-{key_ds_name}-{key_api_name}-{timestamp_utc_iso_date}"

    # Optional: Truncate key if it's too long (Prefect might have a limit, e.g., 255)
    max_key_length = 200 # Adjust as needed
    if len(artifact_key) > max_key_length:
        # Simple truncation; consider a hashing mechanism for very long/dynamic parts if collisions are a concern
        artifact_key = artifact_key[:max_key_length]
        logger.warning(f"Artifact key was truncated to: {artifact_key}")


    markdown_lines = [
        f"### API Data Polled: **{api_name}**",
        f"- **Data Source:** `{data_source_name}`",
        f"- **API URL:** `{api_url}`",
        f"- **Poll Timestamp (UTC):** `{datetime.utcnow().isoformat()}Z`", # Full timestamp for display
        f"\n#### Parsed Data:\n```json\n{json.dumps(parsed_data, indent=2)}\n```"
    ]

    try:
        logger.info(f"Attempting to create markdown artifact with key: {artifact_key}")
        await create_markdown_artifact(
            key=artifact_key,
            markdown="\n".join(markdown_lines),
            description=f"Summary of data polled from API: {api_name} for {data_source_name}"
        )
        logger.info(f"Successfully created markdown artifact: {artifact_key}")

    except Exception as e: # Catch any exception during artifact creation
        logger.error(f"Error creating API data artifact with key '{artifact_key}' for API '{api_name}': {e}", exc_info=True)
        raise # <--- RE-RAISE THE EXCEPTION to fail the task
        # Do not re-raise if artifact creation is non-critical
        # depends on your requirements.

    logger.info(f"Finished task 'Create API Data Artifact' for {api_name}.")