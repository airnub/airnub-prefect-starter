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
    flow_file_path = category_flow_dir / expected_flow_filename
    assert flow_file_path.is_file()

    # Verify category flow file content
    with open(flow_file_path, 'r') as f:
        flow_content = f.read()
    assert f"async def {action_verb_input.lower()}_{expected_cat_identifier}_flow_{dept_identifier}(" in flow_content
    assert f"@flow(name=\"{action_verb_input.capitalize()} {cat_name_input} ({full_dept_name})\"" in flow_content
    assert f"base_tags = ['{dept_identifier}', '{stage_name}', '{expected_cat_identifier}']" in flow_content
    expected_flow_path_comment = f"# flows/{dept_identifier}/{stage_name}/{expected_cat_identifier}/{expected_flow_filename}"
    assert expected_flow_path_comment in flow_content

    expected_config_filename = f"{action_verb_input.lower()}_{expected_cat_identifier}_config_{dept_identifier}.yaml"
    config_file_path = category_config_dir / expected_config_filename
    assert config_file_path.is_file()

    # Verify category config YAML content
    with open(config_file_path, 'r') as f:
        config_content = f.read()
    expected_config_var_comment = f"# Corresponding Prefect Variable Name (proposal - requires setup script update): {dept_identifier}_{stage_name}_{expected_cat_identifier}_config"
    assert expected_config_var_comment in config_content
    expected_config_path_comment = f"# File: configs/variables/{dept_identifier}/{stage_name}/{expected_cat_identifier}/{expected_config_filename}"
    assert expected_config_path_comment in config_content

def test_add_category_idempotency_and_overwrite(
    temp_project_env, mock_input_session, mock_stdout_session
):
    """
    Tests add_category.py for idempotency and overwrite behavior.
    """
    # --- Setup ---
    dept_identifier = "dept_idempotency_test"
    stage_name = "processing"
    full_dept_name = "Idempotency Test Department"
    cat_name_input = "Test Category for Idempotency"
    expected_cat_identifier = "test_category_for_idempotency"
    action_verb_input = "Process"

    # Create department and stage structure
    dept_flow_root_path = temp_project_env / "flows" / dept_identifier
    (dept_flow_root_path / stage_name).mkdir(parents=True, exist_ok=True)
    dept_config_root_path = temp_project_env / "configs" / "variables" / dept_identifier
    (dept_config_root_path / stage_name).mkdir(parents=True, exist_ok=True)
    
    dept_mapping_file = temp_project_env / "configs" / "department_mapping.yaml"
    with open(dept_mapping_file, 'w') as f:
        yaml.dump({dept_identifier: full_dept_name}, f)

    category_flow_dir = dept_flow_root_path / stage_name / expected_cat_identifier
    category_config_dir = dept_config_root_path / stage_name / expected_cat_identifier
    
    expected_flow_filename = f"{action_verb_input.lower()}_{expected_cat_identifier}_flow_{dept_identifier}.py"
    flow_file_path = category_flow_dir / expected_flow_filename
    expected_config_filename = f"{action_verb_input.lower()}_{expected_cat_identifier}_config_{dept_identifier}.yaml"
    config_file_path = category_config_dir / expected_config_filename

    # --- First Run ---
    script_inputs_first_run = [
        "1", # Select department
        "1", # Select stage
        cat_name_input,
        action_verb_input,
    ]
    mock_input_session(script_inputs_first_run)
    add_category.main()

    # Initial assertions
    assert flow_file_path.is_file()
    assert config_file_path.is_file()
    flow_mtime_after_first_run = flow_file_path.stat().st_mtime
    config_mtime_after_first_run = config_file_path.stat().st_mtime

    # --- Second Run (Overwrite "no") ---
    # The script will print a warning and prompt for overwrite.
    # We provide "no" (or let it default to "no" if that's the script's behavior).
    script_inputs_second_run = [
        "1", # Select department
        "1", # Select stage
        cat_name_input,
        action_verb_input,
        "no", # Do you want to proceed and potentially add files inside it?
    ]
    mock_input_session(script_inputs_second_run)
    
    # Capture stdout to check for "Operation cancelled"
    with patch('sys.stdout', mock_stdout_session): # Use the fixture here
      add_category.main()
    
    output = mock_stdout_session.getvalue() # Get captured output

    # Assert files are not modified and script indicates cancellation or skipping
    assert "Operation cancelled." in output or "Skipping" in output # Check for either message
    assert flow_file_path.stat().st_mtime == flow_mtime_after_first_run
    assert config_file_path.stat().st_mtime == config_mtime_after_first_run

    # --- Third Run (Overwrite "yes") ---
    # This time, provide "yes" to the overwrite prompt.
    # The current create_file function in add_category.py skips if file exists.
    # So, files should still not be modified.
    script_inputs_third_run = [
        "1", # Select department
        "1", # Select stage
        cat_name_input,
        action_verb_input,
        "yes", # Do you want to proceed and potentially add files inside it?
    ]
    mock_input_session(script_inputs_third_run)
    add_category.main() # Run with "yes" to overwrite

    # Assert files are still not modified (due to create_file's skip logic)
    assert flow_file_path.stat().st_mtime == flow_mtime_after_first_run
    assert config_file_path.stat().st_mtime == config_mtime_after_first_run
    # If create_file were to actually overwrite, we would check for new m_times here.

@pytest.mark.parametrize(
    "cat_name_input, expected_cat_identifier_part, action_verb_input, expected_action_verb_lower",
    [
        ("Simple Category", "simple_category", "Process", "process"),
        ("Category with Spaces", "category_with_spaces", "Analyze", "analyze"),
        ("Category-With-Hyphens", "category_with_hyphens", "Scrape", "scrape"),
        ("Category & Special*Chars!", "category_special_chars", "Generate", "generate"),
        ("  Leading Trailing Spaces  ", "leading_trailing_spaces", "  TrimAction  ", "trimaction"),
        ("ALL_CAPS_CATEGORY", "all_caps_category", "ALL_CAPS_ACTION", "all_caps_action"),
        ("MixedCaseCategory", "mixedcasecategory", "MixedCaseAction", "mixedcaseaction"), # Adjusted expected_cat_identifier
    ]
)
def test_add_category_with_varied_inputs(
    temp_project_env, mock_input_session, mock_stdout_session,
    cat_name_input, expected_cat_identifier_part, action_verb_input, expected_action_verb_lower
):
    """
    Tests add_category.py with varied category names and action verbs.
    """
    # --- Setup ---
    dept_identifier = "dept_varied_input_test"
    stage_name = "analysis" # Choose a stage
    full_dept_name = "Varied Input Test Department"
    
    # Create department and stage structure
    dept_flow_root_path = temp_project_env / "flows" / dept_identifier
    (dept_flow_root_path / stage_name).mkdir(parents=True, exist_ok=True)
    dept_config_root_path = temp_project_env / "configs" / "variables" / dept_identifier
    (dept_config_root_path / stage_name).mkdir(parents=True, exist_ok=True)
    
    dept_mapping_file = temp_project_env / "configs" / "department_mapping.yaml"
    with open(dept_mapping_file, 'w') as f:
        yaml.dump({dept_identifier: full_dept_name}, f)

    # Script inputs
    script_inputs = [
        "1",  # Select department
        "1",  # Select stage
        cat_name_input,
        action_verb_input, # Action verb can have spaces/mixed case, sanitize_identifier is not directly applied to it for filename
    ]
    mock_input_session(script_inputs)

    # Run the script
    add_category.main()

    # Expected identifiers after script's internal sanitization
    # For category name, add_category.py uses sanitize_identifier
    # For action verb, it's just .lower() for filename, .capitalize() for flow name
    sanitized_cat_identifier = add_category.sanitize_identifier(cat_name_input)
    # Ensure the test's expected_cat_identifier_part matches the script's sanitization logic for the test case
    assert sanitized_cat_identifier == expected_cat_identifier_part, \
        f"Mismatch in expected cat identifier for '{cat_name_input}'. Test expected: '{expected_cat_identifier_part}', Script produced: '{sanitized_cat_identifier}'"

    action_verb_for_filename = action_verb_input.strip().lower() # Script logic for filename
    action_verb_for_flow_name = action_verb_input.strip().capitalize() # Script logic for flow name
    assert action_verb_for_filename == expected_action_verb_lower, \
        f"Mismatch in expected action verb for filename for '{action_verb_input}'. Test expected: '{expected_action_verb_lower}', Script produced: '{action_verb_for_filename}'"


    category_flow_dir = temp_project_env / "flows" / dept_identifier / stage_name / sanitized_cat_identifier
    category_config_dir = temp_project_env / "configs" / "variables" / dept_identifier / stage_name / sanitized_cat_identifier

    assert category_flow_dir.is_dir()
    assert (category_flow_dir / "__init__.py").is_file()
    assert category_config_dir.is_dir()

    # Filenames use the lowercased action verb
    expected_flow_filename = f"{action_verb_for_filename}_{sanitized_cat_identifier}_flow_{dept_identifier}.py"
    flow_file_path = category_flow_dir / expected_flow_filename
    assert flow_file_path.is_file(), f"Flow file not found: {flow_file_path}"

    expected_config_filename = f"{action_verb_for_filename}_{sanitized_cat_identifier}_config_{dept_identifier}.yaml"
    config_file_path = category_config_dir / expected_config_filename
    assert config_file_path.is_file(), f"Config file not found: {config_file_path}"

    # Verify flow file content
    with open(flow_file_path, 'r') as f:
        flow_content = f.read()
    # Function name uses lowercased action verb
    assert f"async def {action_verb_for_filename}_{sanitized_cat_identifier}_flow_{dept_identifier}(" in flow_content
    # Flow name uses capitalized action verb and original (but stripped) category name
    assert f"@flow(name=\"{action_verb_for_flow_name} {cat_name_input.strip()} ({full_dept_name})\"" in flow_content
    assert f"base_tags = ['{dept_identifier}', '{stage_name}', '{sanitized_cat_identifier}']" in flow_content
    expected_flow_path_comment = f"# flows/{dept_identifier}/{stage_name}/{sanitized_cat_identifier}/{expected_flow_filename}"
    assert expected_flow_path_comment in flow_content

    # Verify config YAML content
    with open(config_file_path, 'r') as f:
        config_content = f.read()
    expected_config_var_comment = f"# Corresponding Prefect Variable Name (proposal - requires setup script update): {dept_identifier}_{stage_name}_{sanitized_cat_identifier}_config"
    assert expected_config_var_comment in config_content
    expected_config_path_comment = f"# File: configs/variables/{dept_identifier}/{stage_name}/{sanitized_cat_identifier}/{expected_config_filename}"
    assert expected_config_path_comment in config_content