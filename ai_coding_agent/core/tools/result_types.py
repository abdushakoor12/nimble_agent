"""Base classes and result types for AI Coding Agent tools.

This module provides the foundational classes and result types used across
all tool implementations. It defines the base async tool class and various
result objects used to represent operation outcomes.

Result types should be monadic ADTs that encapsulate the outcome of an operation
"""

from dataclasses import dataclass
from pathlib import Path

from langchain_core.tools import BaseTool

from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import Result, TaskOutput

# Configure logging
logger = get_logger(__name__)


@dataclass
class CommandData:
    """Data class for command execution results."""

    message: str
    working_path: str


@dataclass
class DirectoryData:
    """Data class for directory operation results."""

    message: str
    new_directory: str
    current_directory: str


@dataclass
class DirectoryStateData:
    """Data class for directory state results."""

    directory: str


@dataclass
class FileData:
    """Data class for file operation results."""

    content: str = ""
    message: str = ""


@dataclass
class DirectoryContentData:
    """Data class for directory content results."""

    files: list[str]
    folders: list[str]


@dataclass
class ToolOperationData:
    """Data class for tool operation results."""

    tools: list["BaseTool"]
    message: str = ""


# Type aliases for common Result types
CommandResult = Result[CommandData, str]
DirectoryResult = Result[DirectoryData, str]
PathResult = Result[Path, str]
DirectoryStateResult = Result[DirectoryStateData, str]
FileResult = Result[FileData, str]
DirectoryContentResult = Result[DirectoryContentData, str]
ToolOperationResult = Result[ToolOperationData, str]
StringResult = Result[str, str]
BoolResult = Result[bool, str]
TaskResult = Result[TaskOutput, TaskOutput]
