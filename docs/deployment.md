# Deployment Principles & Examples

This guide outlines general principles and provides examples for deploying your Prefect flows defined in the **`airnub-prefect-starter`** template. The template primarily focuses on using **Docker** for packaging and running your flows.

## Core Deployment Concepts

Understanding these Prefect concepts is key to deploying your flows:

* **Docker Image:** Your flows, Python package (`airnub_prefect_starter/`), and all dependencies are packaged into a Docker image using the project's `Dockerfile.worker`. This image is what your Prefect work pool will typically execute.
* **Prefect Backend (Server/Cloud):** You need a running Prefect API server (either self-hosted, like the one in `docker-compose.yml`, or Prefect Cloud) to orchestrate and monitor flow runs.
* **Work Pool:** A configuration within your Prefect backend that defines *how* and *where* flow runs are executed. For this template, you'll typically use work pools that can run Docker containers (e.g., a `docker` type pool for local Docker, a `kubernetes` pool, or pools for specific cloud container services).
* **Prefect Worker:** A process that polls a specific work pool for flow runs. When it finds one, it uses the infrastructure defined in the deployment (usually your Docker image) to execute the flow. In the local `docker-compose.yml` setup, a worker service is already defined.
* **Deployment:** A configuration stored in your Prefect backend that links your flow's entrypoint (e.g., `flows/dept_project_alpha/ingestion_flow_dept_project_alpha.py:ingestion_flow_dept_project_alpha`) to its execution environment. This includes:
    * The work pool name.
    * Infrastructure configuration (e.g., the Docker image to use, referenced via a `DockerContainer` block or inline).
    * Schedule, parameters, tags, etc.
    * Deployments are typically created using `prefect deployment build ...` and `prefect deployment apply ...` or by defining them in YAML files like `prefect.local.yaml`.
* **Code Storage (Primary Method: Baked into Image):**
    * **Baked into Docker Image (Recommended for this Template):** The simplest and most robust method. Your `Dockerfile.worker` copies your `airnub_prefect_starter` package and `flows/` directory into the image. The worker executes code directly from the image.
    * **Remote Storage (Optional Extension):** For more advanced scenarios, code can be stored in a remote location (e.g., Git repository, S3, GCS) and pulled by the worker at runtime. This is configured in `prefect.yaml`'s `pull:` section and often involves additional Prefect Blocks for access.
* **Data Storage (for Flow Inputs/Outputs):**
    * **Local Filesystem (Demo Default):** The "Project Alpha" demo flows store downloaded files and local JSON manifests within the worker container's filesystem (e.g., under `/app/local_demo_artifacts/`, which can be volume-mapped from `./data/project_alpha_demo_outputs/` on the host).
    * **Remote Object Storage (Extension):** To use cloud storage (like S3, GCS, Azure Blob), you would:
        1.  Add the relevant optional dependency (e.g., `pip install .[aws]`).
        2.  Create a storage block (e.g., `S3Bucket`) in Prefect, configured with your bucket details and credentials.
        3.  Pass the name of this block to your flows and modify your core logic (in `airnub_prefect_starter/core/`) to use it for reading/writing data.
* **Configuration:**
    * **Prefect Variables:** For runtime parameters (see `configs/variables/`).
    * **Prefect Blocks:** For secrets and infrastructure/service configurations.

## `prefect.yaml` Configuration (for Remote Deployments)

The `prefect.yaml` file in your project root defines default build, push, and pull steps, primarily useful when preparing deployments for remote execution environments (not typically used by `prefect.local.yaml`).

* **`build:` Section (Example for building a Docker image):**
    Defines how to build your project's Docker image using `Dockerfile.worker`.
    ```yaml
    build:
      - prefect_docker.deployments.steps.build_docker_image:
          id: build_image
          requires: prefect-docker>=0.4.0 # Ensure you have this in [dev] dependencies
          image_name: your-container-registry/airnub-prefect-starter # TODO: Replace with your registry/image
          tag: latest # Or use a git commit hash, version number, etc.
          dockerfile: Dockerfile.worker
          # platform: "linux/amd64" # Optional: specify platform if needed
    ```
    * **Action:** You **must** update `image_name` to point to your container registry (e.g., Docker Hub, GCR, ECR, ACR).

* **`push:` Section (Example for pushing the image):**
    Defines how to push the built Docker image to the registry.
    ```yaml
    push:
      - prefect_docker.deployments.steps.push_docker_image:
          requires: prefect-docker>=0.4.0
          image_name: "{{ build_image.image_name }}" # References the image_name from the build step
          tag: "{{ build_image.tag }}"
    # --- Optional: Push code to Remote Storage (if NOT baking code into image) ---
    # - prefect_aws.deployments.steps.push_to_s3: # Example for S3
    #     id: push_code_to_s3
    #     requires: prefect-aws>=0.4.5 # Ensure 'aws' extra is installed
    #     bucket: your-code-storage-bucket-name
    #     folder: airnub-prefect-starter/code 
    #     credentials_block_slug: "aws-credentials/your-aws-creds-block" # Example
    ```
    * The S3 push step for code is commented out as baking code into the image is simpler for this template.

* **`pull:` Section (Example for pulling code - if not baked in):**
    Defines how the execution environment should retrieve flow code if it's *not* baked into the Docker image. **If your code is baked into the image, this section can be empty or removed from `prefect.yaml`.**
    ```yaml
    # pull: # Only required if code is NOT baked into the image
    # - prefect_aws.deployments.steps.pull_from_s3: # Example for S3
    #     requires: prefect-aws>=0.4.5
    #     bucket: "{{ push_code_to_s3.bucket }}" # References bucket from an S3 push step
    #     folder: "{{ push_code_to_s3.folder }}"
    #     credentials_block_slug: "aws-credentials/your-aws-creds-block"
    ```

* **`deployments:` Section (Default Template):**
    Provides a template for deployments built using `prefect.yaml`. You typically override specifics like `name`, `entrypoint`, and `work_pool.name` when running `prefect deployment build ...`.
    ```yaml
    # deployments:
    # - name: "Default {{ flow.name }} Deployment" # Example parameterized name
    #   # ... other default deployment settings ...
    #   work_pool:
    #     name: "your-remote-docker-pool" # Example
    #     job_variables:
    #       image: "{{ build_image.image }}" # References the full image URI from the build step
    ```

## General Steps for Deploying to a Remote Environment (e.g., Cloud VM, Kubernetes)

This template focuses on local development, but here's a generic outline for deploying to a remote environment that can run Docker containers:

1.  **Prerequisites for Remote Environment:**
    * A running Prefect Server (self-hosted on a VM, in Kubernetes, or Prefect Cloud) accessible by your workers.
    * A container registry (Docker Hub, GCR, ECR, ACR, etc.) to store your Docker image.
    * An execution environment for your worker (e.g., a VM with Docker, a Kubernetes cluster, a cloud container service like ECS or Google Cloud Run).
    * A Prefect Work Pool configured in your Prefect backend that your remote worker will poll. This pool should be configured to run Docker containers. Example types: `docker`, `kubernetes`, `ecs`, `cloud-run`.

2.  **Prepare `prefect.yaml`:**
    * Uncomment and configure the `build:` and `push:` sections in `prefect.yaml`.
    * Set `image_name` to your target container registry and image name.
    * Ensure `dockerfile: Dockerfile.worker` is correct.
    * If you are *not* baking code into the image, configure `push` and `pull` steps for your chosen code storage (e.g., Git, S3).

3.  **Build and Push Docker Image:**
    * Log in to your container registry (e.g., `docker login your-registry.io`).
    * You can build and push manually:
        ```bash
        make build-docker # Builds using docker-compose, ensure image is tagged correctly for your registry
        docker tag airnub-prefect-starter-worker:latest your-container-registry/your-image-name:latest # Adjust tag if needed
        docker push your-container-registry/your-image-name:latest
        ```
    * Or, use Prefect's deployment build steps if `prefect.yaml` is fully configured (see next step).

4.  **Set up Prefect Blocks for the Remote Environment:**
    * Ensure your Prefect Server/Cloud instance has any necessary Blocks. This might include:
        * `Secret` blocks for API keys your flows use.
        * Storage blocks (e.g., `S3Bucket`, `GCSBucket`) if your flows will interact with remote storage for data.
        * A `DockerContainer` block (or similar infrastructure block like `KubernetesJob`) that points to your pushed image and is used by your remote work pool's default infrastructure. Alternatively, the image can be specified directly in the deployment definition.
    * Use `scripts/setup_prefect_blocks.py` as a template, modifying it to create cloud-specific blocks by providing necessary environment variables (e.g., for cloud credentials).

5.  **Build and Apply Deployment(s) for Remote Execution:**
    Use the Prefect CLI to build deployment configurations, targeting your remote work pool and pushed image.
    ```bash
    # Example for "Project Alpha" Ingestion flow
    prefect deployment build ./flows/dept_project_alpha/ingestion_flow_dept_project_alpha.py:ingestion_flow_dept_project_alpha \
      -n "Ingestion Deployment (Project Alpha) - Remote" \
      -p "your-remote-docker-work-pool-name" \
      --infra-override image="your-container-registry/your-image-name:latest" \
      # Or if using a pre-configured DockerContainer block for remote:
      # --infra-block docker-container/my-remote-docker-infra-block \
      --apply 
      # Add --build if using prefect.yaml build/push steps (ensure Docker is logged into registry)
      # Add --param '{"storage_block_name": "s3-bucket/my-data-bucket"}' # Example for remote data storage
    ```
    * Repeat for other flows. The `-n` (name) should be unique for each deployment.
    * The `work_pool_name` (`-p`) must match the name of a work pool configured in your Prefect backend that your remote workers are polling.

6.  **Ensure Worker is Running in Remote Environment:**
    * Deploy a Prefect Worker in your chosen remote environment (VM, Kubernetes, ECS, etc.).
    * This worker must be configured to poll the correct `PREFECT_API_URL` and the work pool specified in your deployments (e.g., `"your-remote-docker-work-pool-name"`).
    * Ensure the worker has network access to the Prefect API, your container registry, and any other services your flows interact with.

7.  **Run & Monitor:**
    * Trigger flow runs from the Prefect UI or CLI.
    * Monitor runs and logs in the Prefect UI. Configure logging in your remote environment to capture worker and flow run logs effectively.

## Key Considerations for Any Deployment

* **Credentials & Secrets:** Always use Prefect `Secret` blocks for sensitive information. Ensure your execution environment (worker or flow run container) has secure access to these secrets, either via inherited permissions (e.g., IAM roles for cloud services) or by securely providing access to the Prefect API where blocks are stored.
* **Prefect Server Database:** For any non-trivial or production deployment, Prefect Server should use a robust, persistent database like PostgreSQL, not SQLite. (Your `docker-compose.yml` already sets up PostgreSQL for local server development).
* **Networking:** Ensure your workers can reach the Prefect API, any data sources, and any services your flows interact with.
* **Resource Allocation:** Configure adequate CPU/Memory for your workers and flow run containers based on flow requirements.
* **Dependencies:** Ensure all Python package dependencies are correctly listed in `pyproject.toml` so they are included in your `Dockerfile.worker` image.