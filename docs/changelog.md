# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) once it reaches version 1.0.0.

## [Unreleased] - YYYY-MM-DD

### Added
- Initial release of the `airnub-prefect-starter` template.
- Core structure for Prefect flows (Departments, Stages, Categories).
- Generator scripts for scaffolding new departments, categories, and tasks.
- "Project Alpha" example department with categories:
    - `public_api_data`: Demonstrates fetching and parsing public API data.
    - `scheduled_file_downloads`: Demonstrates downloading files, local CAS-like storage, and local JSON manifest creation.
    - `web_page_link_scraping`: Demonstrates basic web scraping, canonical URL handling, and link extraction.
- Core logic modules in `airnub_prefect_starter/core/` for demo tasks.
- Pydantic models for demo manifest entries in `airnub_prefect_starter/core/manifest_models.py`.
- Prefect artifact creation for demo outputs.
- Integrated data science prototyping structure in `airnub_prefect_starter/data_science/`.
- Dockerized local development environment with Prefect Server, UI, PostgreSQL, and custom Worker.
- `Makefile` for common development tasks.
- `pytest` test suite for generator scripts.
- MkDocs documentation site structure.

### Changed
- Template refactored from an AWS-specific base to be cloud-agnostic.
- Default storage for demos is local filesystem.
- Configuration primarily via Prefect Variables (from YAMLs) and Prefect Blocks (for secrets/infra).
- `pyproject.toml` updated for generic dependencies, with cloud-specific libraries as optional extras.
- `CONTRIBUTING.md`, `README.md`, and all documentation updated for the generic template.

### Deprecated
- N/A

### Removed
- Hardcoded AWS dependencies and configurations from the base template.
- Old database-backed manifest system (`manifest_tasks.py`, `common/database.py`, `common/models.py`) from the base template (users can add their own application DB if needed).
- Old common task wrappers from `airnub_prefect_starter/tasks/` (directory is now empty, for user-defined common tasks).

### Fixed
- N/A

### Security
- N/A

---
## [0.0.1] - YYYY-MM-DD 
### Added
- Initial commit placeholder.