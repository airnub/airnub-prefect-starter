#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = airnub-prefect-starter
PYTHON_VERSION ?= 3.12 # Use ?= to allow override from environment
PYTHON_INTERPRETER ?= python # Use ?= to allow override
# Optional: Default setup env file (user can override with exports)
SETUP_ENV_FILE ?= setup.env

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Set up Python interpreter environment using uv
.PHONY: create_environment
create_environment:
	@echo "Creating virtual environment using uv for Python $(PYTHON_VERSION)..."
	uv venv --python $(PYTHON_VERSION)
	@echo ">>> New uv virtual environment created in ./.venv"
	@echo ">>> Activate with:"
	@echo ">>>   Windows: .\\.venv\\Scripts\\activate"
	@echo ">>>   Unix/macOS: source ./.venv/bin/activate"

## Install Python dependencies using uv
.PHONY: install
install:
	@echo "Installing dependencies from pyproject.toml using uv..."
	# Install project in editable mode plus dev dependencies
	uv pip install --no-cache --upgrade -e ".[dev]"
	# python -m pip install --no-cache-dir --upgrade -e ".[dev]"

## Set up required Prefect Infrastructure Blocks
.PHONY: setup-blocks
setup-blocks:
	@echo "Setting up Prefect Blocks via scripts/setup_prefect_blocks.py..."
	@echo "--> Ensure PREFECT_API_URL is set pointing to your Prefect server."
	@echo "--> (Check README.md and script comments for details on required/optional env vars)"
	$(if $(wildcard $(SETUP_ENV_FILE)), \
		@echo "--> Attempting to load variables from $(SETUP_ENV_FILE)"; \
		@export $$(grep -v '^#' $(SETUP_ENV_FILE) | xargs); \
	)
	@$(PYTHON_INTERPRETER) scripts/setup_prefect_blocks.py

## Set up Prefect Variables from YAML configs
.PHONY: setup-variables
setup-variables:
	@echo "Setting up Prefect Variables via scripts/setup_prefect_variables.py..."
	@echo "--> Ensure PREFECT_API_URL is set pointing to your Prefect server."
	@echo "--> Ensure PyYAML is installed ('uv pip install pyyaml' or 'pip install pyyaml')."
	@echo "--> Config files are read from ./configs/variables/"
	@echo "--> Set PREFECT_BLOCK_OVERWRITE=true env var to force updates if variables already exist."
	$(if $(wildcard $(SETUP_ENV_FILE)), \
		@echo "--> Attempting to load variables from $(SETUP_ENV_FILE)"; \
		@export $$(grep -v '^#' $(SETUP_ENV_FILE) | xargs); \
	)
	@$(PYTHON_INTERPRETER) scripts/setup_prefect_variables.py

## Run local Prefect development environment (Docker Compose)
.PHONY: run-local
run-local:
	@echo "Starting local Prefect environment (docker-compose up)..."
	./scripts/run_local_dev.sh

## Stop local Prefect development environment (Docker Compose)
.PHONY: stop-local
stop-local:
	@echo "Stopping local Prefect environment (docker-compose down)..."
	./scripts/stop_local_dev.sh

## Build and apply flow deployments to the local server
.PHONY: build-deployments
build-deployments:
	@echo "Building and applying local deployments..."
	./scripts/build_deployments.sh local

## Build the Prefect worker Docker image locally
.PHONY: build-docker
build-docker:
	@echo "Building Docker image for the 'worker' service locally..."
	docker compose build worker

## Lint source code using ruff
.PHONY: lint
lint:
	@echo "Checking formatting and linting with ruff..."
	ruff format --check .
	ruff check .

## Format source code using ruff
.PHONY: format
format:
	@echo "Formatting and fixing lint issues with ruff..."
	ruff check --fix .
	ruff format .

## Run tests using pytest
.PHONY: test
test:
	@echo "Running tests..."
	$(PYTHON_INTERPRETER) -m pytest tests/

## Delete all compiled Python files and caches
.PHONY: clean
clean:
	@echo "Cleaning up compiled files and caches..."
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

# Add the new target to the help list if desired (check your PRINT_HELP_PYSCRIPT)
# It should be picked up automatically if it follows the ## Comment -> .PHONY pattern

#################################################################################
# PROJECT RULES (Example)                                                      #
#################################################################################

# Note: The 'data' target ran dataset.py directly.
# This might be superseded by running Prefect flows for data processing.
# Keeping it as an example, but consider if it's still needed.
## Make dataset (Example - might be replaced by Prefect flows)
.PHONY: data
data: install
	@echo "Running example data script (consider using Prefect flows instead)..."
	$(PYTHON_INTERPRETER) airnub_prefect_starter/dataset.py


#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Thank you, Franco Papa, for the self-documenting Makefile script
# https://docs.francopapa.com/posts/self-documenting-makefile.html
define PRINT_HELP_PYSCRIPT
import re, sys

lines = '\n'.join([line for line in sys.stdin])
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n\.PHONY: ([a-zA-Z_-]+)', lines)
# Add explicit mapping for targets without .PHONY right above them if needed
# For example, if 'format' didn't have .PHONY immediately above:
# hidden_matches = re.findall(r'\n## (.*)\n([a-zA-Z_-]+):', lines)
# all_matches = {target: help_text for help_text, target in matches}
# for help_text, target in hidden_matches:
#    if target not in all_matches:
#        all_matches[target] = help_text
# sorted_matches = sorted(all_matches.items())

# Simple version assuming .PHONY is always present above the target line
sorted_matches = sorted(matches, key=lambda x: x[1])

print('Available commands:\n')
print('\n'.join(['  \033[36m{:<25}\033[0m {}'.format(target, help_text) for help_text, target in sorted_matches]))

endef
export PRINT_HELP_PYSCRIPT

help:
	@$(PYTHON_INTERPRETER) -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

# Prevent setup.env from being interpreted as a target if user creates it
.PHONY: $(SETUP_ENV_FILE)