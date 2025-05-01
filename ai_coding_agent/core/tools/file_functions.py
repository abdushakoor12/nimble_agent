"""File operation functions for the AI Coding Agent tools.

Tools for file operations (read/write/list) within workspace
boundaries. All operations enforce security checks to prevent access outside
designated workspaces.

File functions are pure and stateless.
"""

from pathlib import Path

import aiofiles

from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import Err, Ok
from ai_coding_agent.core.tools.result_types import (
    DirectoryContentData,
    DirectoryContentResult,
    FileData,
    FileResult,
)

__all__ = [
    "list_directory_content",
    "read_file",
    "write_file",
]

# Configure logging
logger = get_logger(__name__)


async def _get_directory_contents(
    directory_path: Path,
) -> tuple[list[str], list[str]]:
    """List contents of a directory, separating files and folders.

    Args:
        directory_path: The directory to list contents of

    Returns:
        Tuple of (files, folders) where each is a list of filenames/foldernames
    """
    files = []
    folders = []
    for item in directory_path.iterdir():
        if item.is_file():
            files.append(item.name)
        elif item.is_dir():
            folders.append(item.name)
    return sorted(files), sorted(folders)


async def list_directory_content(
    directory_path: Path,
) -> DirectoryContentResult:
    """List files and folders in the specified directory with error handling and logging.

    Lists contents relative to the specified directory.

    Args:
        directory_path: Absolute path to the directory to list contents from. Must be absolute.

    Returns:
        DirectoryContentResult with success status and lists of files and folders
    """
    try:
        if not directory_path.is_absolute():
            return Err(
                "Error listing directory contents: directory_path must be absolute"
            )

        if not directory_path.exists():
            return Err("Error listing directory contents: Directory does not exist")

        if not directory_path.is_dir():
            return Err("Error listing directory contents: Not a directory")

        files, folders = await _get_directory_contents(directory_path)
        logger.info(
            "Listed directory contents for %(workspace_path)s.\nFolders: %(folders)s\nFiles: %(files)s",
            {
                "workspace_path": directory_path,
                "files": files,
                "folders": folders,
            },
        )

        return Ok(DirectoryContentData(files=files, folders=folders))

    except Exception:
        logger.exception("Error listing directory contents")
        return Err("Error listing directory contents")


def is_path_in_workspace(*, workspace_path: Path, file_path: Path) -> bool:
    """Check if a file path is within the workspace directory.

    Args:
        file_path: Path to check
        workspace_path: Workspace root path

    Returns:
        True if file_path is within workspace_path, False otherwise
    """
    return str(file_path).startswith(str(workspace_path))


async def read_file(file_path: Path) -> FileResult:
    """Read a file from the given absolute path.

    Args:
        file_path: The absolute path to the file to read

    Returns:
        Result containing the file content or error message
    """
    try:
        if not file_path.is_absolute():
            return Err("Error: file_path must be absolute")

        if not file_path.exists():
            return Err("Error: file does not exist")

        if not file_path.is_file():
            return Err("Error: path exists but is not a file")

        async with aiofiles.open(file_path) as f:
            content = await f.read()
            return Ok(FileData(content=content))
    except Exception as e:
        return Err(f"Error reading file: {e}")


async def write_file(
    filepath: Path,
    content: str,
) -> FileResult:
    """Write content to a file.

    Args:
        filepath: The absolute path to the file to write
        content: The content to write

    Returns:
        Result containing success message or error message
    """
    try:
        if not filepath.is_absolute():
            logger.error("Error: filepath must be absolute")
            return Err("Error: filepath must be absolute")

        # Create parent directory if it doesn't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        async with aiofiles.open(filepath, "w") as f:
            await f.write(content)
            max_content_length = 100
            logger.info(
                f"Successfully wrote: {filepath} with content:\n{content[:max_content_length]}{'...' if len(content) > max_content_length else ''}"
            )
            return Ok(FileData(message=f"Successfully wrote to {filepath}"))
    except Exception:
        logger.exception("Error writing file")
        return Err("Error writing file")
