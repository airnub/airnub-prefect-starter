# Project Goal: Flow Structure Definition for Airnub Prefect Starter

## Goal

The primary goal is to define a standard, scalable, and maintainable structure for organizing Prefect flows within this **Airnub Prefect Starter** template. This structure is tailored for scenarios involving potentially numerous distinct data sources ("Departments") and data types ("Categories") managed within an organization. This structure aims to:

1.  Establish clear **ownership** by grouping all flows related to a specific data source/domain (Department) together.
2.  Logically separate the different **stages** of work (e.g., `ingestion`, `processing`, `analysis`) *within* each Department's scope.
3.  Organize flows for specific **categories** or data types naturally within their relevant Department and Stage.
4.  Promote **modularity**, **clarity**, and **maintainability** as the number of Departments and Categories grows.
5.  Facilitate **code reuse** through shared tasks and a clear strategy for generic processing logic.
6.  Support straightforward **CI/CD** processes based on departmental changes.
7.  Provide good **visibility** in both the file system and the Prefect UI for developers working within specific domains.

## Guiding Principles

* **Department/Domain Grouping:** The primary organizational unit in the `flows` directory is the Department or data domain (e.g., `dept_project_alpha`). All related code resides within this top-level folder.
* **Stage Orchestration (within Department):** Parent orchestrator flows define the different phases of the workflow (`ingestion`, `processing`, `analysis`) for a Department. These flows reside directly under the department directory (e.g., `flows/dept_project_alpha/ingestion_flow_dept_project_alpha.py`).
* **Category Specificity (within Stage Subdirectories):** Logic for specific data types or sub-sources (Categories) resides within its own directory structure under the relevant stage subdirectory (e.g., `flows/dept_project_alpha/ingestion/public_api_data/`).
* **Focused Flows:** Each category flow file focuses on a specific task within its Department, Stage, and Category context.
* **Deployment Strategy:**
    * Parent orchestrator flows (e.g., `ingestion_flow_dept_project_alpha.py`) are typically the primary deployable units, allowing a stage for an entire department to be run.
    * Individual category-level flows can also be made deployable if granular, independent execution is required.
* **Task Reusability:** Core actions are implemented as reusable tasks within the main Python package (e.g., `airnub_prefect_starter/tasks/`). Department-specific task wrappers reside within the flow structure.
* **Generic Logic:** Truly generic processing logic should ideally live in shared libraries/packages or the common tasks within the `airnub_prefect_starter` package. An optional top-level `flows/generic/` directory can be considered for broadly applicable utility flows.

## Recommended `flows` Directory Structure (Department -> Stage -> Category)

This structure groups flows by Department first, then the parent orchestrator flow for each stage resides in the department directory. Category-specific flows are organized under stage-specific subdirectories.

```text
flows/
├── __init__.py                     # Makes 'flows' a package

├── dept_project_alpha/             # Example: Project Alpha Department
│   ├── __init__.py
│   │
│   ├── ingestion_flow_dept_project_alpha.py    # Parent flow for Ingestion Stage
│   ├── processing_flow_dept_project_alpha.py   # Parent flow for Processing Stage
│   ├── analysis_flow_dept_project_alpha.py     # Parent flow for Analysis Stage
│   │
│   ├── ingestion/                    # Subdirectory for Ingestion stage's categories & tasks
│   │   ├── __init__.py
│   │   ├── tasks/                    # Task wrappers specific to this stage (e.g., common ingest metrics)
│   │   │   ├── __init__.py
│   │   │   └── calculate_ingest_metrics_task_dept_project_alpha.py
│   │   │
│   │   └── public_api_data/          # Category: Public API Data
│   │       ├── __init__.py
│   │       ├── ingest_public_api_data_flow_dept_project_alpha.py  # Category-specific flow
│   │       └── tasks/                # Task wrappers specific to this category/stage
│   │           ├── __init__.py
│   │           └── parse_api_response_task_dept_project_alpha.py
│   │
│   │   └── scheduled_file_downloads/ # Category: Scheduled File Downloads
│   │       ├── __init__.py
│   │       └── download_scheduled_files_flow_dept_project_alpha.py # Category-specific flow
│   │
│   ├── processing/                   # Subdirectory for Processing stage's categories & tasks
│   │   ├── __init__.py
│   │   └── tasks/
│   │       └── __init__.py
│   │       └── # ... stage-level processing task wrappers for Project Alpha ...
│   │
│   └── analysis/                     # Subdirectory for Analysis stage's categories & tasks
│       └── # ... similar structure ...
│
└── dept_project_beta/              # Example: Project Beta Department (illustrating multiple depts)
    └── # ... similar structure ...
```
(The corresponding `configs/variables/` directory mirrors this structure for YAML configuration files.)

## Explanation of Structure

* **`flows/dept_<identifier>/`**: The primary organizational unit (e.g., `dept_project_alpha`). Facilitates team ownership and co-locates related code for a specific domain or project initiative.
* **`flows/dept_<identifier>/[stage_verb]_flow_dept_<identifier>.py`**: These are the parent orchestrator flows for each stage (e.g., `ingestion`, `processing`, `analysis`) within a department. They manage the execution of various category-specific flows for that stage.
* **`flows/dept_<identifier>/<stage_name>/` (e.g., `ingestion/`, `processing/`)**: These subdirectories house the category-specific flows and stage-level task wrappers relevant to that particular stage of work for the department.
* **`flows/dept_<identifier>/<stage_name>/<category_identifier>/` (e.g., `ingestion/public_api_data/`)**: Holds flows and task wrappers related to a specific data type or sub-source *within* that department and stage.
* **`.../<category_identifier>/<action>_<category_name>_flow_dept_<identifier>.py`**: These are the category-specific flows (e.g., `ingest_public_api_data_flow_dept_project_alpha.py`). They are called by the parent stage orchestrator flow.
* **`.../tasks/`**: Subdirectories (at stage or category level) for thin Prefect `@task` wrappers. These wrappers call core logic implemented in the main `airnub_prefect_starter` package.
* **`.../<category_identifier>/subflows/` (Optional)**: Can contain lower-level helper flows called *only* by the main flow of the category they reside within.

## Benefits of This Structure

* **Clear Ownership:** Teams can easily identify and manage all flows and configurations related to their department or project initiative.
* **Scalability:** Adding new departments, stages, or categories is straightforward and follows a consistent pattern, supported by generator scripts.
* **Maintainability:** Code related to specific concerns is well-isolated, making updates and debugging easier.
* **Prefect UI Clarity:** Flow and deployment names derived from this structure (e.g., "Ingestion Flow (Project Alpha)") are descriptive and easy to navigate in the Prefect UI. Tags further enhance filterability.

## Next Steps for Template Users

1.  **Understand the Structure:** Familiarize yourself with the Department -> Stage -> Category organization.
2.  **Use Generator Scripts:** Leverage `scripts/generators/add_department.py`, `add_category.py`, and `add_task.py` to scaffold new components. These scripts enforce the naming and directory conventions.
3.  **Implement Core Logic:** Place reusable business logic and data processing functions within the main `airnub_prefect_starter` package (e.g., in `common/` or new `logic/` modules). Task wrappers in the `flows/` structure should be thin calls to this core logic.
4.  **Configure:**
    * Define non-sensitive parameters in YAML files under `configs/variables/`, mirroring the flow structure. Use `scripts/setup_prefect_variables.py` to load these into Prefect Variables.
    * Use Prefect Blocks for secrets, credentials, and complex or shared infrastructure configurations. Update `scripts/setup_prefect_blocks.py` as needed for generic or new block types.
5.  **Deploy:** Define deployments in `prefect.local.yaml` (for local execution) or other environment-specific YAML files, targeting your parent stage orchestrator flows.

This structured approach provides an excellent foundation for managing complex data workflow environments using Prefect, prioritizing clear ownership, modularity, and maintainability.