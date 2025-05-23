# Development Guide

This guide provides instructions on how to extend the **Airnub Prefect Starter** template by adding new Departments, Categories (data sources/types within a Department/Stage), and department-specific Prefect Tasks.

The primary method for scaffolding new components is by using the generator scripts located in `scripts/generators/`.

## Project Structure Recap

Before adding new components, familiarize yourself with the project structure. Refer to the [Core Concepts & Architecture](architecture.md) guide. Key directories for development include:

* **`flows/`**: Top-level directory for Prefect flow definitions. New departments (e.g., `dept_project_beta/`) will be created here.
    * `flows/dept_<id>/[stage_verb]_flow_dept_<id>.py`: Parent orchestrator flows for each stage.
    * `flows/dept_<id>/<stage_name>/<category_id>/`: Contains category-specific flows.
    * `flows/dept_<id>/<stage_name>/[optional_category_id]/tasks/`: Contains department-specific Prefect task wrappers.
* **`configs/variables/`**: YAML files for Prefect Variables, mirroring the `flows/` structure.
* **`airnub_prefect_starter/`**: The main Python package.
    * `common/utils.py`: For truly generic, reusable utility functions.
    * `core/`: For Prefect-agnostic core Python logic functions (e.g., `file_handlers.py`, `api_handlers.py`) that are called by your task wrappers. **This is where most of your business logic should reside.**
    * `data_science/`: For exploratory scripts and prototyping (e.g., `dataset_processing.py`, `modeling/`).
    * `tasks/`: (Initially empty) Reserved for *future common, reusable Prefect task wrappers* if your project develops them.

## Project Conventions and Generators

The generator scripts located in `scripts/generators/` (`add_department.py`, `add_category.py`, `add_task.py`) are the standard and recommended method for creating new project components. Using these scripts ensures that all new flows, tasks, and configurations adhere to the project's structural and naming conventions. This consistency is vital for maintainability and is verified by the project's automated test suite.

The core of the naming convention often involves a `sanitize_identifier()` helper function (used within the scripts) which converts descriptive names into `snake_case` identifiers suitable for filenames and Python objects. It typically lowercases the input, replaces spaces and various special characters with underscores, and collapses multiple underscores.

Below is a detailed breakdown of the conventions enforced by each generator:

### `add_department.py` Conventions

*   **Purpose:** Scaffolds a new "department," which is a top-level organizational unit within the project.
*   **User Inputs:**
    *   `full_dept_name`: The full, human-readable name for the department (e.g., "Project Beta Operations").
    *   `dept_identifier`: A short, unique identifier for the department. Must start with `dept_` (e.g., `dept_beta_ops`). The script will suggest a sanitized version of the full name.
*   **Directory Structure Created:**
    *   `flows/<dept_identifier>/`: Main directory for the department's flows.
        *   `flows/<dept_identifier>/__init__.py`
        *   `flows/<dept_identifier>/<stage>/`: Subdirectories for standard stages (`ingestion`, `processing`, `analysis`).
            *   `flows/<dept_identifier>/<stage>/__init__.py`
            *   `flows/<dept_identifier>/<stage>/.gitkeep`
    *   `configs/variables/<dept_identifier>/`: Main directory for the department's configuration files.
        *   `configs/variables/<dept_identifier>/<stage>/`: Subdirectories for standard stages.
            *   `configs/variables/<dept_identifier>/<stage>/.gitkeep`
*   **File Naming:**
    *   Parent Orchestrator Flow: `flows/<dept_identifier>/<stage>_flow_<dept_identifier>.py` (e.g., `ingestion_flow_dept_beta_ops.py`).
    *   Parent Orchestrator Config: `configs/variables/<dept_identifier>/<stage>_config_<dept_identifier>.yaml` (e.g., `ingestion_config_dept_beta_ops.yaml`).
*   **Python Function Naming (Parent Flow):**
    *   Function Name: `async def <stage>_flow_<dept_identifier>(...)`
    *   Prefect Decorator: `@flow(name="{stage.capitalize()} Flow ({full_dept_name})", ...)`
*   **YAML Variable Comment (Parent Config):**
    *   `# Corresponding Prefect Variable Name (proposed): <dept_identifier>_<stage>_config`
*   **Other Key Elements:**
    *   `base_tags` list in parent flow: `[dept_identifier, stage]`
    *   Updates `configs/department_mapping.yaml` with the new `dept_identifier: full_dept_name` mapping.
    *   Optionally adds deployment definitions to `prefect.local.yaml`:
        *   Deployment Name: `"{stage.capitalize()} Deployment ({full_dept_name})"`
        *   Entrypoint: `flows/<dept_identifier>/<stage>_flow_<dept_identifier>.py:<stage>_flow_<dept_identifier>`

### `add_category.py` Conventions

*   **Purpose:** Scaffolds a new "category" within an existing department and stage. A category typically represents a specific data source, data type, or sub-process.
*   **User Inputs:**
    *   Selected `dept_identifier` (from existing departments).
    *   Selected `stage` (e.g., `ingestion`, `processing`, `analysis`).
    *   `category_name`: The human-readable name for the category (e.g., "Public API Data Feed").
    *   `action_verb`: The primary action this category flow performs (e.g., "Ingest", "Process", "Analyze").
*   **Derived Identifiers:**
    *   `category_identifier`: Sanitized version of `category_name` (e.g., `public_api_data_feed`).
    *   `action_verb_lower`: Lowercased version of `action_verb` (e.g., `ingest`).
*   **Directory Structure Created:**
    *   `flows/<dept_identifier>/<stage>/<category_identifier>/`: Directory for the category-specific flow.
        *   `flows/<dept_identifier>/<stage>/<category_identifier>/__init__.py`
    *   `configs/variables/<dept_identifier>/<stage>/<category_identifier>/`: Directory for the category-specific configuration.
*   **File Naming:**
    *   Category Flow: `flows/<dept_identifier>/<stage>/<category_identifier>/<action_verb_lower>_<category_identifier>_flow_<dept_identifier>.py` (e.g., `ingest_public_api_data_feed_flow_dept_beta_ops.py`).
    *   Category Config: `configs/variables/<dept_identifier>/<stage>/<category_identifier>/<action_verb_lower>_<category_identifier>_config_<dept_identifier>.yaml` (e.g., `ingest_public_api_data_feed_config_dept_beta_ops.yaml`).
*   **Python Function Naming (Category Flow):**
    *   Function Name: `async def <action_verb_lower>_<category_identifier>_flow_<dept_identifier>(...)`
    *   Prefect Decorator: `@flow(name="{action_verb.capitalize()} {category_name} ({full_dept_name})", ...)` (where `full_dept_name` is retrieved from `department_mapping.yaml`).
*   **YAML Variable Comment (Category Config):**
    *   `# Corresponding Prefect Variable Name (proposal - requires setup script update): <dept_identifier>_<stage>_<category_identifier>_config`
*   **Other Key Elements:**
    *   `base_tags` list in category flow: `[dept_identifier, stage, category_identifier]`
    *   File path comments at the top of generated Python and YAML files.

### `add_task.py` Conventions

*   **Purpose:** Scaffolds a new Prefect task wrapper and its optional configuration file. These tasks are typically specific to a department and may operate at a stage or category level.
*   **User Inputs:**
    *   `task_name_desc`: A descriptive name for the task (e.g., "Parse XML File for Invoices").
    *   `task_func_name`: The Python function name for the task wrapper. Must end with `_task` (e.g., `parse_xml_invoices_task`). The script will suggest a sanitized version of `task_name_desc` + `_task`.
    *   Selected `dept_identifier`.
    *   Selected `stage`.
    *   Optional: Whether the task is category-specific.
        *   If yes, selected or newly created `category_identifier`.
*   **Derived Identifiers:**
    *   `task_filename_base`: Sanitized version of `task_name_desc` (suffix `_task` is NOT included here, e.g., `parse_xml_file_for_invoices`).
*   **Directory Structure Created:**
    *   `flows/<dept_id>/<stage>/[<cat_id>/]tasks/`: Directory for task Python files.
        *   `.../tasks/__init__.py`
    *   `configs/variables/<dept_id>/<stage>/[<cat_id>/]tasks/`: Directory for task configuration files.
        *   `.../tasks/__init__.py`
*   **File Naming:**
    *   Task Python File: `.../tasks/<task_filename_base>_task_<dept_identifier>.py` (e.g., `parse_xml_file_for_invoices_task_dept_beta_ops.py`). The `dept_identifier` is always appended to task filenames to ensure uniqueness when tasks might be imported across different contexts, though primarily they are used within their own department.
    *   Task Config File: `.../tasks/<task_filename_base>_task_config_<dept_identifier>.yaml` (e.g., `parse_xml_file_for_invoices_task_config_dept_beta_ops.yaml`).
*   **Python Function Naming (Task Wrapper):**
    *   Function Name: `async def <task_func_name>(...)` (as provided by user).
    *   Prefect Decorator: `@task(name="{task_name_desc_original_but_title_cased_and_underscores_to_spaces}", ...)` (e.g., `"Parse Xml File For Invoices"` if `task_name_desc` was "Parse_XML File for Invoices"). The script sanitizes the description for the decorator name by replacing underscores with spaces and title-casing.
*   **YAML Variable Comment (Task Config):**
    *   Category-Specific: `# Corresponding Prefect Variable Name (proposal - requires setup script update): <dept_identifier>_<stage>_<category_identifier>_<task_func_name>_config`
    *   Stage-Level (No Category): `# Corresponding Prefect Variable Name (proposal - requires setup script update): <dept_identifier>_<stage>_<task_func_name>_config`
*   **Other Key Elements:**
    *   File path comments at the top of generated Python and YAML files.
    *   The script handles the option to create a new category on the fly if chosen during the prompts.

## Adding a New Department (e.g., "Project Beta")

Use the `add_department.py` script to scaffold a new department. This ensures consistency with naming conventions and directory structures.

1.  **Run the Generator Script:**
    ```bash
    python scripts/generators/add_department.py
    ```
2.  **Follow Prompts:**
    * Enter the full department name (e.g., "Project Beta Operations").
    * Enter or confirm the department identifier (e.g., `dept_beta_ops`).
    * Choose to update `configs/department_mapping.yaml`.
    * Choose to add default deployments to `prefect.local.yaml`.
3.  **Implement Parent Stage Flows:**
    * The script generates placeholder parent flows (e.g., `flows/dept_beta_ops/ingestion_flow_dept_beta_ops.py`).
    * Modify these flows to define parameters for running specific categories and to call the category flows you will create in the next steps.
    * Refer to `flows/dept_project_alpha/ingestion_flow_dept_project_alpha.py` as an example. The generated parent flow will align with the conventions detailed in the "Project Conventions and Generators" section.
4.  **Define Parent Flow Configuration:**
    * The script generates placeholder YAML configs (e.g., `configs/variables/dept_beta_ops/ingestion_config_dept_beta_ops.yaml`). This file will also adhere to the naming and content conventions (like the variable name comment).
    * Update this YAML to include configuration sections for each category flow that the parent flow will manage.
5.  **Add Categories and Tasks:** Follow the sections below. Remember to use the generator scripts for consistency.
6.  **Update Prefect Variables:** After creating/updating YAML configuration files, run:
    ```bash
    make setup-variables
    ```
7.  **Apply Deployments:**
    ```bash
    make build-deployments
    ```

## Adding a New Category to a Stage (e.g., "New Data Feed" in "Project Beta" Ingestion)

Use the `add_category.py` script. This creates the necessary flow file and configuration YAML for a new data type or sub-source within an existing department and stage.

1.  **Run the Generator Script:**
    ```bash
    python scripts/generators/add_category.py
    ```
2.  **Follow Prompts:**
    * Select the target department (e.g., `dept_beta_ops`).
    * Select the target stage (e.g., `ingestion`).
    * Enter the new category's display name (e.g., "New Data Feed Vendor X").
    * Enter the primary action verb for the category flow (e.g., "Ingest", "Process").
3.  **Implement the Category Flow:**
    * A placeholder flow file is created (e.g., `flows/dept_beta_ops/ingestion/new_data_feed_vendor_x/ingest_new_data_feed_vendor_x_flow_dept_beta_ops.py`). This filename and its internal structure (function name, tags, comments) will follow the conventions outlined in "Project Conventions and Generators".
    * Implement the logic for this category. This usually involves:
        * Accepting a `config: Optional[Dict[str, Any]]` parameter (passed from the parent stage flow).
        * Calling department-specific tasks (see "Adding a New Task" below) or common tasks.
        * For an ingestion flow, this might involve fetching data, hashing, storing locally (using core logic from `airnub_prefect_starter/core/file_handlers.py`), and creating manifest entries/artifacts (using logic from `airnub_prefect_starter/core/artifact_creators.py`).
        * Refer to the "Project Alpha" category flows like `flows/dept_project_alpha/ingestion/public_api_data/ingest_public_api_data_flow_dept_project_alpha.py` for detailed examples.
    * The generator script automatically sets up the standard `base_tags` using `with tags(dept_id, stage_id, category_id):`.
4.  **Define Category Configuration:**
    * A placeholder YAML config is created (e.g., `configs/variables/dept_beta_ops/ingestion/new_data_feed_vendor_x/ingest_new_data_feed_vendor_x_config_dept_beta_ops.yaml`). This also follows the documented naming and content conventions.
    * Add parameters needed by your category flow (e.g., API URLs, file paths, processing parameters). This structure will be part of the larger department-stage Prefect Variable.
5.  **Update Parent Stage Flow:**
    * Modify the corresponding parent stage flow (e.g., `flows/dept_beta_ops/ingestion_flow_dept_beta_ops.py`) to:
        * Import your new category flow function (e.g., `from .ingestion.new_data_feed_vendor_x.ingest_new_data_feed_vendor_x_flow_dept_beta_ops import ingest_new_data_feed_vendor_x_flow_dept_beta_ops`).
        * Add a boolean parameter to control its execution (e.g., `run_new_data_feed: bool = True`).
        * Call your new category flow, passing the relevant section of its loaded configuration.
6.  **Update Prefect Variables:** `make setup-variables`

## Adding a New Task (Department-Specific Wrapper)

Prefect tasks in this template are typically thin wrappers around more detailed Python functions (core logic). For a comprehensive list of conventions applied by the script, refer to the "Project Conventions and Generators" section above.

1.  **Implement Core Logic Function(s):**
    * Before creating the Prefect task wrapper, write the underlying Python function(s) that perform the actual work.
    * Place this logic in a suitable module within `airnub_prefect_starter/core/` (e.g., `file_handlers.py`, `api_handlers.py`, or a new `your_logic_module.py`).
    * If the logic is extremely generic and small, `airnub_prefect_starter/common/utils.py` might be appropriate.
    * Ensure this core logic is testable independently of Prefect.
2.  **Run the Generator Script:**
    ```bash
    python scripts/generators/add_task.py
    ```
3.  **Follow Prompts:**
    * Enter a descriptive name for the task (e.g., "Process Vendor X Record").
    * Confirm/edit the suggested Python function name for the task wrapper (e.g., `process_vendor_x_record_task`). Note: the script will append `_<dept_identifier>` to the filename, but the function name itself remains as defined by the user or the initial suggestion based on the description. The example here should be `process_vendor_x_record_task`.
    * Select the department, stage, and optionally the specific category where this task wrapper will be used and reside.
4.  **Implement the Task Wrapper:**
    * A placeholder task wrapper file is created (e.g., `flows/dept_beta_ops/ingestion/new_data_feed_vendor_x/tasks/process_vendor_x_record_task_dept_beta_ops.py`). The filename uses a sanitized base from the description and appends `_task_<dept_identifier>.py`.
    * Edit this file:
        * Import the core logic function(s) you created in Step 1 from `airnub_prefect_starter.core` or `airnub_prefect_starter.common`.
        * Define the task parameters (which should match what your core logic function needs).
        * Call your core logic function(s) from within the `@task`-decorated function. The function name inside will be what you confirmed (e.g., `async def process_vendor_x_record_task(...)`), and the `@task(name=...)` will be derived from your initial description.
        * Return the result.
        * Refer to "Project Alpha" task wrappers like `flows/dept_project_alpha/ingestion/public_api_data/tasks/parse_api_response_task_dept_project_alpha.py` for examples.
5.  **Define Task Configuration (Optional):**
    * A placeholder YAML config is created (e.g., `configs/variables/dept_beta_ops/ingestion/new_data_feed_vendor_x/tasks/process_vendor_x_record_task_config_dept_beta_ops.yaml`). The filename mirrors the Python task file's base name.
    * If your task requires runtime configuration (beyond what's passed directly as parameters), define it here. This config can be loaded within the task wrapper or passed from the calling flow. The comment for the Prefect Variable name will be generated according to the conventions.
6.  **Update `__init__.py`:**
    * Make your new task wrapper importable by adding it to the `__init__.py` file in its `tasks/` directory (e.g., `flows/dept_beta_ops/ingestion/new_data_feed_vendor_x/tasks/__init__.py`).
    * Example: `from .process_vendor_x_record_task_dept_beta_ops import process_vendor_x_record_task` (assuming `process_vendor_x_record_task` was the confirmed function name).
7.  **Call the Task:** Import and call your new task from the relevant category or parent flow.
8.  **Update Prefect Variables:** `make setup-variables` (if you added/changed task config YAMLs).
9.  **Add Unit Tests:** Write unit tests for your core logic functions in `airnub_prefect_starter/core/` or `airnub_prefect_starter/common/`.

## Local Testing and Iteration

* Use the local Docker environment (`make run-local`) extensively.
* Trigger individual flow runs (usually parent stage flows) from the Prefect UI for testing specific departments or categories by adjusting their run parameters.
* Add detailed logging using `get_run_logger()` in your Prefect flows/tasks, and standard `logging` in your core logic functions.
* Inspect worker logs: `docker compose logs -f worker`.
* For the "Project Alpha" demo, check the local demo artifact storage (e.g., under `./data/project_alpha_demo_outputs/` on your host, which maps to `/app/data/project_alpha_demo_outputs/` in the worker) for downloaded files and their JSON manifests.
* Check Prefect UI Artifacts generated by the demo flows.
* Iterate quickly by modifying code. For changes within Python files that are part of your project:
    * If using volume mounts in `docker-compose.yml` for development (common for faster iteration), simply stop and restart the flow run.
    * If your code is baked into the image and you don't use dev volumes, you'll need to:
        1.  Stop local services: `make stop-local`
        2.  Rebuild the worker image: `make build-docker` (or `make build-docker-no-cache` for a clean build)
        3.  Restart local services: `make run-local`
        4.  Reapply deployments (if entrypoints or flow definitions changed significantly, though often not needed if just task logic changed): `make build-deployments`
* Building the full Docker image (`make build-docker`) is primarily necessary if you change Python dependencies in `pyproject.toml` or modify the `Dockerfile.worker` itself.