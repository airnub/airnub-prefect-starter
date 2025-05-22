# Core Concepts & Architecture

This document describes the high-level architecture and core concepts of the **`airnub-prefect_starter`** template. This template provides a foundation for building robust, configurable, and maintainable data pipelines using Prefect 3.

## Key Components

1.  **Prefect 3 Engine:** The workflow orchestration engine used for defining, scheduling, running, and monitoring flows and tasks. This includes the Prefect Server & UI (run locally via Docker Compose in this template, or connectable to Prefect Cloud).
2.  **Prefect Worker:** Executes the flow runs submitted by the Prefect Server. In this template, it runs within a Docker container defined by `Dockerfile.worker`.
3.  **Main Python Package (`airnub_prefect_starter/`):** This is the primary installable Python package containing your project's reusable code and foundational structures.
    * **`common/`**: Houses truly generic, project-wide utilities (e.g., `utils.py` for functions like `sanitize_filename`, `generate_sha256_hash`) and potentially foundational path configurations (path configuration for data science scripts is primarily in `data_science/config_ds.py`, as `common/settings.py` is not included in the base template but could be added by users for more complex path or application database configurations). The base template does not include application-level database models or DB-specific settings here by default.
    * **`core/`**: Contains the core Python logic functions that implement the main data processing and business rules for your operational pipelines. These functions are designed to be Prefect-agnostic and are called by your department-specific Prefect task wrappers. Examples include `api_handlers.py`, `file_handlers.py`, `web_utils.py`, `artifact_creators.py` (for creating Prefect artifacts), and `manifest_models.py` (Pydantic models for demo manifest structures).
    * **`data_science/`**: Includes modules and scripts typically found in data science projects (e.g., inspired by Cookiecutter Data Science). This is the designated area for data exploration, R&D, and prototyping. It contains its own path configuration (e.g., `config_ds.py`) and example scripts like `dataset_processing.py` and `modeling/`. Logic prototyped here can be refactored into `airnub_prefect_starter/core/` for operationalization within Prefect workflows.
    * **`tasks/`**: (Initially empty in the base template) This directory is reserved for any future *common, reusable Prefect task wrappers* that are not specific to a single department/category and might be used across multiple flows.
4.  **Prefect Flow Definitions (`flows/` directory):**
    * This top-level directory contains all Prefect flow definitions and their associated department/category-specific task wrappers.
    * Structure: `flows/dept_<id>/[stage_verb]_flow_dept_<id>.py` for parent stage orchestrators.
    * Category flows and their specific task wrappers reside in `flows/dept_<id>/<stage_name>/<category_id>/`.
5.  **Configuration (`configs/` directory & `.env` file):**
    * **Prefect Variables (from `configs/variables/*.yaml`):** YAML files define runtime parameters for flows and tasks. The `scripts/setup_prefect_variables.py` script loads these into Prefect Variables. The structure mirrors `flows/`.
    * **Prefect Blocks:** Used for managing secrets (e.g., API keys), infrastructure configurations (like the `docker-container/local-worker-infra` block for local Docker execution), and connections to external services. Managed via `scripts/setup_prefect_blocks.py` (for local/generic blocks) or the Prefect UI/CLI.
    * **`.env` file (at project root):** Used by `docker-compose.yml` to set environment variables for the Docker services (e.g., Prefect server database connection, API host settings).
    * **`configs/department_mapping.yaml`**: Maps department identifiers to full display names.
6.  **Demo Manifests & Storage (Local by Default):**
    * The "Project Alpha" demo flows are designed to showcase data ingestion, processing, and manifest creation.
    * **Storage:** Downloaded files for the demo are stored locally within the worker container (e.g., in a CAS-like structure under `/app/local_demo_artifacts/`, which can be mapped to `./data/project_alpha_demo_outputs/` on the host via Docker volumes).
    * **Manifests:** For the demo, manifest entries are created as:
        1.  Local JSON files stored alongside the data in the CAS-like structure.
        2.  Prefect UI Artifacts (Markdown) for visibility within flow runs.
    * The template is extensible to use Prefect Blocks for remote storage (e.g., S3, GCS) if desired.
7.  **Docker (`docker-compose.yml`, `Dockerfile.worker`):**
    * Provides a containerized local development environment for the Prefect server, UI, PostgreSQL database (for Prefect server metadata), and the custom Python worker.

## Core Concepts & Workflow (Data Ingestion Example)

Let's consider an example ingestion flow from "Project Alpha," such as `download_scheduled_files_flow_dept_project_alpha.py`. A typical workflow involves:

1.  **Load Configuration:**
    * The parent stage flow (e.g., `ingestion_flow_dept_project_alpha.py`) loads its main configuration (which includes sections for its category flows) from a Prefect Variable (e.g., `dept_project_alpha_ingestion_config`).
    * It then calls the category flow (e.g., `download_scheduled_files_flow_dept_project_alpha`), passing the relevant part of the configuration.
2.  **Execute Category Flow Logic:**
    The category flow (`download_scheduled_files_flow_dept_project_alpha.py`) performs its specific tasks:
    * It iterates through a list of file URLs defined in its configuration.
    * For each file:
        * It calls a department-specific task wrapper (e.g., `download_file_task_dept_project_alpha` from `flows/dept_project_alpha/ingestion/scheduled_file_downloads/tasks/`).
        * This task wrapper, in turn, calls core logic functions from `airnub_prefect_starter/core/file_handlers.py` (e.g., `core_download_hash_store_and_manifest`).
3.  **Core Logic Functions perform the work:**
    * `core_download_hash_store_and_manifest` (example):
        * Downloads the file from the URL to a temporary location within the worker.
        * Calculates the SHA256 hash of the file content using functions from `common/utils.py`.
        * **Idempotency Check (Conceptual for Demo):** While the base template doesn't include a persistent cross-run manifest database by default, the *principle* of idempotency is key. For the demo, idempotency might be checked by seeing if a file with the same hash already exists in the local demo CAS within the worker container. For a production system, this check would typically involve querying a persistent manifest store (like a database, which a user could add).
        * **Store Locally (CAS-like):** If the file is new (or reprocessing is intended), it's moved to a structured local directory (e.g., `/app/local_demo_artifacts/downloads/project_alpha_scheduled_files/<hash>/<filename>`).
        * **Create Local JSON Manifest:** A JSON file detailing metadata (source URL, hash, local path, headers, timestamp, etc., structured by a Pydantic model from `core/manifest_models.py`) is saved alongside the document in the CAS directory.
    * The task wrapper receives a dictionary of results from the core logic.
4.  **Create Prefect Artifact:**
    * Another department-specific task (e.g., `create_manifest_archive_task_dept_project_alpha`) is called.
    * This task uses a function from `airnub_prefect_starter/core/artifact_creators.py` to generate a Prefect Markdown artifact in the UI, summarizing the downloaded file and linking to its local manifest JSON path (within the worker).
5.  **(Optional) Trigger Downstream Processing:** The parent stage flow could trigger subsequent stages (e.g., processing flows) based on the success or outputs of the ingestion flows.

### Local-First Operation & Extensibility

The template is designed to work seamlessly out-of-the-box for local development:

* **Prefect Server Database:** Uses PostgreSQL running in Docker, configured via `docker-compose.yml` and `.env`.
* **Demo Data Storage & Manifests:** All demo data (downloaded files, scraped content) and their associated JSON manifest files are stored on the local filesystem within the worker container (in a directory like `/app/local_demo_artifacts/` which can be volume-mapped from `./data/project_alpha_demo_outputs/` on the host).
* This local-first approach allows developers to quickly get started without configuring external cloud services. The template can then be **extended** to use cloud storage (S3, GCS, etc.) by:
    1.  Adding optional dependencies (e.g., `prefect-aws`).
    2.  Creating and configuring appropriate Prefect storage blocks (e.g., `S3Bucket`).
    3.  Modifying the core logic (or adding new logic in `airnub_prefect_starter/core/`) and task wrappers to interact with these blocks.

### Configuration Loading Summary

* **Prefect Variables:** Runtime parameters for flows/tasks are loaded from Prefect Variables, which are populated from YAML files in `configs/variables/` via `scripts/setup_prefect_variables.py`.
* **Prefect Blocks:** Secrets, infrastructure details (like the `docker-container/local-worker-infra` block), and connections to external services are managed as Prefect Blocks.
* **Python Module Configuration (`airnub_prefect_starter/data_science/config_ds.py`):** Defines file paths and settings primarily for the standalone data science scripts and notebooks. It calculates paths like `PROJECT_ROOT` itself. The `airnub_prefect_starter/common/settings.py` module is not included in the base template but could be added by users for more complex path or application database configurations.
* **Environment Variables (`.env`):** Used by `docker-compose.yml` to configure services (like Prefect server's database connection and API host) and can be loaded by `python-dotenv` in Python scripts for further configuration.

This architecture promotes separation of concerns, clear organization, configurability, and testability, supporting both local development and providing a solid foundation for extension into more complex, cloud-integrated data pipelines.