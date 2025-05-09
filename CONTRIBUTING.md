# Contributing to Airnub Prefect Starter

First off, thank you for considering contributing! This project aims to provide a robust and extensible foundation for building data pipelines with Prefect 3. Your help in refining and expanding this starter template is invaluable.

This document provides guidelines for contributing new flows, tasks, and configurations to ensure consistency and maintainability across the project. Adhering to these conventions helps keep the codebase organized and makes it easier for scripts (like the generator scripts and the Prefect Variable setup script) to work correctly.

**Please use the generator scripts located in `scripts/generators/` whenever possible to scaffold new Prefect workflow components.**

## Table of Contents

-   [Project Structure](#project-structure)
    -   [Flows Directory (`flows/`)](#flows-directory-flows)
    -   [Configuration Directory (`configs/variables/`)](#configuration-directory-configsvariables)
    -   [Main Python Package (`airnub_prefect_starter/`)](#main-python-package-airnub_prefect_starter)
-   [Naming Conventions](#naming-conventions)
    -   [Directory Names](#directory-names)
    -   [Python File Names (Flows & Tasks)](#python-file-names-flows--tasks)
    -   [Configuration File Names (YAML)](#configuration-file-names-yaml)
    -   [Prefect Flow & Task Names (`@flow`/`@task`)](#prefect-flow--task-names-flowname)
    -   [Prefect Deployment Names (in YAML)](#prefect-deployment-names-in-yaml)
    -   [Prefect Variable Names (from YAML configs)](#prefect-variable-names-from-yaml-configs)
    -   [Python Function Names](#python-function-names)
-   [Generator Scripts](#generator-scripts)
    -   [`scripts/generators/add_department.py`](#scriptsgeneratorsadd_departmentpy)
    -   [`scripts/generators/add_category.py`](#scriptsgeneratorsadd_categorypy)
    -   [`scripts/generators/add_task.py`](#scriptsgeneratorsadd_taskpy)
-   [Adding a New Department](#adding-a-new-department)
-   [Adding a New Category to a Stage](#adding-a-new-category-to-a-stage)
-   [Adding a New Task (Department-Specific Wrapper)](#adding-a-new-task-department-specific-wrapper)
-   [Tagging Strategy](#tagging-strategy)
-   [Configuration Management](#configuration-management)
-   [Submitting Contributions](#submitting-contributions)

## Project Structure

The project follows a structured approach to organize Prefect flows, their specific task wrappers, configurations, and the core reusable Python logic.

### Flows Directory (`flows/`)

Prefect flow definitions and their department/category-specific **task wrappers** are organized by `Department -> Stage -> [Optional Category] -> tasks`.

```plaintext
flows/
├── dept_project_alpha/               # Example: Top-level for "Project Alpha" Department
│   ├── __init__.py
│   ├── ingestion_flow_dept_project_alpha.py   # Parent/Orchestrator flow for Ingestion stage
│   ├── processing_flow_dept_project_alpha.py  # Parent/Orchestrator flow for Processing stage
│   ├── analysis_flow_dept_project_alpha.py    # Parent/Orchestrator flow for Analysis stage
│   │
│   ├── ingestion/                    # Subdirectory for Ingestion stage's categories & tasks
│   │   ├── __init__.py
│   │   ├── tasks/                    # Task wrappers specific to this stage (e.g., common ingest metrics)
│   │   │   ├── __init__.py
│   │   │   └── process_ingestion_summary_task_dept_project_alpha.py # Example stage-level task
│   │   │
│   │   └── public_api_data/          # Example Category directory
│   │       ├── __init__.py
│   │       ├── ingest_public_api_data_flow_dept_project_alpha.py  # Category-specific flow
│   │       └── tasks/                # Task wrappers specific to this category/stage
│   │           ├── __init__.py
│   │           └── parse_api_response_task_dept_project_alpha.py
│   │
│   │   └── scheduled_file_downloads/ # Another Example Category directory
│   │       ├── __init__.py
│   │       ├── download_scheduled_files_flow_dept_project_alpha.py # Category-specific flow
│   │       └── tasks/
│   │           ├── __init__.py
│   │           └── download_file_task_dept_project_alpha.py
│   │
│   └── processing/                   # Subdirectory for Processing stage's categories & tasks
│       ├── __init__.py
│       └── tasks/
│           └── __init__.py
│           └── # ... stage-level processing task wrappers ...
│   └── analysis/                     # Subdirectory for Analysis stage's categories & tasks
│       └── # ... similar structure ...
│
└── # ... other departments (e.g., dept_project_beta) ...
```

* **Parent/Orchestrator Flows:** Reside directly under the department folder (e.g., `ingestion_flow_dept_project_alpha.py`). They manage a specific stage for that department by calling relevant category flows. Generated code includes `with tags(...)`.
* **Category/Component Flows:** Reside under the relevant `stage_name/category_identifier` directory (e.g., `ingestion/public_api_data/ingest_public_api_data_flow_dept_project_alpha.py`). They contain logic for a specific data category within that stage. Generated code includes `with tags(...)`.
* **Department-Specific Task Wrappers (`@task`)**: Reside within a `tasks/` subdirectory at the level they are most relevant (either directly under a stage like `flows/dept_project_alpha/ingestion/tasks/` or under a category like `flows/dept_project_alpha/ingestion/public_api_data/tasks/`). These are thin wrappers around core logic implemented in the main `airnub_prefect_starter` package (typically in `airnub_prefect_starter/core/`). They inherit tags from the calling flow.
* **Helper Flows (`@flow`)**: If a category flow needs further decomposition into smaller, reusable flow units *specific to that category*, they can be placed in a `subflows/` directory within the category directory (e.g., `flows/dept_project_alpha/ingestion/public_api_data/subflows/`). Generated code should include `with tags(...)`.

### Configuration Directory (`configs/variables/`)

Configuration YAML files for Prefect Variables mirror the `flows/` structure precisely, including the `tasks/` subdirectories for task-specific configs.

```plaintext
configs/
└── variables/
    ├── dept_project_alpha/
    │   ├── ingestion_config_dept_project_alpha.yaml     # Config for parent ingest flow
    │   ├── process_config_dept_project_alpha.yaml     # Config for parent process flow
    │   │
    │   ├── ingestion/
    │   │   ├── tasks/
    │   │   │   └── process_ingestion_summary_task_config_dept_project_alpha.yaml
    │   │   └── public_api_data/
    │   │       ├── ingest_public_api_data_config_dept_project_alpha.yaml # Config for category flow
    │   │       └── tasks/
    │   │           └── parse_api_response_task_config_dept_project_alpha.yaml # Config for task wrapper
    │   └── processing/ # etc.
    │
    └── # ... other departments ...
    └── department_mapping.yaml                 # Central mapping of dept_id -> Full Name
```

The `scripts/setup_prefect_variables.py` script loads these YAML files and creates Prefect Variables.

### Main Python Package (`airnub_prefect_starter/`)

This is the primary Python package containing reusable code and the foundational structure for data science prototyping.

* **`airnub_prefect_starter/common/`**: Contains truly generic, project-wide utilities (e.g., `utils.py` for functions like `sanitize_filename`, `generate_sha256_hash`) and foundational path configurations (e.g., `settings.py` if you choose to re-introduce it for managing `PROJECT_ROOT`, `EFFECTIVE_LOCAL_DATA_ROOT` via `pydantic-settings`. Otherwise, path configuration for data science scripts is handled in `airnub_prefect_starter/data_science/config_ds.py`). *This directory does not include database models or DB-specific settings in the base template, as application-level database functionality is an extension to be added by the user.*
* **`airnub_prefect_starter/core/`**: Houses the core Python logic functions that implement the main data processing and business rules for your operational pipelines. These functions are designed to be independent of Prefect and are called by Prefect task wrappers. Examples from the "Project Alpha" demo include `api_handlers.py`, `file_handlers.py`, `web_utils.py`, `artifact_creators.py`, and `manifest_models.py` (for Pydantic models of demo manifests).
* **`airnub_prefect_starter/data_science/`**: Contains modules and scripts originating from a data science project structure (e.g., Cookiecutter Data Science). This is the area for data exploration, R&D, and prototyping. It includes its own configuration for paths (e.g., `config_ds.py`) and example scripts like `dataset_processing.py`, `feature_engineering.py`, and `modeling/`. Logic developed here can be refactored into `airnub_prefect_starter/core/` for operationalization within Prefect workflows.
* **`airnub_prefect_starter/tasks/`**: (Initially empty in the base template) This directory is reserved for any future *common, reusable Prefect task wrappers* that are not specific to a single department/category and might be used across multiple Prefect flows. These wrappers would typically call logic from `airnub_prefect_starter/core/` or `airnub_prefect_starter/common/`.

## Naming Conventions

Consistent naming is crucial. The department identifier (`dept_[id]`) is typically the final component before the extension in filenames for department-specific components located under `flows/` or `configs/variables/`.

### Directory Names

* **Department Directories**: `dept_[identifier]` (e.g., `dept_project_alpha`).
* **Stage Subdirectories (under Department; for categories/tasks)**: `ingestion`, `processing`, `analysis`.
* **Category Directories (under Stage Subdirectory)**: `[category_identifier]` (e.g., `public_api_data`).
* **Tasks Subdirectories**: Always named `tasks`.

### Python File Names (Flows & Tasks)

* **Parent/Orchestrator Flows**: `[stage_verb]_flow_dept_[dept_identifier].py`
    * Example: `flows/dept_project_alpha/ingestion_flow_dept_project_alpha.py`
* **Category/Component Flows**: `[action_verb]_[category_identifier]_flow_dept_[dept_identifier].py` (Note: `category_identifier` is the sanitized directory name)
    * Example: `flows/dept_project_alpha/ingestion/public_api_data/ingest_public_api_data_flow_dept_project_alpha.py`
* **Department-Specific Task Wrappers (in `flows/.../tasks/`)**: `[task_base_name]_task_dept_[dept_identifier].py`
    * Example (Stage Level): `flows/dept_project_alpha/ingestion/tasks/process_ingestion_summary_task_dept_project_alpha.py`
    * Example (Category Level): `flows/dept_project_alpha/ingestion/public_api_data/tasks/parse_api_response_task_dept_project_alpha.py`
* **Common Task Wrappers (in `airnub_prefect_starter/tasks/`)**: `[action]_[entity]_task.py` (No department suffix). This directory is empty in the base template.
    * Example (if one were added): `airnub_prefect_starter/tasks/send_generic_notification_task.py`

### Configuration File Names (YAML)

Principle: Mirror the corresponding Python file, replacing `_flow` or `_task` with `_config`.

* **Parent Flow Config**: `[stage_verb]_config_dept_[dept_identifier].yaml`
    * Example: `configs/variables/dept_project_alpha/ingestion_config_dept_project_alpha.yaml`
* **Category Flow Config**: `[action_verb]_[category_identifier]_config_dept_[dept_identifier].yaml`
    * Example: `configs/variables/dept_project_alpha/ingestion/public_api_data/ingest_public_api_data_config_dept_project_alpha.yaml`
* **Task Config (in `configs/.../tasks/`)**: `[task_base_name]_task_config_dept_[dept_identifier].yaml`
    * Example (Stage Level): `configs/variables/dept_project_alpha/ingestion/tasks/process_ingestion_summary_task_config_dept_project_alpha.yaml`
    * Example (Category Level): `configs/variables/dept_project_alpha/ingestion/public_api_data/tasks/parse_api_response_task_config_dept_project_alpha.yaml`

### Prefect Flow & Task Names (`@flow`/`@task`)

Use natural language for readability in the UI.

* **Parent/Orchestrator Flows**: `"[Stage] Flow ([Full Department Name])"`
    * Example: `@flow(name="Ingestion Flow (Project Alpha)")`
* **Category/Component Flows**: `"[Action Verb] [Category Display Name] ([Full Department Name])"`
    * Example: `@flow(name="Ingest Public API Data (Project Alpha)")`
* **Task Wrappers**: `"[Action/Description Title Case]"`
    * Example: `@task(name="Process Ingestion Summary")`
    * Example: `@task(name="Parse API Response")`

### Prefect Deployment Names (in YAML)

Identify specific configurations for running parent orchestrator flows.

* **Pattern**: `"[Stage] Deployment ([Full Department Name])"`
* Example for `prefect.local.yaml` (as generated by `add_department.py`):
    * `name: "Ingestion Deployment (Project Alpha) - Local Dev"`
* (Note: The ` - Local Dev` suffix is added by the generator for clarity in the local deployment file).

### Prefect Variable Names (from YAML configs)

Generated by `scripts/setup_prefect_variables.py`.

* **Pattern**: `[dept_identifier]_[stage]_[optional_category_identifier]_[optional_task_base_name]_config`
* Examples:
    * `dept_project_alpha_ingestion_config`
    * `dept_project_alpha_ingestion_public_api_data_config`
    * `dept_project_alpha_ingestion_public_api_data_parse_api_response_task_config`
* Note: The `scripts/setup_prefect_variables.py` script handles the derivation from the file path and name.

### Python Function Names

Use `snake_case` (e.g., `ingest_flow_dept_project_alpha`, `ingest_public_api_data_flow_dept_project_alpha`, `process_ingestion_summary_task_dept_project_alpha`). Core logic functions in `airnub_prefect_starter/core/` should also be `snake_case` (e.g., `core_fetch_json_from_api`).

## Generator Scripts

Use these scripts in `scripts/generators/` to scaffold new Prefect workflow components consistently:

### `scripts/generators/add_department.py`

* Creates the directory structure for a new department under `flows/` and `configs/variables/`.
* Generates placeholder parent orchestrator flow files (`[stage]_flow_dept_[id].py`) directly in the department folder, and config files (`[stage]_config_dept_[id].yaml`) in the corresponding config department folder. Creates stage subdirectories (e.g., `ingestion/`, `processing/`) with `__init__.py` and `.gitkeep` for housing category flows and tasks. Includes `with tags(...)` in parent flows.
* Updates the `configs/department_mapping.yaml` file.
* Optionally adds default deployment definitions (`[Stage] Deployment ([Dept Name]) - Local Dev`) to `prefect.local.yaml`.

### `scripts/generators/add_category.py`

* Creates a category subdirectory under the specified `department/stage_name` in `flows/` and `configs/variables/`.
* Generates a placeholder category flow file (`[action]_[cat_id]_flow_dept_[id].py`) and config file (`[action]_[cat_id]_config_dept_[id].yaml`). Includes `with tags(...)` in category flows.
* Detects existing departments and their stage subdirectories to guide selection.

### `scripts/generators/add_task.py`

* Creates a placeholder task wrapper file (`[base]_task_dept_[id].py`) within the specified `department/stage_name/[optional_category]/tasks/` subdirectory in `flows/`.
* Creates a corresponding placeholder config file (`[base]_task_config_dept_[id].yaml`) in the parallel `configs/variables/.../tasks/` directory.
* Guides the user to implement core logic separately in the `airnub_prefect_starter/core/` subpackage. Does **not** add `with tags(...)` to the task wrapper itself.
* Detects existing departments, stages, and categories to guide placement.

## Adding a New Department

1.  Run `python scripts/generators/add_department.py`.
2.  Follow the prompts (e.g., Full Name: "Beta Project Group", Identifier: `dept_beta_group`).
3.  Implement logic in generated parent flow files (e.g., `flows/dept_beta_group/ingest_flow_dept_beta_group.py`) to call category flows.
4.  Define configurations in generated config files (e.g., `configs/variables/dept_beta_group/ingest_config_dept_beta_group.yaml`) for the parent flow and its categories.
5.  Use `scripts/generators/add_category.py` to add category flows/configs under the stage subdirectories (e.g., `flows/dept_beta_group/ingestion/`).
6.  Use `scripts/generators/add_task.py` to add department-specific task wrappers/configs within the new department structure, calling core logic from `airnub_prefect_starter/core/`.
7.  **Crucially**: Run `python scripts/setup_prefect_variables.py` to create/update Prefect Variables from the new YAML files.
8.  Review/add deployment definitions in `prefect.local.yaml` (or other environment-specific YAMLs).
9.  Apply deployments using `prefect deploy ...` (e.g., `make build-deployments`).

## Adding a New Category to a Stage

1.  Run `python scripts/generators/add_category.py`.
2.  Follow the prompts (e.g., select department `dept_project_alpha`, stage `ingestion`, category name "User Input Files", action verb "Process").
3.  Implement logic in the generated category flow file (e.g., `flows/dept_project_alpha/ingestion/user_input_files/process_user_input_files_flow_dept_project_alpha.py`).
4.  Define configuration in the generated category config file.
5.  Modify the parent stage orchestrator flow (e.g., `flows/dept_project_alpha/ingest_flow_dept_project_alpha.py`) to import and call your new category flow.
    * Example Import: `from .ingestion.user_input_files.process_user_input_files_flow_dept_project_alpha import process_user_input_files_flow_dept_project_alpha` (adjust based on actual generated names).
6.  Use `scripts/generators/add_task.py` to add any tasks specific to this category.
7.  Run `python scripts/setup_prefect_variables.py`.

## Adding a New Task (Department-Specific Wrapper)

1.  Run `python scripts/generators/add_task.py`.
2.  Follow the prompts for description, function name, department, stage, and optionally category.
3.  Implement the core logic in a suitable function within the `airnub_prefect_starter.core` subpackage (e.g., in `core/custom_processing_logic.py`, `core/file_handlers.py`) or, if truly generic and small, in `airnub_prefect_starter/common/utils.py`.
4.  Update the generated task wrapper file (e.g., `flows/dept_project_alpha/ingestion/public_api_data/tasks/parse_api_response_task_dept_project_alpha.py`) to import and call the core logic function. Define parameters and return types.
5.  Define configuration in the generated task config file.
6.  Update the relevant `__init__.py` file(s) (e.g., `flows/dept_project_alpha/ingestion/public_api_data/tasks/__init__.py`) to make the task wrapper importable.
    * Example: Add `from .parse_api_response_task_dept_project_alpha import parse_api_response_task_dept_project_alpha` to the `tasks/__init__.py`.
    * Then import from a flow in that category using `from .tasks import parse_api_response_task_dept_project_alpha`.
7.  Run `python scripts/setup_prefect_variables.py` if the new task config should become a Prefect Variable.
8.  Add unit tests for the core logic function in `airnub_prefect_starter/core/` or `airnub_prefect_starter/common/`.

## Tagging Strategy

* **Flows (Parent & Category)**: Generated by the scripts include a `with tags(...)` block that applies tags for the `department_id`, `stage`, and `category_id` (if applicable) to the context. Tasks/subflows called within this context will inherit these tags.
* **Tasks**: Department-specific task wrappers generated by `add_task.py` do not include their own `with tags(...)` block, as they inherit tags from the calling flow's context.
* **Deployments**: Deployment definitions in YAML should include relevant tags (e.g., `dept_project_alpha`, `ingestion`, `example`). These tags are automatically applied to all flow runs created from that deployment. The `add_department.py` script adds default tags to the generated local deployments.

## Configuration Management

* **Prefect Variables (from YAML)**: Used for non-sensitive flow/task parameters (URLs, selectors, thresholds, etc.). Structure defined in `configs/variables/`. Created/updated via `scripts/setup_prefect_variables.py`. Flows/tasks load these via `prefect.variables.Variable.get(...)`.
* **Prefect Blocks**: Used for sensitive information (credentials like API keys), infrastructure definitions (e.g., `DockerContainer`), or configurations for external services.
    * The base template's `scripts/setup_prefect_blocks.py` primarily handles local infrastructure blocks (like a Docker container block for the worker).
    * When extending the template for specific cloud services (e.g., for remote storage like AWS S3, GCS, Azure Blob), you would typically:
        1. Add the relevant Prefect integration library (e.g., `prefect-aws`, `prefect-gcp`) as an optional dependency in `pyproject.toml` (e.g., under an `[project.optional-dependencies].aws` group).
        2. Update `scripts/setup_prefect_blocks.py` (or create a new script) to handle the creation of provider-specific blocks (e.g., `S3Bucket`, `GCSBucket`, `AzureBlobStorageContainer`), often requiring specific environment variables for credentials and resource names.
        3. Pass the names of these configured blocks as parameters to your flows or define them in Prefect Variables if the block name itself needs to be configurable per environment.
* `configs/department_mapping.yaml`: Central mapping of `dept_identifier` to Full Department Name. Keep this updated when adding departments (handled automatically by `add_department.py`).

## Submitting Contributions

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix (e.g., `git checkout -b feat/add-dept-X` or `fix/bug-in-Y`).
3.  Make your changes, adhering to the project structure and naming conventions defined in this document. Use the generator scripts where applicable.
4.  Add unit tests for any new core logic functionality in `airnub_prefect_starter/core/` or `airnub_prefect_starter/common/`.
5.  Ensure your code lints (`make lint` if available, or follow project linting guidelines).
6.  Update documentation (including this `CONTRIBUTING.md` if conventions change) if you've added new flows, changed configurations, or modified behavior.
7.  Commit your changes with clear, descriptive commit messages.
8.  Push your branch to your fork.
9.  Open a Pull Request against the main repository.
    * Clearly describe the changes you've made and why.
    * Link to any relevant issues.

We appreciate your contributions to making this project more comprehensive!
