# tests/generators/test_add_department.py
import yaml
import pytest
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
        flow_file_path = dept_flow_path / expected_flow_filename
        assert flow_file_path.is_file()

        # Verify parent flow file content
        with open(flow_file_path, 'r') as f:
            flow_content = f.read()
        assert f"async def {stage}_flow_{dept_identifier}(" in flow_content
        assert f"@flow(name=\"{stage.capitalize()} Flow ({dept_full_name})\"" in flow_content
        assert f"base_tags = ['{dept_identifier}', '{stage}']" in flow_content

        expected_config_filename = f"{stage}_config_{dept_identifier}.yaml"
        config_file_path = dept_config_path / expected_config_filename
        assert config_file_path.is_file()

        # Verify parent config YAML content
        with open(config_file_path, 'r') as f:
            config_content = f.read()
        assert f"# Corresponding Prefect Variable Name (proposed): {dept_identifier}_{stage}_config" in config_content

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

    # Test Idempotency for prefect.local.yaml
    # Store the number of deployments
    with open(prefect_local_yaml_path, 'r') as f:
        deployment_data_before_second_run = yaml.safe_load(f)
    num_deployments_before_second_run = len(deployment_data_before_second_run["deployments"])

    # Run the script again with the same inputs
    mock_input_session(script_inputs) # Reset mock inputs for the second run
    add_department.main()

    # Reload prefect.local.yaml and assert that the number of deployments has not increased
    with open(prefect_local_yaml_path, 'r') as f:
        deployment_data_after_second_run = yaml.safe_load(f)
    
    assert len(deployment_data_after_second_run["deployments"]) == num_deployments_before_second_run, \
        "Number of deployments increased after running the script a second time."

    # Assert that the content related to the specific department's deployments remains unchanged
    for stage in stages_in_script:
        expected_deployment_name = f"{stage.capitalize()} Deployment ({dept_full_name})"
        expected_entrypoint = f"flows/{dept_identifier}/{stage}_flow_{dept_identifier}.py:{stage}_flow_{dept_identifier}"
        
        # Count occurrences of the deployment in both lists
        count_before = sum(
            1 for d in deployment_data_before_second_run["deployments"]
            if isinstance(d, dict) and
            d.get("name") == expected_deployment_name and
            d.get("entrypoint") == expected_entrypoint
        )
        count_after = sum(
            1 for d in deployment_data_after_second_run["deployments"]
            if isinstance(d, dict) and
            d.get("name") == expected_deployment_name and
            d.get("entrypoint") == expected_entrypoint
        )
        assert count_before == count_after, \
            f"Deployment content for stage '{stage}' changed after running the script a second time."

# Parameterized test for varied department names
@pytest.mark.parametrize(
    "dept_full_name_input, expected_sanitized_id_part",
    [
        ("My Test Department", "my_test_department"),
        ("MyTestDepartment", "my_test_department"),
        ("My-Test & Dept/Ops", "my_test_dept_ops"),
        ("  Leading Trailing Spaces  ", "leading_trailing_spaces"),
        ("Department with !@#$%^&*()_+", "department_with"), # Sanitizer removes most special chars
        ("department_already_snake", "department_already_snake"),
        ("DEPT UPPERCASE", "dept_uppercase"),
    ]
)
def test_add_department_with_varied_names(
    temp_project_env, mock_input_session, mock_stdout_session,
    dept_full_name_input, expected_sanitized_id_part
):
    """
    Tests add_department.py with various department names to ensure
    correct sanitization and usage of the identifier.
    """
    dept_identifier_prefix = "dept_"
    expected_dept_identifier = dept_identifier_prefix + expected_sanitized_id_part
    
    # STAGES constant is defined within add_department.py
    stages_in_script = add_department.STAGES

    script_inputs = [
        dept_full_name_input,
        expected_dept_identifier, # Simulate user accepting the sanitized version or providing their own
        "yes",  # Update department_mapping.yaml
        "yes",  # Add deployments to prefect.local.yaml
    ]
    mock_input_session(script_inputs)

    prefect_local_yaml_path = temp_project_env / "prefect.local.yaml"
    initial_yaml_content = {"deployments": []}
    with open(prefect_local_yaml_path, 'w') as f:
        yaml.dump(initial_yaml_content, f)

    add_department.main()

    flows_dir = temp_project_env / "flows"
    configs_dir = temp_project_env / "configs" / "variables"

    dept_flow_path = flows_dir / expected_dept_identifier
    assert dept_flow_path.is_dir(), f"Department flow directory not found: {dept_flow_path}"
    assert (dept_flow_path / "__init__.py").is_file()

    dept_config_path = configs_dir / expected_dept_identifier
    assert dept_config_path.is_dir(), f"Department config directory not found: {dept_config_path}"

    for stage in stages_in_script:
        # Check stage directories
        assert (dept_flow_path / stage).is_dir()
        assert (dept_config_path / stage).is_dir()

        # Check parent flow file and its content
        expected_flow_filename = f"{stage}_flow_{expected_dept_identifier}.py"
        flow_file_path = dept_flow_path / expected_flow_filename
        assert flow_file_path.is_file()
        with open(flow_file_path, 'r') as f:
            flow_content = f.read()
        assert f"async def {stage}_flow_{expected_dept_identifier}(" in flow_content
        assert f"@flow(name=\"{stage.capitalize()} Flow ({dept_full_name_input.strip()})\"" in flow_content # Use stripped name for comparison
        assert f"base_tags = ['{expected_dept_identifier}', '{stage}']" in flow_content

        # Check parent config file and its content
        expected_config_filename = f"{stage}_config_{expected_dept_identifier}.yaml"
        config_file_path = dept_config_path / expected_config_filename
        assert config_file_path.is_file()
        with open(config_file_path, 'r') as f:
            config_content = f.read()
        assert f"# Corresponding Prefect Variable Name (proposed): {expected_dept_identifier}_{stage}_config" in config_content
    
    # Check department mapping
    dept_mapping_file = temp_project_env / "configs" / "department_mapping.yaml"
    assert dept_mapping_file.is_file()
    with open(dept_mapping_file, 'r') as f:
        mapping_data = yaml.safe_load(f)
    assert mapping_data[expected_dept_identifier] == dept_full_name_input.strip() # Script strips input for full name

    # Check prefect.local.yaml deployments
    with open(prefect_local_yaml_path, 'r') as f:
        deployment_data = yaml.safe_load(f)
    for stage in stages_in_script:
        # Use stripped full name for deployment name as per script's behavior
        expected_deployment_name = f"{stage.capitalize()} Deployment ({dept_full_name_input.strip()})"
        expected_entrypoint = f"flows/{expected_dept_identifier}/{stage}_flow_{expected_dept_identifier}.py:{stage}_flow_{expected_dept_identifier}"
        found_deployment = any(
            d.get("name") == expected_deployment_name and d.get("entrypoint") == expected_entrypoint
            for d in deployment_data["deployments"]
        )
        assert found_deployment, f"Deployment for stage '{stage}' with identifier '{expected_dept_identifier}' not found."