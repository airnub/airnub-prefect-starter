# Usage Guide

This section explains how to run the example flows provided by the **`airnub-prefect-starter`** template and understand their output. The primary example department is "Project Alpha."

## Running Flows Locally (Docker Compose)

The recommended way to run flows during development is using the local Docker Compose environment.

1.  **Ensure Setup:** Complete all steps in the [Getting Started](getting-started.md) guide. This includes:
    * Cloning the repository and setting up your Python environment.
    * Configuring your `PREFECT_API_URL` (usually `http://127.0.0.1:4200/api` for local).
    * Starting the local services: `make run-local`.
    * Setting up essential Prefect Blocks: `make setup-blocks` (this creates `docker-container/local-worker-infra`).
    * Setting up Prefect Variables from YAML files: `make setup-variables`.
2.  **Apply Deployments:** Make sure the example "Project Alpha" flows are registered as deployments with your local Prefect server:
    ```bash
    make build-deployments
    ```
    This command reads `prefect.local.yaml`, which should now contain deployments for "Project Alpha" stages (e.g., "Ingestion Deployment (Project Alpha) - Local Dev").

3.  **Trigger a Flow via UI:**
    * Open the Prefect UI in your browser: `http://127.0.0.1:4200`
    * Navigate to the **Deployments** page.
    * Find an example deployment, such as **"Ingestion Deployment (Project Alpha) - Local Dev"**.
    * Click the "Run" button (▶️).
    * A modal will appear where you can:
        * Give the run a custom name (optional).
        * Modify flow parameters if the flow accepts them (see "Flow Parameters" below). For example, you might toggle the execution of specific categories within the "Project Alpha" ingestion flow.
        * Schedule for later or add to a work queue (for local, "default" is fine).
    * Click "Run" to start the flow run.

4.  **Trigger a Flow via CLI:**
    You can also trigger flow runs from your activated virtual environment using the deployment name:
    ```bash
    # Ensure PREFECT_API_URL is set to [http://127.0.0.1:4200/api](http://127.0.0.1:4200/api)
    prefect deployment run "Ingestion Flow (Project Alpha)/Ingestion Deployment (Project Alpha) - Local Dev"
    
    # Example: Run with a parameter to only execute a specific category (if the flow supports it)
    # prefect deployment run "Ingestion Flow (Project Alpha)/Ingestion Deployment (Project Alpha) - Local Dev" --param run_public_api_data=true --param run_scheduled_file_downloads=false 
    ```
    *(Note: The exact 'Flow Name/Deployment Name' string can be found on the Deployments page in the UI).*

5.  **Monitoring Flow Runs:**
    * View running and completed flows on the **Flow Runs** page in the UI.
    * Click on a specific flow run to see its task graph, real-time logs, parameter values, and any generated artifacts.
    * For detailed worker logs (showing worker polling activity and underlying execution details), use your terminal: `docker compose logs -f worker`.

## Understanding Output from "Project Alpha" Demo Flows

The example flows for "Project Alpha" are designed to demonstrate common patterns and will produce the following types of output:

* **Logs:**
    * Flows and tasks generate logs visible in the Prefect UI run view and the worker's Docker logs.
    * These logs indicate:
        * Progress of the flow (e.g., "Starting Ingestion Flow (Project Alpha)...").
        * Configuration being used (e.g., API URLs, file URLs from Prefect Variables).
        * Actions performed by core logic functions (e.g., "Core File: Downloading file from...", "Core API: Fetched JSON from...").
        * Content hashes calculated.
        * Paths where demo files and their JSON manifests are stored locally within the worker container.
        * Any errors encountered during execution.
* **Local Demo Storage (within Docker Worker):**
    * The `scheduled_file_downloads` category demo downloads files and stores them in a CAS-like (Content-Addressable Storage) structure within the worker container, typically under a path like `/app/local_demo_artifacts/project_alpha_scheduled_files/<file_hash>/<original_filename>`.
    * The `public_api_data` and `web_page_link_scraping` categories might also save their fetched/processed data as local files for demo purposes.
    * **Accessing these files:** If you've mapped a local host directory to `/app/data/` (or similar, like `/app/local_demo_artifacts/`) in your `docker-compose.yml` for the worker service (e.g., `./data/project_alpha_demo_outputs:/app/local_demo_artifacts`), you can browse these files directly on your host machine. Otherwise, you can use `docker exec` or `docker cp`.
* **Local JSON Manifest Files (Demo):**
    * Alongside downloaded files (e.g., in the `scheduled_file_downloads` demo), a corresponding `.manifest.json` file is created. This file contains metadata about the downloaded item (source URL, hash, timestamp, headers, local storage path, etc.), structured using Pydantic models defined in `airnub_prefect_starter/core/manifest_models.py`.
    * The `web_page_link_scraping` demo also creates a JSON manifest for the scraped page metadata.
* **Prefect UI Artifacts:**
    * The demo flows (specifically the "Create Manifest Archive" type tasks) generate Prefect Markdown artifacts.
    * These artifacts appear in the Prefect UI on the flow run page and provide a summary of the processed item, including its hash, source, and the path to the document and its JSON manifest *within the worker container*.

*Note: This starter template does not include an application-level database for manifests by default. The "manifests" for the demo are the local JSON files and the Prefect UI artifacts. Prefect server uses its own PostgreSQL database (in Docker) for its operational metadata (flow runs, deployments, blocks, etc.).*

## Example Flow Parameters for "Project Alpha"

The parent stage flows for "Project Alpha" (e.g., `ingestion_flow_dept_project_alpha.py`) are designed to accept parameters that control which of their category subflows are executed. These parameters can be adjusted when triggering a run (via UI or CLI `--param` flag).

Example parameters for `ingestion_flow_dept_project_alpha`:

* `run_public_api_data: bool = True`: Controls whether the "Public API Data Polling" category flow is executed.
* `run_scheduled_file_downloads: bool = True`: Controls whether the "Scheduled File Downloads" category flow is executed.
* `run_web_page_link_scraping: bool = True`: Controls whether the "Web Page Link Scraping" category flow is executed.
* `config_variable_name: Optional[str] = "dept_project_alpha_ingestion_config"`: Specifies the name of the main Prefect Variable containing configurations for all categories within the ingestion stage of Project Alpha.

You would also have corresponding configuration sections within the `dept_project_alpha_ingestion_config` Variable (sourced from `configs/variables/dept_project_alpha/ingestion_config_dept_project_alpha.yaml` and the category-specific YAMLs) that provide the actual URLs, API parameters, etc., for each category. For example:

```yaml
# In configs/variables/dept_project_alpha/ingestion_config_dept_project_alpha.yaml (simplified)
# This main config variable would typically be structured by scripts/setup_prefect_variables.py
# to include the content from category-specific config YAMLs.

# Example structure that the flow might expect after variable loading and JSON parsing:
# {
#   "public_api_data": {
#     "data_source_name": "project_alpha_public_api",
#     "apis_to_poll": [
#       {"name": "Cat Fact API", "url": "[https://catfact.ninja/fact](https://catfact.ninja/fact)", "extract_key": "fact"}
#     ]
#   },
#   "scheduled_file_downloads": {
#     "data_source_name": "project_alpha_external_files",
#     "files_to_acquire": [
#       {"name": "Sample CSV", "url": "[https://example.com/data.csv](https://example.com/data.csv)", "link_title": "Some Data"}
#     ],
#     "local_storage_base": "/app/local_demo_artifacts/downloads" 
#   },
#   // ... config for web_page_link_scraping ...
# }
```
Check the flow function signatures in `flows/dept_project_alpha/` for the exact parameter names and their defaults, and review the corresponding YAML configuration files in `configs/variables/dept_project_alpha/` to understand the expected structure for the Prefect Variables that these flows will load.

## Interacting with Data Science Scripts

This template also includes a structure for data science exploration and prototyping, primarily within the `airnub_prefect_starter/data_science/` sub-package and the top-level `notebooks/` directory.

* **Running Scripts:** Standalone Python scripts (e.g., `airnub_prefect_starter/data_science/dataset_processing.py`, `airnub_prefect_starter/data_science/modeling/train.py`) can be run directly from your activated virtual environment for R&D purposes:
    ```bash
    python -m airnub_prefect_starter.data_science.dataset_processing 
    # or if they are set up as entry points in pyproject.toml:
    # process-data 
    ```
    These scripts typically use path configurations defined in `airnub_prefect_starter/data_science/config_ds.py` to read from and write to directories like `data/raw/`, `data/processed/`, `models/`, etc.

* **Jupyter Notebooks:** The `notebooks/` directory is provided for exploratory data analysis using Jupyter Lab or Jupyter Notebook. Ensure your `dev` dependencies (which include `jupyterlab` and `notebook`) are installed (`make install` or `uv pip install -e ".[dev]"`).
    ```bash
    # From your project root, with virtual environment activated:
    jupyter lab
    ```

* **Transitioning to Prefect Workflows:**
    The typical workflow is to prototype data processing logic or model training routines in these scripts or notebooks. Once the logic is mature and needs to be automated, scheduled, and monitored, you should:
    1.  Refactor the core Python logic into reusable functions within the `airnub_prefect_starter/core/` sub-package.
    2.  Create department-specific Prefect task wrappers (using `scripts/generators/add_task.py`) in the relevant `flows/dept_.../.../tasks/` directory that call this core logic.
    3.  Orchestrate these tasks within Prefect flows.

This integrated approach allows for a smooth transition from research and development to operational pipelines.
