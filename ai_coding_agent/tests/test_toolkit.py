"""Tests for toolkit functions and tools.

This set of tests uses the tool functions directly and
does not use mocks.
"""

import os
import uuid
from pathlib import Path
from typing import TypeVar

import pytest

from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import Err, Ok, is_err, is_ok, unwrap
from ai_coding_agent.core.tools import (
    list_directory_content,
    read_file,
    write_file,
)
from ai_coding_agent.core.tools.command_functions import execute_command
from ai_coding_agent.core.tools.file_functions import is_path_in_workspace
from ai_coding_agent.tests.conftest import TestInfo
from ai_coding_agent.tests.test_functions import create_test_file

logger = get_logger(__name__)

T = TypeVar("T")

# Fixtures are now in conftest.py


async def create_test_directories(workspace_path: str, directories: list[str]) -> None:
    """Create test directories."""
    for directory in directories:
        os.makedirs(os.path.join(str(workspace_path), directory), exist_ok=True)


@pytest.mark.asyncio
async def test_directory_content_edge_cases(dev_agent: TestInfo):  # noqa: C901
    """Test directory content operations with edge cases and error conditions."""
    workspace_path = str(dev_agent.dev_agent.workspace_path)

    # Test relative path error
    relative_path = Path("test_dir")
    result = await list_directory_content(relative_path)
    assert is_err(result)
    match result:
        case Err(error=err):
            assert "directory_path must be absolute" in err
        case Ok(_):
            pytest.fail("Expected error result")

    # Test non-existent directory
    nonexistent = Path(workspace_path) / "nonexistent"
    result = await list_directory_content(nonexistent)
    assert is_err(result)
    match result:
        case Err(error=err):
            assert "Directory does not exist" in err
        case Ok(_):
            pytest.fail("Expected error result")

    # Test file instead of directory
    test_file = Path(workspace_path) / "test.txt"
    await create_test_file(test_file.resolve(), "content")
    result = await list_directory_content(test_file)
    assert is_err(result)
    match result:
        case Err(error=err):
            assert "Not a directory" in err
        case Ok(_):
            pytest.fail("Expected error result")

    # Test with a random UUID-based filename outside workspace
    random_filename = f"{uuid.uuid4()}.txt"
    read_file_result = await read_file(
        Path(workspace_path) / Path(f"../{random_filename}").resolve()
    )
    match read_file_result:
        case Err(error=err):
            assert "Error: file does not exist" in err
        case Ok(_):
            pytest.fail("Expected error result")

    # Test invalid file read
    read_file_result = await read_file(
        Path(workspace_path).resolve() / "nonexistent.txt"
    )
    match read_file_result:
        case Err(error=err):
            assert "file does not exist" in err
        case Ok(_):
            pytest.fail("Expected error result")

    # Test write file with invalid permissions
    test_dir = Path(workspace_path) / "readonly"
    test_dir.mkdir(exist_ok=True)
    os.chmod(test_dir, 0o444)  # Read-only
    write_file_result = await write_file(
        Path(workspace_path).resolve() / "readonly/test.txt", "content"
    )
    match write_file_result:
        case Err(error=err):
            assert "Error writing file" in err
        case Ok(_):
            pytest.fail("Expected error result")
    os.chmod(test_dir, 0o755)  # Restore permissions


@pytest.mark.asyncio
async def test_directory_content_listing(dev_agent: TestInfo):
    """Test directory content listing with files and folders."""
    workspace_path = str(dev_agent.dev_agent.workspace_path)

    # Create test structure
    test_dir = Path(workspace_path) / "test_dir"
    test_dir.mkdir(exist_ok=True)

    # Create some files
    file1 = test_dir / "file1.txt"
    file2 = test_dir / "file2.txt"
    await create_test_file(file1, "content1")
    await create_test_file(file2, "content2")

    # Create some folders
    folder1 = test_dir / "folder1"
    folder2 = test_dir / "folder2"
    folder1.mkdir(exist_ok=True)
    folder2.mkdir(exist_ok=True)

    # Test listing
    result = await list_directory_content(test_dir)
    assert is_ok(result)
    content = unwrap(result)

    file_count = 2

    # Verify files
    assert len(content.files) == file_count
    assert "file1.txt" in content.files
    assert "file2.txt" in content.files

    # Verify folders
    assert len(content.folders) == file_count
    assert "folder1" in content.folders
    assert "folder2" in content.folders


@pytest.mark.asyncio
async def test_path_workspace_validation(dev_agent: TestInfo):
    """Test path validation functions."""
    workspace_path = str(dev_agent.dev_agent.workspace_path)

    # Test valid paths
    assert is_path_in_workspace(
        workspace_path=Path(workspace_path),
        file_path=Path(workspace_path) / "test.txt",
    )
    assert is_path_in_workspace(
        workspace_path=Path(workspace_path),
        file_path=Path(workspace_path) / "dir/test.txt",
    )

    # Test invalid paths
    assert not is_path_in_workspace(
        workspace_path=Path(workspace_path),
        file_path=Path(workspace_path).parent / "test.txt",
    )
    assert not is_path_in_workspace(
        workspace_path=Path(workspace_path),
        file_path=Path("/completely/different/path"),
    )

    # Test with invalid path strings
    assert not is_path_in_workspace(
        workspace_path=Path(workspace_path), file_path=Path("\0invalid")
    )  # NULL byte
    assert not is_path_in_workspace(
        workspace_path=Path("\0invalid"), file_path=Path("test.txt")
    )  # Invalid workspace path

    # Test symlink handling
    symlink_dir = Path(workspace_path) / "symlink_dir"
    target_dir = Path(workspace_path) / "target_dir"
    target_dir.mkdir(exist_ok=True)
    try:
        os.symlink(target_dir, symlink_dir)
        assert is_path_in_workspace(
            workspace_path=Path(workspace_path), file_path=symlink_dir / "test.txt"
        )
    except OSError:
        logger.warning("Symlink creation failed - skipping symlink test")


@pytest.mark.asyncio
async def test_file_operations_with_special_chars(dev_agent: TestInfo):
    """Test file operations with special characters in paths."""
    workspace_path = str(dev_agent.dev_agent.workspace_path)

    special_chars = [
        "spaces in name",
        "unicode_⚡️_char",
        "!@#$%^&()_+-=",
        "multiple..dots",
        ".hidden",
    ]

    for name in special_chars:
        # Test directory operations
        dir_path = os.path.join(workspace_path, name)
        os.makedirs(dir_path, exist_ok=True)

        # Create a subdirectory
        subdir_path = os.path.join(dir_path, "subdir")
        os.makedirs(subdir_path, exist_ok=True)

        # Test file operations
        file_path = f"{name}/test.txt"
        content = f"Content for {name}"

        # Write and verify
        write_result = await write_file(
            Path(workspace_path).resolve() / file_path, content
        )
        assert is_ok(write_result)

        # Read and verify
        read_result = await read_file(Path(workspace_path).resolve() / file_path)
        assert is_ok(read_result)
        assert unwrap(read_result).content == content

        # List directory contents and verify
        abs_dir_path = Path(workspace_path) / name
        list_result = await list_directory_content(abs_dir_path)
        assert is_ok(list_result)
        dir_content = unwrap(list_result)
        assert "test.txt" in dir_content.files
        assert "subdir" in dir_content.folders


@pytest.mark.asyncio
async def test_command_timeout(dev_agent: TestInfo) -> None:
    """Test command execution timeout behavior."""
    workspace_path = dev_agent.dev_agent.workspace_path
    result = await execute_command(
        working_path=Path(workspace_path), command="sleep 2", process_timeout=0.1
    )
    assert is_err(result)
    match result:
        case Err(error=err):
            assert "timed out" in err
        case Ok(_):
            pytest.fail("Expected error result")


@pytest.mark.asyncio
async def test_nonexistent_command(dev_agent: TestInfo) -> None:
    """Test execution of a nonexistent command."""
    workspace_path = dev_agent.dev_agent.workspace_path
    result = await execute_command(
        working_path=Path(workspace_path), command="nonexistent_command"
    )
    assert is_err(result)
    match result:
        case Err(error=err):
            assert "Command failed" in err
        case Ok(_):
            pytest.fail("Expected error result")


@pytest.mark.asyncio
async def test_invalid_working_path() -> None:
    """Test command execution with invalid working path."""
    result = await execute_command(working_path=Path("/nonexistent/path"), command="ls")
    assert is_err(result)
    match result:
        case Err(error=err):
            assert "Invalid working path" in err
        case Ok(_):
            pytest.fail("Expected error result")


@pytest.mark.asyncio
async def test_command_with_stderr(dev_agent: TestInfo) -> None:
    """Test command execution that produces stderr output."""
    workspace_path = dev_agent.dev_agent.workspace_path
    result = await execute_command(
        working_path=Path(workspace_path), command="ls nonexistent_file"
    )
    assert is_err(result)
    match result:
        case Err(error=err):
            assert "Command failed" in err
        case Ok(_):
            pytest.fail("Expected error result")


@pytest.mark.asyncio
async def test_command_with_suppressed_stderr(dev_agent: TestInfo) -> None:
    """Test successful command execution with suppressed stderr output."""
    workspace_path = dev_agent.dev_agent.workspace_path
    result = await execute_command(
        working_path=Path(workspace_path),
        command="ls nonexistent 2>/dev/null || true",
    )
    assert is_ok(result)


@pytest.mark.asyncio
async def test_command_execution_working_directory(dev_agent: TestInfo):
    """Test that execute_command runs commands in the correct working directory."""
    workspace_path = str(dev_agent.dev_agent.workspace_path)

    # Create nested test directories
    test_dirs = ["dir1", "dir1/subdir"]
    await create_test_directories(workspace_path, test_dirs)

    # Test command in workspace root
    result = await execute_command(working_path=Path(workspace_path), command="pwd")
    assert is_ok(result)
    assert Path(unwrap(result).working_path).samefile(workspace_path)
    assert Path(unwrap(result).message.strip()).samefile(workspace_path)

    # Test command in subdirectory
    result = await execute_command(
        working_path=Path(workspace_path) / "dir1", command="pwd"
    )
    assert is_ok(result)
    expected_path = Path(workspace_path) / "dir1"
    assert Path(unwrap(result).working_path).samefile(expected_path)
    assert Path(unwrap(result).message.strip()).samefile(expected_path)

    # Test command in nested subdirectory
    result = await execute_command(
        working_path=Path(workspace_path) / "dir1/subdir", command="pwd"
    )
    assert is_ok(result)
    expected_path = Path(workspace_path) / "dir1/subdir"
    assert Path(unwrap(result).working_path).samefile(expected_path)
    assert Path(unwrap(result).message.strip()).samefile(expected_path)

    # Test that file operations work in the correct directory
    result = await execute_command(
        working_path=Path(workspace_path) / "dir1/subdir",
        command="touch test.txt && ls test.txt",
    )
    assert is_ok(result)
    assert "test.txt" in unwrap(result).message
    assert (Path(workspace_path) / "dir1/subdir/test.txt").exists()
    assert not (Path(workspace_path) / "test.txt").exists()


@pytest.mark.asyncio
async def test_git_operations(workspace: tuple[str, str]) -> None:
    """Test git operations using the tools directly."""
    _, workspace_path_str = workspace
    workspace_path = Path(workspace_path_str)

    # Initialize git
    result = await execute_command(working_path=workspace_path, command="git init")
    assert is_ok(result)
    assert (workspace_path / Path(".git")).resolve().exists()

    # Create README
    readme_content = (
        "# Test Repository\nThis is a test repository created by AI Coding Agent."
    )
    await create_test_file(Path(workspace_path).resolve() / "README.md", readme_content)
    assert (workspace_path / Path("README.md")).resolve().exists()

    # Git operations
    result = await execute_command(working_path=workspace_path, command="git add .")
    assert is_ok(result)

    result = await execute_command(
        working_path=workspace_path, command="git commit -m 'Initial commit'"
    )
    assert is_ok(result)

    # Verify git commit exists
    assert (workspace_path / Path(".git/refs/heads/master")).resolve().exists() or (
        workspace_path / Path(".git/refs/heads/main")
    ).resolve().exists()


@pytest.mark.skip(reason="Flaky CI test that needs to be fixed")
@pytest.mark.asyncio
async def test_flutter_operations(workspace: tuple[str, str]) -> None:
    """Test Flutter operations using the tools directly."""
    _, workspace_path = workspace

    # Check if Flutter is installed
    result = await execute_command(
        working_path=Path(workspace_path), command="flutter --version"
    )
    if is_ok(result) and "Flutter" not in unwrap(result).message:
        pytest.skip("Flutter is not installed. Skipping Flutter tests.")

    # Create Flutter app
    result = await execute_command(
        working_path=Path(workspace_path), command="flutter create test"
    )
    assert is_ok(result)
    assert "Creating project test..." in unwrap(result).message

    # Verify key files exist
    expected_files = [
        "test/pubspec.yaml",
        "test/lib/main.dart",
        "test/android/app/build.gradle",
        "test/ios/Runner.xcodeproj/project.pbxproj",
    ]

    for file in expected_files:
        file_path = os.path.join(str(workspace_path), file)
        assert os.path.exists(file_path), f"File does not exist: {file_path}"


@pytest.mark.asyncio
async def test_npm_operations(workspace: tuple[str, str]) -> None:
    """Test npm operations using the tools directly."""
    _, workspace_path_str = workspace
    workspace_path = Path(workspace_path_str)

    # Check if npm is installed
    result = await execute_command(working_path=workspace_path, command="npm --version")
    if not is_ok(result):
        pytest.skip("npm is not installed. Skipping npm tests.")

    # Initialize npm project
    result = await execute_command(working_path=workspace_path, command="npm init -y")
    assert is_ok(result)
    assert (workspace_path / Path("package.json")).exists()

    # Create server.js
    await create_test_file(
        Path(workspace_path).resolve() / "server.js",
        """const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.get('/', (req, res) => {
res.send('Hello World!');
});

app.listen(port, () => {
console.log(`Server running on port ${port}`);
});""",
    )
    assert (workspace_path / Path("server.js")).exists()

    # Install express
    result = await execute_command(
        working_path=workspace_path, command="npm install express"
    )
    assert is_ok(result)
    assert (workspace_path / Path("node_modules/express")).exists()

    # Create README and .gitignore
    await create_test_file(
        Path(workspace_path).resolve() / "README.md",
        "# Node.js Express Server\n\nSimple Express.js server.\n\n## Setup\n\n1. npm install\n2. node server.js",
    )
    await create_test_file(
        Path(workspace_path).resolve() / ".gitignore",
        "node_modules\n.env\n.DS_Store",
    )

    # Initialize git
    result = await execute_command(working_path=workspace_path, command="git init")
    assert is_ok(result)
    assert (workspace_path / Path(".git")).exists()


@pytest.mark.asyncio
async def test_process_cleanup_edge_cases(dev_agent: TestInfo) -> None:
    """Test process cleanup edge cases with real processes."""
    workspace_path = dev_agent.dev_agent.workspace_path

    # Test process that ignores SIGTERM
    script_path = workspace_path / "ignore_sigterm.sh"
    await create_test_file(
        script_path,
        """#!/bin/bash
trap "" SIGTERM
while true; do
    sleep 0.1
done""",
    )
    os.chmod(script_path, 0o755)

    # Process that ignores SIGTERM should be SIGKILL'd
    result = await execute_command(
        working_path=workspace_path,
        command="./ignore_sigterm.sh",
        process_timeout=0.5,
    )
    assert is_err(result)
    match result:
        case Err(error=err):
            assert "timed out" in err
        case Ok(_):
            pytest.fail("Expected error result")

    # Test process that can't be killed (requires root)
    result = await execute_command(
        working_path=workspace_path,
        command="sudo -n chattr +i file.txt 2>/dev/null || true",  # Will fail without root, which is fine
        process_timeout=0.5,
    )
    assert is_ok(result)

    # Test process that exits during cleanup
    script_path = workspace_path / "exit_during_cleanup.sh"
    await create_test_file(
        script_path,
        """#!/bin/bash
trap "exit 0" SIGTERM
while true; do
    sleep 0.1
done""",
    )
    os.chmod(script_path, 0o755)

    result = await execute_command(
        working_path=workspace_path,
        command="./exit_during_cleanup.sh",
        process_timeout=0.5,
    )
    assert is_err(result)
    match result:
        case Err(error=err):
            assert "timed out" in err
        case Ok(_):
            pytest.fail("Expected error result")


@pytest.mark.asyncio
async def test_command_with_large_output(dev_agent: TestInfo) -> None:
    """Test command execution with large output."""
    workspace_path = dev_agent.dev_agent.workspace_path

    # Generate large output
    result = await execute_command(
        working_path=workspace_path,
        command="dd if=/dev/zero bs=1M count=10 2>/dev/null | base64",
        process_timeout=2,
    )
    assert is_ok(result)
    assert len(unwrap(result).message) > 1000000  # noqa: PLR2004


@pytest.mark.asyncio
async def test_command_with_unicode_output(dev_agent: TestInfo) -> None:
    """Test command execution with Unicode output."""
    workspace_path = dev_agent.dev_agent.workspace_path

    # Test various Unicode outputs
    unicode_tests = [
        "echo '🚀'",  # Emoji
        "echo '∑∏∫'",  # Math symbols
        "echo '你好世界'",  # Chinese
        "echo 'Привет мир'",  # Russian
        "echo '안녕하세요'",  # Korean
    ]

    for cmd in unicode_tests:
        result = await execute_command(
            working_path=workspace_path,
            command=cmd,
        )
        assert is_ok(result)
        assert unwrap(result).message.strip() != ""


@pytest.mark.asyncio
async def test_command_with_environment_vars(dev_agent: TestInfo) -> None:
    """Test command execution with environment variables."""
    workspace_path = dev_agent.dev_agent.workspace_path

    # Test environment variable handling
    result = await execute_command(
        working_path=workspace_path,
        command="TEST_VAR='Hello World' bash -c 'echo $TEST_VAR'",
    )
    assert is_ok(result)
    assert "Hello World" in unwrap(result).message

    # Test PATH inheritance
    result = await execute_command(
        working_path=workspace_path,
        command="echo $PATH",
    )
    assert is_ok(result)
    assert unwrap(result).message.strip() != ""


@pytest.mark.asyncio
async def test_command_with_shell_features(dev_agent: TestInfo) -> None:
    """Test command execution with various shell features."""
    workspace_path = dev_agent.dev_agent.workspace_path

    # Test command with pipes
    result = await execute_command(
        working_path=workspace_path,
        command="echo 'hello world' | tr 'a-z' 'A-Z'",
    )
    assert is_ok(result)
    assert "HELLO WORLD" in unwrap(result).message

    # Test command with redirection
    result = await execute_command(
        working_path=workspace_path,
        command="echo 'test' > test.txt && cat test.txt",
    )
    assert is_ok(result)
    assert "test" in unwrap(result).message

    # Test command with background processes
    result = await execute_command(
        working_path=workspace_path,
        command="(sleep 0.1 & echo 'immediate') && sleep 0.2",
    )
    assert is_ok(result)
    assert "immediate" in unwrap(result).message
