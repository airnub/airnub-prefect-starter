# Example: Project Alpha - Scheduled File Downloads

This example demonstrates the `scheduled_file_downloads` category within the `ingestion` stage of the `dept_project_alpha` department. Its primary purpose is to show how to download files from specified URLs, store them locally in a content-addressable manner (for this demo), and create manifest entries.

## Key Features Demonstrated

* Downloading files from external URLs.
* Calculating content hashes (SHA256) for idempotency and versioning.
* Storing files locally in a structured "Content-Addressable Storage" (CAS-like) demo format: `<base_demo_artifacts_dir>/<data_source_name>/<file_hash>/<original_filename>`.
* Generating a local JSON manifest file alongside each downloaded document, containing its metadata.
* Creating a Prefect Markdown artifact in the UI that summarizes the download and points to the local manifest and document paths (within the worker).
* Usage of department-specific task wrappers calling core logic functions.

## File Structure

* **Category Flow:** `flows/dept_project_alpha/ingestion/scheduled_file_downloads/download_scheduled_files_flow_dept_project_alpha.py`
* **Task Wrappers:** `flows/dept_project_alpha/ingestion/scheduled_file_downloads/tasks/`
    * `download_file_task_dept_project_alpha.py` (This wrapper calls the core logic for download, hash, and storage)
    * `create_manifest_archive_task_dept_project_alpha.py` (This wrapper calls the core logic for creating the Prefect artifact)
* **Category Configuration:** `configs/variables/dept_project_alpha/ingestion/scheduled_file_downloads/download_scheduled_files_config_dept_project_alpha.yaml`
* **Task Configurations (Optional):** `configs/variables/dept_project_alpha/ingestion/scheduled_file_downloads/tasks/` (e.g., `download_file_task_config_dept_project_alpha.yaml`)
* **Core Logic:**
    * `airnub_prefect_starter/core/file_handlers.py` (containing `core_process_scheduled_file_download` which handles download, hash, local CAS storage, and local JSON manifest creation)
    * `airnub_prefect_starter/common/utils.py` (e.g., `generate_sha256_for_file`)
    * `airnub_prefect_starter/core/artifact_creators.py` (e.g., `core_create_file_download_artifact_with_manifest_link`)
    * `airnub_prefect_starter/core/manifest_models.py` (e.g., `DemoFileManifestEntry` Pydantic model)

## Configuration Example

The `download_scheduled_files_config_dept_project_alpha.yaml` (which informs the `dept_project_alpha_ingestion_scheduled_file_downloads_config` Prefect Variable, typically nested under the main stage config variable) might look like this:

```yaml
# Part of the content for dept_project_alpha_ingestion_scheduled_file_downloads_config Variable
data_source_name: "project_alpha_demo_files"
# logical_path_base_demo: "ProjectAlpha/ScheduledDownloads" # Optional for conceptual grouping in manifests
local_artifacts_storage_base: "/app/local_demo_artifacts/downloads" # Base path inside worker for CAS

files_to_acquire:
  - name: "Prefect README Snapshot"
    url: "[https://raw.githubusercontent.com/PrefectHQ/prefect/main/README.md](https://raw.githubusercontent.com/PrefectHQ/prefect/main/README.md)"
    link_title: "Prefect Main README"
    source_page_url: "[https://github.com/PrefectHQ/prefect](https://github.com/PrefectHQ/prefect)" # Example
  - name: "Sample Text File (Alice in Wonderland)"
    url: "[https://www.gutenberg.org/files/11/11-0.txt](https://www.gutenberg.org/files/11/11-0.txt)"
    link_title: "Alice's Adventures in Wonderland (Plain Text)"
```

## Flow Logic Overview

The `download_scheduled_files_flow_dept_project_alpha.py` (the category flow for "Scheduled File Downloads" within "Project Alpha's" ingestion stage) typically orchestrates the following steps:

1.  **Load Configuration:**
    * The flow receives its specific configuration dictionary as a parameter from its parent stage flow (`ingestion_flow_dept_project_alpha.py`). This configuration originates from the `dept_project_alpha_ingestion_scheduled_file_downloads_config` Prefect Variable (which was populated from the corresponding YAML file, `configs/variables/dept_project_alpha/ingestion/scheduled_file_downloads/download_scheduled_files_config_dept_project_alpha.yaml`).
    * This config typically includes:
        * `data_source_name`: An identifier for this specific data source (e.g., `project_alpha_demo_files`).
        * `local_artifacts_storage_base`: The base path within the worker container where downloaded files and their JSON manifests will be stored (e.g., `/app/local_demo_artifacts/downloads`). This path is often derived from `config_ds.DATA_DIR` within the core logic.
        * `files_to_acquire`: A list of dictionaries, each specifying a file's `name` (for logging/display), `url` (for download), `link_title`, and optionally `source_page_url`.

2.  **Iterate and Process Files:**
    The flow loops through each item in the `files_to_acquire` list. For each file:
    * It calls the department-specific task wrapper, for example, **`download_file_task_dept_project_alpha`**. This task is located in `flows/dept_project_alpha/ingestion/scheduled_file_downloads/tasks/`.
    * This task wrapper then calls the core logic function `core_process_scheduled_file_download` (from `airnub_prefect_starter/core/file_handlers.py`).

3.  **Core Logic (`core_process_scheduled_file_download`):**
    This central function in `airnub_prefect_starter/core/file_handlers.py` performs the main work:
    * **Downloads the file:** Uses `httpx` to fetch the content from the provided `url` and saves it to a temporary file within the worker container. It also captures HTTP headers and the original filename (sanitized).
    * **Calculates Content Hash:** Computes the SHA256 hash of the downloaded file's content using `generate_sha256_for_file` (from `airnub_prefect_starter/common/utils.py`).
    * **Idempotency Check (Conceptual for Demo):** For this demo, idempotency might involve checking if a file with the same content hash already exists in the target local CAS directory. A more robust system (which users can build upon this template) would use a persistent manifest (like a database or a central manifest file store) to track processed hashes.
    * **Stores File Locally (CAS-like):** If the file is determined to be new (or reprocessing is intended), the temporary file is moved to a structured local directory. The structure is:
        `<local_artifacts_storage_base>/<data_source_name>/<file_content_hash>/<sanitized_original_filename>`
        (e.g., `/app/local_demo_artifacts/downloads/project_alpha_demo_files/a1b2c3d4e5f6.../Prefect_Main_README.md`)
    * **Creates Local JSON Manifest:** A `DemoFileManifestEntry` Pydantic model instance (from `airnub_prefect_starter/core/manifest_models.py`) is populated with metadata (source URL, hash, local storage path, headers, timestamp, etc.). This model is then serialized to a JSON string and saved as `<sanitized_original_filename>.manifest.json` alongside the document in the CAS directory.
    * The core logic function returns a dictionary containing all this metadata and the processing status (e.g., "SUCCESS", "FAILED_DOWNLOAD").

4.  **Create Prefect UI Artifact:**
    * After the file processing task wrapper (`download_file_task_dept_project_alpha`) completes and returns the metadata dictionary, the category flow calls another department-specific task wrapper, for example, **`create_manifest_archive_task_dept_project_alpha`**.
    * This task wrapper calls `core_create_file_download_artifact_with_manifest_link` (from `airnub_prefect_starter/core/artifact_creators.py`).
    * This core function takes the metadata dictionary (returned by the previous task) and generates a Prefect Markdown artifact. This artifact is visible in the Prefect UI for the flow run and provides a summary of the downloaded file, its hash, and the paths to the document and its JSON manifest *within the worker container*.

## Expected Output

When this "Scheduled File Downloads" category flow for "Project Alpha" runs successfully for a new file:

* **Logs:** Detailed logs in the Prefect UI and worker console, tracing the download, hashing, local storage of the file and its JSON manifest, and Prefect UI artifact creation steps.
* **Local File Storage (in Worker):**
    * The downloaded file will be stored in a path similar to:
      `/app/local_demo_artifacts/downloads/project_alpha_demo_files/<SHA256_HASH>/<original_filename>`
    * (If you have volume-mapped a host directory like `./data/project_alpha_demo_outputs/downloads/` to the worker's `/app/local_demo_artifacts/downloads/` via `docker-compose.yml`, you can browse these files on your host machine.)
* **Local JSON Manifest File (in Worker):**
    * A JSON file named `<original_filename>.manifest.json` will be created in the same directory as the downloaded file above (i.e., within the `<SHA256_HASH>` subdirectory). It will contain structured metadata about the downloaded file based on the `DemoFileManifestEntry` Pydantic model.
* **Prefect UI Artifact:**
    * A Markdown artifact will appear on the flow run's page in the Prefect UI. This artifact will summarize the downloaded file's details (source URL, hash, size, content type) and include the worker paths to both the stored document and its local JSON manifest file.

This example showcases a complete local ingestion pipeline for files, including content hashing for idempotency principles, local CAS-like storage for demo purposes, local JSON manifest generation, and rich observability through Prefect artifacts.