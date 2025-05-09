# Configuration Management

This **Airnub Prefect Starter** template employs a layered approach to configuration, prioritizing clarity, flexibility, and security for your data pipelines. The main mechanisms are Prefect Variables (derived from YAML files), Prefect Blocks, and environment variables (often managed via a `.env` file for local development).

## 1. Prefect Variables (for Flow & Task Parameters)

Non-sensitive runtime parameters for your Prefect flows and tasks are primarily managed using **Prefect Variables**. This allows you to change behavior without modifying code.

* **Source:** YAML files located in the `configs/variables/` directory. This directory mirrors the structure of your `flows/` directory.
    * Example for a parent stage flow: `configs/variables/dept_project_alpha/ingestion_config_dept_project_alpha.yaml`
    * Example for a category flow: `configs/variables/dept_project_alpha/ingestion/public_api_data/ingest_public_api_data_config_dept_project_alpha.yaml`
    * Example for a task within a category: `configs/variables/dept_project_alpha/ingestion/public_api_data/tasks/parse_api_response_task_config_dept_project_alpha.yaml`
* **Creation:** The `scripts/setup_prefect_variables.py` script scans these YAML files, derives variable names (e.g., `dept_project_alpha_ingestion_public_api_data_config`), and creates or updates the corresponding Prefect Variables in your Prefect backend (local server or Cloud).
    * Run with: `make setup-variables`
* **Usage in Flows/Tasks:**
    ```python
    from prefect import flow, task, variables
    import json

    @task
    async def my_example_task(task_specific_param: str):
        logger = get_run_logger()
        logger.info(f"Task received: {task_specific_param}")

    @flow
    async def ingest_public_api_data_flow_dept_project_alpha(config_override: Optional[dict] = None):
        logger = get_run_logger()
        flow_config = {}
        if config_override:
            flow_config = config_override
        else:
            try:
                # Variable name derived from conventions
                variable_name = "dept_project_alpha_ingestion_public_api_data_config"
                config_json_str = await variables.Variable.get(variable_name)
                if config_json_str:
                    flow_config = json.loads(config_json_str)
                logger.info(f"Loaded configuration from Prefect Variable: {variable_name}")
            except Exception as e:
                logger.error(f"Could not load/parse variable {variable_name}: {e}")
        
        api_url = flow_config.get("api_url", "[http://default.example.com/api](http://default.example.com/api)")
        # ... use api_url and other configs ...
        # Example of passing a task-specific part of the config:
        # await my_example_task.submit(
        #     task_specific_param=flow_config.get("my_task_settings", {}).get("param_value")
        # )
    ```
* **Content:** These YAML files can contain API URLs, file paths (though often relative or to be combined with base paths), processing thresholds, query parameters, list of items to process, etc.

## 2. Prefect Blocks (for Secrets & Infrastructure)

**Prefect Blocks** are the secure and preferred way to manage:

* **Secrets:** API keys, database credentials, tokens, and any sensitive information. Blocks encrypt secrets at rest.
* **Infrastructure Configuration:** Definitions for how and where your flows run, particularly when moving beyond simple local execution.
    * The primary block used by this template for local development is a `DockerContainer` block, typically named `docker-container/local-worker-infra`. This block tells Prefect how to run your flows as Docker containers using the local Docker daemon (as orchestrated by `docker-compose.yml`). It specifies the image name, network, etc.
* **Connections to External Services (When Extending):** If you extend the template to use cloud services (e.g., S3 for storage, a cloud data warehouse), you would create and use blocks like `S3Bucket`, `GCSBucket`, `SnowflakeConnector`, etc. These blocks would store connection details and credentials.

### Setting Up Blocks (`scripts/setup_prefect_blocks.py`)

* The `scripts/setup_prefect_blocks.py` script helps automate the creation of essential *local infrastructure* blocks.
* **For the base template, this script primarily focuses on creating the `docker-container/local-worker-infra` block.**
* It does **not** create cloud-specific blocks (like `S3Bucket` or `AwsCredentials`) by default. To add such blocks:
    1.  Install the relevant Prefect integration library (e.g., `prefect-aws` via `pip install -e ".[aws]"`).
    2.  Modify `scripts/setup_prefect_blocks.py` (or create a new script) to include logic for creating these blocks. This will typically involve reading credentials or resource names from environment variables (e.g., `SETUP_S3_BUCKET_NAME`, `SETUP_AWS_ACCESS_KEY_ID`).
    3.  Run the script: `make setup-blocks` (after setting any necessary environment variables for the blocks you're adding).

### Using Blocks in Flows

Flows load blocks using `from prefect.blocks.core import Block; await Block.load("block-type/block-name")` or specific block type load methods (e.g., `await DockerContainer.load("local-worker-infra")`).

```python
from prefect import flow
from prefect.blocks.core import Block # Generic load
# from prefect_docker.deployments.steps import DockerContainer # Specific type if known

@flow
async def my_flow_using_blocks():
    logger = get_run_logger()
    try:
        # Example: Loading a generic JSON block storing non-sensitive API info
        # (Though this type of config is now primarily handled by Prefect Variables from YAMLs)
        # api_info_block = await Block.load("json/project-alpha-public-api-details")
        # api_key = api_info_block.value.get("api_key_if_it_were_here_but_use_secret_block_instead")
        
        # More typically, you'd load a Secret block for an API key
        api_key_secret = await Block.load("secret/my-service-api-key")
        actual_api_key = api_key_secret.get() # Access the secret value
        logger.info("Successfully loaded API key secret.")

        # Infrastructure blocks are usually referenced in deployment definitions (prefect.local.yaml)
        # but can be loaded in flows if needed for dynamic infrastructure.
        # docker_infra = await DockerContainer.load("local-worker-infra")
        # logger.info(f"Using Docker infra: {docker_infra.image}")

    except ValueError:
        logger.error("A required block was not found. Ensure it's created in your Prefect backend.")
    except Exception as e:
        logger.error(f"Error loading a block: {e}")
```

## 3. Environment Variables (`.env` file at Project Root)

* **Purpose:** Primarily used by `docker-compose.yml` to configure the services running in your local development environment (Prefect server, UI, PostgreSQL database for Prefect server, Worker). It can also be loaded by Python scripts (like those in `airnub_prefect_starter/data_science/`) using `python-dotenv` to allow for environment-specific settings or overrides.
* **Examples (in `.env` that `docker-compose.yml` would use):**
    * `PREFECT_API_DATABASE_CONNECTION_URL="postgresql+asyncpg://prefect:prefect_password@database:5432/prefect_server"` (For Prefect server to connect to its PostgreSQL DB)
    * `PREFECT_SERVER_API_HOST="0.0.0.0"` (Crucial for UI accessibility from your host machine)
    * `PREFECT_UI_API_URL="http://127.0.0.1:4200/api"`
    * Variables that your application code (running inside the worker) might need, which can be passed through `docker-compose.yml`'s `environment` or `env_file` sections (e.g., `LOCAL_DATA_ROOT_OVERRIDE` if you choose to support this in `data_science/config_ds.py`).
* **Management:**
    * A `.env.example` file is provided in the template root. **Copy it to `.env` and customize it.**
    * **Always add your actual `.env` file to `.gitignore`** to avoid committing secrets or local-specific configurations.

## 4. Python Module Configuration (`airnub_prefect_starter/data_science/config_ds.py`)

* **Purpose:** This Python file (`config_ds.py`, or `config.py` if you kept that name, located within `airnub_prefect_starter/data_science/`) defines file system paths and settings primarily for the standalone data science scripts (e.g., `dataset_processing.py`, `feature_engineering.py`, `modeling/train.py`) and notebooks located in `airnub_prefect_starter/data_science/` and the top-level `notebooks/` directory.
* **How it works:**
    * It typically calculates `PROJECT_ROOT` based on its own file location (e.g., `Path(__file__).resolve().parents[2]` if `config_ds.py` is in `data_science/`).
    * It defines `DATA_DIR` (usually `<PROJECT_ROOT>/data/`) and specific subdirectories like `RAW_DATA_DIR`, `PROCESSED_DATA_DIR`, `MODELS_DIR_PROJECT_ROOT` (pointing to the top-level `models/` directory).
    * It may load the root `.env` file using `python-dotenv` to allow environment variables to influence these path definitions if you design it to do so (e.g., allowing `DATA_DIR` to be overridden).
* **Usage:**
    * Data science scripts import paths directly:
      ```python
      # Example in airnub_prefect_starter/data_science/dataset_processing.py
      from .config_ds import RAW_DATA_DIR, PROCESSED_DATA_DIR, logger 
      # Or if config_ds.py imports and re-exports from common.settings:
      # from .config_ds import PROJECT_ROOT 
      ```
    * Prefect core logic functions (in `airnub_prefect_starter/core/`) can also import paths from `config_ds.py` if they need to interact with these conventionally structured data directories (e.g., for saving demo artifacts to a subdirectory of `DATA_DIR`).
      ```python
      # Example in airnub_prefect_starter/core/file_handlers.py
      from ..data_science.config_ds import DATA_DIR
      
      DEMO_ARTIFACT_BASE = DATA_DIR / "project_alpha_demo_outputs"
      ```

## Configuration Hierarchy & Best Practices

For clarity, here's a suggested way to think about configuration:

1.  **Prefect Blocks (Secrets & Infrastructure):**
    * **Use for:** All secrets (API keys, passwords, tokens), and definitions of infrastructure your flows run on (like the `docker-container/local-worker-infra` block for local execution).
    * **Why:** Secure storage for secrets, standard way to define runtime environments. Easily manageable via UI or API.

2.  **Prefect Variables (Runtime Flow/Task Parameters - from `configs/variables/*.yaml`):**
    * **Use for:** Non-sensitive parameters that control the behavior of your deployed flows and tasks (e.g., URLs for data sources, file paths *relative to a base defined elsewhere*, batch sizes, feature flags, model names, query parameters).
    * **Why:** Allows changing flow behavior without code changes, easily managed via UI or API after being set up by `make setup-variables`. Stored in Prefect backend, accessible by any worker.

3.  **`.env` File (at Project Root):**
    * **Use for:** Configuring the local Docker Compose environment (e.g., database credentials *for the Prefect server's DB*, `PREFECT_SERVER_API_HOST`). Can also be used to pass environment variables into the worker container that your Python application code might read (e.g., via `os.getenv()` in `config_ds.py` if you want to allow overrides of `DATA_DIR`).
    * **Why:** Standard Docker Compose practice, keeps local service configuration out of version control.

4.  **`airnub_prefect_starter/data_science/config_ds.py` (Python Module Config):**
    * **Use for:** Defining the *structural layout* of your project's data directories (`PROJECT_ROOT`, `DATA_DIR`, `RAW_DATA_DIR`, etc.) primarily for use by data science scripts and notebooks, and as a fallback or base for local demo storage in Prefect flows.
    * **Why:** Provides Python-native, easily importable path constants for your scripts.

**General Guidance:**

* **Secrets always go in Prefect Blocks.**
* **Parameters you want to easily change for a deployed flow without touching code go into YAML files for Prefect Variables.**
* Configure your local Docker services via the root `.env` file.
* Define your project's data directory structure for data science work in `data_science/config_ds.py`.
* Your Prefect flows and core logic can then intelligently combine these:
    * Load a base URL from a Prefect Variable.
    * Load an API key from a Prefect Secret Block.
    * Know where to save a demo output file locally using a path derived from `config_ds.DATA_DIR`.

This layered approach provides flexibility and security, supporting both local development and preparing for more complex configurations as your project evolves.