# tests/generators/conftest.py
import pytest
import tempfile
from pathlib import Path
import shutil
from unittest.mock import patch # unittest.mock can still be used with pytest
import sys
import os
import yaml # For creating dummy YAML files

# Determine the project root from conftest.py's location
# conftest.py in tests/generators/ -> parent is tests/ -> parent.parent is project_root
PROJECT_ROOT_ACTUAL = Path(__file__).resolve().parents[2]
# This will be the import path for the generator modules when tests are run
# assuming 'scripts' is on sys.path or discoverable.
# Ensure scripts/ and scripts/generators/ have __init__.py
SCRIPTS_MODULE_PATH_FOR_PATCHING = 'scripts.generators'

@pytest.fixture(scope="function") # Run once per test function
def temp_project_env(request): # request is a pytest internal fixture
    """
    Creates a temporary project directory structure and patches the
    PROJECT_ROOT global variable in each generator script to point to this
    temporary directory.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="test_proj_"))
    
    # Create minimal required directory structure within the temp dir
    (temp_dir / "configs" / "variables").mkdir(parents=True, exist_ok=True)
    (temp_dir / "flows").mkdir(parents=True, exist_ok=True)
    # No need to create scripts/generators in the temp_dir,
    # as we'll be importing and testing the actual scripts from their real location.

    patchers = []

    def start_patch(target_script_module_name):
        patch_target = f"{SCRIPTS_MODULE_PATH_FOR_PATCHING}.{target_script_module_name}.PROJECT_ROOT"
        try:
            p = patch(patch_target, temp_dir)
            p.start()
            patchers.append(p)
        except AttributeError:
            pytest.fail(f"Failed to patch PROJECT_ROOT for {patch_target}. "
                        f"Ensure {target_script_module_name}.py defines PROJECT_ROOT globally.")
        except ModuleNotFoundError:
            pytest.fail(f"Module not found for patching: {patch_target}. "
                        f"Ensure scripts are importable. Current sys.path: {sys.path}")

    start_patch('add_department')
    start_patch('add_category')
    start_patch('add_task')

    yield temp_dir  # This Path object is what the test functions will receive

    # Teardown: stop all patchers and remove the temporary directory
    for p in patchers:
        p.stop()
    shutil.rmtree(temp_dir)

@pytest.fixture(autouse=True)
def ensure_scripts_importable(monkeypatch):
    """
    Ensures that the 'scripts' directory (parent of 'scripts/generators')
    is in sys.path for the duration of the test session.
    """
    scripts_package_path = str(PROJECT_ROOT_ACTUAL) # Add project root for `from scripts...`
    # This assumes you run pytest from the project root.
    # If scripts/ is not directly a top-level package, adjust accordingly.
    # If your scripts/generators are directly importable because scripts/ is in PYTHONPATH
    # or because you run pytest from project root, this might be simplified.
    # The goal is `from scripts.generators import add_department` should work.
    monkeypatch.syspath_prepend(scripts_package_path)


@pytest.fixture
def mock_input_session(monkeypatch):
    """
    Fixture to mock builtins.input.
    Returns a function that can be used to set the input responses.
    """
    mock_responses_queue = []

    def mocked_input_function(prompt=""):
        # print(f"\nMock input prompt: {prompt}") # Optional: for debugging tests
        if not mock_responses_queue:
            raise EOFError("Mock input response queue is empty")
        response = mock_responses_queue.pop(0)
        # print(f"Mock input returning: {response}") # Optional: for debugging
        return response

    monkeypatch.setattr('builtins.input', mocked_input_function)

    # This function will be returned by the fixture for tests to use
    def set_script_inputs(responses):
        nonlocal mock_responses_queue
        mock_responses_queue.clear()
        mock_responses_queue.extend(responses)

    return set_script_inputs


@pytest.fixture
def mock_stdout_session(monkeypatch):
    """Fixture to suppress stdout (print statements) for the test session."""
    devnull = open(os.devnull, 'w')
    monkeypatch.setattr(sys, 'stdout', devnull)
    yield # Fixture is active
    devnull.close() # Cleanup
    monkeypatch.undo() # Restore original stdout