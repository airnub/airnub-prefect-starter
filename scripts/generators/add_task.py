#!/usr/bin/env python3
# scripts/generators/add_task.py
"""
Script to scaffold a placeholder file for a new Prefect Task Wrapper and its config.

Prompts the user for the task name, associated department, stage, and optionally
a specific category within that stage (detecting existing categories).

Creates the task Python file within the relevant 'flows/[dept]/[stage]/[cat]/tasks/'
or 'flows/[dept]/[stage]/tasks/' directory.
Creates a corresponding placeholder config YAML file within a parallel structure
under 'configs/variables/'.

Filename convention: [action]_[entity]_task_[dept_id].py / [action]_[entity]_task_config_[dept_id].yaml
(Filename suffix is consistent, directory structure provides category/stage context)

The generated task function is intended to be a thin wrapper around
core implementation logic defined elsewhere in the main package.

Designed to be idempotent - it will not overwrite existing files.
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# --- Configuration ---
# Determine project root (assuming this script is in project_root/scripts/generators/)
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except IndexError:
    print("Error: Could not determine project root. Place this script in a 'scripts/generators' directory.")
    sys.exit(1)

# Define base directories
FLOWS_DIR = PROJECT_ROOT / "flows"
CONFIGS_DIR = PROJECT_ROOT / "configs" / "variables"
STAGES = ["ingestion", "processing", "analysis"] # Standard stages
# Define the base package name for imports from the main library
PACKAGE_NAME = "airnub_prefect_starter"

# --- Helper Functions (Adapted from other generator scripts) ---

def sanitize_identifier(name: str, suffix: str = "_task") -> str:
    """Converts a string to a safe snake_case identifier, optionally adding a suffix."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    s3 = re.sub(r'[\s\-/\\&]+', '_', s2) # Include common separators
    s3 = re.sub(r'\W+', '', s3) # Remove non-alphanumeric chars AFTER replacing separators
    s4 = re.sub(r'_+', '_', s3).strip('_') # Collapse multiple underscores
    base_name = s4 if s4 else "default"
    # Add suffix only if provided and not already present
    if suffix and not base_name.endswith(suffix):
         base_name += suffix
    return base_name

def prompt_user(prompt_text: str, default: str = "") -> str:
    """Prompts the user for input with an optional default."""
    prompt_full = f"{prompt_text}"
    if default:
        prompt_full += f" (default: '{default}')"
    prompt_full += ": "
    response = input(prompt_full).strip()
    return response or default

def prompt_choice(prompt_text: str, options: List[str], allow_cancel: bool = True) -> Optional[str]:
    """Prompts the user to choose from a list of options."""
    if not options:
        print("Error: No options available to choose from.")
        return None

    print(prompt_text)
    for i, option in enumerate(options):
        print(f"  {i + 1}. {option}")

    cancel_option = "(or press Enter to cancel)" if allow_cancel else ""

    while True:
        try:
            choice = input(f"Enter the number of your choice (1-{len(options)}) {cancel_option}: ")
            if not choice and allow_cancel:
                 print("\nOperation cancelled by user.")
                 return None
            index = int(choice) - 1
            if 0 <= index < len(options):
                return options[index]
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except EOFError: # Handle Ctrl+D
             print("\nOperation cancelled by user.")
             return None


def prompt_yes_no(prompt_text: str, default_yes: bool = True) -> bool:
    """Prompts the user for a yes/no answer."""
    default_indicator = "[Y/n]" if default_yes else "[y/N]"
    prompt_full = f"{prompt_text} {default_indicator}: "
    while True:
        response = input(prompt_full).strip().lower()
        if not response:
            return default_yes
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False
        print("Please answer 'yes' or 'no'.")

def get_existing_departments() -> List[str]:
    """Scans the flows directory for existing department identifiers."""
    departments = []
    if FLOWS_DIR.is_dir():
        for item in FLOWS_DIR.iterdir():
            if item.is_dir() and item.name.startswith("dept_") and item.name != "dept_":
                departments.append(item.name)
    return sorted(departments)

def get_existing_categories(dept_identifier: str, stage: str) -> List[str]:
    """Scans the flows/[dept]/[stage] directory for existing category directories."""
    categories = []
    stage_dir = FLOWS_DIR / dept_identifier / stage
    if stage_dir.is_dir():
        for item in stage_dir.iterdir():
            # Check if it's a directory and not a special dir/file
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('__') and item.name != 'tasks':
                categories.append(item.name)
    return sorted(categories)

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
            create_directory(file_path.parent) # Ensure parent exists
            file_path.write_text(content, encoding='utf-8')
            print(f"  Created File: {file_path.relative_to(PROJECT_ROOT)}")
        except IOError as e:
            print(f"  ERROR creating file {file_path}: {e}")
            sys.exit(1)
        except Exception as e:
             print(f"  UNEXPECTED ERROR creating file {file_path}: {e}")
             sys.exit(1)

# --- Placeholder Content Generator (Unchanged) ---

def get_task_wrapper_content(
    task_name_desc: str,
    task_func_name: str, # e.g., parse_xml_task
    full_file_path: Path, # Use full path for comment
    dept_identifier: str,
    stage: str, # Stage is now always present
    category_identifier: Optional[str]
) -> str:
    """Generates placeholder Python content for a new async task wrapper."""

    async_keyword = "async "
    await_keyword = "await "
    task_decorator_name = task_name_desc.replace('_', ' ').title()
    core_logic_func_name = task_func_name.replace('_task', '_logic')
    suggested_common_import = f"{PACKAGE_NAME}.common.utils"
    suggested_logic_import = f"{PACKAGE_NAME}.logic.{core_logic_func_name}"

    if category_identifier:
        intended_use_comment = f"Task specific to '{category_identifier}' category within '{dept_identifier}' ({stage} stage)."
    else:
        intended_use_comment = f"Task for general use within the '{stage}' stage of '{dept_identifier}' department."

    relative_path_str = str(full_file_path.relative_to(PROJECT_ROOT))

    template = f'''\
# {relative_path_str}
import asyncio # Keep asyncio for potential async logic call
from prefect import task, get_run_logger
from typing import Any, Optional, Dict # Added Dict

# --- TODO: Import the core implementation logic ---
# Suggestion: Implement the actual logic in a separate function within the
# '{PACKAGE_NAME}' package (e.g., in '{suggested_common_import}'
# or a new module like '{suggested_logic_import}').
# Then import it here:
# from {PACKAGE_NAME}.logic import {core_logic_func_name} # Example
# ---

logger = get_run_logger()

@task(name="{task_decorator_name}", log_prints=True, retries=0, retry_delay_seconds=5)
{async_keyword}def {task_func_name}(
    # TODO: Define parameters needed by the core logic
    input_data: Any, # Example parameter
    config: Optional[Dict[str, Any]] = None, # Optional config dict
    **kwargs: Any
) -> Any: # TODO: Define a specific return type matching core logic
    """
    Prefect task wrapper for: {task_name_desc}
    {intended_use_comment}

    This task wraps the core implementation logic defined elsewhere in the package.

    Args:
        input_data: Description of primary input.
        config: Optional configuration dictionary for the task.
        **kwargs: Additional keyword arguments passed to the core logic.

    Returns:
        The result from the core logic function. TODO: Specify type.
    """
    logger.info(f"Starting task '{task_decorator_name}'...")
    logger.debug(f"Received input_data type: {{type(input_data)}}, config keys: {{config.keys() if config else 'None'}}")

    result = None
    try:
        # --- TODO: Call the imported core logic function ---
        logger.info("Calling core logic function (placeholder)...")
        # Example: Replace with actual call after importing
        # core_logic_params = config.get("core_logic_params", {{}}) if config else {{}}
        # result = {await_keyword}{core_logic_func_name}(
        #     input_data=input_data,
        #     **core_logic_params, # Pass config params to logic
        #     **kwargs # Pass other kwargs
        # )
        await asyncio.sleep(0.1) # Placeholder for async call simulation
        result = f"Core logic processed input successfully (placeholder)."
        logger.info("Core logic function executed.")
        # --- End Core Logic Call ---

    except Exception as e:
        logger.error(f"Error during task '{task_decorator_name}': {{e}}", exc_info=True)
        raise # Re-raise to fail the task run

    logger.info(f"Finished task '{task_decorator_name}'.")
    return result

# Note: Testing should focus on the core logic function directly.
'''
    return template

def get_task_config_content(
    task_name_desc: str,
    task_func_name: str,
    full_config_path: Path,
    dept_identifier: str,
    stage: str, # Stage is always present now
    category_identifier: Optional[str]
) -> str:
    """Generates placeholder YAML content for a task's config file."""
    if category_identifier:
        scope = f"'{category_identifier}' category ({stage} stage)"
        variable_name = f"{dept_identifier}_{stage}_{category_identifier}_{task_func_name}_config"
    else:
        scope = f"general '{dept_identifier}' department ({stage} stage)"
        variable_name = f"{dept_identifier}_{stage}_{task_func_name}_config" # Added stage here

    return f"""\
# Configuration for task: {task_name_desc}
# File: {full_config_path.relative_to(PROJECT_ROOT)}
# Intended scope: {scope}
# Corresponding Prefect Variable Name (proposal - requires setup script update): {variable_name}

# Define parameters that might configure the '{task_func_name}' task.
# Example Parameters:
# api_endpoint: "https://api.example.com/endpoint"
# processing_threshold: 0.8
"""

# --- Main Script Logic ---

def main():
    print("-" * 60)
    print("--- Add New Task Wrapper Script ---")
    print("-" * 60)

    # 1. Get Task Info
    task_name_desc = prompt_user("Enter a descriptive name for the new task (e.g., Parse XML File, Calculate Risk Score)")
    if not task_name_desc:
        print("Error: Task name cannot be empty.")
        sys.exit(1)

    suggested_func_name = sanitize_identifier(task_name_desc, suffix="_task")
    task_func_name = prompt_user("Enter the task wrapper function name (snake_case, ending with '_task')", default=suggested_func_name)

    if not task_func_name.endswith("_task") or not re.match(r'^[a-z][a-z0-9_]*_task$', task_func_name):
        print(f"Error: Invalid function name '{task_func_name}'. Must be snake_case and end with '_task'.")
        sys.exit(1)

    # 2. Select Associated Department (Mandatory)
    existing_departments = get_existing_departments()
    if not existing_departments:
        print("\nError: No existing department directories found in 'flows/'. Cannot create task.")
        sys.exit(1)
    else:
        dept_identifier = prompt_choice("\nSelect the primary department this task relates to:", existing_departments)
        if not dept_identifier: sys.exit(1)

    # 3. Select Stage (Mandatory)
    stage = prompt_choice("\nSelect the STAGE this task primarily belongs to:", STAGES)
    if not stage: sys.exit(1)

    # 4. Optionally Select Category
    category_identifier = None
    is_cat_specific = prompt_yes_no(f"\nIs this task specific to a CATEGORY within '{dept_identifier}' ({stage} stage)?", default_yes=False)

    if is_cat_specific:
        # *** Get existing categories for the selected dept/stage ***
        existing_categories = get_existing_categories(dept_identifier, stage)
        category_options = existing_categories + ["[Create New Category]", "[None - Place at Stage Level instead]"]
        
        chosen_category_option = prompt_choice(f"\nSelect an existing category, create new, or place at stage level:", category_options)

        if chosen_category_option is None: # User cancelled
            sys.exit(1)
        elif chosen_category_option == "[Create New Category]":
            new_category_name = prompt_user("Enter the new category name:")
            if new_category_name:
                category_identifier = sanitize_identifier(new_category_name, suffix="") # Sanitize without suffix
                if not category_identifier: # Handle empty string after sanitize
                     print("Invalid new category name. Assuming task is stage-level.")
                     category_identifier = None
            else:
                print("No new category name entered. Assuming task is stage-level.")
        elif chosen_category_option == "[None - Place at Stage Level instead]":
            category_identifier = None # Explicitly set to None
            print("Placing task at stage level.")
        else:
            # User selected an existing category
            category_identifier = chosen_category_option
            print(f"Using existing category: '{category_identifier}'")
        # *** End Category Selection Logic ***

    # 5. Determine Paths and Filenames
    task_filename_base = sanitize_identifier(task_name_desc, suffix="")
    # Filename *always* includes department suffix
    task_py_filename = f"{task_filename_base}_task_{dept_identifier}.py"
    task_config_filename = f"{task_filename_base}_task_config_{dept_identifier}.yaml"

    # Determine target directories based on scope (now always includes stage)
    if category_identifier:
        # Category specific paths
        target_flow_dir_base = FLOWS_DIR / dept_identifier / stage / category_identifier
        target_config_dir_base = CONFIGS_DIR / dept_identifier / stage / category_identifier
        scope_desc = f"Category '{category_identifier}' ({stage} stage)"
    else:
        # Stage level paths
        target_flow_dir_base = FLOWS_DIR / dept_identifier / stage
        target_config_dir_base = CONFIGS_DIR / dept_identifier / stage
        scope_desc = f"Department '{dept_identifier}' ({stage} stage)"

    # Define specific 'tasks' subdirectory within the target base directory
    target_task_py_dir = target_flow_dir_base / "tasks"
    target_task_config_dir = target_config_dir_base / "tasks"

    task_filepath = target_task_py_dir / task_py_filename
    config_filepath = target_task_config_dir / task_config_filename

    print(f"\n--- Summary ---")
    print(f"Task Description: '{task_name_desc}'")
    print(f"Function Name:    '{task_func_name}'")
    print(f"Scope:            {scope_desc}")
    print(f"Task Filename:    '{task_py_filename}'")
    print(f"Config Filename:  '{task_config_filename}'")
    print(f"Task Path:        '{task_filepath.relative_to(PROJECT_ROOT)}'")
    print(f"Config Path:      '{config_filepath.relative_to(PROJECT_ROOT)}'")
    print(f"Asynchronous:     Yes (Placeholder)")
    print("-" * 15)

    # 6. Create Placeholder Files (Idempotent)
    print("\nCreating placeholder files...")

    # Create Task Python File
    task_content = get_task_wrapper_content(
        task_name_desc, task_func_name, task_filepath, dept_identifier, category_identifier, stage
    )
    create_file(task_filepath, task_content)
    create_file(target_task_py_dir / "__init__.py", "") # Ensure tasks subdir is package

    # Create Task Config File
    config_content = get_task_config_content(
        task_name_desc, task_func_name, config_filepath, dept_identifier, stage, category_identifier
    )
    create_file(config_filepath, config_content)
    create_file(target_task_config_dir / "__init__.py", "") # Ensure config tasks subdir exists

    # 7. Update __init__.py (Manual Step Reminder)
    print("-" * 60)
    print("Scaffolding complete!")
    print("Next Steps:")
    print(f"1. Create the core logic function (e.g., '{task_func_name.replace('_task', '_logic')}') within the '{PACKAGE_NAME}' package.")
    print(f"2. Implement the actual logic within that core function.")
    print(f"3. Update the task wrapper file '{task_filepath.relative_to(PROJECT_ROOT)}' to import and call the core logic.")
    print(f"4. **IMPORTANT:** Update the relevant '__init__.py' file(s) to make the task importable from flows.")
    # Update import examples based on new location
    if category_identifier:
         print(f"   - Example: Add `from .{task_py_filename[:-3]} import {task_func_name}` to 'flows/{dept_identifier}/{stage}/{category_identifier}/tasks/__init__.py'.")
         print(f"   - Then import from a flow in 'flows/{dept_identifier}/{stage}/{category_identifier}/' using `from .tasks import {task_func_name}`.")
    else: # Stage level
         print(f"   - Example: Add `from .{task_py_filename[:-3]} import {task_func_name}` to 'flows/{dept_identifier}/{stage}/tasks/__init__.py'.")
         print(f"   - Then import from a flow in 'flows/{dept_identifier}/{stage}/' using `from .tasks import {task_func_name}` (or from parent flow using `from .{stage}.tasks import ...`).")
    print(f"5. Ensure 'scripts/setup_prefect_variables.py' handles task config files if they should become Variables.")
    print(f"6. Add unit tests primarily for the core logic function.")
    print("-" * 60)

if __name__ == "__main__":
    # Add PyYAML dependency check (Needed for config file generation)
    try:
        import yaml
    except ImportError:
        print("Error: PyYAML is not installed. Please install it to run this script:")
        print("  pip install pyyaml")
        sys.exit(1)
    main()
# 