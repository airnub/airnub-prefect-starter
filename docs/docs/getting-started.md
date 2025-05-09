# Getting Started

This guide walks you through setting up the `airnub-prefect-starter` project on your local machine for development and running your first flow.

## Prerequisites

Before you begin, ensure you have the following installed:

* **Python:** Version specified in `pyproject.toml` (e.g., 3.12+). We recommend using a Python version manager like `pyenv`.
* **Docker:** Required for running the local development environment (Prefect Server, Database, Worker). Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine/CLI.
* **Docker Compose:** Usually included with Docker Desktop. Verify with `docker compose version`.
* **Git:** For cloning the repository.
* **`make`:** (Optional, Recommended) For using the convenient Makefile commands. Available on Linux/macOS, may require installation on Windows (e.g., via Chocolatey or WSL).

## Setup Steps

1.  **Clone the Repository:**
    Open your terminal and clone the project repository:
    ```bash
    git clone <your-repository-url> # e.g., [https://github.com/your-org/airnub-prefect-starter.git](https://github.com/your-org/airnub-prefect-starter.git)
    cd airnub-prefect-starter
    ```

2.  **Create and Activate Virtual Environment:**
    It's crucial to work within a virtual environment to manage dependencies.
    ```bash
    # Create the environment (using uv, as per Makefile):
    make create_environment
    # Or using Python's built-in venv:
    # python -m venv .venv

    # Activate the environment
    # On macOS/Linux:
    source .venv/bin/activate
    # On Windows (Command Prompt):
    # .\.venv\Scripts\activate.bat
    # On Windows (PowerShell):
    # .\.venv\Scripts\Activate.ps1
    ```
    You should see `(.venv)` at the beginning of your terminal prompt.

3.  **Install Dependencies:**
    This project uses `uv` (a fast Python package installer/resolver). The `make install` command handles installing `uv` (if not present globally and then project dependencies).
    ```bash
    make install
    ```
    *(This typically runs `uv pip install --no-cache --upgrade -e ".[dev]"` which includes development dependencies).*

4.  **Configure Prefect API Target:**
    Prefect needs to know which API endpoint to communicate with (your local server or Prefect Cloud). Set the `PREFECT_API_URL` environment variable.
    ```bash
    # For the local Docker Compose setup (we'll start this soon):
    export PREFECT_API_URL="[http://127.0.0.1:4200/api](http://127.0.0.1:4200/api)"

    # If connecting to Prefect Cloud (replace with your actual URL/Key):
    # export PREFECT_API_URL="YOUR_PREFECT_CLOUD_API_URL"
    # export PREFECT_API_KEY="YOUR_PREFECT_CLOUD_API_KEY" # Required for Cloud
    ```
    **Tip:** For persistent local configuration, consider adding this `export` line to your shell's profile (`.zshrc`, `.bashrc`, `.bash_profile`) or use a `.env` file at the project root (see `README.md` for notes on `.env` usage with Docker Compose and scripts).

5.  **Start Local Development Services:**
    This uses Docker Compose to start the Prefect Server, UI, PostgreSQL database, and the custom Prefect Worker based on the project's `Dockerfile.worker`.
    ```bash
    make run-local
    ```
    Wait for the services to initialize. You'll see logs in your terminal.

6.  **Access Prefect UI:**
    Open your web browser and navigate to `http://127.0.0.1:4200`. You should see the Prefect UI.

7.  **Set up Prefect Blocks:**
    The base template's `make setup-blocks` command primarily sets up essential local infrastructure blocks, such as a `DockerContainer` block named `local-worker-infra` which is used by local deployments defined in `prefect.local.yaml`.
    ```bash
    # Ensure PREFECT_API_URL is set to the local server (Step 4)
    # You can place PREFECT_API_URL and PREFECT_BLOCK_OVERWRITE=true in a setup.env file too.
    make setup-blocks
    ```
    If you wish to extend this template to use specific cloud services (e.g., for remote file storage), you would typically:
    1. Add the required optional dependencies (e.g., `uv pip install -e ".[aws]"` for AWS S3).
    2. Modify `scripts/setup_prefect_blocks.py` or create a new script to define and create blocks for those cloud services (e.g., `S3Bucket`, `GCSBucket`). This would likely involve setting cloud provider-specific environment variables (like `SETUP_CLOUD_ACCESS_KEY`, `SETUP_BUCKET_NAME`) before running your modified script.
    
    Verify any created blocks (e.g., `docker-container/local-worker-infra`) appear in the Prefect UI under the "Blocks" section. See the [Configuration Guide](configuration.md) for more details.

8.  **Set up Prefect Variables:**
    This step loads configurations from the YAML files in `configs/variables/` into Prefect Variables, which your flows will use for runtime parameters.
    ```bash
    # Ensure PREFECT_API_URL is set
    make setup-variables
    ```
    *(You can set `PREFECT_VARIABLE_OVERWRITE=true` as an environment variable if you want to force updates to existing variables).*

9.  **Apply Flow Deployments:**
    Register the example flows defined in the `flows/` directory (e.g., for the "Project Alpha" department) with the running local Prefect server.
    ```bash
    make build-deployments
    ```
    Check the "Deployments" page in the UI. You should see deployments for the example "Project Alpha" department, such as "Ingestion Deployment (Project Alpha) - Local Dev".

10. **Run Your First Flow:**
    * Navigate to the "Deployments" page in the Prefect UI (`http://127.0.0.1:4200/deployments`).
    * Find an example deployment (e.g., "Ingestion Deployment (Project Alpha) - Local Dev").
    * Click the "Run" button (usually a play icon ▶️) in the top right.
    * Accept the defaults or provide parameters if needed, and click "Run".
    * You can monitor the flow run's progress on the "Flow Runs" page. Check the logs within the UI or using `docker compose logs -f worker` in your terminal.

11. **Stopping the Local Environment:**
    When you're finished developing locally:
    ```bash
    make stop-local
    ```
    This stops and removes the Docker containers, network, and database volume.

## Next Steps

* Learn more about the project's **[Configuration](configuration.md)**.
* Understand the **[Core Concepts & Architecture](architecture.md)**.
* Explore how to **[Use and Run Flows](usage.md)** in more detail.
* See the guide on **[Development](development.md)** for adding your own flows and tasks.