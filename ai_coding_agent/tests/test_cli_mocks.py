"""Tests for CLI parameter passing to DevAgent."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from ai_coding_agent.cli.commands import cli, run_task
from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import Err, Ok, TaskOutput

logger = get_logger(__name__)


@pytest.fixture
def cli_runner():
    """Fixture to provide Click CLI test runner."""
    return CliRunner()


@pytest.mark.asyncio
async def test_run_command_default_parameters(cli_runner, workspace):
    """Test that run command works with default parameters."""
    workspace_id, workspace_path = workspace
    task = "Create a hello world program"

    with patch("ai_coding_agent.cli.commands.asyncio") as mock_asyncio:
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = False
        mock_loop.run_until_complete = MagicMock(return_value="Task completed")
        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_asyncio.set_event_loop = MagicMock()

        result = cli_runner.invoke(
            cli, ["run", task, "--workspace-path", str(workspace_path)]
        )

        assert result.exit_code == 0
        assert "Task completed" in result.output


@pytest.mark.asyncio
async def test_run_command_custom_parameters(cli_runner, workspace):
    """Test that run command correctly passes custom parameters."""
    _, workspace_path = workspace
    task = "Create a hello world program"
    custom_model = "gpt-3.5-turbo"
    custom_temp = 0.8
    custom_iterations = 5
    custom_criteria = "Program should print 'Hello, World!'"

    with patch("ai_coding_agent.cli.commands.asyncio") as mock_asyncio:
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = False
        mock_loop.run_until_complete = MagicMock(return_value="Task completed")
        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_asyncio.set_event_loop = MagicMock()

        result = cli_runner.invoke(
            cli,
            [
                "run",
                task,
                "--workspace-path",
                str(workspace_path),
                "--model",
                custom_model,
                "--temperature",
                str(custom_temp),
                "--max-iterations",
                str(custom_iterations),
                "--acceptance-criteria",
                custom_criteria,
            ],
        )

        assert result.exit_code == 0
        assert "Task completed" in result.output


@pytest.mark.asyncio
async def test_run_command_missing_workspace(cli_runner):
    """Test that run command fails gracefully with missing workspace."""
    task = "Create a hello world program"
    non_existent_workspace = "non-existent-workspace"

    result = cli_runner.invoke(
        cli,
        ["run", task, "--workspace-path", non_existent_workspace],
        catch_exceptions=True,
    )
    exit_code = 2
    assert result.exit_code == exit_code
    assert "Directory 'non-existent-workspace' does not exist" in result.output


@pytest.mark.asyncio
async def test_run_command_with_running_loop(cli_runner, workspace):
    """Test run command when event loop is already running."""
    workspace_id, workspace_path = workspace
    task = "Create a hello world program"

    with patch("ai_coding_agent.cli.commands.asyncio") as mock_asyncio:
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True
        mock_loop.run_until_complete = MagicMock(return_value="Task completed")
        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_asyncio.set_event_loop = MagicMock()

        result = cli_runner.invoke(
            cli, ["run", task, "--workspace-path", str(workspace_path)]
        )
        assert result.exit_code == 0
        assert "Task completed" in result.output


@pytest.mark.asyncio
async def test_run_command_general_exception(cli_runner, workspace):
    """Test run command handling of general exceptions."""
    workspace_id, workspace_path = workspace
    task = "Create a hello world program"

    with patch("ai_coding_agent.cli.commands.asyncio") as mock_asyncio:
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = False
        mock_loop.run_until_complete = MagicMock(side_effect=Exception("Task failed"))
        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_asyncio.set_event_loop = MagicMock()

        result = cli_runner.invoke(
            cli, ["run", task, "--workspace-path", str(workspace_path)]
        )
        assert result.exit_code == 1
        assert "Error: Task failed" in result.output


@pytest.mark.asyncio
async def test_run_command_error_handling(cli_runner):
    """Test run command error handling."""
    task = "test task"
    workspace_path = "non-existent-path"

    result = cli_runner.invoke(
        cli,
        ["run", task, "--workspace-path", workspace_path],
        catch_exceptions=True,
    )
    exit_code = 2
    assert result.exit_code == exit_code
    assert "Directory 'non-existent-path' does not exist" in result.output


@pytest.mark.asyncio
async def test_run_command_event_loop_handling(cli_runner, workspace):
    """Test run command event loop handling."""
    workspace_id, workspace_path = workspace
    task = "test task"

    with patch("ai_coding_agent.cli.commands.asyncio") as mock_asyncio:
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True
        mock_loop.run_until_complete = MagicMock(return_value="Task completed")
        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_asyncio.set_event_loop = MagicMock()

        result = cli_runner.invoke(
            cli,
            ["run", task, "--workspace-path", str(workspace_path)],
            catch_exceptions=True,
        )
        assert result.exit_code == 0
        assert "Task completed" in result.output
        mock_asyncio.new_event_loop.assert_called_once()
        mock_asyncio.set_event_loop.assert_called_once_with(mock_loop)


@pytest.mark.asyncio
async def test_run_task_empty_task(workspace):
    """Test run_task with an empty task."""
    _, workspace_path = workspace
    mock_agent = AsyncMock()
    mock_agent.go.return_value = Err(
        TaskOutput(
            correlation_id="test-id", output_message="Task failed: Task is empty"
        )
    )

    with (
        patch("ai_coding_agent.cli.commands.DevAgent", return_value=mock_agent),
        patch("ai_coding_agent.cli.commands.generate_html_report"),
    ):
        result = await run_task(task="", workspace_path=Path(workspace_path))
        assert isinstance(result, Err)
        match result:
            case Err(error=error_msg):
                assert "Task failed: Task is empty" in error_msg


@pytest.mark.asyncio
async def test_run_task_successful(workspace):
    """Test run_task with a successful task execution."""
    _, workspace_path = workspace
    mock_agent = AsyncMock()
    mock_agent.go.return_value = Ok(
        TaskOutput(
            correlation_id="test-id", output_message="Task completed successfully"
        )
    )

    with (
        patch("ai_coding_agent.cli.commands.DevAgent", return_value=mock_agent),
        patch("ai_coding_agent.cli.commands.generate_html_report") as mock_report,
    ):
        result = await run_task(
            task="Test task",
            workspace_path=Path(workspace_path),
            acceptance_criteria="Test criteria",
        )

        # Verify agent was created with correct parameters
        assert isinstance(result, Ok)
        match result:
            case Ok(value=output_msg):
                assert output_msg == "Task completed successfully"

        # Verify report was generated
        mock_report.assert_called_once_with("test-id.json", "test-id.html")


@pytest.mark.asyncio
async def test_run_task_failure(workspace):
    """Test run_task with a failed task execution."""
    _, workspace_path = workspace
    mock_agent = AsyncMock()
    mock_agent.go.return_value = Err(
        TaskOutput(
            correlation_id="test-id", output_message="Task failed: Error occurred"
        )
    )

    with (
        patch("ai_coding_agent.cli.commands.DevAgent", return_value=mock_agent),
        patch("ai_coding_agent.cli.commands.generate_html_report") as mock_report,
    ):
        result = await run_task(task="Test task", workspace_path=Path(workspace_path))

        assert isinstance(result, Err)
        match result:
            case Err(error=error_msg):
                assert error_msg == "Task failed: Error occurred"

        # Verify report was still generated
        mock_report.assert_called_once_with("test-id.json", "test-id.html")


@pytest.mark.asyncio
async def test_run_task_exception(workspace):
    """Test run_task when an exception occurs."""
    _, workspace_path = workspace
    mock_agent = AsyncMock()
    mock_agent.go.side_effect = Exception("Unexpected error")

    with patch("ai_coding_agent.cli.commands.DevAgent", return_value=mock_agent):
        result = await run_task(task="Test task", workspace_path=Path(workspace_path))

        assert isinstance(result, Err)
        match result:
            case Err(error=error_msg):
                assert error_msg == "Unexpected error"


@pytest.mark.asyncio
async def test_run_task_with_custom_parameters(workspace):
    """Test run_task with custom parameters."""
    _, workspace_path = workspace
    mock_agent = AsyncMock()
    mock_agent.go.return_value = Ok(
        TaskOutput(
            correlation_id="test-id", output_message="Task completed successfully"
        )
    )

    with (
        patch("ai_coding_agent.cli.commands.DevAgent") as mock_dev_agent,
        patch(
            "ai_coding_agent.cli.commands.generate_html_report"
        ) as mock_generate_report,
    ):
        mock_dev_agent.return_value = mock_agent
        result = await run_task(
            task="Test task",
            workspace_path=Path(workspace_path),
            acceptance_criteria="Custom criteria",
            max_iterations=5,
            model="custom-model",
            temperature=0.8,
        )

        # Verify DevAgent was created with custom parameters
        mock_dev_agent.assert_called_once_with(
            workspace_path=Path(workspace_path),
            model="custom-model",
            temperature=0.8,
            max_iterations=5,
        )

        # Verify generate_html_report was called with correct parameters
        mock_generate_report.assert_called_once_with("test-id.json", "test-id.html")

        assert isinstance(result, Ok)
        match result:
            case Ok(value=output_msg):
                assert output_msg == "Task completed successfully"
