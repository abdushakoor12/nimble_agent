"""Local workspace manager for the AI Coding Agent. Only concerned with the local disk."""

import shutil
from pathlib import Path
from uuid import uuid4

from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import Err, Ok
from ai_coding_agent.core.tools.result_types import BoolResult, StringResult

logger = get_logger(__name__)


class LocalWorkspaceManager:
    """Manages workspace directories on the local filesystem.

    Handles creation and cleanup of isolated workspace directories.
    Only concerned with filesystem operations, no metadata tracking.
    """

    def __init__(self, base_path: str):
        """Initialize workspace manager with base directory for all workspaces.

        Args:
            base_path: Root directory where all workspaces will be created
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def create_workspace(self, workspace_id: str | None = None) -> StringResult:
        """Create new workspace with isolated directory.

        Args:
            workspace_id: Optional unique identifier for workspace. If not provided, a UUID will be generated.

        Returns:
            Result containing the workspace path on success, or error message on failure
        """
        logger.info(f"Creating workspace with ID: {workspace_id}")
        try:
            if workspace_id is None:
                workspace_id = uuid4().hex
                logger.debug(f"Generated workspace ID: {workspace_id}")

            workspace_path = self.base_path / workspace_id
            if workspace_path.exists():
                logger.error(f"Workspace directory {workspace_path} already exists")
                return Err(f"Workspace directory {workspace_path} already exists")

            logger.debug(f"Creating workspace directory at: {workspace_path}")
            workspace_path.mkdir(parents=True, exist_ok=True)
            workspace_path = workspace_path.resolve()
            logger.debug(f"Resolved workspace path: {workspace_path}")

            return Ok(str(workspace_path))
        except Exception as e:
            logger.exception("Failed to create workspace", exc_info=True)
            return Err(f"Failed to create workspace: {e!s}")

    async def delete_workspace(self, workspace_id: str) -> BoolResult:
        """Delete a workspace directory and its contents.

        Args:
            workspace_id: The ID of the workspace to delete

        Returns:
            Result indicating success or error message
        """
        try:
            workspace_path = self.base_path / workspace_id
            if not workspace_path.exists():
                return Err(f"Workspace directory {workspace_path} not found")

            shutil.rmtree(workspace_path)
            return Ok(True)
        except Exception as e:
            return Err(f"Failed to delete workspace: {e!s}")

    def get_workspace_path(self, workspace_id: str) -> str | None:
        """Get path for existing workspace.

        Args:
            workspace_id: Workspace identifier

        Returns:
            Path to workspace directory if exists, None otherwise
        """
        workspace_path = (self.base_path / workspace_id).resolve()
        return str(workspace_path) if workspace_path.exists() else None
