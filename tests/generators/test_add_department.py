# tests/generators/test_add_department.py
import yaml
from pathlib import Path
from unittest.mock import patch # For mocking specific module globals if needed beyond PROJECT_ROOT

# Import the actual script module we want to test
from scripts.generators import add_department

def test_add_department_script_scaffolding(
    temp_project_env, mock_input_session, mock_stdout_session # Fixtures from conftest.py
):
    """
    Tests add_department.py for correct directory/file scaffolding,
    department_mapping.yaml update, and prefect.local.yaml deployment additions.
    """
    # temp_project_env is the Path object for our temporary project directory.
    # PROJECT_ROOT within add_department module is already patched to temp_project_env.
    
    dept_full_name = "Project Alpha Demo"
    dept_identifier = "dept_alpha_demo"
    # STAGES constant is defined within add_department.py, so we use it from there.
    stages_in_script = add_department.STAGES 

    # Set up the mock inputs for the script
    script_inputs = [
        dept_full_name,
        dept_identifier,
        "yes",  # Update department_mapping.yaml
        "yes",  # Add deployments to prefect.local.yaml
    ]
    mock_input_session(script_inputs) # Use the fixture to set responses

    # Create a dummy prefect.local.yaml in the temp directory
    prefect_local_yaml_path = temp_project_env / "prefect.local.yaml"
    initial_yaml_content = {"deployments": []} 
    with open(prefect_local_yaml_path, 'w') as f:
        yaml.dump(initial_yaml_content, f)

    # Run the main function of the script
    add_department.main()

    # --- Assertions ---
    flows_dir = temp_project_env / "flows"
    configs_dir = temp_project_env / "configs" / "variables"

    # 1. Department directory and __init__.py
    dept_flow_path = flows_dir / dept_identifier
    assert dept_flow_path.is_dir()
    assert (dept_flow_path / "__init__.py").is_file()

    dept_config_path = configs_dir / dept_identifier
    assert dept_config_path.is_dir()
    # The script add_department.py creates __init__.py in dept_flow_path,
    # and stage subdirectories in both flows and configs.
    # It does not create an __init__.py directly in dept_config_path.

    # 2. Stage directories and files
    for stage in stages_in_script:
        stage_flow_dir = dept_flow_path / stage
        assert stage_flow_dir.is_dir()
        assert (stage_flow_dir / "__init__.py").is_file()
        assert (stage_flow_dir / ".gitkeep").is_file(), f".gitkeep missing in {stage_flow_dir}"

        stage_config_dir = dept_config_path / stage
        assert stage_config_dir.is_dir()
        assert (stage_config_dir / ".gitkeep").is_file(), f".gitkeep missing in {stage_config_dir}"

        # Parent orchestrator flow and config files are directly under dept_flow_path and dept_config_path
        expected_flow_filename = f"{stage}_flow_{dept_identifier}.py"
        assert (dept_flow_path / expected_flow_filename).is_file()

        expected_config_filename = f"{stage}_config_{dept_identifier}.yaml"
        assert (dept_config_path / expected_config_filename).is_file()

    # 3. Department mapping file
    dept_mapping_file = temp_project_env / "configs" / "department_mapping.yaml"
    assert dept_mapping_file.is_file()
    with open(dept_mapping_file, 'r') as f:
        mapping_data = yaml.safe_load(f)
    assert dept_identifier in mapping_data
    assert mapping_data[dept_identifier] == dept_full_name

    # 4. prefect.local.yaml deployments
    assert prefect_local_yaml_path.is_file()
    with open(prefect_local_yaml_path, 'r') as f:
        deployment_data = yaml.safe_load(f)
    
    assert "deployments" in deployment_data
    # Check if at least as many deployments as stages were added
    assert len(deployment_data["deployments"]) >= len(stages_in_script) 

    for stage in stages_in_script:
        expected_deployment_name = f"{stage.capitalize()} Deployment ({dept_full_name}) - Local Dev"
        expected_entrypoint = f"flows/{dept_identifier}/{stage}_flow_{dept_identifier}.py:{stage}_flow_{dept_identifier}"
        
        found_deployment = any(
            isinstance(d, dict) and
            d.get("name") == expected_deployment_name and
            d.get("entrypoint") == expected_entrypoint
            for d in deployment_data["deployments"]
        )
        assert found_deployment, (
            f"Deployment for stage '{stage}' not found or incorrect. "
            f"Expected name: '{expected_deployment_name}', entrypoint: '{expected_entrypoint}'"
        )