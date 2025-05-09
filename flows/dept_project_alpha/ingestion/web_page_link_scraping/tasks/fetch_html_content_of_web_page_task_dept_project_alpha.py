# flows/dept_project_alpha/ingestion/web_page_link_scraping/tasks/fetch_html_content_of_web_page_task_dept_project_alpha.py
from prefect import task, get_run_logger
from typing import Any, Optional, Dict

from airnub_prefect_starter.core.web_utils import core_fetch_html_content

@task(name="Fetch HTML Content of Web Page (Project Alpha)", log_prints=True, retries=1, retry_delay_seconds=15)
async def fetch_html_content_of_web_page_task(
    url: str,
    # config: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Prefect task wrapper for fetching HTML content of a web page.
    Calls core_fetch_html_content from web_utils.py.
    """
    logger = get_run_logger()
    logger.info(f"Starting task 'Fetch HTML Content of Web Page' for URL: {url}")

    html_content: Optional[str] = None
    try:
        html_content = await core_fetch_html_content(url=url)
        if html_content:
            logger.info(f"Successfully fetched HTML from {url} (length: {len(html_content)}).")
        else:
            logger.warning(f"Failed to fetch HTML or no content returned from {url}.")
    except Exception as e:
        logger.error(f"Error during task 'Fetch HTML Content of Web Page' for {url}: {e}", exc_info=True)
        raise # Re-raise to fail the task run

    logger.info(f"Finished task 'Fetch HTML Content of Web Page' for {url}.")
    return html_content