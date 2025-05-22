# Data Science & Prototyping Workflow

A key feature of the **Airnub Prefect Starter** template is its integrated structure that supports both data science exploration/prototyping and the operationalization of that work into robust Prefect data pipelines. This document outlines the intended workflow.

## The Dual Structure

The template provides distinct areas for these two phases:

1.  **Data Science & Prototyping (`airnub_prefect_starter/data_science/` & `notebooks/`):**
    * **`airnub_prefect_starter/data_science/`**: This Python sub-package contains scripts inspired by common data science project structures (e.g., Cookiecutter Data Science).
        * `config_ds.py`: Defines file system paths for various data stages (raw, processed, interim, models, etc.), typically within the project's root `data/` directory.
        * `dataset_processing.py`: Placeholder for scripts that perform initial data cleaning, transformation, and preparation (e.g., creating primary datasets from raw data).
        * `feature_engineering.py`: Placeholder for scripts that generate features for machine learning models.
        * `modeling/`: Contains scripts for model training (`train.py`) and prediction/inference (`predict.py`).
        * `visualization_scripts.py` (or `plots.py`): Placeholder for scripts that generate plots and visualizations.
    * **`notebooks/`**: The top-level directory for Jupyter notebooks. This is ideal for iterative exploration, ad-hoc analysis, and experimenting with different approaches before formalizing them into scripts.

2.  **Prefect Operationalization (`flows/` & `airnub_prefect_starter/core/`):**
    * **`airnub_prefect_starter/core/`**: This Python sub-package is where you place reusable, Prefect-agnostic core logic functions that encapsulate the business rules and data transformations derived from your data science work.
    * **`flows/`**: This top-level directory contains all your Prefect flow definitions and their department/category-specific task wrappers. These task wrappers are typically thin calls to the functions in `airnub_prefect_starter/core/`.

## The Intended Workflow: From Research to Production

1.  **Exploration & Prototyping (Data Science Phase):**
    * Use Jupyter notebooks in the `notebooks/` directory for initial data exploration, visualization, and trying out different algorithms or processing steps.
    * Formalize repeatable data processing, feature engineering, or model training steps into Python scripts within `airnub_prefect_starter/data_science/` (e.g., `dataset_processing.py`, `feature_engineering.py`, `modeling/train.py`).
    * These scripts utilize `airnub_prefect_starter/data_science/config_ds.py` to manage paths to raw, interim, processed data, and models, typically stored within the project's `data/` and `models/` directories.
    * Run these scripts standalone (e.g., `python -m airnub_prefect_starter.data_science.train_model`) for development and iteration.

2.  **Refactoring for Operationalization (Core Logic):**
    * Once a piece of data processing logic, feature engineering step, or model inference routine is stable and well-understood from the prototyping phase, refactor its core functionality into reusable Python functions.
    * Place these functions in appropriate modules within `airnub_prefect_starter/core/` (e.g., data cleaning functions in `core/data_cleaning.py`, model inference logic in `core/model_inference.py`).
    * These core functions should be well-tested and independent of Prefect decorators.

3.  **Creating Prefect Tasks (Wrappers):**
    * Use the `scripts/generators/add_task.py` script to create new department/category-specific Prefect task wrappers within the relevant `flows/dept_.../.../tasks/` directory.
    * These task wrappers will import and call the core logic functions you created in `airnub_prefect_starter/core/`.
    * The task wrapper handles Prefect-specific concerns like logging (`get_run_logger()`), retries, and parameterization from flow configurations.

4.  **Building Prefect Flows (Orchestration):**
    * Use `scripts/generators/add_category.py` and `scripts/generators/add_department.py` to scaffold your Prefect flows.
    * Implement your category and parent stage flows in the `flows/` directory to orchestrate these tasks.
    * Configure your flows using YAML files in `configs/variables/` (which become Prefect Variables) and Prefect Blocks for secrets/infrastructure.

5.  **Deployment & Scheduling:**
    * Define deployments for your parent stage flows in `prefect.local.yaml` (for local execution) or other deployment manifests.
    * Run and schedule your flows using the Prefect UI or CLI.

## Benefits of this Approach

* **Separation of Concerns:** Keeps exploratory/prototyping code distinct from production workflow code.
* **Rapid Prototyping:** Data scientists can work quickly in notebooks and standalone scripts without needing to immediately understand all of Prefect's intricacies.
* **Robust Operationalization:** Mature logic is refactored into testable core functions and then reliably orchestrated by Prefect.
* **Clear Path to Production:** Provides a structured way to move from an idea prototyped in a data science environment to a scheduled, monitored Prefect data pipeline.

This integrated workflow leverages the strengths of both traditional data science project structures and modern workflow orchestration with Prefect.