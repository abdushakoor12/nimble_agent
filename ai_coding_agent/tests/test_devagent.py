"""End-to-end tests for AI Coding Agent."""

from pathlib import Path

import pytest

from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import is_err, is_ok, unwrap
from ai_coding_agent.tests.conftest import TestInfo, go_and_generate_report

logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_dev_agent_git_operations(dev_agent: TestInfo) -> None:
    """Test git operations using DevAgent."""
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name
    workspace_path = agent.workspace_path

    # Initialize git
    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Initialize a git repository",
    )
    assert is_ok(result)
    assert Path(workspace_path / ".git").resolve().exists()

    # Create and add README
    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Create a README.md file with a test repository description and add it to git",
    )
    assert is_ok(result)
    assert Path(workspace_path / "README.md").resolve().exists()

    # Commit changes
    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command='Commit the changes with the message "Initial commit"',
    )
    assert is_ok(result)
    assert (
        Path(workspace_path / ".git/refs/heads/master").resolve().exists()
        or (workspace_path / ".git/refs/heads/main").resolve().exists()
    )


@pytest.mark.skip(reason="Flaky CI test that needs to be fixed")
@pytest.mark.asyncio
async def test_dev_agent_flutter_operations(dev_agent: TestInfo) -> None:
    """Test Flutter operations using DevAgent."""
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name
    workspace_path = agent.workspace_path

    # Check Flutter installation
    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Check if Flutter is installed by running flutter --version",
    )
    assert is_ok(result)
    task_result = unwrap(result)
    if "Flutter" not in task_result.output_message:
        pytest.fail("Flutter is not installed. Please install Flutter and try again.")

    # Create Flutter app
    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Create a new Flutter app named test. Please don't run the app.",
    )
    assert is_ok(result)

    # Verify key files exist
    expected_files = [
        "test/pubspec.yaml",
        "test/lib/main.dart",
        "test/android/app/build.gradle",
        "test/ios/Runner.xcodeproj/project.pbxproj",
    ]

    for file in expected_files:
        file_path = workspace_path / file
        assert file_path.exists(), f"File does not exist: {file_path}"


@pytest.mark.asyncio
async def test_dev_agent_npm_operations(dev_agent: TestInfo) -> None:
    """Test npm operations using DevAgent."""
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name
    workspace_path = agent.workspace_path

    # Check npm installation
    result = await go_and_generate_report(
        dev_agent=agent,
        command="Check if npm is installed by running npm --version",
        test_name=test_name,
    )
    assert is_ok(result)
    task_result = unwrap(result)
    if "npm" not in task_result.output_message.lower():
        pytest.skip("npm is not installed. Skipping npm tests.")

    # Initialize npm project
    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Run npm with the args init -y",
    )
    assert is_ok(result)
    assert (workspace_path / "package.json").exists()

    # Create server.js
    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Create a basic Express.js server in server.js that listens on port 3000 and responds with 'Hello World!' on the root route. No need to run the server.",
    )
    assert is_ok(result)
    assert (workspace_path / "server.js").exists()

    # Install express
    result = await go_and_generate_report(
        dev_agent=agent,
        command="Install the express package using npm",
        test_name=test_name,
    )
    assert is_ok(result)
    assert (workspace_path / "node_modules/express").exists()

    # Create README and .gitignore
    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Create a README.md with setup instructions and a .gitignore file for a Node.js project",
    )
    assert is_ok(result)
    assert (workspace_path / "README.md").exists()
    assert (workspace_path / ".gitignore").exists()


@pytest.mark.asyncio
async def test_dev_agent_create_directory(dev_agent: TestInfo) -> None:
    """Test creating a directory using DevAgent."""
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name
    workspace_path = agent.workspace_path

    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Create a directory named testfolder",
    )
    assert is_ok(result)
    assert (Path(workspace_path) / "testfolder").exists()
    assert (Path(workspace_path) / "testfolder").is_dir()


@pytest.mark.asyncio
async def test_dev_agent_change_to_directory(dev_agent: TestInfo) -> None:
    """Test changing into a directory using DevAgent."""
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name
    workspace_path = agent.workspace_path

    # Setup: Create directory
    test_dir = Path(workspace_path) / "testfolder"
    test_dir.mkdir(exist_ok=True)

    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Change current directory to testfolder",
    )
    assert is_ok(result)
    assert str(agent.current_dir) == "testfolder"


@pytest.mark.asyncio
async def test_dev_agent_change_to_directory_nested(dev_agent: TestInfo) -> None:
    """Test changing into a directory using DevAgent."""
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name
    workspace_path = agent.workspace_path

    first_folder = Path(workspace_path / "testfolder").resolve()
    first_folder.mkdir(exist_ok=True)

    second_folder = Path(first_folder / "testfolder2").resolve()
    second_folder.mkdir(exist_ok=True)

    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Change current directory to testfolder. List the contents of the directory, and then change to the only folder in that directory",
    )
    assert is_ok(result)
    assert str(agent.current_dir) == "testfolder/testfolder2"


@pytest.mark.asyncio
async def test_dev_agent_change_to_directory_nested_withac(dev_agent: TestInfo) -> None:
    """Test changing into a directory using DevAgent."""
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name
    workspace_path = agent.workspace_path

    first_folder = Path(workspace_path / "testfolder").resolve()
    first_folder.mkdir(exist_ok=True)

    second_folder = Path(first_folder / "testfolder2").resolve()
    second_folder.mkdir(exist_ok=True)

    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Change current directory to testfolder. List the contents of the directory, and then change to the only folder in that directory",
        acceptance_criteria="Current directory is the directory I asked you to navigate to",
    )
    assert is_ok(result)
    assert str(agent.current_dir) == "testfolder/testfolder2"


@pytest.mark.asyncio
async def test_dev_agent_create_file_with_content(dev_agent: TestInfo) -> None:
    """Test creating a file with content using DevAgent."""
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name
    workspace_path = agent.workspace_path

    # Setup: Create and change to directory
    test_dir = Path(workspace_path) / "testfolder"
    test_dir.mkdir(exist_ok=True)
    agent.current_dir = Path("testfolder")

    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Create a file named testfile.txt with the content 'Hello from test'",
    )
    assert is_ok(result)
    test_file_path = Path(workspace_path) / "testfolder/testfile.txt"
    assert test_file_path.exists()
    assert test_file_path.read_text().strip() == "Hello from test"


@pytest.mark.asyncio
async def test_dev_agent_delete_file(dev_agent: TestInfo) -> None:
    """Test deleting a file using DevAgent."""
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name
    workspace_path = agent.workspace_path

    # Setup: Create directory and file
    test_dir = Path(workspace_path) / "testfolder"
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "testfile.txt"
    test_file.write_text("Hello from test")
    agent.current_dir = Path("testfolder")

    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Delete the file testfile.txt",
    )
    assert is_ok(result)
    assert not test_file.exists()


@pytest.mark.asyncio
async def test_dev_agent_change_to_root(dev_agent: TestInfo) -> None:
    """Test changing back to root directory using DevAgent."""
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name
    workspace_path = agent.workspace_path

    # Setup: Create directory and set current directory
    test_dir = Path(workspace_path) / "testfolder"
    test_dir.mkdir(exist_ok=True)
    agent.current_dir = Path("testfolder")

    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Change directory back to the workspace root",
    )
    assert is_ok(result)
    assert str(agent.current_dir) == "/"


@pytest.mark.asyncio
async def test_dev_agent_delete_directory(dev_agent: TestInfo) -> None:
    """Test deleting a directory using DevAgent."""
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name
    workspace_path = agent.workspace_path

    # Setup: Create directory
    test_dir = Path(workspace_path) / "testfolder"
    test_dir.mkdir(exist_ok=True)
    agent.current_dir = Path("/")

    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="Delete the directory named testfolder",
    )
    assert is_ok(result)
    assert not test_dir.exists()


@pytest.mark.asyncio
async def test_dev_agent_go_empty_input(dev_agent: TestInfo) -> None:
    """Test DevAgent go method with empty input."""
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name
    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="",
    )
    assert is_err(result), "Expected error result"

    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command="   ",
    )
    assert is_err(result), "Expected error result"


@pytest.mark.asyncio
async def test_dev_agent_go_with_acceptance_criteria(
    dev_agent: TestInfo,
) -> None:
    """Test DevAgent go method with acceptance criteria."""
    agent = dev_agent.dev_agent
    test_name = dev_agent.test_name
    # Test with simple task and acceptance criteria
    task = "Create a file named test.txt with content 'test'"
    acceptance_criteria = "File test.txt exists and contains the word 'test'"

    result = await go_and_generate_report(
        dev_agent=agent,
        test_name=test_name,
        command=task,
        acceptance_criteria=acceptance_criteria,
    )
    assert is_ok(result)

    # Verify the file was created according to acceptance criteria
    test_file = Path(agent.workspace_path) / "test.txt"
    assert test_file.exists()
    assert "test" in test_file.read_text()


@pytest.mark.asyncio
async def test_dev_agent_create_react_app(dev_agent: TestInfo) -> None:
    """Test creating a React app and verifying its structure."""
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
        test_name=test_name,
        command="List the contents of the reactapp/src directory",
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
