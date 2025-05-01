"""Test file for debugging Flutter CLI command execution."""

import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

from ai_coding_agent.core.logger import get_logger

logger = get_logger(__name__)


def test_create_flutter_app_and_change_dir():
    """Create a Flutter app and change to the app directory testapp."""
    # TODO: not safe to run in parallel, use a unique workspace path
    directory_name = uuid.uuid4().hex
    workspace_path = Path.cwd() / directory_name
    workspace_path.mkdir(exist_ok=True)

    # Build the command as a list for proper argument handling
    cmd = [
        sys.executable,  # Use the current Python interpreter
        "main.py",
        "run",
        "--workspace-path",
        directory_name,
        "--max-iterations",
        "15",
        "1. Create a Flutter app with flutter create testapp 2. Change to the app directory testapp",
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Output: {result.stdout}")
        assert result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.info(f"Error output: {e.stderr}")
        raise
    finally:
        # Clean up the workspace
        shutil.rmtree(workspace_path, ignore_errors=True)


@pytest.mark.skip(reason="Manual debugging test - skip in CI")
def test_create_and_run_flutter_app():
    """Test the Flutter CLI command with all parameters for debugging.

    This test actually executes the CLI process, allowing you to attach a debugger
    to the Python process. To debug:
    1. Set a breakpoint in ai_coding_agent/cli/commands.py
    2. Run this test with debugger attached
    """
    # An absolute path in the temp folder
    workspace_path = Path(tempfile.gettempdir()) / "test_workspace"
    workspace_path.mkdir(exist_ok=True)

    # Build the command as a list for proper argument handling
    cmd = [
        sys.executable,  # Use the current Python interpreter
        "main.py",
        "run",
        "--workspace-path",
        str(workspace_path),
        "--acceptance-criteria",
        "Can navigate between several account screens, and the app runs on macOS. Run it and see if it works.",
        "--max-iterations",
        "30",
        "Create a Flutter app with basic accounting screens and named app routes for accountants. Start with flutter create.",
    ]

    # Run the process and capture output
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Output: {result.stdout}")
        assert result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.info(f"Error output: {e.stderr}")
        raise


if __name__ == "__main__":
    # This allows running the test directly with Python for easier debugging
    test_create_and_run_flutter_app()
