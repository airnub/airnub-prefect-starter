# Airnub Prefect Starter Documentation

This directory contains the source files for the official documentation of the `airnub-prefect-starter` project template, built using [MkDocs](https://www.mkdocs.org/) with the Material theme.

## Building and Serving Locally

To build and serve the documentation locally:

1.  Ensure you have Python and `pip` (or `uv`) installed.
2.  Navigate to the project root directory (the parent of this `docs/` directory).
3.  Install documentation dependencies (includes MkDocs and the Material theme):
    ```bash
    # If you have a 'docs_build' extra in pyproject.toml, from project root:
    uv pip install -e ".[docs_build]"
    # Or, if not using extras, install directly:
    # uv pip install mkdocs mkdocs-material pymdown-extensions
    ```
4.  Navigate into this `docs/` directory:
    ```bash
    cd docs
    ```
5.  Build the documentation (optional, `serve` does this implicitly):
    ```bash
    mkdocs build
    ```
    This will generate the static site in the `docs/site/` directory.
6.  Serve the documentation locally:
    ```bash
    mkdocs serve
    ```
    Open your browser and navigate to `http://127.0.0.1:8000` to view the live documentation. Changes to the Markdown files will automatically reload the site.

For the main project `README.md`, please see the file in the project root directory.