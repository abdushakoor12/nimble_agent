"""Tests for toolkit functions and tools.

This set of tests uses the tools with mocks only. It doesn't
physically touch the filesystem or processes.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool, StructuredTool
from langchain_openai import ChatOpenAI

from ai_coding_agent.core.agents.dev_agent import DevAgent
from ai_coding_agent.core.agents.dev_agent_functions import (
    create_agent,
    create_agent_executor,
    get_prompt_template,
)
from ai_coding_agent.core.constants import (
    DEFAULT_GPT_MODEL,
    DEFAULT_MAXITERATIONS,
    DEFAULT_TEMPERATURE,
    ERROR_MESSAGE_TARGET_PATH_INVALID_CHARACTER,
    ROOT_RELATIVE_PATH,
)
from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import Err, Ok, is_ok
from ai_coding_agent.core.tools.result_types import StringResult, TaskOutput
from ai_coding_agent.tests.test_functions import runtest

logger = get_logger(__name__)


@pytest.fixture
def mock_tool() -> BaseTool:
    """Create a mock tool for testing."""

    def mock_func(x: str) -> StringResult:  # noqa: ARG001
        return Ok("success")

    return StructuredTool.from_function(
        func=mock_func,
        name="mock_tool",
        description="A mock tool for testing",
    )


@pytest.fixture
def mock_llm() -> ChatOpenAI:
    """Create a mock LLM for testing."""
    return ChatOpenAI(model="gpt-3.5-turbo", temperature=0)


@pytest.mark.asyncio
async def test_dev_agent_error_handling():
    """Test DevAgent error handling and retry scenarios."""

    async def test_body(workspace_path: str):
        # Initialize agent
        agent = DevAgent(
            workspace_path=Path(workspace_path),
            model=DEFAULT_GPT_MODEL,
            temperature=DEFAULT_TEMPERATURE,
            max_iterations=3,
        )

        # Mock sleep to speed up tests
        async def mock_sleep(_):
            return

        # Mock both summarize_messages and sleep
        with (
            patch.object(agent, "_summarize_messages", return_value=None),
            patch("asyncio.sleep", mock_sleep),
        ):
            # Test task execution without retries
            with patch("langchain.agents.AgentExecutor.ainvoke") as mock_invoke:
                # First call fails with error message
                mock_invoke.side_effect = [
                    {"output": "Task failed: First attempt error"},
                    {"output": "Success!"},
                ]

                result = await agent.go(
                    "test task",
                    "test criteria",
                )
                match result:
                    case Ok():
                        pytest.fail("Expected error result")
                    case Err(error=e):
                        assert isinstance(e, TaskOutput)
                        assert e.output_message == "Task failed: First attempt error"

                # Test task execution with exception
                with patch(
                    "langchain.agents.AgentExecutor.ainvoke"
                ) as mock_invoke_exception:
                    mock_invoke_exception.side_effect = Exception("Test exception")
                    try:
                        result = await agent.go(
                            "test task",
                            "test criteria",
                        )
                        match result:
                            case Ok():
                                pytest.fail("Expected error result")
                            case Err(error=e):
                                assert str(e) == "Test exception"
                    except Exception as e:
                        assert (  # noqa: PT017
                            str(e) == "Test exception"
                        ), "Expected 'Test exception' to be raised"

    await runtest(test_body)


def test_get_prompt_template() -> None:
    """Test get_prompt_template function."""
    prompt = get_prompt_template()
    assert prompt is not None

    # Test that the prompt has the expected structure
    messages = prompt.messages
    assert len(messages) > 0
    assert any(isinstance(msg, SystemMessage) for msg in messages)

    # Test that the prompt includes key components
    prompt_str = str(prompt)
    assert "Objective: {input}" in prompt_str
    assert "Acceptance Criteria:" in prompt_str
    assert "Guidelines:" in prompt_str


def test_create_agent(mock_llm: ChatOpenAI, mock_tool: BaseTool) -> None:
    """Test create_agent function."""
    prompt = get_prompt_template()
    tools = [mock_tool]

    agent = create_agent(llm=mock_llm, prompt=prompt, tools=tools)

    assert agent is not None
    # Test essential agent functionality
    assert hasattr(agent, "invoke")
    assert hasattr(agent, "ainvoke")


def test_create_agent_executor(mock_llm: ChatOpenAI, mock_tool: BaseTool) -> None:
    """Test create_agent_executor function."""
    prompt = get_prompt_template()
    tools = [mock_tool]

    agent = create_agent(llm=mock_llm, prompt=prompt, tools=tools)
    executor = create_agent_executor(
        agent=agent,
        tools=tools,
        max_iterations=DEFAULT_MAXITERATIONS,
        callbacks=[],
    )

    max_execution_time = 300

    assert executor is not None
    # Test executor functionality instead of internal structure
    assert hasattr(executor, "invoke")
    assert hasattr(executor, "ainvoke")
    assert executor.max_iterations == DEFAULT_MAXITERATIONS
    assert executor.max_execution_time == max_execution_time
    assert executor.early_stopping_method == "force"


def test_change_directory_corner_cases(workspace: tuple[str, str]) -> None:  # noqa: PLR0912, C901, PLR0915
    """Test all corner cases for the change_directory method."""
    _, workspace_path = workspace
    agent = DevAgent(
        workspace_path=Path(workspace_path),
        model=DEFAULT_GPT_MODEL,
        temperature=DEFAULT_TEMPERATURE,
        max_iterations=3,
    )

    # Test root directory cases
    result = agent.change_directory(Path(ROOT_RELATIVE_PATH))
    assert is_ok(result)
    assert str(agent.current_dir) == ROOT_RELATIVE_PATH

    result = agent.change_directory(Path(""))
    assert is_ok(result)
    assert str(agent.current_dir) == ROOT_RELATIVE_PATH

    result = agent.change_directory(Path("."))
    assert is_ok(result)
    assert str(agent.current_dir) == ROOT_RELATIVE_PATH

    # Test invalid characters
    result = agent.change_directory(Path("test\0dir"))
    match result:
        case Ok():
            pytest.fail("Expected error result")
        case Err(error=e):
            assert e == ERROR_MESSAGE_TARGET_PATH_INVALID_CHARACTER

    # Test directory not found
    with patch.object(Path, "is_dir") as mock_is_dir:
        mock_is_dir.return_value = False
        result = agent.change_directory(Path("nonexistent"))
        match result:
            case Ok():
                pytest.fail("Expected error result")
            case Err(_):
                pass

    # Test unqualified path
    with (
        patch.object(Path, "is_dir") as mock_is_dir,
        patch.object(Path, "resolve") as mock_resolve,
    ):

        def is_dir_side_effect(path=None):  # noqa: ARG001
            return str(mock_is_dir._mock_self) == str(
                agent.get_full_current_dir_path() / "subdir"
            )

        mock_is_dir.side_effect = is_dir_side_effect
        mock_resolve.return_value = agent.get_full_current_dir_path() / "subdir"
        result = agent.change_directory(Path("subdir"))
        match result:
            case Ok():
                pytest.fail("Expected error result")
            case Err(_):
                pass

    # Test navigating outside workspace
    with (
        patch.object(Path, "resolve") as mock_resolve,
        patch.object(Path, "is_dir") as mock_is_dir,
    ):
        mock_resolve.return_value = Path("/outside/workspace")
        mock_is_dir.return_value = True
        result = agent.change_directory(Path("../outside"))
        match result:
            case Ok():
                pytest.fail("Expected error result")
            case Err(_):
                pass

    # Test directory does not exist
    with (
        patch.object(Path, "exists") as mock_exists,
        patch.object(Path, "is_dir") as mock_is_dir,
    ):
        mock_exists.return_value = False
        mock_is_dir.return_value = True
        result = agent.change_directory(Path("nonexistent"))
        match result:
            case Ok():
                pytest.fail("Expected error result")
            case Err(_):
                pass

    # Test non-absolute path
    with (
        patch.object(Path, "is_absolute") as mock_is_absolute,
        patch.object(Path, "is_dir") as mock_is_dir,
        patch.object(Path, "exists") as mock_exists,
    ):
        mock_is_absolute.return_value = False
        mock_is_dir.return_value = True
        mock_exists.return_value = True
        result = agent.change_directory(Path("relative"))
        match result:
            case Ok():
                pytest.fail("Expected error result")
            case Err(_):
                pass

    # Test exception handling
    with patch.object(Path, "resolve") as mock_resolve:
        mock_resolve.side_effect = Exception("Test error")
        result = agent.change_directory(Path("error"))
        match result:
            case Ok():
                pytest.fail("Expected error result")
            case Err(_):
                pass
