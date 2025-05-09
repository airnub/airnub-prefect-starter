import unittest
from unittest.mock import patch, mock_open
import tempfile
import shutil
import sys
from pathlib import Path
import os
import yaml # For checking YAML file content

# Ensure the scripts directory is in the Python path for imports
# Assuming the tests are run from the project root or a 'tests' subdirectory
PROJECT_ROOT_FOR_TESTS = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT_FOR_TESTS / "scripts" / "generators"
sys.path.insert(0, str(SCRIPTS_DIR.parent)) # Add 'scripts' to path
sys.path.insert(0, str(SCRIPTS_DIR))      # Add 'scripts/generators' to path


class TestGeneratorScripts(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory to simulate the project root
        self.temp_project_dir = Path(tempfile.mkdtemp())
        self.maxDiff = None # Show full diff on assertion failure

        # Create simulated 'configs' and 'flows' dirs within the temp project dir
        (self.temp_project_dir / "configs" / "variables").mkdir(parents=True, exist_ok=True)
        (self.temp_project_dir / "flows").mkdir(parents=True, exist_ok=True)
        (self.temp_project_dir / "scripts" / "generators").mkdir(parents=True, exist_ok=True)


        # --- Mock PROJECT_ROOT for each generator script ---
        # This is crucial: the scripts determine PROJECT_ROOT based on their __file__
        # We need to tell them to use our temporary directory as their project root.

        # For add_department
        self.patch_add_dept_project_root = patch(
            'generators.add_department.PROJECT_ROOT', self.temp_project_dir
        )
        self.mock_add_dept_project_root = self.patch_add_dept_project_root.start()

        # For add_category
        self.patch_add_cat_project_root = patch(
            'generators.add_category.PROJECT_ROOT', self.temp_project_dir
        )
        self.mock_add_cat_project_root = self.patch_add_cat_project_root.start()

        # For add_task
        self.patch_add_task_project_root = patch(
            'generators.add_task.PROJECT_ROOT', self.temp_project_dir
        )
        self.mock_add_task_project_root = self.patch_add_task_project_root.start()

        # Import the scripts *after* PROJECT_ROOT is patched for them
        # This is a bit tricky with how modules are loaded.
        # Re-importing or using importlib.reload might be necessary if scripts
        # compute PROJECT_ROOT at import time globally.
        # For simplicity here, we assume the patch works before main() is called.
        # If scripts define PROJECT_ROOT globally at module level, this patching
        # needs to happen before the module is first imported.
        # A safer way is to modify sys.modules or use importlib.reload if issues arise.

        # We'll import them dynamically within each test method after patching if necessary,
        # or rely on the setUp patching if the scripts' PROJECT_ROOT is accessible for patching.


    def tearDown(self):
        # Stop the patches
        self.patch_add_dept_project_root.stop()
        self.patch_add_cat_project_root.stop()
        self.patch_add_task_project_root.stop()

        # Remove the temporary directory and its contents
        shutil.rmtree(self.temp_project_dir)
        # Clean up sys.path modifications if necessary, though for tests it's usually fine
        if str(SCRIPTS_DIR) in sys.path:
            sys.path.remove(str(SCRIPTS_DIR))
        if str(SCRIPTS_DIR.parent) in sys.path:
            sys.path.remove(str(SCRIPTS_DIR.parent))


    def test_add_department_script(self):
        # Import here to ensure patched PROJECT_ROOT is used by the module
        from generators import add_department

        dept_full_name = "Test Department Alpha"
        dept_identifier = "dept_test_alpha"
        stages = ["ingestion", "processing", "analysis"]

        # Mock user inputs for add_department.py
        # Order: Full Dept Name, Dept ID, Update Mapping (yes), Add Deployments (yes)
        mock_inputs = [
            dept_full_name,
            dept_identifier,
            "yes", # Update mapping
            "yes"  # Add deployments
        ]

        # Create a dummy prefect.local.yaml to be modified
        prefect_local_yaml_path = self.temp_project_dir / "prefect.local.yaml"
        initial_yaml_content = {"deployments": []}
        with open(prefect_local_yaml_path, 'w') as f:
            yaml.dump(initial_yaml_content, f)

        with patch('builtins.input', side_effect=mock_inputs):
            with patch('sys.stdout'): # Suppress print statements
                add_department.main()

        # --- Assertions for add_department.py ---
        temp_flows_dir = self.temp_project_dir / "flows"
        temp_configs_dir = self.temp_project_dir / "configs" / "variables"

        # 1. Department directory and __init__.py
        dept_flow_path = temp_flows_dir / dept_identifier
        self.assertTrue(dept_flow_path.is_dir())
        self.assertTrue((dept_flow_path / "__init__.py").is_file())

        dept_config_path = temp_configs_dir / dept_identifier
        self.assertTrue(dept_config_path.is_dir())

        # 2. Stage directories and files
        for stage in stages:
            stage_flow_dir = dept_flow_path / stage
            self.assertTrue(stage_flow_dir.is_dir())
            self.assertTrue((stage_flow_dir / "__init__.py").is_file())
            self.assertTrue((stage_flow_dir / ".gitkeep").is_file()) # Assuming .gitkeep is added

            stage_config_dir = dept_config_path / stage
            self.assertTrue(stage_config_dir.is_dir())
            self.assertTrue((stage_config_dir / ".gitkeep").is_file())

            # Parent orchestrator flow and config
            expected_flow_filename = f"{stage}_flow_{dept_identifier}.py"
            self.assertTrue((dept_flow_path / expected_flow_filename).is_file())

            expected_config_filename = f"{stage}_config_{dept_identifier}.yaml"
            self.assertTrue((dept_config_path / expected_config_filename).is_file())

        # 3. Department mapping file
        dept_mapping_file = self.temp_project_dir / "configs" / "department_mapping.yaml"
        self.assertTrue(dept_mapping_file.is_file())
        with open(dept_mapping_file, 'r') as f:
            mapping_data = yaml.safe_load(f)
        self.assertIn(dept_identifier, mapping_data)
        self.assertEqual(mapping_data[dept_identifier], dept_full_name)

        # 4. prefect.local.yaml deployments
        with open(prefect_local_yaml_path, 'r') as f:
            deployment_data = yaml.safe_load(f)
        self.assertIn("deployments", deployment_data)
        self.assertTrue(len(deployment_data["deployments"]) >= len(stages)) # Should have at least one per stage

        for stage in stages:
            expected_deployment_name = f"{stage.capitalize()} Deployment ({dept_full_name}) - Local Dev"
            found_deployment = any(
                d.get("name") == expected_deployment_name and
                d.get("entrypoint") == f"flows/{dept_identifier}/{stage}_flow_{dept_identifier}.py:{stage}_flow_{dept_identifier}"
                for d in deployment_data["deployments"] if isinstance(d, dict)
            )
            self.assertTrue(found_deployment, f"Deployment for {stage} stage not found or incorrect.")


    def test_add_category_script(self):
        from generators import add_category

        # First, set up a department and stage using a simplified version of add_department's work
        dept_identifier = "dept_test_beta"
        stage_name = "ingestion"
        full_dept_name = "Test Department Beta"

        dept_flow_path = self.temp_project_dir / "flows" / dept_identifier
        (dept_flow_path / stage_name).mkdir(parents=True, exist_ok=True)
        (self.temp_project_dir / "configs" / "variables" / dept_identifier / stage_name).mkdir(parents=True, exist_ok=True)

        # Create dummy department mapping file
        dept_mapping_file = self.temp_project_dir / "configs" / "department_mapping.yaml"
        with open(dept_mapping_file, 'w') as f:
            yaml.dump({dept_identifier: full_dept_name}, f)

        cat_name = "Monthly Reports"
        cat_identifier = "monthly_reports"
        action_verb = "Ingest"

        # Mock user inputs for add_category.py
        # Order: Select Dept, Select Stage, Category Name, Action Verb
        # Assuming dept_test_beta is the first and only option, stage 'ingestion' is the same.
        mock_inputs = [
            "1", # Select dept_test_beta
            "1", # Select ingestion stage
            cat_name,
            action_verb
        ]

        with patch('builtins.input', side_effect=mock_inputs):
            with patch('sys.stdout'): # Suppress print
                add_category.main()

        # --- Assertions for add_category.py ---
        category_flow_dir = self.temp_project_dir / "flows" / dept_identifier / stage_name / cat_identifier
        category_config_dir = self.temp_project_dir / "configs" / "variables" / dept_identifier / stage_name / cat_identifier

        self.assertTrue(category_flow_dir.is_dir())
        self.assertTrue((category_flow_dir / "__init__.py").is_file())
        self.assertTrue(category_config_dir.is_dir())

        expected_flow_filename = f"{action_verb.lower()}_{cat_identifier}_flow_{dept_identifier}.py"
        self.assertTrue((category_flow_dir / expected_flow_filename).is_file())

        expected_config_filename = f"{action_verb.lower()}_{cat_identifier}_config_{dept_identifier}.yaml"
        self.assertTrue((category_config_dir / expected_config_filename).is_file())


    def test_add_task_script_stage_level(self):
        from generators import add_task

        dept_identifier = "dept_test_gamma"
        stage_name = "processing"
        full_dept_name = "Test Department Gamma" # Not directly used by add_task, but setup for context

        # Setup department and stage
        dept_flow_path = self.temp_project_dir / "flows" / dept_identifier
        (dept_flow_path / stage_name).mkdir(parents=True, exist_ok=True)
        (self.temp_project_dir / "configs" / "variables" / dept_identifier / stage_name).mkdir(parents=True, exist_ok=True)


        task_desc = "Clean Raw Data"
        task_func_name_sanitized_base = "clean_raw_data" # sanitized from desc
        task_func_name = f"{task_func_name_sanitized_base}_task" # as prompted

        # Mock user inputs for add_task.py
        # Order: Task Desc, Task Func Name, Select Dept, Select Stage, Is Category Specific? (no)
        mock_inputs = [
            task_desc,
            task_func_name, # User confirms/enters this
            "1", # Select dept_test_gamma
            "1", # Select processing stage (assuming it's the first option among stages)
            "no" # Not category specific
        ]

        # To make selection predictable, mock get_existing_departments and STAGES for add_task
        with patch('generators.add_task.get_existing_departments', return_value=[dept_identifier]):
            with patch('generators.add_task.STAGES', [stage_name]): # Ensure 'processing' is the only choice
                with patch('builtins.input', side_effect=mock_inputs):
                    with patch('sys.stdout'): # Suppress print
                        add_task.main()

        # --- Assertions for add_task.py (Stage Level) ---
        task_py_dir = self.temp_project_dir / "flows" / dept_identifier / stage_name / "tasks"
        task_config_dir = self.temp_project_dir / "configs" / "variables" / dept_identifier / stage_name / "tasks"

        self.assertTrue(task_py_dir.is_dir())
        self.assertTrue((task_py_dir / "__init__.py").is_file())
        self.assertTrue(task_config_dir.is_dir())
        # The script should also create an __init__.py in the tasks config dir
        self.assertTrue((task_config_dir / "__init__.py").is_file())


        expected_task_py_filename = f"{task_func_name_sanitized_base}_task_{dept_identifier}.py"
        self.assertTrue((task_py_dir / expected_task_py_filename).is_file())

        expected_task_config_filename = f"{task_func_name_sanitized_base}_task_config_{dept_identifier}.yaml"
        self.assertTrue((task_config_dir / expected_task_config_filename).is_file())


    def test_add_task_script_category_level(self):
        from generators import add_task

        dept_identifier = "dept_test_delta"
        stage_name = "analysis"
        cat_identifier = "user_behavior"
        full_dept_name = "Test Department Delta"

        # Setup department, stage, and category
        cat_flow_path = self.temp_project_dir / "flows" / dept_identifier / stage_name / cat_identifier
        cat_flow_path.mkdir(parents=True, exist_ok=True)
        (self.temp_project_dir / "configs" / "variables" / dept_identifier / stage_name / cat_identifier).mkdir(parents=True, exist_ok=True)

        task_desc = "Generate User Segments"
        task_func_name_sanitized_base = "generate_user_segments"
        task_func_name = f"{task_func_name_sanitized_base}_task"


        # Mock user inputs
        # Order: Task Desc, Task Func Name, Select Dept, Select Stage, Is Cat Specific? (yes), Select Category
        mock_inputs = [
            task_desc,
            task_func_name,
            "1", # Select dept_test_delta
            "1", # Select analysis stage
            "yes", # Is category specific
            "1"  # Select user_behavior category
        ]

        with patch('generators.add_task.get_existing_departments', return_value=[dept_identifier]):
            with patch('generators.add_task.STAGES', [stage_name]):
                with patch('generators.add_task.get_existing_categories', return_value=[cat_identifier]):
                    with patch('builtins.input', side_effect=mock_inputs):
                        with patch('sys.stdout'): # Suppress print
                            add_task.main()

        # --- Assertions for add_task.py (Category Level) ---
        task_py_dir = self.temp_project_dir / "flows" / dept_identifier / stage_name / cat_identifier / "tasks"
        task_config_dir = self.temp_project_dir / "configs" / "variables" / dept_identifier / stage_name / cat_identifier / "tasks"

        self.assertTrue(task_py_dir.is_dir())
        self.assertTrue((task_py_dir / "__init__.py").is_file())
        self.assertTrue(task_config_dir.is_dir())
        self.assertTrue((task_config_dir / "__init__.py").is_file())

        expected_task_py_filename = f"{task_func_name_sanitized_base}_task_{dept_identifier}.py"
        self.assertTrue((task_py_dir / expected_task_py_filename).is_file())

        expected_task_config_filename = f"{task_func_name_sanitized_base}_task_config_{dept_identifier}.yaml"
        self.assertTrue((task_config_dir / expected_task_config_filename).is_file())

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)