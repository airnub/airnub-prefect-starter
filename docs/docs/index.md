# Welcome to the Airnub Prefect Starter Documentation!

This site contains the official documentation for the `airnub-prefect-starter` project template.

## What is this Template?

The **Airnub Prefect Starter** provides a standardized, robust foundation for building data pipelines using **Prefect 3**. It's designed with best practices in mind for:

* **Modern Orchestration:** Leveraging Prefect 3's features for defining flows, tasks, scheduling, retries, logging, and observability.
* **Structured Configuration:** Utilizing Prefect Variables (from organized YAML files) for runtime parameters and Prefect Blocks for secrets and infrastructure definitions.
* **Local-First Development:** A Dockerized environment (via Docker Compose) for a seamless local development experience, including a local Prefect server, UI, and PostgreSQL database. Demo flows default to local filesystem storage.
* **Clear Project Organization:** A well-defined structure separating:
    * The main Python package (`airnub_prefect_starter/`) with:
        * `common/` utilities.
        * `core/` for reusable, Prefect-agnostic business logic.
        * `data_science/` for prototyping and exploratory scripts.
        * `tasks/` (initially empty) for future common Prefect task wrappers.
    * Prefect flow definitions (`flows/`) organized by Department and Stage.
    * Configuration files (`configs/`).
    * Helper scripts (`scripts/`), including generators for new components.
* **Scalability:** The "Department -> Stage -> Category" flow structure is designed to manage projects with numerous data sources and teams effectively.
* **Integrated Data Science Workflow:** Provides a clear path from data science exploration and prototyping (using scripts in `airnub_prefect_starter/data_science/`) to operationalized, scheduled Prefect workflows.
* **Idempotency Patterns:** Encourages practices like content hashing for data to prevent unnecessary reprocessing.
* **Extensibility & Cloud Agnosticism:** The core template is cloud-agnostic. It can be readily extended to integrate with various cloud services (e.g., remote object storage like S3/GCS/Azure Blob, container orchestrators) by adding optional dependencies (like `prefect-aws`, `prefect-gcp`) and configuring appropriate Prefect Blocks.

## Who is this for?

This template is intended for engineers and data scientists who need to build reliable, maintainable, and scalable data pipelines using Prefect 3. It aims to provide a quick start while incorporating important patterns for development, configuration, testing, and deployment, supporting both local iteration and eventual extension to cloud environments.

## Getting Help

* **This Site:** Browse the navigation sidebar to find detailed guides on setup, core concepts, configuration, usage, development, and deployment principles.
* **Project Repository:** Visit the [project repository on GitHub](https://github.com/your-org/airnub-prefect-starter) (TODO: Update link) for the source code and to raise issues.
* **Prefect Community:** For general Prefect questions, check the [Prefect Documentation](https://docs.prefect.io/) or join the [Prefect Community Slack](https://prefect.io/slack).

## Ready to start?

Proceed to the **[Getting Started](getting-started.md)** guide!