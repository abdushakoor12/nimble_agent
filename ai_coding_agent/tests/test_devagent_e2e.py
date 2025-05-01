"""End-to-end tests for AI Coding Agent."""

import asyncio
import os
from pathlib import Path

import pytest

from ai_coding_agent.core.agents.dev_agent import DevAgent
from ai_coding_agent.core.constants import DEFAULT_GPT_MODEL, DEFAULT_TEMPERATURE
from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import Err, Ok, is_ok, unwrap
from ai_coding_agent.core.tools import command_functions
from ai_coding_agent.tests.conftest import TestInfo, go_and_generate_report

logger = get_logger(__name__)


def get_workspace_file(workspace_path: str | Path, filepath: str) -> Path:
    """Helper to get full path to a file in the workspace."""
    return Path(workspace_path) / filepath


def file_exists(workspace_path: str | Path, filepath: str) -> bool:
    """Helper to check if file exists in workspace."""
    return get_workspace_file(workspace_path, filepath).exists()


def read_file_content(workspace_path: str | Path, filepath: str) -> str | None:
    """Helper to read file content from workspace."""
    file_path = get_workspace_file(workspace_path, filepath)
    return file_path.read_text() if file_path.exists() else None


@pytest.mark.asyncio
async def test_simple_task(dev_agent: TestInfo):
    """Test executing a simple task that creates a text file."""
    workspace_path = dev_agent.dev_agent.workspace_path
    # Use the dev_agent fixture
    agent = DevAgent(
        workspace_path=Path(workspace_path),
        model=DEFAULT_GPT_MODEL,
        temperature=DEFAULT_TEMPERATURE,
        max_iterations=10,
    )

    # Define a simple task
    task = """Please help me create a text file named 'hello.txt' in the workspace root directory. The file should contain exactly these three lines:
Hello, World!
This is a test file.
Created by AI Coding Agent.

Use the write_file tool with two parameters:
- filepath: "hello.txt"
- content: the three lines exactly as shown above"""

    acceptance_criteria = """
1. File 'hello.txt' exists in workspace root
2. File content matches exactly these three lines:
Hello, World!
This is a test file.
Created by AI Coding Agent."""

    # Execute the task
    result = await go_and_generate_report(
        dev_agent=agent,
        command=task,
        acceptance_criteria=acceptance_criteria,
        test_name="test_simple_task",
    )

    # Verify the task completed successfully
    assert isinstance(result, Ok)
    task_result = unwrap(result)
    assert not task_result.output_message.startswith(
        "Task failed",
    ), f"Agent failed to complete task: {task_result.output_message}"

    # Verify the file exists
    file_path = os.path.join(workspace_path, "hello.txt")
    assert os.path.exists(file_path), "hello.txt was not created"

    # Verify the file content
    expected_content = """Hello, World!
This is a test file.
Created by AI Coding Agent."""

    actual_content = Path(file_path).read_text().strip()
    assert (
        actual_content == expected_content
    ), f"File content does not match expected content.\nExpected:\n{expected_content}\nActual:\n{actual_content}"


@pytest.mark.asyncio
async def test_react_typescript_setup(dev_agent: TestInfo):
    """Test setting up a React app with TypeScript."""
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name

    # First step: Create the React app
    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Create a new React app in a folder called reactapp using create-react-app. Don't start the app. create-react-app takes a long time so give it a timeout of 2 mins ",
    )
    assert is_ok(result)
    task_result = unwrap(result)
    assert (
        "error" not in task_result.output_message.lower()
    ), "Failed to create React app"

    # Second step: List and verify src contents
    result = await go_and_generate_report(
        dev_agent=agent,
        command="List the contents of the reactapp/src directory",
        test_name=test_name,
    )
    assert is_ok(result)
    task_result = unwrap(result)
    assert (
        "error" not in task_result.output_message.lower()
    ), "Failed to list src directory"

    # Verify essential React files exist
    react_src_path = Path(agent.workspace_path) / "reactapp" / "src"
    assert react_src_path.exists(), "src directory not found"

    essential_files = ["App.js", "App.css", "index.js", "index.css"]
    for file in essential_files:
        assert (react_src_path / file).exists(), f"{file} not found in src directory"


@pytest.mark.asyncio
@pytest.mark.timeout(300)  # 5 minute timeout for Flutter test
async def test_flutter_accounting_app(dev_agent: TestInfo) -> None:
    """Test creating a Flutter app with basic widget tests."""
    workspace_path = dev_agent.dev_agent.workspace_path
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name

    # Override max_iterations for this test
    agent.max_iterations = 30

    # Verify Flutter installation
    result = await command_functions.execute_command(
        working_path=Path(workspace_path),
        command="flutter --version",
    )
    match result:
        case Ok():
            pass
        case Err(error=e):
            raise ValueError(f"Running flutter --version failed: {e}")

    task = """Create a basic Flutter app with:
1. A basic Flutter app with the standard flutter create command
2. A single home screen that shows user "Bob Smith" text
3. A simple widget test that verifies the text is displayed

App name: accounting_app
App folder: accounting_app

Don't run the app, but do run the tests."""

    acceptance_criteria = """
1. Widget test exists and passes
2. Test verifies the "Bob Smith" text is displayed"""

    agent_result = await go_and_generate_report(
        dev_agent=agent,
        command=task,
        acceptance_criteria=acceptance_criteria,
        test_name=test_name,
    )
    assert is_ok(agent_result)
    task_result = unwrap(agent_result)
    assert not task_result.output_message.startswith(
        "Task failed",
    ), f"Agent failed to complete task: {task_result.output_message}"

    # Give Flutter some time to process after each task
    await asyncio.sleep(2)

    # Verify project creation
    project_path = os.path.join(workspace_path, "accounting_app")
    assert os.path.exists(project_path), "Project directory was not created"

    # Run Flutter tests
    result = await command_functions.execute_command(
        working_path=Path(project_path),
        command="flutter test",
    )
    match result:
        case Ok():
            pass
        case Err(error=e):
            raise ValueError(f"Running flutter test failed: {e}")

    # Verify widget test exists and has required content
    test_content = Path(os.path.join(project_path, "test/widget_test.dart")).read_text()
    assert "testWidgets" in test_content, "Widget test not found"
    assert "find" in test_content, "Widget finder not used in tests"
    assert "Bob Smith" in test_content, "Test is not checking for 'Accounting App' text"
    assert "pump" in test_content, "pump action not found in tests"
