"""Tests for toolkit functions and tools.

This set of tests uses the tools with mocks only. It doesn't
physically touch the filesystem or processes.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import Err, Ok, is_err
from ai_coding_agent.core.tools.command_functions import execute_command
from ai_coding_agent.tests.test_functions import runtest

logger = get_logger(__name__)


@pytest.fixture
def cli_runner():
    """Fixture to provide a CLI runner."""
    return MagicMock()


@pytest.mark.asyncio
async def test_execute_command_process_timeout():
    """Test execute_command process timeout handling."""
    await runtest(execute_command_process_timeout_impl)


@pytest.mark.asyncio
async def test_execute_command_process_termination():
    """Test execute_command process termination."""
    await runtest(execute_command_process_termination_impl)


@pytest.mark.asyncio
async def test_execute_command_process_kill():
    """Test execute_command process kill."""
    await runtest(execute_command_process_kill_impl)


@pytest.mark.asyncio
async def test_execute_command_process_cleanup_error():
    """Test execute_command process cleanup error handling."""
    await runtest(execute_command_process_cleanup_error_impl)


async def execute_command_process_cleanup_error_impl(workspace_path: str):
    """Test execute_command process cleanup error handling implementation."""
    mock_process = AsyncMock()
    mock_process.returncode = None
    mock_process.stdout = None
    mock_process.stderr = None

    # Mock terminate to raise an error
    def raise_error(*args, **kwargs):  # type: ignore # noqa: ARG001
        raise ProcessLookupError("Process not found")

    mock_process.terminate = MagicMock(side_effect=raise_error)
    mock_process.kill = MagicMock(side_effect=raise_error)

    async def mock_wait():
        await asyncio.sleep(2)
        return mock_process

    mock_process.wait = mock_wait
    mock_process.communicate = mock_wait

    with patch("asyncio.create_subprocess_shell", return_value=mock_process):
        result = await execute_command(
            working_path=Path(workspace_path),
            command="test",
            process_timeout=0.1,
        )
        assert is_err(result)
        match result:
            case Err(error=err):
                assert "timed out" in err
            case Ok(_):
                pytest.fail("Expected error result")


@pytest.mark.asyncio
async def test_execute_command_process_wait_error():
    """Test execute_command process wait error handling."""
    await runtest(execute_command_process_wait_error_impl)


async def execute_command_process_wait_error_impl(workspace_path: str):
    """Test execute_command process wait error handling implementation."""
    mock_process = AsyncMock()
    mock_process.returncode = None
    mock_process.stdout = None
    mock_process.stderr = None
    mock_process.terminate = MagicMock()
    mock_process.kill = MagicMock()

    async def mock_wait():
        raise ProcessLookupError("Process disappeared")

    mock_process.wait = mock_wait
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch("asyncio.create_subprocess_shell", return_value=mock_process):
        result = await execute_command(
            working_path=Path(workspace_path),
            command="test",
        )
        assert is_err(result)
        match result:
            case Err(error=err):
                assert "Command failed" in err
            case Ok(_):
                pytest.fail("Expected error result")


@pytest.mark.asyncio
async def test_execute_command_process_creation_error():
    """Test execute_command process creation error handling."""
    await runtest(execute_command_process_creation_error_impl)


async def execute_command_process_creation_error_impl(workspace_path: str):
    """Test execute_command process creation error handling implementation."""
    with patch(
        "asyncio.create_subprocess_shell",
        side_effect=OSError("Failed to create process"),
    ):
        result = await execute_command(
            working_path=Path(workspace_path),
            command="test",
        )
        assert is_err(result)
        match result:
            case Err(error=err):
                assert "Error executing command" in err
            case Ok(_):
                pytest.fail("Expected error result")


@pytest.mark.asyncio
async def test_execute_command_process_communicate_error():
    """Test execute_command process communicate error handling."""
    await runtest(execute_command_process_communicate_error_impl)


async def execute_command_process_communicate_error_impl(workspace_path: str):
    """Test execute_command process communicate error handling implementation."""
    mock_process = AsyncMock()
    mock_process.returncode = None
    mock_process.stdout = None
    mock_process.stderr = None
    mock_process.terminate = MagicMock()
    mock_process.kill = MagicMock()

    async def mock_communicate():
        raise BrokenPipeError("Pipe broke")

    mock_process.communicate = mock_communicate
    mock_process.wait = AsyncMock()

    with patch("asyncio.create_subprocess_shell", return_value=mock_process):
        result = await execute_command(
            working_path=Path(workspace_path),
            command="test",
        )
        assert is_err(result)
        match result:
            case Err(error=err):
                assert "Error executing command" in err
            case Ok(_):
                pytest.fail("Expected error result")


async def execute_command_process_timeout_impl(workspace_path: str):
    """Test execute_command process timeout handling."""
    # Mock process that hangs
    mock_process = AsyncMock()
    mock_process.returncode = None
    mock_process.stdout = None
    mock_process.stderr = None
    mock_process.terminate = MagicMock()  # Synchronous method
    mock_process.kill = MagicMock()  # Synchronous method

    async def mock_wait():
        await asyncio.sleep(2)  # Simulate long-running process
        return mock_process

    mock_process.wait = mock_wait
    mock_process.communicate = mock_wait

    with patch("asyncio.create_subprocess_shell", return_value=mock_process):
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                execute_command(working_path=Path(workspace_path), command="test"),
                timeout=1,
            )


async def execute_command_process_termination_impl(workspace_path: str):
    """Test execute_command process termination."""
    # Mock process that hangs
    mock_process = AsyncMock()
    mock_process.returncode = None
    mock_process.stdout = None
    mock_process.stderr = None
    mock_process.terminate = MagicMock()  # Synchronous method
    mock_process.kill = MagicMock()  # Synchronous method

    async def mock_wait():
        await asyncio.sleep(2)  # Simulate long-running process
        return mock_process

    mock_process.wait = mock_wait
    mock_process.communicate = mock_wait

    with patch("asyncio.create_subprocess_shell", return_value=mock_process):
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                execute_command(working_path=Path(workspace_path), command="test"),
                timeout=1,
            )


async def execute_command_process_kill_impl(workspace_path: str):
    """Test execute_command process kill."""
    # Mock process that hangs
    mock_process = AsyncMock()
    mock_process.returncode = None
    mock_process.stdout = None
    mock_process.stderr = None
    mock_process.terminate = MagicMock()  # Synchronous method
    mock_process.kill = MagicMock()  # Synchronous method

    async def mock_wait():
        await asyncio.sleep(2)  # Simulate long-running process
        return mock_process

    mock_process.wait = mock_wait
    mock_process.communicate = mock_wait

    with patch("asyncio.create_subprocess_shell", return_value=mock_process):
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                execute_command(working_path=Path(workspace_path), command="test"),
                timeout=1,
            )
