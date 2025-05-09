# flows/dept_project_alpha/ingestion/web_page_link_scraping/tasks/extract_links_from_html_content_task_dept_project_alpha.py
from prefect import task, get_run_logger
from typing import Any, Optional, Dict

from airnub_prefect_starter.core.web_utils import core_parse_links_and_canonical_from_html

@task(name="Extract Links from HTML Content (Project Alpha)", log_prints=True)
async def extract_links_from_html_content_task(
    html_content: str,
    original_page_url: str,
    # config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Prefect task wrapper for extracting links and canonical URL from HTML.
    Calls core_parse_links_and_canonical_from_html from web_utils.py.
    """
    logger = get_run_logger()
    logger.info(f"Starting task 'Extract Links from HTML Content' for page: {original_page_url}")

    if not html_content:
        logger.warning("No HTML content provided for parsing. Returning empty result.")
        return {
            "original_url": original_page_url,
            "canonical_url": None,
            "canonical_url_hash_sha256": None,
            "extracted_links": [],
            "status": "NO_HTML_PROVIDED"
        }

    parsed_result: Dict[str, Any] = {}
    try:
        parsed_result = core_parse_links_and_canonical_from_html(
            html_content=html_content,
            original_page_url=original_page_url
        )
        if parsed_result.get("status") == "SUCCESS":
            logger.info(f"Successfully parsed HTML for {original_page_url}. Found {len(parsed_result.get('extracted_links',[]))} links.")
        else:
            logger.warning(f"HTML parsing did not complete successfully for {original_page_url}. Status: {parsed_result.get('status')}")

    except Exception as e:
        logger.error(f"Error during task 'Extract Links from HTML Content' for {original_page_url}: {e}", exc_info=True)
        # Return a failure dictionary consistent with core_parse_links_and_canonical_from_html
        return {
            "original_url": original_page_url,
            "status": "TASK_EXCEPTION",
            "error_message": str(e),
            "extracted_links": [],
        }


    logger.info(f"Finished task 'Extract Links from HTML Content' for {original_page_url}.")
    return parsed_result