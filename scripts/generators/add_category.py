#!/usr/bin/env python3
# scripts/generators/add_category.py
"""
Script to scaffold the directory structure and placeholder files for a new category
within an existing department and stage.

Prompts the user for the department, stage, category name, and action verb,
detecting existing stages/categories to guide the user. Creates the necessary
placeholder flow and config files based on the project's naming conventions.

Designed to be idempotent - it will not overwrite existing files.
"""

import os
import sys
import re
import yaml # Import YAML library
from pathlib import Path
from typing import List, Optional, Dict

# --- Configuration ---
# Determine project root (assuming this script is in project_root/scripts/generators/)
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except IndexError:
    print("Error: Could not determine project root. Place this script in a 'scripts/generators' directory.")
    sys.exit(1)

FLOWS_DIR = PROJECT_ROOT / "flows"
CONFIGS_DIR = PROJECT_ROOT / "configs" / "variables"
# Location of the department name mapping file
DEPT_MAPPING_FILE = PROJECT_ROOT / "configs" / "department_mapping.yaml"
# Standard stages - script will detect existing ones within the selected department
# STAGES = ["ingestion", "processing", "analysis"] # No longer hardcoded list

# --- Helper Functions ---

def sanitize_identifier(name: str) -> str:
    """Converts a string to a safe snake_case identifier."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    s3 = re.sub(r'[\s\-/\\&]+', '_', s2)
    s3 = re.sub(r'\W+', '', s3)
    s4 = re.sub(r'_+', '_', s3).strip('_')
    return s4 if s4 else "default_category"

def prompt_user(prompt_text: str, default: str = "") -> str:
    """Prompts the user for input with an optional default."""
    prompt_full = f"{prompt_text}"
    if default:
        prompt_full += f" (default: '{default}')"
    prompt_full += ": "
    response = input(prompt_full).strip()
    return response or default

def prompt_choice(prompt_text: str, options: List[str]) -> Optional[str]:
    """Prompts the user to choose from a list of options."""
    if not options:
        print("Error: No options available to choose from.")
        return None

    print(prompt_text)
    for i, option in enumerate(options):
        print(f"  {i + 1}. {option}")

    while True:
        try:
            choice = input(f"Enter the number of your choice (1-{len(options)}): ")
            index = int(choice) - 1
            if 0 <= index < len(options):
                return options[index]
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except EOFError:
             print("\nOperation cancelled by user.")
             return None


def create_directory(dir_path: Path):
    """Creates a directory if it doesn't exist."""
    if not dir_path.exists():
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created Dir: {dir_path.relative_to(PROJECT_ROOT)}")
        except OSError as e:
            print(f"  ERROR creating directory {dir_path}: {e}")
            sys.exit(1)

def create_file(file_path: Path, content: str):
    """Creates a file with content if it doesn't exist."""
    if file_path.exists():
        print(f"   Exists: {file_path.relative_to(PROJECT_ROOT)} (Skipping)")
    else:
        try:
            create_directory(file_path.parent)
            file_path.write_text(content, encoding='utf-8')
            print(f"  Created File: {file_path.relative_to(PROJECT_ROOT)}")
        except IOError as e:
            print(f"  ERROR creating file {file_path}: {e}")
            sys.exit(1)
        except Exception as e:
             print(f"  UNEXPECTED ERROR creating file {file_path}: {e}")
             sys.exit(1)

def get_existing_departments() -> List[str]:
    """Scans the flows directory for existing department identifiers."""
    departments = []
    if FLOWS_DIR.is_dir():
        for item in FLOWS_DIR.iterdir():
            if item.is_dir() and item.name.startswith("dept_") and item.name != "dept_":
                departments.append(item.name)
    return sorted(departments)

# --- New Functions to Detect Stages/Categories ---
def get_existing_stages(dept_flows_path: Path) -> List[str]:
    """Scans a department's flow directory for existing stage subdirectories."""
    stages = []
    if dept_flows_path.is_dir():
        for item in dept_flows_path.iterdir():
            # Check if it's a directory and its name is one of the known stages
            if item.is_dir() and item.name in ["ingestion", "processing", "analysis"]:
                 stages.append(item.name)
    return sorted(stages)

def get_existing_categories(stage_flows_path: Path) -> List[str]:
    """Scans a stage directory for existing category subdirectories."""
    categories = []
    # Define exclusions
    exclude_dirs = {"__pycache__", "tasks", "subflows"} # Directories to ignore
    if stage_flows_path.is_dir():
        for item in stage_flows_path.iterdir():
            # Check if it's a directory and not in exclusions
            if item.is_dir() and item.name not in exclude_dirs:
                 categories.append(item.name)
    return sorted(categories)
# --- End New Functions ---

def load_department_mapping() -> Dict[str, str]:
    """Loads the identifier-to-full-name mapping from the YAML file."""
    mapping = {}
    mapping_file_rel = DEPT_MAPPING_FILE.relative_to(PROJECT_ROOT)
    if not DEPT_MAPPING_FILE.is_file():
        print(f"Warning: Department mapping file not found at '{mapping_file_rel}'.")
        print("         Full department names will need manual input or fallback.")
        return mapping

    try:
        with open(DEPT_MAPPING_FILE, 'r', encoding='utf-8') as f:
            mapping = yaml.safe_load(f)
            if mapping is None: return {} # Handle empty file
            if not isinstance(mapping, dict):
                print(f"Warning: Content of '{mapping_file_rel}' is not a valid dictionary. Mapping disabled.")
                return {}
            print(f"Successfully loaded department mapping from '{mapping_file_rel}'")
            return mapping
    except yaml.YAMLError as e:
        print(f"Error parsing department mapping file '{mapping_file_rel}': {e}")
        return {}
    except Exception as e:
        print(f"Error reading department mapping file '{mapping_file_rel}': {e}")
        return {}

# --- Placeholder Content Generators ---

# *** THIS FUNCTION IS UPDATED ***
def get_category_flow_content(
    action_verb: str,
    category_name: str,
    category_identifier: str,
    full_dept_name: str,
    dept_identifier: str,
    stage: str
) -> str:
    """Generates placeholder Python content for a category-level flow."""
    flow_name = f"{action_verb.capitalize()} {category_name} ({full_dept_name})"
    # Use the consistent filename convention
    func_name = f"{action_verb.lower()}_{category_identifier}_flow_{dept_identifier}"
    # relative_path = f"flows/{dept_identifier}/{stage}/{action_verb.lower()}_{category_identifier}_flow_{dept_identifier}.py"
    relative_path = f"flows/{dept_identifier}/{stage}/{category_identifier}/{action_verb.lower()}_{category_identifier}_flow_{dept_identifier}.py" # Corrected path
    variable_name = f"{dept_identifier}_{stage}_{category_identifier}_config"
    # Define base tags for this flow
    base_tags_list = [dept_identifier, stage, category_identifier] # Example base tags

    template = f'''\
# {relative_path}
import asyncio
import json
# *** UPDATED IMPORT ***
from prefect import flow, get_run_logger, variables, tags
from typing import Dict, Any, Optional

# TODO: Import necessary shared tasks (e.g., from common, tasks directories)
# from .....airnub_prefect_starter.tasks import manifest_tasks, storage_tasks, scraping_tasks, processing_tasks
# TODO: Import any necessary category-specific tasks (from ./tasks/)

logger = get_run_logger()

@flow(name="{flow_name}", log_prints=True)
async def {func_name}(
    config: Optional[Dict[str, Any]] = None, # Config passed down from parent
    # TODO: Add other parameters specific to this category/action
):
    """
    Flow for {action_verb.lower()}ing data related to the '{category_name}' category
    within the {full_dept_name}.

    Typically called by the parent '{stage.capitalize()} Flow ({full_dept_name})'.
    Receives its specific configuration section from the parent.
    Applies '{dept_identifier}', '{stage}', and '{category_identifier}' tags to child runs.
    """
    logger.info(f"Starting {flow_name}...")

    # Define base tags for tasks called within this flow run
    base_tags = {base_tags_list!r} # Use repr to get list literal in string

    # *** WRAP MAIN LOGIC WITH TAGS ***
    with tags(*base_tags):
        logger.info(f"Applying tags to context: {{base_tags}}")

        if config:
            logger.info("Received configuration:")
            logger.info(f"Config keys: {{list(config.keys())}}")
        else:
            logger.warning("No configuration dictionary provided to flow.")
            # If independent run needed, add logic to load variable: '{variable_name}'

        # --- TODO: Implement {action_verb} Logic ---
        # Example steps:
        # 1. Load specific task configs if needed (passed in main config or loaded separately)
        # 2. Call relevant tasks (imported from shared tasks or local ./tasks/ dir)
        #    - e.g., scraping_tasks.fetch_page(...)
        #    - e.g., manifest_tasks.get_existing_hashes_for_source(...)
        #    - e.g., custom_task_for_this_category(...)

        await asyncio.sleep(1) # Placeholder for async work
        logger.info("Placeholder: Implement actual logic.")
        # --- End Implementation ---

    # This log is outside the 'with tags' block
    logger.info(f"Finished {flow_name}.")
    # TODO: Return a meaningful summary dictionary
    return {{"status": "SUCCESS_PLACEHOLDER", "category": "{category_name}"}}

# Example of how parent might call this (in {stage}_flow_{dept_identifier}.py):
# if run_{category_identifier}:
#     logger.info("Calling {category_name} flow...")
#     cat_coro = {func_name}(
#         config=main_config.get("{category_identifier}", {{}}),
#         # pass other params
#     )
#     tasks_to_await.append(cat_coro)
'''
    return template
# *** END OF UPDATED FUNCTION ***

def get_category_config_content(
    action_verb: str,
    category_name: str,
    category_identifier: str,
    full_dept_name: str,
    dept_identifier: str,
    stage: str
) -> str:
    """Generates placeholder YAML content for a category-level config file."""
    variable_name = f"{dept_identifier}_{stage}_{category_identifier}_config"
    # Use the consistent filename convention
    relative_path = f"configs/variables/{dept_identifier}/{stage}/{category_identifier}/{action_verb.lower()}_{category_identifier}_config_{dept_identifier}.yaml" # Corrected path

    return f"""\
# Configuration for: {action_verb.capitalize()} {category_name} ({full_dept_name})
# File: {relative_path}
# Corresponding Prefect Variable Name (proposal - requires setup script update): {variable_name}

# Define parameters needed by the '{action_verb.lower()}_{category_identifier}_flow_{dept_identifier}.py' flow.
# This structure will likely be loaded into a Prefect Variable (e.g., '{variable_name}')
# or included within a larger department/stage configuration Variable.

# Example Parameters:
data_source_name: "{dept_identifier}_{stage}_{category_identifier}" # For manifest tasks
source_url: "http://example.com/{dept_identifier}/{stage}/{category_identifier}/data.csv"
# api_endpoint: null
# target_table: "processed_{category_identifier}"
# scraping_selectors:
#   - container: ".item-list"
#     link: "a.data-link[href]"
# processing_threshold: 0.95
"""

# --- Main Script Logic ---

def main():
    print("-" * 60)
    print("--- Add New Category Script ---")
    print("-" * 60)

    dept_mapping = load_department_mapping()

    # 1. Select Department
    existing_departments = get_existing_departments()
    if not existing_departments:
        print("Error: No existing department directories found in 'flows/'.")
        sys.exit(1)

    dept_identifier = prompt_choice("Select the department to add the category to:", existing_departments)
    if not dept_identifier: sys.exit(1)

    full_dept_name = dept_mapping.get(dept_identifier)
    if not full_dept_name:
        print(f"\nWarning: Full name for '{dept_identifier}' not found in {DEPT_MAPPING_FILE}.")
        full_dept_name = prompt_user(f"Enter the full name for department '{dept_identifier}'")
        if not full_dept_name: sys.exit(1)
        print(f"Consider adding '{dept_identifier}: \"{full_dept_name}\"' to {DEPT_MAPPING_FILE}")
    else:
        print(f"Selected Department: '{dept_identifier}' ('{full_dept_name}')")

    # 2. Select Stage
    dept_flows_path = FLOWS_DIR / dept_identifier
    existing_stages = get_existing_stages(dept_flows_path)
    if not existing_stages:
        print(f"\nError: No stage directories (e.g., 'ingestion', 'processing') found within '{dept_flows_path}'.")
        print("Please run 'add_department.py' to ensure the structure exists.")
        sys.exit(1)

    stage = prompt_choice("\nSelect the stage for the new category:", existing_stages)
    if not stage: sys.exit(1)

    # 3. Get Category Info
    stage_flows_path = dept_flows_path / stage
    existing_categories = get_existing_categories(stage_flows_path)
    if existing_categories:
        print("\nExisting categories in this stage:")
        for cat in existing_categories:
            print(f"  - {cat}")
    else:
        print("\nNo existing categories found in this stage.")

    category_name = prompt_user(f"\nEnter the NEW category name for stage '{stage}' (e.g., Monthly Revenue, User Profiles)")
    if not category_name:
        print("Error: Category name cannot be empty.")
        sys.exit(1)
    category_identifier = sanitize_identifier(category_name)

    # Check if category directory already exists to prevent accidental overwrite of structure
    new_category_flow_dir = stage_flows_path / category_identifier
    if new_category_flow_dir.exists():
        print(f"\nWarning: A directory for category '{category_identifier}' already exists at:")
        print(f"         '{new_category_flow_dir.relative_to(PROJECT_ROOT)}'")
        overwrite_confirm = prompt_user("Do you want to proceed and potentially add files inside it? (yes/no)", default="no")
        if overwrite_confirm.lower() != 'yes':
            print("Operation cancelled.")
            sys.exit(0)

    # 4. Get Action Verb
    default_action = stage.capitalize() if stage != "ingestion" else "Ingest"
    action_verb = prompt_user(f"Enter the primary action verb for this category flow (e.g., Ingest, Process, Analyze, Scrape)", default=default_action)
    if not action_verb:
        print("Error: Action verb cannot be empty.")
        sys.exit(1)
    action_verb_lower = action_verb.lower()

    print(f"\n--- Summary ---")
    print(f"Target Department: '{dept_identifier}' ('{full_dept_name}')")
    print(f"Target Stage:      '{stage}'")
    print(f"New Category:      '{category_name}' (Identifier: '{category_identifier}')")
    print(f"Action Verb:       '{action_verb}'")
    print("-" * 15)

    # 5. Define Paths (including new category directory)
    category_flow_dir = stage_flows_path / category_identifier
    category_config_dir = CONFIGS_DIR / dept_identifier / stage / category_identifier

    # Create category directories if they don't exist (idempotent)
    create_directory(category_flow_dir)
    create_file(category_flow_dir / "__init__.py", "") # Make category dir a package
    create_directory(category_config_dir)

    # 6. Construct Filenames using the consistent convention
    flow_filename = f"{action_verb_lower}_{category_identifier}_flow_{dept_identifier}.py"
    config_filename = f"{action_verb_lower}_{category_identifier}_config_{dept_identifier}.yaml"

    flow_filepath = category_flow_dir / flow_filename # Place inside category dir
    config_filepath = category_config_dir / config_filename # Place inside category dir

    # 7. Create Placeholder Files (Idempotent)
    print("\nCreating placeholder files...")

    # Category Flow File
    flow_content = get_category_flow_content( # Uses updated function
        action_verb, category_name, category_identifier, full_dept_name, dept_identifier, stage
    )
    create_file(flow_filepath, flow_content)

    # Category Config File
    config_content = get_category_config_content(
         action_verb, category_name, category_identifier, full_dept_name, dept_identifier, stage
    )
    create_file(config_filepath, config_content)

    print("-" * 60)
    print("Scaffolding complete!")
    print("Next Steps:")
    print(f"1. Implement the specific logic within '{flow_filepath.relative_to(PROJECT_ROOT)}'.")
    print(f"2. Define the necessary configuration in '{config_filepath.relative_to(PROJECT_ROOT)}'.")
    print(f"3. **IMPORTANT:** Update the parent stage orchestrator flow ('{stage}_flow_{dept_identifier}.py')")
    print(f"   to import and call the new '{action_verb_lower}_{category_identifier}_flow_{dept_identifier}' function.")
    print(f"   Example Import: `from .{stage}.{category_identifier}.{flow_filename[:-3]} import {action_verb_lower}_{category_identifier}_flow_{dept_identifier}`")
    print(f"4. Ensure 'scripts/setup_prefect_variables.py' is updated to handle the new config file pattern/location if needed.")
    print(f"5. Add tests for the new category flow.")
    print(f"6. Ensure the department mapping in '{DEPT_MAPPING_FILE.relative_to(PROJECT_ROOT)}' is up-to-date.")
    print("-" * 60)

if __name__ == "__main__":
    # Add PyYAML dependency check
    try:
        import yaml
    except ImportError:
        print("Error: PyYAML is not installed. Please install it to run this script:")
        print("  pip install pyyaml")
        sys.exit(1)
    main()

# 