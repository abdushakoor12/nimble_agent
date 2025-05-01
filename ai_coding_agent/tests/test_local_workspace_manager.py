"""Tests for WorkspaceManager functionality.

Tests are organized by feature and use both real filesystem and mocked approaches
where appropriate.
"""

import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_coding_agent.core.local_workspace_manager import LocalWorkspaceManager
from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import Err, Ok, is_err

logger = get_logger(__name__)


@pytest.fixture
def base_path():
    """Provide a temporary base path for tests."""
    path = "/tmp/test_workspaces"
    os.makedirs(path, exist_ok=True)
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def workspace_manager(base_path) -> LocalWorkspaceManager:
    """Provide a WorkspaceManager instance."""
    return LocalWorkspaceManager(base_path=base_path)


@pytest.mark.asyncio
async def test_workspace_creation_success(workspace_manager: LocalWorkspaceManager):
    """Test successful workspace creation."""
    workspace_id = "test-workspace"
    result = await workspace_manager.create_workspace(workspace_id)
    match result:
        case Ok(value=workspace_path):
            assert os.path.exists(workspace_path)
            assert workspace_id in os.path.basename(workspace_path)
        case Err():
            pytest.fail("Expected Ok result")


@pytest.mark.asyncio
async def test_workspace_creation_duplicate(workspace_manager: LocalWorkspaceManager):
    """Test attempting to create a duplicate workspace."""
    workspace_id = "test-workspace"
    await workspace_manager.create_workspace(workspace_id)
    result = await workspace_manager.create_workspace(workspace_id)
    match result:
        case Ok(_):
            pytest.fail("Expected Err result")
        case Err(error=e):
            assert "already exists" in e


@pytest.mark.asyncio
async def test_workspace_path_retrieval(workspace_manager: LocalWorkspaceManager):
    """Test workspace path retrieval for existing and non-existing workspaces."""
    workspace_id = "test-workspace"
    workspace_result = await workspace_manager.create_workspace(workspace_id)
    match workspace_result:
        case Ok(value=workspace_path):
            assert workspace_manager.get_workspace_path(workspace_id) == str(
                Path(workspace_path).resolve()
            )
            assert workspace_manager.get_workspace_path("nonexistent") is None
        case Err():
            pytest.fail("Expected Ok result")


@pytest.mark.asyncio
async def test_workspace_deletion_nonexistent(workspace_manager: LocalWorkspaceManager):
    """Test deleting a non-existent workspace."""
    result = await workspace_manager.delete_workspace("nonexistent-workspace")
    assert is_err(result)
    match result:
        case Ok(_):
            pytest.fail("Expected Err result")
        case Err(error=e):
            assert "not found" in e


@pytest.mark.asyncio
async def test_workspace_deletion_success(workspace_manager: LocalWorkspaceManager):
    """Test successful workspace deletion."""
    workspace_id = "test-workspace"
    await workspace_manager.create_workspace(workspace_id)
    result = await workspace_manager.delete_workspace(workspace_id)
    match result:
        case Ok(value=success):
            assert success is True
            assert not os.path.exists(
                os.path.join(workspace_manager.base_path, workspace_id)
            )
        case Err():
            pytest.fail("Expected Ok result")


@pytest.mark.asyncio
async def test_workspace_creation_permission_error():
    """Test workspace creation with permission error."""
    base_path = "/tmp/test_workspaces"
    manager = LocalWorkspaceManager(base_path=base_path)

    with patch("pathlib.Path.mkdir", side_effect=PermissionError("Access denied")):
        result = await manager.create_workspace("error-workspace")
        assert is_err(result)
        match result:
            case Ok(_):
                pytest.fail("Expected Err result")
            case Err(error=e):
                assert "Failed to create workspace" in e


@pytest.mark.asyncio
async def test_workspace_deletion_permission_error(
    workspace_manager: LocalWorkspaceManager,
):
    """Test workspace deletion with permission error."""
    workspace_id = "test-workspace"
    await workspace_manager.create_workspace(workspace_id)

    with patch("shutil.rmtree", side_effect=PermissionError("Access denied")):
        result = await workspace_manager.delete_workspace(workspace_id)
        assert is_err(result)
        match result:
            case Ok(_):
                pytest.fail("Expected Err result")
            case Err(error=e):
                assert "Failed to delete workspace" in e
