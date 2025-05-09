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
    assert (task_py_dir / expected_task_py_filename).is_file()

    expected_task_config_filename = f"{expected_task_filename_base}_task_config_{dept_identifier}.yaml"
    assert (task_config_dir / expected_task_config_filename).is_file()


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
    assert (task_py_dir / expected_task_py_filename).is_file()

    expected_task_config_filename = f"{expected_task_filename_base}_task_config_{dept_identifier}.yaml"
    assert (task_config_dir / expected_task_config_filename).is_file()