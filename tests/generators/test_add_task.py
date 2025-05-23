# tests/generators/test_add_task.py
import yaml
from pathlib import Path
from unittest.mock import patch # For mocking specific module globals

from scripts.generators import add_task # Script to test

def test_add_task_script_stage_level(
    temp_project_env, mock_input_session, mock_stdout_session
):
    """Tests add_task.py for creating stage-level tasks."""
    dept_identifier = "dept_test_gamma"
    stage_name = "processing"
    # full_dept_name is not directly used by add_task.py logic but helps with context

    # --- Setup initial department and stage structure ---
    (temp_project_env / "flows" / dept_identifier / stage_name).mkdir(parents=True, exist_ok=True)
    (temp_project_env / "configs" / "variables" / dept_identifier / stage_name).mkdir(parents=True, exist_ok=True)
    # --- End Setup ---

    task_desc_input = "Clean Raw Data"
    # add_task.py will sanitize "Clean Raw Data" to "clean_raw_data" for filename base
    expected_task_filename_base = "clean_raw_data" 
    task_func_name_input = f"{expected_task_filename_base}_task" # User confirms/enters this

    script_inputs = [
        task_desc_input,
        task_func_name_input,
        "1",  # Select dept_test_gamma
        "1",  # Select processing stage
        "no", # Not category specific
    ]
    mock_input_session(script_inputs)

    # Mock functions within add_task that list existing items to make choices deterministic
    with patch('scripts.generators.add_task.get_existing_departments', return_value=[dept_identifier]), \
         patch('scripts.generators.add_task.STAGES', [stage_name]): # Ensure only 'processing' is an option
        add_task.main()

    # --- Assertions ---
    task_py_dir = temp_project_env / "flows" / dept_identifier / stage_name / "tasks"
    task_config_dir = temp_project_env / "configs" / "variables" / dept_identifier / stage_name / "tasks"

    assert task_py_dir.is_dir()
    assert (task_py_dir / "__init__.py").is_file()
    
    assert task_config_dir.is_dir()
    assert (task_config_dir / "__init__.py").is_file() # add_task.py creates this

    expected_task_py_filename = f"{expected_task_filename_base}_task_{dept_identifier}.py"
    task_py_file_path = task_py_dir / expected_task_py_filename
    assert task_py_file_path.is_file()

    # Verify task Python file content (Stage Level)
    with open(task_py_file_path, 'r') as f:
        task_py_content = f.read()
    assert f"async def {task_func_name_input}(" in task_py_content
    assert f"@task(name=\"{task_desc_input.replace('_', ' ').title()}\"" in task_py_content
    expected_py_path_comment = f"# {task_py_file_path.relative_to(temp_project_env)}"
    assert expected_py_path_comment in task_py_content

    expected_task_config_filename = f"{expected_task_filename_base}_task_config_{dept_identifier}.yaml"
    task_config_file_path = task_config_dir / expected_task_config_filename
    assert task_config_file_path.is_file()

    # Verify task config YAML content (Stage Level)
    with open(task_config_file_path, 'r') as f:
        task_config_content = f.read()
    expected_config_var_comment = f"# Corresponding Prefect Variable Name (proposal - requires setup script update): {dept_identifier}_{stage_name}_{task_func_name_input}_config"
    assert expected_config_var_comment in task_config_content
    expected_config_path_comment = f"# File: {task_config_file_path.relative_to(temp_project_env)}"
    assert expected_config_path_comment in task_config_content

    # --- Test Idempotency ---
    # Record modification times
    task_py_mtime_before = task_py_file_path.stat().st_mtime
    task_config_mtime_before = task_config_file_path.stat().st_mtime

    # Run the script again with the same inputs
    mock_input_session(script_inputs) # Reset mock inputs for the second run
    
    # Capture stdout to check for "Skipping" messages
    with patch('sys.stdout', mock_stdout_session): # Use the fixture here
        with patch('scripts.generators.add_task.get_existing_departments', return_value=[dept_identifier]), \
             patch('scripts.generators.add_task.STAGES', [stage_name]):
            add_task.main()
    
    output = mock_stdout_session.getvalue() # Get captured output

    assert f"Exists: {task_py_file_path.relative_to(temp_project_env)} (Skipping)" in output
    assert f"Exists: {task_config_file_path.relative_to(temp_project_env)} (Skipping)" in output

    # Assert that modification times have not changed
    assert task_py_file_path.stat().st_mtime == task_py_mtime_before
    assert task_config_file_path.stat().st_mtime == task_config_mtime_before

@pytest.mark.parametrize(
    "task_desc_input, user_task_func_name_input, expected_task_filename_base_part, expected_func_name_used",
    [
        ("Process Complex Data!", "process_complex_data_task", "process_complex_data", "process_complex_data_task"),
        ("  Generate Report  ", "custom_report_generation_task", "generate_report", "custom_report_generation_task"),
        ("Handle_Edge-Cases", "handle_edge_cases_task", "handle_edge_cases", "handle_edge_cases_task"),
        # Case where user input for func name is different from sanitized desc
        ("Another Task", "specific_task_implementation_task", "another_task", "specific_task_implementation_task"),
        # Case where user input for func name is the same as sanitized desc + _task
        ("Simple Task", "simple_task_task", "simple_task", "simple_task_task"),
    ]
)
def test_add_task_with_varied_inputs(
    temp_project_env, mock_input_session, mock_stdout_session,
    task_desc_input, user_task_func_name_input, expected_task_filename_base_part, expected_func_name_used
):
    """Tests add_task.py with varied task descriptions and function names (stage-level)."""
    dept_identifier = "dept_varied_inputs"
    stage_name = "processing"

    # Setup structure
    (temp_project_env / "flows" / dept_identifier / stage_name).mkdir(parents=True, exist_ok=True)
    (temp_project_env / "configs" / "variables" / dept_identifier / stage_name).mkdir(parents=True, exist_ok=True)

    script_inputs = [
        task_desc_input,
        user_task_func_name_input, # User provides this exact function name
        "1",  # Select department
        "1",  # Select stage
        "no", # Not category specific
    ]
    mock_input_session(script_inputs)

    with patch('scripts.generators.add_task.get_existing_departments', return_value=[dept_identifier]), \
         patch('scripts.generators.add_task.STAGES', [stage_name]):
        add_task.main()

    # add_task.py uses sanitize_identifier(desc, suffix="") for filename base
    # and the user_task_func_name_input directly for the function name if valid.
    sanitized_filename_base = add_task.sanitize_identifier(task_desc_input, suffix="")
    assert sanitized_filename_base == expected_task_filename_base_part, \
        f"Mismatch in expected filename base for '{task_desc_input}'. Test expected: '{expected_task_filename_base_part}', Script produced: '{sanitized_filename_base}'"

    task_py_dir = temp_project_env / "flows" / dept_identifier / stage_name / "tasks"
    task_config_dir = temp_project_env / "configs" / "variables" / dept_identifier / stage_name / "tasks"

    assert task_py_dir.is_dir()
    assert task_config_dir.is_dir()

    expected_task_py_filename = f"{sanitized_filename_base}_task_{dept_identifier}.py"
    task_py_file_path = task_py_dir / expected_task_py_filename
    assert task_py_file_path.is_file(), f"Task Python file not found: {task_py_file_path}"

    expected_task_config_filename = f"{sanitized_filename_base}_task_config_{dept_identifier}.yaml"
    task_config_file_path = task_config_dir / expected_task_config_filename
    assert task_config_file_path.is_file(), f"Task config file not found: {task_config_file_path}"

    # Verify Python file content
    with open(task_py_file_path, 'r') as f:
        task_py_content = f.read()
    assert f"async def {expected_func_name_used}(" in task_py_content
    # @task name is based on the original task_desc_input, then Title Cased
    expected_decorator_name = add_task.sanitize_identifier(task_desc_input, suffix="").replace('_', ' ').title()
    assert f"@task(name=\"{expected_decorator_name}\"" in task_py_content # Corrected decorator name check
    expected_py_path_comment = f"# {task_py_file_path.relative_to(temp_project_env)}"
    assert expected_py_path_comment in task_py_content


    # Verify Config YAML content
    with open(task_config_file_path, 'r') as f:
        task_config_content = f.read()
    # Variable name uses the actual function name used in the .py file
    expected_config_var_comment = f"# Corresponding Prefect Variable Name (proposal - requires setup script update): {dept_identifier}_{stage_name}_{expected_func_name_used}_config"
    assert expected_config_var_comment in task_config_content
    expected_config_path_comment = f"# File: {task_config_file_path.relative_to(temp_project_env)}"
    assert expected_config_path_comment in task_config_content

def test_add_task_create_new_category(
    temp_project_env, mock_input_session, mock_stdout_session
):
    """Tests add_task.py for creating tasks with a new category."""
    dept_identifier = "dept_test_epsilon"
    stage_name = "ingestion"
    new_cat_name_input = "Dynamic Source Data"
    expected_new_cat_identifier = "dynamic_source_data" # Sanitized version

    # --- Setup initial department and stage structure ---
    (temp_project_env / "flows" / dept_identifier / stage_name).mkdir(parents=True, exist_ok=True)
    (temp_project_env / "configs" / "variables" / dept_identifier / stage_name).mkdir(parents=True, exist_ok=True)
    # --- End Setup ---

    task_desc_input = "Fetch Dynamic Data"
    expected_task_filename_base = "fetch_dynamic_data"
    task_func_name_input = f"{expected_task_filename_base}_task"

    script_inputs = [
        task_desc_input,
        task_func_name_input,
        "1",  # Select dept_test_epsilon
        "1",  # Select ingestion stage
        "yes",# Is category specific
        "1",  # Select "[Create New Category]" (assuming it's the first if no existing categories)
        new_cat_name_input, # Provide the new category name
    ]
    mock_input_session(script_inputs)

    # Mock functions within add_task
    # For this test, assume get_existing_categories returns empty list, so "[Create New Category]" is a primary option.
    with patch('scripts.generators.add_task.get_existing_departments', return_value=[dept_identifier]), \
         patch('scripts.generators.add_task.STAGES', [stage_name]), \
         patch('scripts.generators.add_task.get_existing_categories', return_value=[]): # No existing categories
        add_task.main()

    # --- Assertions ---
    # Assert new category directory is created
    new_category_flow_dir = temp_project_env / "flows" / dept_identifier / stage_name / expected_new_cat_identifier
    assert new_category_flow_dir.is_dir(), f"New category directory not created: {new_category_flow_dir}"
    
    new_category_config_dir = temp_project_env / "configs" / "variables" / dept_identifier / stage_name / expected_new_cat_identifier
    assert new_category_config_dir.is_dir(), f"New category config directory not created: {new_category_config_dir}"


    task_py_dir = new_category_flow_dir / "tasks"
    task_config_dir = new_category_config_dir / "tasks"

    assert task_py_dir.is_dir()
    assert (task_py_dir / "__init__.py").is_file()
    assert task_config_dir.is_dir()
    assert (task_config_dir / "__init__.py").is_file()

    expected_task_py_filename = f"{expected_task_filename_base}_task_{dept_identifier}.py"
    task_py_file_path = task_py_dir / expected_task_py_filename
    assert task_py_file_path.is_file()

    expected_task_config_filename = f"{expected_task_filename_base}_task_config_{dept_identifier}.yaml"
    task_config_file_path = task_config_dir / expected_task_config_filename
    assert task_config_file_path.is_file()

    # Verify task Python file content (New Category)
    with open(task_py_file_path, 'r') as f:
        task_py_content = f.read()
    assert f"async def {task_func_name_input}(" in task_py_content
    assert f"@task(name=\"{task_desc_input.replace('_', ' ').title()}\"" in task_py_content
    expected_py_path_comment = f"# {task_py_file_path.relative_to(temp_project_env)}"
    assert expected_py_path_comment in task_py_content

    # Verify task config YAML content (New Category)
    with open(task_config_file_path, 'r') as f:
        task_config_content = f.read()
    expected_config_var_comment = f"# Corresponding Prefect Variable Name (proposal - requires setup script update): {dept_identifier}_{stage_name}_{expected_new_cat_identifier}_{task_func_name_input}_config"
    assert expected_config_var_comment in task_config_content
    expected_config_path_comment = f"# File: {task_config_file_path.relative_to(temp_project_env)}"
    assert expected_config_path_comment in task_config_content


def test_add_task_script_category_level(
    temp_project_env, mock_input_session, mock_stdout_session
):
    """Tests add_task.py for creating category-level tasks."""
    dept_identifier = "dept_test_delta"
    stage_name = "analysis"
    cat_identifier = "user_behavior" # Sanitized version of a category name
    # full_dept_name is not directly used by add_task.py logic

    # --- Setup initial department, stage, and category structure ---
    cat_flow_path = temp_project_env / "flows" / dept_identifier / stage_name / cat_identifier
    cat_flow_path.mkdir(parents=True, exist_ok=True)
    (cat_flow_path.parent / "__init__.py").touch() # Ensure stage_name dir is package for relative imports if any
    (cat_flow_path.parent.parent / "__init__.py").touch() # Ensure dept_identifier dir is package

    cat_config_path = temp_project_env / "configs" / "variables" / dept_identifier / stage_name / cat_identifier
    cat_config_path.mkdir(parents=True, exist_ok=True)
    # --- End Setup ---

    task_desc_input = "Generate User Segments"
    expected_task_filename_base = "generate_user_segments"
    task_func_name_input = f"{expected_task_filename_base}_task"

    script_inputs = [
        task_desc_input,
        task_func_name_input,
        "1",  # Select dept_test_delta
        "1",  # Select analysis stage
        "yes",# Is category specific
        "1",  # Select user_behavior category
    ]
    mock_input_session(script_inputs)

    # Mock functions within add_task
    with patch('scripts.generators.add_task.get_existing_departments', return_value=[dept_identifier]), \
         patch('scripts.generators.add_task.STAGES', [stage_name]), \
         patch('scripts.generators.add_task.get_existing_categories', return_value=[cat_identifier]):
        add_task.main()

    # --- Assertions ---
    task_py_dir = temp_project_env / "flows" / dept_identifier / stage_name / cat_identifier / "tasks"
    task_config_dir = temp_project_env / "configs" / "variables" / dept_identifier / stage_name / cat_identifier / "tasks"

    assert task_py_dir.is_dir()
    assert (task_py_dir / "__init__.py").is_file()

    assert task_config_dir.is_dir()
    assert (task_config_dir / "__init__.py").is_file() # add_task.py creates this

    expected_task_py_filename = f"{expected_task_filename_base}_task_{dept_identifier}.py"
    task_py_file_path = task_py_dir / expected_task_py_filename
    assert task_py_file_path.is_file()

    # Verify task Python file content (Category Level)
    with open(task_py_file_path, 'r') as f:
        task_py_content = f.read()
    assert f"async def {task_func_name_input}(" in task_py_content
    assert f"@task(name=\"{task_desc_input.replace('_', ' ').title()}\"" in task_py_content
    expected_py_path_comment = f"# {task_py_file_path.relative_to(temp_project_env)}"
    assert expected_py_path_comment in task_py_content

    expected_task_config_filename = f"{expected_task_filename_base}_task_config_{dept_identifier}.yaml"
    task_config_file_path = task_config_dir / expected_task_config_filename
    assert task_config_file_path.is_file()

    # Verify task config YAML content (Category Level)
    with open(task_config_file_path, 'r') as f:
        task_config_content = f.read()
    expected_config_var_comment = f"# Corresponding Prefect Variable Name (proposal - requires setup script update): {dept_identifier}_{stage_name}_{cat_identifier}_{task_func_name_input}_config"
    assert expected_config_var_comment in task_config_content
    expected_config_path_comment = f"# File: {task_config_file_path.relative_to(temp_project_env)}"
    assert expected_config_path_comment in task_config_content