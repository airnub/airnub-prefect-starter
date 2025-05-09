# flows/dept_project_alpha/ingestion/web_page_link_scraping/tasks/__init__.py

from .fetch_html_content_of_web_page_task_dept_project_alpha import fetch_html_content_of_web_page_task
from .extract_links_from_html_content_task_dept_project_alpha import extract_links_from_html_content_task
from .create_scrape_artifact_task_dept_project_alpha import create_scrape_artifact_task

__all__ = [
    "fetch_html_content_of_web_page_task",
    "extract_links_from_html_content_task",
    "create_scrape_artifact_task",
]