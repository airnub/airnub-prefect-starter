# Example: Project Alpha - Public API Data Polling

This example demonstrates the `public_api_data` category within the `ingestion` stage of the `dept_project_alpha` department. It showcases fetching data from simple, public JSON APIs, parsing the response, and creating a summary artifact for observability in the Prefect UI.

This category illustrates a common pattern where structured data is retrieved from external web services.

## Key Features Demonstrated

* Fetching JSON data from external REST APIs using `httpx` via core logic functions.
* Basic parsing of JSON responses to extract relevant information.
* Creating a Prefect Markdown artifact to display the fetched and parsed data.
* Usage of department-specific Prefect task wrappers that call functions from the `airnub_prefect_starter/core/` package.
* Configuration of API endpoints and parameters via Prefect Variables (sourced from YAML).

## File Structure

The relevant files for this example include:

* **Category Flow:**
    * `flows/dept_project_alpha/ingestion/public_api_data/ingest_public_api_data_flow_dept_project_alpha.py`
* **Task Wrappers (Department-Specific):**
    * `flows/dept_project_alpha/ingestion/public_api_data/tasks/fetch_public_api_data_task_dept_project_alpha.py`
    * `flows/dept_project_alpha/ingestion/public_api_data/tasks/parse_api_response_task_dept_project_alpha.py`
    * (Potentially) A new task wrapper like `create_api_polling_artifact_task_dept_project_alpha.py`
* **Category Configuration (YAML for Prefect Variable):**
    * `configs/variables/dept_project_alpha/ingestion/public_api_data/ingest_public_api_data_config_dept_project_alpha.yaml`
* **Task Configurations (Optional YAMLs for Prefect Variables):**
    * `configs/variables/dept_project_alpha/ingestion/public_api_data/tasks/` (e.g., `Workspace_public_api_data_task_config_dept_project_alpha.yaml`)
* **Core Logic (in `airnub_prefect_starter` package):**
    * `airnub_prefect_starter/core/api_handlers.py` (containing `core_fetch_json_from_api` and `core_parse_api_response_for_demo`)
    * `airnub_prefect_starter/core/artifact_creators.py` (would contain a function like `core_create_api_data_artifact` if you create one for this purpose)

## Configuration Example

The `ingest_public_api_data_config_dept_project_alpha.yaml` file defines the parameters for this category. This YAML content is loaded into a Prefect Variable (e.g., `dept_project_alpha_ingestion_public_api_data_config`) by the `make setup-variables` command.

An example configuration might look like this:

```yaml
# configs/variables/dept_project_alpha/ingestion/public_api_data/ingest_public_api_data_config_dept_project_alpha.yaml
# This content populates the 'dept_project_alpha_ingestion_public_api_data_config' Prefect Variable.

# Identifier for this data source, used if saving data or creating detailed manifests
data_source_name: "project_alpha_public_apis_demo"

# List of APIs to poll for this category
apis_to_poll:
  - name: "Cat Fact Ninja" # Display name for logging/artifacts
    url: "[https://catfact.ninja/fact](https://catfact.ninja/fact)"
    # Optional: query parameters for the API if needed
    # params: 
    #   max_length: 140
    extract_key: "fact" # The primary key in the JSON response to highlight

  - name: "Bored API Activity"
    url: "[https://www.boredapi.com/api/activity](https://www.boredapi.com/api/activity)"
    extract_key: "activity" # The primary key to highlight
```

## Flow Logic Overview

The `ingest_public_api_data_flow_dept_project_alpha.py` (the category flow for "Public API Data Polling" within "Project Alpha's" ingestion stage) typically orchestrates the following steps for each configured API endpoint:

1.  **Load Configuration:**
    * The flow receives its specific configuration dictionary as a parameter from its parent stage flow (`ingestion_flow_dept_project_alpha.py`). This configuration originates from the `dept_project_alpha_ingestion_public_api_data_config` Prefect Variable (which was populated from the corresponding YAML file, `configs/variables/dept_project_alpha/ingestion/public_api_data/ingest_public_api_data_config_dept_project_alpha.yaml`).
    * This config typically includes:
        * `data_source_name`: An identifier for this specific data source (e.g., `project_alpha_public_apis`).
        * `apis_to_poll`: A list of dictionaries. Each dictionary defines an API to poll, specifying its `name` (for display), `url`, optional request `params` for the API, and an `extract_key` to identify the main piece of information to highlight from the JSON response.
        * (Optional) `local_artifacts_storage_base`: If you choose to save API responses locally for the demo, this would be the base path within the worker container (e.g., `/app/local_demo_artifacts/api_responses`).

2.  **Iterate and Process APIs:**
    The flow loops through each API definition in the `apis_to_poll` list. For each API:
    * It calls the department-specific task wrapper **`Workspace_public_api_data_task_dept_project_alpha`**. This task is located in `flows/dept_project_alpha/ingestion/public_api_data/tasks/`.
        * This task wrapper, in turn, calls the core logic function `core_fetch_json_from_api` (from `airnub_prefect_starter/core/api_handlers.py`) using the API's `url` and any specified `params`.
    * If data is successfully fetched (i.e., a JSON response dictionary is returned):
        * It calls the department-specific task wrapper **`parse_api_response_task_dept_project_alpha`**.
        * This task wrapper calls the core logic function `core_parse_api_response_for_demo` (also from `airnub_prefect_starter/core/api_handlers.py`) with the fetched JSON data and the configured `extract_key`. This function returns a dictionary with the extracted information.
    * **Create Prefect UI Artifact:** The flow then (typically) calls another department-specific task (e.g., a new `create_api_data_artifact_task_dept_project_alpha` if you created one).
        * This task wrapper would use a function from `airnub_prefect_starter/core/artifact_creators.py` (e.g., a new function like `core_create_api_polling_artifact`) to generate a Prefect Markdown artifact. This artifact summarizes the API polled and displays the key information extracted by the parsing task.

3.  **Core Logic Functions (located in `airnub_prefect_starter/core/api_handlers.py`):**
    * `core_fetch_json_from_api`:
        * Uses the `httpx` library to make an asynchronous GET request to the specified API URL with any given parameters.
        * Handles HTTP errors and other request exceptions gracefully.
        * Returns the parsed JSON dictionary or `None` if the request fails or the response is not valid JSON.
    * `core_parse_api_response_for_demo`:
        * Takes the JSON dictionary and the `extract_key` from the configuration.
        * It attempts to find the value associated with the `extract_key`.
        * Returns a dictionary containing this extracted value and potentially other contextual information (like a snippet of the original response if the key isn't found, or other relevant fields from common demo APIs like `length` from cat facts or `type` from the Bored API).

## Expected Output

When this "Public API Data Polling" category flow for "Project Alpha" runs successfully for a configured API:

* **Logs:** Detailed logs in the Prefect UI and worker console, indicating which APIs are being polled, the URLs called, parameters used, and a summary of the fetched and parsed data for each.
* **Prefect UI Artifacts:**
    * For each successfully polled API and parsed response, a Markdown artifact will appear on the flow run's page in the Prefect UI.
    * This artifact will typically display:
        * The name of the API that was polled (e.g., "Cat Fact Ninja").
        * The source URL.
        * The key information extracted from the API response (e.g., the actual cat fact or the suggested activity).
        * Timestamp of the polling attempt.
* **Local JSON Manifest/Data Files (Optional for Demo):**
    * While the primary demo output for this category is typically the Prefect UI artifact for simplicity, the flow could be extended to also:
        1.  Save the raw JSON response from each API to a local file within the worker container. For example, under a path like `/app/local_demo_artifacts/api_responses/<data_source_name>/<api_name_sanitized>/<timestamp_or_hash>.json`.
        2.  Create a simple local JSON manifest file detailing the API call and where the raw response is stored, similar to the `scheduled_file_downloads` example, using a Pydantic model from `airnub_prefect_starter/core/manifest_models.py`.
    * For this starter template's API polling demo, focusing on the UI artifact for immediate visibility of results is often sufficient to illustrate the pattern effectively.

This example demonstrates how to build a simple yet effective data ingestion pipeline for API sources, highlighting configuration-driven behavior, modular core logic, specific task wrappers, and rich observability through Prefect artifacts.