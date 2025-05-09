#!/usr/bin/env python3
# scripts/generators/add_department.py
"""
Script to scaffold the directory structure and placeholder files for a new department.

Prompts the user for the department's full name and a short identifier,
then creates the necessary directories and basic flow/config files based
on the project's naming conventions.

Also updates the central department mapping file (configs/department_mapping.yaml)
and optionally adds basic deployment definitions to prefect.local.yaml using the
'[Stage] Deployment ([Dept Full Name])' naming convention.

Designed to be idempotent - it will not overwrite existing files or directories,
and will only add/update the relevant entry in the mapping file and add missing
deployments to prefect.local.yaml if requested.
"""

import os
import sys
import re
import asyncio
import yaml # Import YAML library
from pathlib import Path
from typing import Dict, Any, List, Optional

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
# Location of the local deployment file to update
PREFECT_LOCAL_YAML = PROJECT_ROOT / "prefect.local.yaml"
STAGES = ["ingestion", "processing", "analysis"] # Standard stages to create

# --- Helper Functions ---

def sanitize_identifier(name: str) -> str:
    """Converts a string to a safe snake_case identifier."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    s3 = re.sub(r'\W+', '_', s2)
    s4 = re.sub(r'_+', '_', s3).strip('_')
    return s4 if s4 else "default_id"

def prompt_user(prompt_text: str, default: str = "") -> str:
    """Prompts the user for input with an optional default."""
    prompt_full = f"{prompt_text}"
    if default:
        prompt_full += f" (default: '{default}')"
    prompt_full += ": "
    response = input(prompt_full).strip()
    return response or default

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
             return False # Treat cancel as 'no'

def create_directory(dir_path: Path, add_gitkeep: bool = False):
    """Creates a directory if it doesn't exist. Optionally adds .gitkeep."""
    if not dir_path.exists():
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created Dir: {dir_path.relative_to(PROJECT_ROOT)}")
            if add_gitkeep:
                gitkeep_path = dir_path / ".gitkeep"
                if not gitkeep_path.exists():
                    gitkeep_path.touch()
                    print(f"  Created File: {gitkeep_path.relative_to(PROJECT_ROOT)}")
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

# --- Department Mapping File Handling ---

def load_department_mapping() -> Dict[str, str]:
    """Loads the identifier-to-full-name mapping from the YAML file."""
    mapping = {}
    if not DEPT_MAPPING_FILE.is_file():
        print(f"Info: Department mapping file not found at '{DEPT_MAPPING_FILE.relative_to(PROJECT_ROOT)}'. Will create it.")
        return mapping
    try:
        print(f"Loading existing department mapping from '{DEPT_MAPPING_FILE.relative_to(PROJECT_ROOT)}'...")
        with open(DEPT_MAPPING_FILE, 'r', encoding='utf-8') as f:
            loaded_content = yaml.safe_load(f)
        if loaded_content is None:
            print("   Mapping file is empty or contains only null.")
            return {}
        if not isinstance(loaded_content, dict):
            print(f"Warning: Content of '{DEPT_MAPPING_FILE.relative_to(PROJECT_ROOT)}' is not a valid dictionary. Mapping disabled.")
            return {}
        print(f"   Successfully loaded {len(loaded_content)} existing mapping(s).")
        return loaded_content
    except yaml.YAMLError as e:
        print(f"ERROR parsing department mapping file '{DEPT_MAPPING_FILE.relative_to(PROJECT_ROOT)}': {e}")
        return {}
    except Exception as e:
        print(f"ERROR reading department mapping file '{DEPT_MAPPING_FILE.relative_to(PROJECT_ROOT)}': {e}")
        return {}

def save_department_mapping(mapping_data: Dict[str, str]):
    """Saves the department mapping data back to the YAML file, sorted."""
    try:
        print(f"Saving updated department mapping to '{DEPT_MAPPING_FILE.relative_to(PROJECT_ROOT)}'...")
        create_directory(DEPT_MAPPING_FILE.parent)
        sorted_mapping = dict(sorted(mapping_data.items()))
        with open(DEPT_MAPPING_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(sorted_mapping, f, default_flow_style=False, sort_keys=False, allow_unicode=True, indent=2)
        print("   Successfully saved mapping file.")
    except Exception as e:
        print(f"ERROR saving department mapping file '{DEPT_MAPPING_FILE.relative_to(PROJECT_ROOT)}': {e}")

# --- Placeholder Content Generators ---

def get_parent_flow_content(stage: str, full_dept_name: str, dept_identifier: str) -> str:
    """Generates placeholder Python content for a parent orchestrator flow."""
    flow_name = f"{stage.capitalize()} Flow ({full_dept_name})"
    func_name = f"{stage}_flow_{dept_identifier}"
    base_tags_list = [dept_identifier, stage]

    template = f'''\
# flows/{dept_identifier}/{stage}_flow_{dept_identifier}.py
import asyncio
import json
from prefect import flow, get_run_logger, variables, tags
from typing import List, Dict, Any, Optional, Coroutine

# TODO: Import category flows from .{stage}.[category]...

logger = get_run_logger()

@flow(name="{flow_name}", log_prints=True)
async def {func_name}(
    config_variable_name: Optional[str] = "{dept_identifier}_{stage}_config",
    # TODO: Add params like run_category_x: bool = True
):
    """
    Parent orchestrator flow for the {stage} stage for {full_dept_name}.
    Applies '{dept_identifier}' and '{stage}' tags to child runs.
    """
    logger.info(f"Starting {flow_name}...")
    logger.info(f"Config Variable targeted: {{config_variable_name}}")
    base_tags = {base_tags_list!r}
    with tags(*base_tags):
        logger.info(f"Applying tags to context: {{base_tags}}")
        main_config = {{}}
        if config_variable_name:
            try:
                config_value = await variables.Variable.get(config_variable_name)
                if config_value is not None:
                     main_config = json.loads(config_value)
                     logger.info(f"Successfully loaded config Variable '{{config_variable_name}}'")
                else:
                     logger.warning(f"Config Variable '{{config_variable_name}}' is None.")
            except Exception as e:
                logger.error(f"Failed to load/parse config Variable '{{config_variable_name}}': {{e}}", exc_info=False)

        tasks_to_await: List[Coroutine] = []
        # Example:
        # if run_category_x:
        #     logger.info("Calling Category X flow...")
        #     # Subflow call is within the 'with tags' block and should inherit tags
        #     cat_x_coro = category_x_flow_{dept_identifier}(
        #         config=main_config.get("category_x", {{}}),
        #         # pass other params
        #     )
        #     tasks_to_await.append(cat_x_coro)
        # TODO: Add logic to call category flows based on params/config

        if not tasks_to_await:
            logger.warning("No category flows selected to run.")
        else:
            logger.info(f"Waiting for {{len(tasks_to_await)}} category flows...")
            results = await asyncio.gather(*tasks_to_await, return_exceptions=True)
            logger.info(f"Category flows finished. Results/Exceptions: {{results}}")

        # --- TODO: Add Summary Task/Artifact Creation ---
        # If calling a summary task, ensure its .submit() or direct await call
        # is also within this 'with tags' block if you want it tagged.
        logger.info(f"Placeholder: Add summary logic.")
    logger.info(f"Finished {flow_name}.")

# if __name__ == "__main__":
#     # asyncio.run({func_name}())
'''
    return template

def get_parent_config_content(stage: str, full_dept_name: str, dept_identifier: str) -> str:
    """Generates placeholder YAML content for a parent orchestrator config file."""
    return f"""\
# Configuration for: {stage.capitalize()} Flow ({full_dept_name})
# File: configs/variables/{dept_identifier}/{stage}_config_{dept_identifier}.yaml
# Corresponding Prefect Variable Name (proposed): {dept_identifier}_{stage}_config
# department_name: "{full_dept_name}"
# subflow_configs:
#   category_x: {{}}
"""

# --- Deployment YAML Handling ---

def generate_deployment_dict(
    full_dept_name: str,
    dept_identifier: str,
    stage: str,
    context: str = "Local Dev" # Default context for local yaml
) -> Dict[str, Any]:
    """Generates the dictionary structure for a single deployment entry."""
    # Use the user-preferred naming convention
    deployment_name = f"{stage.capitalize()} Deployment ({full_dept_name})"
    entrypoint_func_name = f"{stage}_flow_{dept_identifier}"
    entrypoint = f"flows/{dept_identifier}/{entrypoint_func_name}.py:{entrypoint_func_name}"
    description = f"{context} deployment for {full_dept_name} {stage} orchestrator"
    tags = ["example", stage, dept_identifier] # Base tags

    deployment_entry = {
        "name": deployment_name,
        "version": None,
        "tags": tags,
        "description": description,
        "entrypoint": entrypoint,
        "parameters": {},
        "schedule": None,
        "work_pool": {
            "name": "default",
            "work_queue_name": "default",
        },
        "infrastructure": {
            "type": "docker-container",
            "block_slug": "docker-container/local-worker-infra",
        },
        "storage": None,
        "pull": [
            {
                "prefect.deployments.steps.set_working_directory": {
                    "directory": "/app"
                }
            }
        ]
    }
    return deployment_entry

def add_deployments_to_yaml(
    yaml_path: Path,
    new_deployments: List[Dict[str, Any]]
):
    """Loads, updates, and saves the deployment YAML file idempotently."""
    yaml_path_rel = yaml_path.relative_to(PROJECT_ROOT)
    if not yaml_path.is_file():
        print(f"Warning: Deployment YAML file not found: '{yaml_path_rel}'. Cannot add deployments.")
        return # Don't proceed if file doesn't exist

    print(f"\nUpdating deployment file: '{yaml_path_rel}'...")
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            # Use yaml.safe_load - comment preservation is not guaranteed
            data = yaml.safe_load(f) or {}

        if 'deployments' not in data or data['deployments'] is None:
            data['deployments'] = []

        if not isinstance(data['deployments'], list):
            print(f"Error: 'deployments' key in '{yaml_path_rel}' is not a list. Cannot add deployments.")
            return

        existing_names = {d.get('name') for d in data['deployments'] if isinstance(d, dict) and d.get('name')}
        added_count = 0

        for new_dep in new_deployments:
            new_name = new_dep.get('name')
            if new_name in existing_names:
                print(f"   Exists: Deployment '{new_name}'. Skipping.")
            else:
                print(f"  Adding: Deployment '{new_name}'...")
                data['deployments'].append(new_dep)
                added_count += 1

        if added_count > 0:
            try:
                # Save with standard PyYAML - may lose comments/some formatting
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True, indent=2)
                print(f"   Successfully added {added_count} deployment(s) to '{yaml_path_rel}'.")
            except Exception as e:
                print(f"   ERROR saving deployment YAML file: {e}")
        else:
            print("   No new deployments to add.")

    except yaml.YAMLError as e:
        print(f"ERROR parsing deployment YAML file '{yaml_path_rel}': {e}")
    except Exception as e:
        print(f"ERROR processing deployment YAML file '{yaml_path_rel}': {e}")


# --- Main Script Logic ---

def main():
    print("-" * 60)
    print("--- Add New Department Script ---")
    print("-" * 60)

    dept_mapping = load_department_mapping()

    # 1. Get Department Info
    full_dept_name = prompt_user("Enter the full department name (e.g., Department of Social Protection)")
    if not full_dept_name: sys.exit("Error: Full department name cannot be empty.")

    suggested_id = "dept_" + sanitize_identifier(full_dept_name)
    dept_identifier = prompt_user("Enter a short identifier (snake_case, starting with 'dept_')", default=suggested_id)

    if not dept_identifier.startswith("dept_") or not re.match(r'^dept_[a-z0-9_]+$', dept_identifier):
        sys.exit(f"Error: Invalid identifier '{dept_identifier}'. Must start with 'dept_' and use snake_case.")

    print(f"\nUsing Full Name: '{full_dept_name}'")
    print(f"Using Identifier: '{dept_identifier}'")

    # Update Department Mapping
    needs_save = False
    if dept_identifier in dept_mapping:
        if dept_mapping[dept_identifier] != full_dept_name:
            print(f"Warning: Mapping for '{dept_identifier}' exists but with a different name: '{dept_mapping[dept_identifier]}'")
            update_confirm = prompt_user(f"Update mapping to '{full_dept_name}'? (yes/no)", default="yes")
            if update_confirm.lower() == 'yes':
                dept_mapping[dept_identifier] = full_dept_name
                needs_save = True
            else:
                print("Skipping mapping update.")
    else:
        print(f"Adding new mapping for '{dept_identifier}' -> '{full_dept_name}'")
        dept_mapping[dept_identifier] = full_dept_name
        needs_save = True

    if needs_save:
        save_department_mapping(dept_mapping)

    # 2. Define Paths
    dept_flow_dir = FLOWS_DIR / dept_identifier
    dept_config_dir = CONFIGS_DIR / dept_identifier

    # 3. Create Directories
    print("\nCreating directories...")
    create_directory(dept_flow_dir)
    create_directory(dept_config_dir)
    create_file(dept_flow_dir / "__init__.py", "")

    for stage in STAGES:
        stage_flow_dir = dept_flow_dir / stage
        stage_config_dir = dept_config_dir / stage
        create_directory(stage_flow_dir, add_gitkeep=True)
        create_directory(stage_config_dir, add_gitkeep=True)
        create_file(stage_flow_dir / "__init__.py", "")

    # 4. Create Placeholder Files and Collect Deployment Info
    print("\nCreating placeholder files...")
    deployments_to_add = []
    for stage in STAGES:
        # Parent Orchestrator Flow File
        flow_filename = f"{stage}_flow_{dept_identifier}.py"
        flow_filepath = dept_flow_dir / flow_filename
        flow_content = get_parent_flow_content(stage, full_dept_name, dept_identifier)
        create_file(flow_filepath, flow_content)

        # Parent Orchestrator Config File
        config_filename = f"{stage}_config_{dept_identifier}.yaml"
        config_filepath = dept_config_dir / config_filename
        config_content = get_parent_config_content(stage, full_dept_name, dept_identifier)
        create_file(config_filepath, config_content)

        # Generate deployment dict for this stage
        deployment_dict = generate_deployment_dict(full_dept_name, dept_identifier, stage, context="Local Dev")
        deployments_to_add.append(deployment_dict)

    # *** 5. Ask user and potentially add Deployments to prefect.local.yaml ***
    print("-" * 20)
    add_deps = prompt_yes_no(f"Add {len(deployments_to_add)} default local deployment definitions to '{PREFECT_LOCAL_YAML.name}'?", default_yes=True)
    if add_deps:
        add_deployments_to_yaml(PREFECT_LOCAL_YAML, deployments_to_add)
    else:
        print("Skipping addition of deployments to YAML file.")
    # *** End Deployment Add ***

    print("-" * 60)
    print("Scaffolding complete!")
    print("Next Steps:")
    print(f"1. Implement logic in placeholder flow files in '{dept_flow_dir.relative_to(PROJECT_ROOT)}'.")
    print(f"2. Add category flow files under stage directories using 'scripts/generators/add_category.py'.")
    print(f"3. Define configurations in YAML files under '{dept_config_dir.relative_to(PROJECT_ROOT)}'.")
    print(f"4. **IMPORTANT:** Update 'scripts/setup_prefect_variables.py' to handle the nested config structure.")
    # *** UPDATED STEP 5 & 6 ***
    if add_deps:
        print(f"5. Review the deployment definitions added to '{PREFECT_LOCAL_YAML.relative_to(PROJECT_ROOT)}'.")
        print(f"6. Run `prefect deploy --all -f {PREFECT_LOCAL_YAML.name}` to apply the new deployments to the server.")
    else:
        print(f"5. Manually add deployment definitions for the new stages (e.g., '{STAGES[0].capitalize()} Deployment ({full_dept_name})') to '{PREFECT_LOCAL_YAML.name}'.")
        print(f"6. Run `prefect deploy ...` to apply the deployments once added.")
    print(f"7. Verify the mapping in '{DEPT_MAPPING_FILE.relative_to(PROJECT_ROOT)}' is correct.")
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