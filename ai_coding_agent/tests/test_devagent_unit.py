"""End-to-end tests for AI Coding Agent."""

import os
from pathlib import Path

import pytest
from langchain_core.messages import SystemMessage

from ai_coding_agent.core.agents.dev_agent import DevAgent
from ai_coding_agent.core.constants import (
    DEFAULT_GPT_MODEL,
    DEFAULT_MAXITERATIONS,
    DEFAULT_TEMPERATURE,
    ERROR_MESSAGE_TARGET_NOT_DIRECTORY,
    ERROR_MESSAGE_TARGET_PATH_INVALID_CHARACTER,
    ERROR_MESSAGE_WORKSPACE_NOT_ABSOLUTE,
)
from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import Err, Ok, is_err, is_ok, unwrap
from ai_coding_agent.tests.conftest import TestInfo
from ai_coding_agent.tests.test_functions import create_test_file, get_directory

logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_dev_agent_initialization(workspace: tuple[str, str]) -> None:
    """Test DevAgent initialization with various parameters."""
    _, workspace_base_path = workspace

    dev_agent = DevAgent(
        workspace_path=Path(workspace_base_path),
    )

    # Test default parameters from fixture
    assert dev_agent.llm.model_name == DEFAULT_GPT_MODEL
    assert dev_agent.llm.temperature == DEFAULT_TEMPERATURE
    assert dev_agent.max_iterations == DEFAULT_MAXITERATIONS
    assert isinstance(dev_agent.workspace_path, Path)

    # Test with custom parameters
    custom_model = "gpt-3.5-turbo"
    custom_temp = 0.8
    custom_agent = DevAgent(
        workspace_path=dev_agent.workspace_path,
        model=custom_model,
        temperature=custom_temp,
    )
    assert custom_agent.llm.model_name == custom_model
    assert custom_agent.llm.temperature == custom_temp
    assert isinstance(custom_agent.workspace_path, Path)


@pytest.mark.asyncio
async def test_dev_agent_invalid_workspace() -> None:
    """Test DevAgent initialization with invalid workspace."""
    with pytest.raises(ValueError, match=ERROR_MESSAGE_WORKSPACE_NOT_ABSOLUTE):
        DevAgent(workspace_path=Path("invalid_path"))


@pytest.mark.asyncio
async def test_dev_agent_create_chain(dev_agent: TestInfo) -> None:
    """Test DevAgent chain creation."""
    agent = dev_agent.dev_agent
    chain = agent._create_agent_executor()
    assert chain is not None
    assert chain.agent is not None
    assert chain.tools == agent.tools
    assert chain.max_iterations == agent.max_iterations


@pytest.mark.asyncio
async def test_directory_operations_and_errors(dev_agent: TestInfo):
    """Test directory operations and error handling."""
    agent = dev_agent.dev_agent
    workspace_path = str(agent.workspace_path)

    # Create test directories
    test_dirs = ["test", "test/subdir", "dir1/dir2"]
    for d in test_dirs:
        os.makedirs(os.path.join(workspace_path, d), exist_ok=True)

    # Test change_directory with invalid paths
    result = agent.change_directory(target_dir=Path("../invalid"))
    assert is_err(result)
    match result:
        case Err(error=err):
            assert ERROR_MESSAGE_TARGET_NOT_DIRECTORY in err
        case Ok(_):
            pytest.fail("Expected error result")

    result = agent.change_directory(Path("nonexistent"))
    assert is_err(result)
    match result:
        case Err(error=err):
            assert ERROR_MESSAGE_TARGET_NOT_DIRECTORY in err
        case Ok(_):
            pytest.fail("Expected error result")

    # Test get_directory with invalid workspace path
    get_dir_result = await get_directory("/nonexistent/path")
    match get_dir_result:
        case Err(error=err):
            assert "Workspace path does not exist" in err
        case Ok(_):
            pytest.fail("Expected error result")

    # Test get_directory with current_dir outside workspace
    get_dir_result = await get_directory(workspace_path, "../outside")

    match get_dir_result:
        case Ok(value=x):
            assert x.directory == "../outside"
        case Err(error=err):
            pytest.fail(f"Expected Ok result, got error: {err}")


@pytest.mark.asyncio
async def test_directory_operations_edge_cases(dev_agent: TestInfo):  # noqa: PLR0915, C901
    """Test directory operations edge cases."""
    agent = dev_agent.dev_agent
    workspace_path = str(agent.workspace_path)

    # Test root directory handling
    result = agent.change_directory(Path("/"))
    assert is_ok(result)
    assert unwrap(result) == "Successfully changed directory to root (/)"

    result = agent.change_directory(Path(""))
    assert is_ok(result)
    assert unwrap(result) == "Successfully changed directory to root (/)"

    # Test current directory handling
    result = agent.change_directory(target_dir=Path("existing_dir"))
    assert is_err(result)
    match result:
        case Err(error=err):
            assert ERROR_MESSAGE_TARGET_NOT_DIRECTORY in err
        case Ok(_):
            pytest.fail("Expected error result")

    # Create a file to test not-a-directory error
    await create_test_file(
        Path(workspace_path).resolve() / "testfile.txt",
        "content",
    )
    result = agent.change_directory(Path("testfile.txt"))
    assert is_err(result)
    match result:
        case Err(error=err):
            assert ERROR_MESSAGE_TARGET_NOT_DIRECTORY in err
        case Ok(_):
            pytest.fail("Expected error result")

    # Test invalid path
    result = agent.change_directory(Path("\0invalid"))
    assert is_err(result)
    match result:
        case Err(error=err):
            assert ERROR_MESSAGE_TARGET_PATH_INVALID_CHARACTER in err
        case Ok(_):
            pytest.fail("Expected error result")

    # Test get_directory with invalid workspace
    get_dir_result = await get_directory("/nonexistent/path")
    match get_dir_result:
        case Err(error=err):
            assert "Workspace path does not exist" in err
        case Ok(_):
            pytest.fail("Expected error result")

    # Test get_directory with file instead of directory
    file_path = Path(workspace_path) / "not_a_dir.txt"
    await create_test_file(file_path, "content")
    get_dir_result = await get_directory(Path(workspace_path) / "not_a_dir.txt")
    match get_dir_result:
        case Err(error=err):
            assert "not a directory" in err
        case Ok(_):
            pytest.fail("Expected error result")

    # Test get_directory with invalid path
    get_dir_result = await get_directory("\0invalid")
    match get_dir_result:
        case Err(error=err):
            assert "Workspace path does not exist" in err
        case Ok(_):
            pytest.fail("Expected error result")


@pytest.mark.asyncio
async def test_invoke_agent_success(dev_agent: TestInfo) -> None:
    """Test successful invocation of invoke_agent."""
    agent = dev_agent.dev_agent
    # Create a chain that will return a simple success message
    agent.chain = agent._create_agent_executor()

    # TODO: move this into a method of DevAgent
    chain_input = {
        "input": "Echo test message",
        "acceptance_criteria": "Message should be echoed",
        "chat_history": agent.chat_history.messages,
        "notes": agent.notes.get_messages,
    }

    # Call invoke_agent
    result = await agent._invoke_agent(chain_input)

    # Verify success
    assert is_ok(result), "Expected successful result"
    output = unwrap(result)
    logger.info(f"Output: {output}")
    assert isinstance(output, str), "Expected string output"


@pytest.mark.asyncio
async def test_invoke_agent_failure(dev_agent: TestInfo) -> None:
    """Test failure handling in invoke_agent."""
    agent = dev_agent.dev_agent
    # Set chain to None to trigger error
    agent.chain = None

    # Prepare input data
    chain_input = {
        "input": "This should fail",
        "acceptance_criteria": "This should fail",
        "chat_history": agent.chat_history.messages,
    }

    # Call invoke_agent and verify it returns an error result
    result = await agent._invoke_agent(chain_input)
    assert is_err(result), "Expected error result"
    match result:
        case Err(error=err):
            assert err == "Chain not initialized"
        case Ok(_):
            pytest.fail("Expected error result")


@pytest.mark.asyncio
async def test_dev_agent_summarize_messages(dev_agent: TestInfo) -> None:
    """Test DevAgent message summarization."""
    agent = dev_agent.dev_agent
    # Add some test messages
    original_messages = [
        "First message",
        "First response",
        "Second message",
        "Second response",
    ]
    agent.chat_history.add_user_message(original_messages[0])
    agent.chat_history.add_ai_message(original_messages[1])
    agent.chat_history.add_user_message(original_messages[2])
    agent.chat_history.add_ai_message(original_messages[3])

    initial_message_count = len(agent.chat_history.messages)
    assert initial_message_count > 0

    # Summarize messages
    await agent._summarize_messages()

    # Verify that messages were summarized
    assert len(agent.chat_history.messages) == 1
    assert isinstance(agent.chat_history.messages[0], SystemMessage)
    summary = agent.chat_history.messages[0].content
    assert isinstance(summary, str)

    # Use LLM to verify the summary quality
    verification_prompt = f"""Given these original messages:
{original_messages}

And this summary:
{summary}

Is this a good summary that captures the key points of the conversation? Answer with just 'yes' or 'no' with no full stop."""

    verification = await agent.llm.apredict(verification_prompt)
    assert (
        verification.lower().strip() == "yes"
    ), f"Summary quality check failed. LLM response: {verification}"


@pytest.mark.asyncio
async def test_dev_agent_notes(dev_agent: TestInfo) -> None:
    """Test DevAgent notes functionality."""
    agent = dev_agent.dev_agent
    # Test initial state
    assert agent.notes is not None
    assert "current_dir" in agent.notes.get_messages[0].content

    # Test setting and getting notes
    agent.notes.set_item("test_key", "test_value")
    messages = agent.notes.get_messages
    second_message_content = messages[1].content
    assert (  # noqa: PT018
        "test_key" in second_message_content and "test_value" in second_message_content
    )

    # Test overwriting existing note
    agent.notes.set_item("test_key", "new_value")
    messages = agent.notes.get_messages
    second_message_content = messages[1].content
    assert (  # noqa: PT018
        "test_key" in second_message_content and "new_value" in second_message_content
    )


@pytest.mark.asyncio
async def test_dev_agent_tools_initialization(dev_agent: TestInfo) -> None:
    """Test DevAgent tools initialization."""
    agent = dev_agent.dev_agent
    # Verify all required tools are present
    tool_names = {tool.name for tool in agent.tools}
    required_tools = {
        "execute_command",
        "write_file",
        "read_file",
        "list_directory_content",
        "change_directory",
    }
    assert required_tools.issubset(
        tool_names
    ), f"Missing tools: {required_tools - tool_names}"

    # Verify tool properties
    for tool in agent.tools:
        assert tool.name is not None
        assert tool.description is not None
        func = getattr(tool, "func", None)
        coroutine = getattr(tool, "coroutine", None)

        if func is not None:
            assert coroutine is None
            assert callable(func)
        else:
            assert coroutine is not None
            assert callable(coroutine)
