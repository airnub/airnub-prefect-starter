# Example Department: Project Alpha Overview

The "Project Alpha" department (`dept_project_alpha`) is included in this template as a practical, working example to demonstrate the core concepts, directory structure, naming conventions, and development patterns for building Prefect data pipelines.

It showcases how to:

* Structure flows by **Department -> Stage -> Category**.
* Create parent orchestrator flows for each stage (Ingestion, Processing, Analysis).
* Develop category-specific flows for different data sources or types within a stage.
* Implement department-specific Prefect task wrappers that call core logic functions.
* Manage configuration using YAML files for Prefect Variables.
* Utilize core logic functions from the main `airnub_prefect_starter` package.
* Generate local demo "manifests" (JSON files) and Prefect UI artifacts.

## Categories within "Project Alpha" (Ingestion Stage)

The `ingestion` stage of "Project Alpha" includes the following example categories to illustrate common data acquisition patterns:

1.  **Public API Data Polling (`public_api_data`):**
    * Demonstrates fetching data from simple public JSON APIs.
    * Includes tasks for fetching and parsing API responses.
    * Shows how to handle basic API interaction and data extraction.
    * See: [Project Alpha - API Polling Example](project-alpha-api-polling.md)

2.  **Scheduled File Downloads (`scheduled_file_downloads`):**
    * Illustrates downloading files from static URLs.
    * Includes tasks for downloading, content hashing, local "CAS-like" storage, and creating demo manifest entries (local JSON files and Prefect UI artifacts).
    * Highlights idempotency concepts via content hashing.
    * See: [Project Alpha - File Downloads Example](project-alpha-file-downloads.md)

3.  **Web Page Link Scraping (`web_page_link_scraping`):**
    * Shows basic web scraping to fetch HTML content from a page.
    * Includes tasks for fetching HTML, extracting links, identifying canonical URLs, and creating a summary manifest/artifact.
    * Demonstrates using libraries like `httpx` and `BeautifulSoup` within core logic.
    * See: [Project Alpha - Web Scraping Example](project-alpha-web-scraping.md)

## How to Use "Project Alpha"

* **As a Learning Tool:** Examine the code in `flows/dept_project_alpha/` and `configs/variables/dept_project_alpha/` to understand how the components are structured and interact.
* **As a Template for New Departments:** Use its structure as a model when you run `scripts/generators/add_department.py` to create your own departments.
* **For Testing Your Setup:** The "Project Alpha" flows are the first ones you should try running after setting up the local environment to ensure everything is working correctly.

The subsequent pages in this "Examples" section will dive deeper into the implementation details of each "Project Alpha" category.