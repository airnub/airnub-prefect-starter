#!/usr/bin/env python3
# scripts/setup_prefect_variables.py
"""
Handles creation and updates of Prefect Variables from YAML configuration files
stored in a nested directory structure under 'configs/variables/'.

Scans for YAML files matching '*_config_dept_*.yaml', derives Variable names
and tags from the path and filename, and loads the YAML content.

Checks for existing Variables and prompts the user before overwriting unless
the PREFECT_VARIABLE_OVERWRITE environment variable is set to 'true'.

Requires PyYAML and python-dotenv: pip install pyyaml python-dotenv
"""

import asyncio
import os
import sys
import traceback
import json
import yaml # Requires PyYAML
from pathlib import Path
from typing import Dict, Any, List, Optional

# --- Prefect Imports ---
try:
    from prefect.variables import Variable
    from prefect.exceptions import ObjectNotFound
    from prefect.client.orchestration import get_client
except ImportError as e:
    print(f"FATAL ERROR: Failed to import Prefect modules: {e}")
    print("Ensure Prefect and its dependencies are installed correctly.")
    sys.exit(1)
except Exception as e:
    print(f"FATAL ERROR: Unexpected error during Prefect imports: {e}")
    sys.exit(1)

# --- python-dotenv Import ---
try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv not installed. .env file will not be loaded.")
    load_dotenv = None

# --- Configuration ---
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
except IndexError:
    PROJECT_ROOT = Path.cwd()
    print(f"Warning: Could not determine project root relative to script location. Assuming CWD: {PROJECT_ROOT}")
    if not (PROJECT_ROOT / "configs").is_dir() or not (PROJECT_ROOT / "flows").is_dir():
        print("Error: Expected 'configs' and 'flows' directories not found in current working directory.")
        sys.exit(1)

CONFIG_VARIABLES_DIR = PROJECT_ROOT / "configs" / "variables"
FILENAME_SUFFIX_PATTERN = "_config_dept_"
VALID_STAGES = ["ingestion", "processing", "analysis"]

# --- Helper Functions --- (prompt_yes_no, set_variable - assuming these are correct from previous versions)
def prompt_yes_no(prompt_text: str, default_yes: bool = True) -> bool:
    """Prompts the user for a yes/no answer."""
    default_indicator = "[Y/n]" if default_yes else "[y/N]"
    prompt_full = f"{prompt_text} {default_indicator}: "
    while True:
        try:
            response = input(prompt_full).strip().lower()
            if not response:
                return default_yes
            if response in ['y', 'yes']:
                return True
            if response in ['n', 'no']:
                return False
            print("Please answer 'yes' or 'no'.")
        except EOFError:
             print("\nOperation cancelled by user.")
             return False

async def set_variable(var_name: str, var_value: Any, force_overwrite: bool, tags: Optional[List[str]] = None):
    """
    Creates or updates a Prefect Variable, handling overwrite logic.

    Args:
        var_name: The name of the Prefect Variable.
        var_value: The value to set (will be JSON serialized if dict/list).
        force_overwrite: Boolean indicating if overwrites are forced via ENV var.
        tags: Optional list of tags for the variable.
    """
    print(f"\nProcessing Variable: '{var_name}'")
    should_set = False
    try:
        existing_var = await Variable.get(var_name, default=None)
        if existing_var is None:
            print(f"- Variable '{var_name}' does not exist. Creating...")
            should_set = True
            action = "Created"
        elif force_overwrite:
            print(f"- Variable '{var_name}' exists. Overwriting (PREFECT_VARIABLE_OVERWRITE=true).")
            should_set = True
            action = "Updated"
        else:
            # Variable exists, and overwrite not forced by ENV var
            print(f"- Variable '{var_name}' already exists.")
            if prompt_yes_no(f"  Overwrite existing variable '{var_name}'?", default_yes=False):
                should_set = True
                action = "Updated"
            else:
                print(f"- Skipping update for '{var_name}'.")
                should_set = False

        if should_set:
            # Store complex values as JSON strings without indentation
            value_str = json.dumps(var_value) if isinstance(var_value, (dict, list)) else str(var_value)
            await Variable.set(name=var_name, value=value_str, tags=tags or [], overwrite=True)
            print(f"- {action} Variable: '{var_name}'")
    except ObjectNotFound: # Should be caught by default=None, but good for safety
         print(f"- Variable '{var_name}' does not exist (ObjectNotFound). Creating...")
         try:
             value_str = json.dumps(var_value) if isinstance(var_value, (dict, list)) else str(var_value)
             await Variable.set(name=var_name, value=value_str, tags=tags or [], overwrite=False)
             print(f"- Created Variable: '{var_name}'")
         except Exception as e_set:
             print(f"ERROR: Failed to create Variable '{var_name}' after ObjectNotFound: {e_set}")
             traceback.print_exc()
    except Exception as e:
        print(f"ERROR: Failed processing Variable '{var_name}': {e}")
        traceback.print_exc()

def derive_variable_info(config_file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Derives the Prefect Variable name and tags from the config file path.
    Correctly handles parent stage files like 'ingestion_config_dept_project_alpha.yaml'.
    """
    try:
        relative_path_to_config_vars_dir = config_file_path.relative_to(CONFIG_VARIABLES_DIR)
        filename = config_file_path.name

        if FILENAME_SUFFIX_PATTERN not in filename:
            print(f"  Warning: Skipping file '{filename}' - does not match suffix pattern '{FILENAME_SUFFIX_PATTERN}*'.")
            return None

        base_name_part_from_file, dept_id_from_filename = filename.rsplit(FILENAME_SUFFIX_PATTERN, 1)
        dept_identifier = "dept_" + dept_id_from_filename.replace(".yaml", "").replace(".yml", "")

        # Directory parts relative to CONFIG_VARIABLES_DIR (e.g., ['dept_project_alpha', 'ingestion', 'tasks'])
        dir_parts_from_config_vars = list(relative_path_to_config_vars_dir.parts[:-1])

        if not dir_parts_from_config_vars or dir_parts_from_config_vars[0] != dept_identifier:
            print(f"  Warning: Skipping file '{filename}'. Directory structure mismatch. Expected base dir: '{dept_identifier}', found: '{dir_parts_from_config_vars[0] if dir_parts_from_config_vars else 'None'}'. Relative path: {relative_path_to_config_vars_dir}")
            return None

        variable_name_segments = [dept_identifier]
        tags = [dept_identifier]

        # Path depth relative to the department directory (dept_identifier)
        # Example:
        # .../dept_project_alpha/ -> path_parts_within_dept = [] (depth 0 within dept) -> parent stage config
        # .../dept_project_alpha/ingestion/ -> path_parts_within_dept = ['ingestion'] (depth 1 within dept) -> category/stage-task config
        # .../dept_project_alpha/ingestion/category_x/ -> path_parts_within_dept = ['ingestion', 'category_x'] (depth 2 within dept) -> category-task config
        path_parts_within_dept = dir_parts_from_config_vars[1:] # Parts after the department directory itself

        is_parent_stage_config = False
        identified_stage = None
        identified_category = None
        is_task_config = "tasks" in path_parts_within_dept # 'tasks' can be at different levels

        if not path_parts_within_dept: # File is directly under department dir
            if base_name_part_from_file in VALID_STAGES:
                is_parent_stage_config = True
                identified_stage = base_name_part_from_file
        else: # File is in a subdirectory of the department
            if path_parts_within_dept[0] in VALID_STAGES:
                identified_stage = path_parts_within_dept[0]
            if len(path_parts_within_dept) > 1 and path_parts_within_dept[1] != "tasks":
                identified_category = path_parts_within_dept[1]

        # Construct variable name parts
        if is_parent_stage_config:
            # e.g., dept_project_alpha_ingestion_config
            variable_name_segments.append(identified_stage)
            tags.append(identified_stage)
            tags.append("stage-config")
        else: # Category flow, stage-level task, or category-level task
            if identified_stage:
                variable_name_segments.append(identified_stage)
                tags.append(identified_stage)
            if identified_category:
                variable_name_segments.append(identified_category)
                tags.append(identified_category)
            
            # For category flows (e.g., ingest_public_api_data_config_dept_...)
            # or task files (e.g., parse_api_response_task_config_dept_...)
            # base_name_part_from_file is like "ingest_public_api_data" or "parse_api_response_task"
            variable_name_segments.append(base_name_part_from_file)
            
            if is_task_config:
                tags.append("task-config")
            elif identified_category : # It's a category flow config
                tags.append("category-config") # Optional: specific tag for category configs

        variable_name_segments.append("config")
        
        # Join, filter empty, and clean up
        final_variable_name = "_".join(filter(None, variable_name_segments))
        while "__" in final_variable_name:
            final_variable_name = final_variable_name.replace("__", "_")
        final_variable_name = final_variable_name.strip("_")
        
        unique_tags = sorted(list(set(tags)))

        return {"name": final_variable_name, "tags": unique_tags}

    except Exception as e:
        print(f"  ERROR in derive_variable_info for '{config_file_path.name}': {e}")
        traceback.print_exc()
        return None

# --- Variable Creation Logic --- (create_variables_from_configs - assumed correct from previous)
async def create_variables_from_configs(config_base_dir: Path, force_overwrite: bool):
    """
    Recursively scans config directories for YAML files, derives Variable names/tags,
    and creates/updates Prefect Variables.
    """
    print(f"\n--- Scanning for Config Files in '{config_base_dir}' ---")
    if not config_base_dir.is_dir():
        print(f"ERROR: Base configuration directory not found: {config_base_dir}")
        return

    # Use rglob to find files matching the pattern recursively
    config_files = list(config_base_dir.rglob(f"*{FILENAME_SUFFIX_PATTERN}*.yaml")) \
                 + list(config_base_dir.rglob(f"*{FILENAME_SUFFIX_PATTERN}*.yml"))

    if not config_files:
        print(f"No config files matching '*{FILENAME_SUFFIX_PATTERN}*.yaml/.yml' found in subdirectories.")
        return

    print(f"Found {len(config_files)} potential config files to process.")

    variable_creation_tasks = [] # Coroutines for set_variable

    for config_file_path in config_files:
        print("-" * 20)
        print(f"Processing: {config_file_path.relative_to(PROJECT_ROOT)}")

        # Derive variable name and tags from path
        var_info = derive_variable_info(config_file_path)
        if not var_info:
            print(f"  Skipping file {config_file_path.name} due to info derivation issue.")
            continue

        variable_name = var_info["name"]
        tags = var_info["tags"]
        print(f"  Derived Variable Name: '{variable_name}'")
        print(f"  Derived Tags: {tags}")

        # Read and parse the YAML file
        try:
            file_content = config_file_path.read_text(encoding='utf-8')
            config_value = yaml.safe_load(file_content)

            if config_value is None:
                print(f"  Warning: Config file '{config_file_path.name}' is empty or contains only null. Skipping variable '{variable_name}'.")
                continue
            if not isinstance(config_value, (dict, list)):
                 print(f"  Warning: Content of '{config_file_path.name}' is not a dictionary/list. Skipping variable '{variable_name}'.")
                 continue

            variable_creation_tasks.append(set_variable(
                var_name=variable_name,
                var_value=config_value,
                force_overwrite=force_overwrite,
                tags=tags
            ))
        except yaml.YAMLError as e:
            print(f"  ERROR: Failed to parse YAML file '{config_file_path.name}': {e}")
        except Exception as e:
            print(f"  ERROR: Failed processing file '{config_file_path.name}': {e}")
            traceback.print_exc()

    # Run all variable setting tasks concurrently
    if variable_creation_tasks:
        print("-" * 20)
        print(f"\nSubmitting {len(variable_creation_tasks)} variable set operations...")
        await asyncio.gather(*variable_creation_tasks)
        print("Finished submitting variable set operations.")
    else:
         print("No valid variables to create or update from the processed files.")

# --- Main Execution Block --- (assumed correct from previous)
if __name__ == "__main__":
    # --- Dependency Checks ---
    try:
        import yaml
    except ImportError:
        print("Error: PyYAML is not installed. Please install it to run this script:")
        print("  pip install pyyaml")
        sys.exit(1)

    # --- Load .env ---
    dotenv_path = PROJECT_ROOT / '.env'
    if load_dotenv:
        print(f"Attempting to load environment variables from: {dotenv_path}")
        try:
            loaded = load_dotenv(dotenv_path=dotenv_path, override=True)
            if loaded: print("Successfully loaded variables from .env file.")
            else: print("No .env file found or it was empty.")
        except Exception as e: print(f"Warning: Error loading .env file: {e}")
    else: print(".env file loading skipped as python-dotenv is not installed.")

    # --- Prefect API Config ---
    api_url = os.environ.get("PREFECT_API_URL")
    api_key = os.environ.get("PREFECT_API_KEY")
    if not api_url:
        print("\nERROR: PREFECT_API_URL environment variable not set.")
        print("Please set it directly or via the .env file.")
        sys.exit(1)
    if "prefect.cloud" in api_url and not api_key:
        print("\nWARNING: PREFECT_API_URL looks like Prefect Cloud, but PREFECT_API_KEY is not set.")

    # --- Overwrite Setting ---
    force_overwrite = os.environ.get("PREFECT_VARIABLE_OVERWRITE", "false").lower() == "true"
    print(f"\nForce Overwrite Existing Variables (via ENV): {force_overwrite}")
    if not force_overwrite:
        print("Will prompt before overwriting existing variables.")

    # --- Run Main Logic ---
    print(f"\nTargeting Prefect API: {api_url}")
    print(f"Scanning for config files in: {CONFIG_VARIABLES_DIR}")
    print(f"Deriving Variable names from path/filename structure...")
    print("Starting variable creation...\n")

    try:
        asyncio.run(create_variables_from_configs(CONFIG_VARIABLES_DIR, force_overwrite))
    except Exception as e:
        print(f"\nCRITICAL ERROR during script execution: {e}")
        traceback.print_exc()

    print("\nVariable setup script finished.")