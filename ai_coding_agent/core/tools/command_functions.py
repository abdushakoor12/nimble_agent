"""Command execution functions AI Coding Agent for tools.

This module provides tools for executing shell commands within workspace
boundaries. All commands are executed with proper security checks.

Pure functions, with no state.
"""

import asyncio
from pathlib import Path

from ai_coding_agent.core.constants import (
    DEFAULT_COMMAND_TIMEOUT,
)
from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import Err, Ok
from ai_coding_agent.core.tools.result_types import CommandData, CommandResult

# Configure logging
logger = get_logger(__name__)


async def execute_command(
    *,
    working_path: Path,
    command: str,
    process_timeout: float = DEFAULT_COMMAND_TIMEOUT,
) -> CommandResult:
    """Execute a shell command.

    Args:
        working_path: Absolute path to the directory where the command will be run
        command: Command to execute
        process_timeout: Timeout for the process to complete

    Returns:
        Result with success status and command output
    """
    if (
        not working_path.is_absolute()
        or not working_path.is_dir()
        or not working_path.exists()
    ):
        error_msg = "Invalid working path"
        logger.error(
            error_msg,
            extra={
                "command": command,
                "working_path": str(working_path),
                "timeout": process_timeout,
                "error": error_msg,
            },
        )
        return Err(error_msg)

    process = None
    try:
        # Create subprocess
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(working_path),
        )

        # Add a timeout for command execution
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=process_timeout
        )
        output = stdout.decode() if stdout else stderr.decode()

        if process.returncode != 0:
            error_msg = f"Command failed with exit code {process.returncode}: {output}"
            logger.error(
                "Command execution failed",
                extra={
                    "command": command,
                    "working_path": str(working_path),
                    "timeout": process_timeout,
                    "error": error_msg,
                },
            )
            return Err(error_msg)

        logger.info(
            "Command executed successfully.\nCommand\n%(command)s\nOutput\n%(output)s\nWorking Path:\n%(working_path)s\nTimeout\n%(timeout)s",
            {
                "command": command,
                "output": output,
                "working_path": str(working_path),
                "timeout": process_timeout,
            },
        )

        return Ok(CommandData(message=output, working_path=str(working_path)))
    except TimeoutError:
        error_msg = "Command timed out"
        logger.exception(
            error_msg,
            extra={
                "command": command,
                "working_path": str(working_path),
                "timeout": process_timeout,
                "error": error_msg,
            },
        )
        if process:
            try:
                process.terminate()
                try:
                    logger.info(
                        "Waiting for process to terminate", extra={"pid": process.pid}
                    )
                    await asyncio.wait_for(process.wait(), timeout=0.5)
                except TimeoutError:
                    logger.warning(
                        "Process could not be terminated", extra={"pid": process.pid}
                    )
                    process.kill()  # Force kill if terminate doesn't work
                    try:
                        logger.info(
                            "Waiting for process to be killed",
                            extra={"pid": process.pid},
                        )
                        await asyncio.wait_for(process.wait(), timeout=0.5)
                    except TimeoutError:
                        logger.warning(
                            "Process could not be killed", extra={"pid": process.pid}
                        )
            except Exception as e:
                logger.warning(
                    f"Error cleaning up process: {e}", extra={"pid": process.pid}
                )
        return Err(f"Command timed out after {process_timeout} seconds")
    except Exception as e:
        error_msg = f"Error executing command: {e}"
        logger.exception(
            error_msg,
            extra={
                "command": command,
                "working_path": str(working_path),
                "timeout": process_timeout,
                "error": error_msg,
            },
        )
        return Err(error_msg)
