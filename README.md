# Airnub Prefect Starter

![Prefect Version](https://img.shields.io/badge/Prefect-%E2%98%95%203.x-0052FF?logo=prefect&labelColor=000000)
![Python Version](https://img.shields.io/badge/python-3.12%2B%20%7C%203.12-blue)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.md)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-green.svg)](https://airnub.github.io/airnub-prefect-starter/)

A robust starter template for building data pipelines with Prefect 3. This template provides a standardized foundation for creating configurable, containerized, and maintainable data workflows.

## Overview

This project provides a best-practice foundation for building data pipelines using **Prefect 3**. Key features include:

* **Modern Prefect Workflows:** Utilizes Prefect 3 flows, tasks, and deployment patterns.
* **Dockerized Environment:** Includes `Dockerfile.worker` and `docker-compose.yml` for easy local development and reproducible containerized deployments.
* **Configurable Pipelines:** Leverages Prefect Blocks for dynamic configuration and secrets management. Flow parameters can be easily managed for different environments using Prefect Variables (derived from YAML files).
* **Local-First Development:** Designed for a seamless local development experience with sensible defaults, including local filesystem for demo data storage and local JSON manifests. Prefect server uses a local PostgreSQL database via Docker.
* **Scalable Structure:** Organized by "Departments" (e.g., `dept_project_alpha`) and "Categories" to manage complex projects with multiple data sources and teams. Includes generator scripts to scaffold new Prefect workflow components consistently.
* **Integrated Data Science Prototyping:** Incorporates a structure for data science exploration and prototyping scripts, with a clear path to operationalizing logic into Prefect workflows.
* **Idempotent by Design:** Core patterns demonstrated (e.g., content hashing) encourage preventing reprocessing of existing data.
* **Extensible:** While this starter is cloud-agnostic, it can be extended to integrate with various cloud services (like object storage or container orchestrators) by adding relevant Prefect Blocks and optional dependencies.

**➡️ For detailed setup, usage, and development guides, please see the full documentation site hosted at:**
**[https://airnub.github.io/airnub-prefect-starter/](https://airnub.github.io/airnub-prefect-starter/)**

## Quick Start (Local Development)

1.  **Prerequisites:**
    * Python (see `pyproject.toml` for version, e.g., 3.12+)
    * Docker & Docker Compose
    * `make` (Optional, but recommended for convenience)
    * Git

2.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/airnub/airnub-prefect-starter.git](https://github.com/airnub/airnub-prefect-starter.git) # Replace with your actual repo URL if different
    cd airnub-prefect-starter
    ```

3.  **Setup Environment & Configuration Files:**
    * **Environment Variables (`.env` file):**
        This project uses a `.env` file at the project root to manage environment variables for Docker Compose and some scripts.
        Copy the example file (if one is provided in the template, e.g., `.env.example`):
        ```bash
        cp .env.example .env # Create .env if .env.example exists
        ```
        Then, review and customize your `.env` file. It's primarily used by `docker-compose.yml` for Prefect server settings.
        **Important:** Ensure your `.env` file (if it contains secrets) is listed in your `.gitignore` file.

    * **Python Virtual Environment & Dependencies:**
        *This uses `uv` (a fast Python package manager) as defined in the Makefile.*
        ```bash
        make create_environment
        source .venv/bin/activate  # On Unix/macOS
        # .\.venv\Scripts\activate  # On Windows
        make install
        ```

4.  **Configure Prefect API Target & Server Settings:**
    * **Set API URL for Client:** Tell your local Prefect CLI and scripts where to connect. You can set this in your shell, or add it to your `.env` file (if your Python scripts load it) or a `setup.env` file (for `make` targets).
        ```bash
        # For the local Docker Compose setup (started in the next step):
        export PREFECT_API_URL="[http://127.0.0.1:4200/api](http://127.0.0.1:4200/api)"

        # For Prefect Cloud (replace with your actual URL and ensure PREFECT_API_KEY is set):
        # export PREFECT_API_URL="YOUR_PREFECT_CLOUD_API_URL"
        # export PREFECT_API_KEY="YOUR_PREFECT_CLOUD_API_KEY"
        ```

    * **Review Docker Compose Configuration (Important for UI Access):**
        The `docker-compose.yml` file configures the Prefect server. For the UI to be accessible from your host machine (e.g., `http://127.0.0.1:4200`), the Prefect server inside the Docker container must listen on `0.0.0.0`. This is typically set via `PREFECT_SERVER_API_HOST: "0.0.0.0"` in the `environment` section of the `server` service in `docker-compose.yml` (often sourced from the `.env` file). This template's `docker-compose.yml` is pre-configured for this.

5.  **Run Local Development Services:**
    This starts the Prefect Server & UI, a PostgreSQL database (for Prefect server metadata), and a custom Prefect Worker using Docker Compose. These services may use configurations from your `.env` file.
    ```bash
    make run-local
    ```
    *Access the Prefect UI at: `http://127.0.0.1:4200`*

6.  **Set up Prefect Blocks & Variables (Configuration):**
    Flows load configuration from Prefect Blocks (for infrastructure/secrets) and Prefect Variables (for runtime parameters from YAML files).
    * **Create a `setup.env` file (Optional but Recommended for `make` targets):**
        Place environment variables needed by `make setup-blocks` and `make setup-variables` in a `setup.env` file (add to `.gitignore` if it contains secrets). The `make` targets will attempt to load it.
        Example `setup.env` content:
        ```env
        # PREFECT_API_URL="[http://127.0.0.1:4200/api](http://127.0.0.1:4200/api)" # Can also be set here
        # PREFECT_BLOCK_OVERWRITE=true # To force overwrite existing Variables/Blocks
        ```
    * **Run Setup Scripts:**
        ```bash
        # Ensure PREFECT_API_URL is set (from step 4, .env, or setup.env)
        make setup-blocks  # Sets up essential infrastructure blocks (e.g., placeholder Secret).
        make setup-variables # Creates Prefect Variables from configs/variables/*.yaml.
        ```
        *(The generic `setup-blocks` script primarily sets up local infrastructure blocks. Extending for specific cloud providers involves modifying this script or adding new ones for provider-specific blocks and likely new env vars.)*

7.  **Apply Flow Deployments:**
    Register the example flows (e.g., for "Project Alpha") with the local Prefect server.
    ```bash
    make build-deployments
    ```
    Check the "Deployments" page in the Prefect UI. (Note: These may fail to run without the `local-worker-infra` block).

8.  **Run Your First Flow:**
    * Navigate to the "Deployments" page in the Prefect UI.
    * Find an example deployment (e.g., "Ingestion Deployment (Project Alpha)").
    * Click the "Run" button (▶️) and accept the defaults.
    * Monitor the flow run on the "Flow Runs" page and check worker logs: `docker compose logs -f worker`.

## Documentation

For full details on project structure, adding new flows/tasks, configuration, and extending the template, please refer to the **official documentation site**:

**[https://airnub.github.io/airnub-prefect-starter/](https://airnub.github.io/airnub-prefect-starter/)**

You can also build and view the documentation locally:

1.  Navigate to the `docs/` directory:
    ```bash
    cd docs
    ```
2.  Install documentation tools (if not already installed via `make install` with a `docs_build` extra):
    ```bash
    # Assuming mkdocs and mkdocs-material are in pyproject.toml [project.optional-dependencies].docs_build
    uv pip install -e "..[docs_build]" # Install from parent directory with docs extra
    # Or manually: pip install mkdocs mkdocs-material
    ```
3.  Serve the documentation locally:
    ```bash
    mkdocs serve
    ```
    *View the documentation site at `http://127.0.0.1:8000`.*

## Core Project Structure Overview

* **`airnub_prefect_starter/`**: The main Python package.
    * `common/`: Truly generic utilities (e.g., `utils.py`) and foundational path configurations (e.g., from `config.py` if `common/settings.py` is not used for paths).
    * `core/`: Contains the core Python logic functions that are wrapped by your Prefect tasks (e.g., `api_handlers.py`, `file_handlers.py`). This is where the main "business logic" for operational pipelines resides.
    * `data_science/`: Modules and scripts for data exploration, R&D, and prototyping (e.g., `config_ds.py`, `dataset_processing.py`, `modeling/`).
    * `tasks/`: (Initially empty) Intended for future *common, reusable Prefect task wrappers* that might span multiple departments.
* **`configs/`**:
    * `variables/`: YAML configuration files for Prefect flows/tasks, loaded into Prefect Variables. Structure mirrors `flows/`.
    * `department_mapping.yaml`: Maps department identifiers to full names.
* **`data/`**: Default local directory for data science stages (raw, processed, etc.) and demo artifacts (gitignored).
* **`docs/`**: Project documentation source files.
* **`flows/`**: Prefect flow definitions and their department/category-specific task wrappers, organized by `dept_<id>/<stage_name>/<category_id>/`.
* **`scripts/`**: Helper scripts for development and operations.
    *   `generators/`: Scripts to scaffold new Prefect workflow components. These scripts enforce specific project conventions for file naming and directory structure. For details, see the [Project Conventions documentation](docs/docs/development.md#project-conventions-and-generators).
* **`tests/`**: Unit and integration tests.
* **`.env.example`**: Example environment variables for `docker-compose.yml`. **Copy to `.env` and customize.**
* **`.env`**: Local environment configuration file used by Docker Compose (should be in `.gitignore`).
* **`docker-compose.yml`**: Defines the local development environment.
* **`Dockerfile.worker`**: Builds the custom Prefect worker image.
* **`Makefile`**: Convenience commands for common tasks.
* **`prefect.local.yaml`**: Default Prefect deployment definitions for the local environment.
* **`prefect.yaml`**: Base Prefect project configuration, often for remote deployment build/push/pull steps.
* **`pyproject.toml`**: Project metadata and Python dependencies.
* **`notebooks/`**: For Jupyter notebooks used in data exploration and prototyping.
* **`models/`**: For serialized trained machine learning models (if applicable).
* **`reports/`**: For generated reports and figures.

## Contributing

Contributions are welcome! Please refer to `CONTRIBUTING.md` for guidelines on how to add new components and adhere to project conventions.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.