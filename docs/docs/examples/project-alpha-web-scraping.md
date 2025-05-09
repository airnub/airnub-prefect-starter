# Example: Project Alpha - Web Page Link Scraping

This example demonstrates the `web_page_link_scraping` category within the `ingestion` stage of the `dept_project_alpha` department. It showcases fetching HTML from a web page, extracting links, identifying the canonical URL, and creating a summary manifest (local JSON file) and a Prefect UI artifact.

This category illustrates how to handle unstructured web data and extract meaningful information like canonical links for deduplication or tracking purposes.

## Key Features Demonstrated

* Fetching HTML content from a web page using `httpx` via core logic functions.
* Parsing HTML using `BeautifulSoup` to extract links.
* Identifying the canonical URL (`<link rel="canonical">`) from the HTML.
* Hashing the canonical URL (using `hashlib`) for potential deduplication or as a unique identifier for the page's primary representation.
* Saving a local JSON manifest file with scrape metadata (original URL, canonical URL, its hash, extracted links).
* Creating a Prefect Markdown artifact to display the scraped information in the UI.
* Usage of department-specific Prefect task wrappers calling functions from `airnub_prefect_starter/core/`.

## File Structure

The relevant files for this example include:

* **Category Flow:**
    * `flows/dept_project_alpha/ingestion/web_page_link_scraping/ingest_web_page_link_scraping_flow_dept_project_alpha.py`
* **Task Wrappers (Department-Specific):**
    * `flows/dept_project_alpha/ingestion/web_page_link_scraping/tasks/fetch_html_content_of_web_page_task_dept_project_alpha.py`
    * `flows/dept_project_alpha/ingestion/web_page_link_scraping/tasks/extract_links_from_html_task_dept_project_alpha.py`
    * (A new task wrapper, e.g.) `create_scraped_page_manifest_and_artifact_task_dept_project_alpha.py`
* **Category Configuration (YAML for Prefect Variable):**
    * `configs/variables/dept_project_alpha/ingestion/web_page_link_scraping/ingest_web_page_link_scraping_config_dept_project_alpha.yaml`
* **Core Logic (in `airnub_prefect_starter` package):**
    * `airnub_prefect_starter/core/web_utils.py` (containing `core_fetch_html_content` and `core_parse_links_and_canonical_from_html`)
    * `airnub_prefect_starter/common/utils.py` (e.g., `generate_sha256_hash_from_string`)
    * `airnub_prefect_starter/core/artifact_creators.py` (containing `save_scraped_page_manifest_locally` and `core_create_scraped_page_artifact`)
    * `airnub_prefect_starter/core/manifest_models.py` (e.g., `DemoScrapedPageManifestEntry` Pydantic model)

## Configuration Example

The `ingest_web_page_link_scraping_config_dept_project_alpha.yaml` file defines parameters for this category. This YAML content becomes part of the `dept_project_alpha_ingestion_web_page_link_scraping_config` Prefect Variable.

An example configuration:

```yaml
# configs/variables/dept_project_alpha/ingestion/web_page_link_scraping/ingest_web_page_link_scraping_config_dept_project_alpha.yaml

data_source_name: "project_alpha_web_pages_demo"
# Base path inside worker for storing local JSON manifests for scraped pages
local_manifests_storage_base: "/app/local_demo_artifacts/web_scrape_manifests" 

pages_to_scrape:
  - name: "Prefect Blog Main Page"
    url: "[https://www.prefect.io/blog/](https://www.prefect.io/blog/)" # Example: A page likely to have a canonical URL and links
  - name: "Python Org About Page"
    url: "[https://www.python.org/about/](https://www.python.org/about/)"
```

## Flow Logic Overview

The `ingest_web_page_link_scraping_flow_dept_project_alpha.py` (the category flow for "Web Page Link Scraping" within "Project Alpha's" ingestion stage) typically orchestrates the following steps for each configured page URL:

1.  **Load Configuration:**
    * The flow receives its specific configuration dictionary as a parameter from its parent stage flow (`ingestion_flow_dept_project_alpha.py`). This configuration originates from the `dept_project_alpha_ingestion_web_page_link_scraping_config` Prefect Variable (which was populated from `configs/variables/dept_project_alpha/ingestion/web_page_link_scraping/ingest_web_page_link_scraping_config_dept_project_alpha.yaml`).
    * This config typically includes:
        * `data_source_name`: An identifier for this specific data source (e.g., `project_alpha_web_pages_demo`).
        * `local_manifests_storage_base`: The base path within the worker container where local JSON manifests for scraped pages will be stored (e.g., `/app/local_demo_artifacts/web_scrape_manifests`). This path is often derived from `config_ds.DATA_DIR` within the core logic.
        * `pages_to_scrape`: A list of dictionaries, each specifying a page's `name` (for logging/display) and `url` to be scraped.

2.  **Iterate and Process Web Pages:**
    The flow loops through each page definition in the `pages_to_scrape` list. For each page `url`:
    * **Fetch HTML:** It calls the department-specific task wrapper **`Workspace_html_content_of_web_page_task_dept_project_alpha`**.
        * This task wrapper, located in `flows/dept_project_alpha/ingestion/web_page_link_scraping/tasks/`, calls the core logic function `core_fetch_html_content` (from `airnub_prefect_starter/core/web_utils.py`) to retrieve the raw HTML content of the page.
    * **Extract Links & Canonical URL:** If HTML content is successfully fetched, it calls the department-specific task wrapper **`extract_links_from_html_task_dept_project_alpha`**.
        * This task wrapper calls the core logic function `core_parse_links_and_canonical_from_html` (also from `airnub_prefect_starter/core/web_utils.py`).
        * This core function parses the HTML (using `BeautifulSoup`), identifies the canonical URL (if present), hashes the canonical URL string (using `generate_sha256_hash_from_string` from `common/utils.py`), and extracts all valid HTTP/HTTPS links from `<a>` tags.
        * It returns a dictionary (`scrape_result`) containing the original URL, the found canonical URL, the hash of the canonical URL, and the list of extracted links.
    * **Create Local Manifest and Prefect UI Artifact:** The flow then typically calls another department-specific task (e.g., `create_scraped_page_manifest_and_artifact_task_dept_project_alpha`).
        * This task wrapper would orchestrate calls to:
            1.  `save_scraped_page_manifest_locally` (from `airnub_prefect_starter/core/artifact_creators.py` or `web_utils.py`): This function takes the `scrape_result` dictionary, populates a `DemoScrapedPageManifestEntry` Pydantic model (from `core/manifest_models.py`), serializes it to JSON, and saves it to a local file within the worker. The storage path for this JSON manifest is structured using the `data_source_name` and the `canonical_url_hash` (e.g., `<local_manifests_storage_base>/<data_source_name>/scraped_pages_manifests/<canonical_url_hash>/<original_url_slugified>.manifest.json`).
            2.  `core_create_scraped_page_artifact` (from `airnub_prefect_starter/core/artifact_creators.py`): This function uses the `scrape_result` dictionary and the path to the saved local JSON manifest to generate a Prefect Markdown artifact in the UI.

3.  **Core Logic Functions (highlights):**
    * **`airnub_prefect_starter/core/web_utils.py`:**
        * `core_fetch_html_content`: Uses `httpx` to get the page's HTML content.
        * `core_parse_links_and_canonical_from_html`: Employs `BeautifulSoup` for parsing HTML, `urljoin` for resolving relative links, and calls a hashing utility for the canonical URL.
    * **`airnub_prefect_starter/common/utils.py`:**
        * `generate_sha256_hash_from_string`: Hashes the canonical URL string.
        * `sanitize_filename`: Used for creating safe filenames for local manifests.
    * **`airnub_prefect_starter/core/artifact_creators.py`:**
        * `save_scraped_page_manifest_locally`: Handles the creation and saving of the local JSON manifest file based on the `DemoScrapedPageManifestEntry` model.
        * `core_create_scraped_page_artifact`: Takes the structured scrape data (including the path to the local JSON manifest) and creates an informative Prefect Markdown artifact.

## Expected Output

When this "Web Page Link Scraping" category flow for "Project Alpha" runs successfully for a configured web page:

* **Logs:** Detailed logs in the Prefect UI and worker console, showing the URL being scraped, the canonical URL identified (and its hash), and a summary of the number of links extracted.
* **Local JSON Manifest File (in Worker):**
    * A JSON file (e.g., `<original_url_slugified>.manifest.json`) will be created in a path within the worker container, structured by data source and canonical URL hash. For example:
      `/app/local_demo_artifacts/web_scrape_manifests/project_alpha_web_pages/scraped_pages_manifests/<CANONICAL_URL_HASH>/`
    * This JSON file contains structured metadata about the scrape: original URL, canonical URL (and its hash), scrape timestamp, and the full list of extracted links, based on the `DemoScrapedPageManifestEntry` Pydantic model.
    * (If you have volume-mapped a host directory like `./data/project_alpha_demo_outputs/web_scrape_manifests/` to the worker's `/app/local_demo_artifacts/web_scrape_manifests/` via `docker-compose.yml`, you can browse these manifest files on your host.)
* **Prefect UI Artifact:**
    * A Markdown artifact will appear on the flow run's page in the Prefect UI for each scraped page.
    * This artifact will summarize the key details: original URL, canonical URL, canonical URL hash, a preview of the extracted links, and the worker path to its detailed local JSON manifest file.

This example illustrates a basic web scraping pipeline, focusing on extracting links and canonical URL information for potential deduplication or tracking. It demonstrates how to manifest this information both locally as a structured JSON file and within the Prefect UI for enhanced observability.