# tests/generators/test_add_category.py
import yaml
from pathlib import Path
from unittest.mock import patch # For mocking module-specific globals if needed

from scripts.generators import add_category # Script to test

def test_add_category_script_scaffolding(
    temp_project_env, mock_input_session, mock_stdout_session
):
    """
    Tests add_category.py for correct directory/file scaffolding for a new category.
    """
    # --- Setup initial department and stage structure manually for the test ---
    dept_identifier = "dept_test_beta"
    stage_name = "ingestion"
    full_dept_name = "Test Department Beta" # For prompts/naming

    # Create department flow and config dirs
    dept_flow_root_path = temp_project_env / "flows" / dept_identifier
    dept_flow_root_path.mkdir(parents=True, exist_ok=True)
    
    dept_config_root_path = temp_project_env / "configs" / "variables" / dept_identifier
    dept_config_root_path.mkdir(parents=True, exist_ok=True)

    # Create stage subdirectories within the department
    (dept_flow_root_path / stage_name).mkdir(parents=True, exist_ok=True)
    (dept_config_root_path / stage_name).mkdir(parents=True, exist_ok=True)
    
    # Create a dummy department mapping file
    dept_mapping_file = temp_project_env / "configs" / "department_mapping.yaml"
    with open(dept_mapping_file, 'w') as f:
        yaml.dump({dept_identifier: full_dept_name}, f)
    # --- End Setup ---

    cat_name_input = "Monthly Reports" # User input for category name
    # add_category.py will sanitize this to "monthly_reports"
    expected_cat_identifier = "monthly_reports" 
    action_verb_input = "Ingest" # User input for action verb

    script_inputs = [
        "1",  # Select the first (and only) department: dept_test_beta
        "1",  # Select the first (and only) stage: ingestion
        cat_name_input,
        action_verb_input,
    ]
    mock_input_session(script_inputs)

    # Run the script's main function
    add_category.main()

    # --- Assertions ---
    category_flow_dir = temp_project_env / "flows" / dept_identifier / stage_name / expected_cat_identifier
    category_config_dir = temp_project_env / "configs" / "variables" / dept_identifier / stage_name / expected_cat_identifier

    assert category_flow_dir.is_dir()
    assert (category_flow_dir / "__init__.py").is_file()
    
    assert category_config_dir.is_dir()
    # add_category.py creates the category config dir, but __init__.py inside it
    # is typically created when add_task.py adds a task config there.
    # So, we don't assert __init__.py for category_config_dir here unless add_category.py creates it.
    # Based on add_category.py: `create_directory(category_config_dir)` - doesn't add __init__.py

    expected_flow_filename = f"{action_verb_input.lower()}_{expected_cat_identifier}_flow_{dept_identifier}.py"
    assert (category_flow_dir / expected_flow_filename).is_file()

    expected_config_filename = f"{action_verb_input.lower()}_{expected_cat_identifier}_config_{dept_identifier}.yaml"
    assert (category_config_dir / expected_config_filename).is_file()