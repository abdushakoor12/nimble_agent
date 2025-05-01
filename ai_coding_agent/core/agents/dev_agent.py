"""Development Agent for AI-powered coding assistance.

This module implements the core development agent that uses LangChain and OpenAI
to provide intelligent coding assistance. The agent can execute system commands,
manage files, and maintain conversation context across workspace interactions.

The agent is responsible for maintaining state and passing values to the tools.
Tools should not maintain state. Their functions should be pure functions.
In particular the agent should maintain the current directory relative to the
workspace root.

Temperature should be on the Agent OR the execute call
but not both. The temperate should be passed however
LangChain expects it.

"""

import asyncio
import inspect
import uuid
from pathlib import Path
from typing import Any, Final, TypeVar

from langchain.agents import AgentExecutor  # type: ignore
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool, StructuredTool
from langchain_openai import ChatOpenAI

from ai_coding_agent.core.agents.dev_agent_callbacks import LLMDebugHandler
from ai_coding_agent.core.agents.dev_agent_functions import (
    create_agent,
    create_agent_executor,
    get_prompt_template,
)
from ai_coding_agent.core.agents.notes_list import NotesList
from ai_coding_agent.core.constants import (
    DEFAULT_COMMAND_TIMEOUT,
    DEFAULT_GPT_MODEL,
    DEFAULT_MAXITERATIONS,
    DEFAULT_TEMPERATURE,
    ERROR_MESSAGE_DIRECTORY_CHANGE_FAILED,
    ERROR_MESSAGE_NAVIGATE_OUTSIDE_WORKSPACE,
    ERROR_MESSAGE_TARGET_DIRECTORY_NOT_EXIST,
    ERROR_MESSAGE_TARGET_NOT_DIRECTORY,
    ERROR_MESSAGE_TARGET_PATH_INVALID_CHARACTER,
    ERROR_MESSAGE_UNQUALIFIED_PATH,
    ERROR_MESSAGE_WORKSPACE_DOT_NOT_EXIST,
    ERROR_MESSAGE_WORKSPACE_NOT_ABSOLUTE,
    ERROR_MESSAGE_WORKSPACE_NOT_DIRECTORY,
    ROOT_RELATIVE_PATH,
)
from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import Err, Ok, Result, TaskOutput
from ai_coding_agent.core.tools import command_functions, file_functions
from ai_coding_agent.core.tools.file_functions import is_path_in_workspace
from ai_coding_agent.core.tools.result_types import TaskResult
from ai_coding_agent.core.tools.tool_schemas import (
    ChangeDirectorySchema,
    ExecuteCommandSchema,
    ListDirectoryContentSchema,
    ReadFileSchema,
    WriteFileSchema,
    WriteNoteSchema,
)

# Configure our logger
logger: Final = get_logger(__name__)

T = TypeVar("T")


class DevAgent:
    """The main actor."""

    current_dir: Path
    tools: list[BaseTool]
    chain: AgentExecutor | None
    chat_history: ChatMessageHistory
    current_task: str
    workspace_path: Path
    max_iterations: int
    iteration: int
    notes: NotesList
    llm_debug_handler: LLMDebugHandler
    llm: ChatOpenAI

    def __init__(
        self,
        workspace_path: Path,
        model: str = DEFAULT_GPT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_iterations: int = DEFAULT_MAXITERATIONS,
    ):
        """Initialize the development agent.

        Args:
            workspace_path: Path to the workspace directory. Must be absolute.
            model: Name of the OpenAI model to use
            temperature: Temperature parameter for the model
            max_iterations: Maximum number of iterations for task execution

        Raises:
            ValueError: If workspace_path does not exist or is not a directory
        """
        self.workspace_path = workspace_path
        if not self.workspace_path.is_absolute():
            raise ValueError(ERROR_MESSAGE_WORKSPACE_NOT_ABSOLUTE)
        if not self.workspace_path.is_dir():
            raise ValueError(ERROR_MESSAGE_WORKSPACE_NOT_DIRECTORY)
        if not self.workspace_path.exists():
            raise ValueError(ERROR_MESSAGE_WORKSPACE_DOT_NOT_EXIST)

        self.current_dir = Path(ROOT_RELATIVE_PATH)
        self.max_iterations = max_iterations
        self.iteration = 0
        self.notes = NotesList()
        self.llm_debug_handler = LLMDebugHandler()
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            callbacks=[self.llm_debug_handler],
        )
        self.tools = self._get_tools()
        self.chain = None
        self.chat_history = ChatMessageHistory()
        self.current_task = ""
        self.current_acceptance_criteria = ""

        self.notes.set_item("current_dir", str(self.current_dir))

    def _get_tools(self) -> list[BaseTool]:
        """Get the tools available to the agent."""
        execute_command_tool = StructuredTool.from_function(
            coroutine=self.execute_command,
            name="execute_command",
            description="Execute a command in the workspace",
            args_schema=ExecuteCommandSchema,
        )

        write_file_tool = StructuredTool.from_function(
            func=lambda filename, content, note_key=None, note_value=None: asyncio.run(
                self._write_file(filename, content, note_key, note_value)
            ),
            name="write_file",
            description="Write content to a file in the workspace",
            args_schema=WriteFileSchema,
        )

        read_file_tool = StructuredTool.from_function(
            func=lambda filename: str(
                asyncio.run(
                    file_functions.read_file(
                        Path(self.get_full_current_dir_path() / filename).resolve()
                    )
                )
            ),
            name="read_file",
            description="Read content from a file in the workspace",
            args_schema=ReadFileSchema,
        )

        list_directory_content_tool = StructuredTool.from_function(
            func=lambda: str(
                asyncio.run(
                    file_functions.list_directory_content(
                        directory_path=self.get_full_current_dir_path(),
                    )
                )
            ),
            name="list_directory_content",
            description="List files and folders in the workspace or a subdirectory",
            args_schema=ListDirectoryContentSchema,
        )

        change_directory_tool = StructuredTool.from_function(
            func=lambda target_dir=ROOT_RELATIVE_PATH: str(
                self.change_directory(Path(target_dir))
            ),
            name="change_directory",
            description="Change the current working directory",
            args_schema=ChangeDirectorySchema,
        )

        write_note_tool = StructuredTool.from_function(
            func=self.write_note,
            name="write_note",
            description="Give yourself a note for further operations later. These notes persist across tasks and sessions. You can overwrite them and they each have a key",
            args_schema=WriteNoteSchema,
        )

        return [
            execute_command_tool,
            write_file_tool,
            read_file_tool,
            list_directory_content_tool,
            change_directory_tool,
            write_note_tool,
        ]

    # Tool methods -----------

    async def execute_command(
        self,
        command: str,
        timeout: float = DEFAULT_COMMAND_TIMEOUT,  # noqa: ASYNC109
    ) -> str:
        """Execute a command in the workspace."""
        result = await command_functions.execute_command(
            working_path=self.get_full_current_dir_path(),
            command=command,
            process_timeout=timeout,
        )

        match result:
            case Ok(value=cd):
                return f"Success: {cd.message}"
            case Err(error=err):
                return f"Error: {err}"

    def get_full_current_dir_path(self):
        """Get the full path to the current working directory safely."""
        return self.resolve_with_workspace(self.current_dir)

    def resolve_with_workspace(self, target_path: Path):
        """Resolve a path relative to the workspace root."""
        if str(target_path) == "/":
            return self.workspace_path
        else:
            return Path(self.workspace_path / target_path).resolve()

    async def _write_file(
        self,
        filename: str,
        content: str,
        note_key: str | None = None,
        note_value: str | None = None,
    ) -> str:
        """Write content to a file, checking workspace boundaries."""
        if note_key is not None and note_value is not None:
            self.notes.set_item(note_key, note_value)
        full_path = Path(self.get_full_current_dir_path() / filename).resolve()
        if not is_path_in_workspace(
            workspace_path=self.workspace_path, file_path=full_path
        ):
            logger.error(
                "Error: Cannot write file outside workspace: %(path)s",
                {"path": full_path},
            )
            return "Error: Cannot write file outside workspace"
        return str(await file_functions.write_file(filepath=full_path, content=content))

    # Private methods -----------

    def _create_agent_executor(self) -> Any:
        """Create the AgentExecutor with an agent that has a prompt using LCEL. This only happens once unless there is a retry necessary."""
        prompt = get_prompt_template()

        agent = create_agent(
            llm=self.llm,
            prompt=prompt,
            tools=self.tools,
        )

        return create_agent_executor(
            agent=agent,
            tools=self.tools,
            max_iterations=self.max_iterations,
            callbacks=[self.llm_debug_handler],
        )

    # Note: this mutates state

    async def _summarize_messages(self) -> None:
        """Summarize the chat history to save on context."""
        summary_prompt = """Summarize the conversation so far in a few paragraphs, focusing on:
1. What has been completed
2. What is currently in progress
3. Any important context needed
4. Anything that went wrong
5. Directives for the next steps"""

        # Get summary from LLM
        messages = list(self.chat_history.messages)
        summary_msg = await self.llm.apredict(
            summary_prompt
            + "\n\nSummarized Conversation:\n"
            + "\n".join(str(m) for m in messages)
        )

        # Create new history with task context and summary
        self.chat_history = ChatMessageHistory(
            messages=[SystemMessage(content=summary_msg)]
        )

        logger.info(f"Summarized chat history into: {summary_msg}")

    # Public methods -----------

    def change_directory(self, target_dir: Path) -> Result[str, str]:  # noqa: PLR0911
        """Change the current working directory. target_dir must be a relative path within the workspace."""
        try:
            # Handle root directory cases
            if str(target_dir) in ("", ROOT_RELATIVE_PATH, "."):
                self.set_current_dir(Path(ROOT_RELATIVE_PATH))
                return Ok("Successfully changed directory to root (/)")

            # Check for invalid characters
            if "\0" in str(target_dir):
                logger.error("Error: There is an invalid character in the path")
                return Err(ERROR_MESSAGE_TARGET_PATH_INVALID_CHARACTER)

            # Resolve the target directory relative to workspace
            target_path = self.resolve_with_workspace(target_dir)

            if not target_path.is_dir():
                if (self.get_full_current_dir_path() / target_dir).resolve().is_dir():
                    logger.error(
                        "The agent attempted to navigate to directory without fully qualifying the path: %s",
                        target_dir,
                    )
                    return Err(
                        ERROR_MESSAGE_UNQUALIFIED_PATH.format(
                            target_dir=target_dir, current_dir=self.current_dir
                        )
                    )
                else:
                    logger.error(f"Error: {target_dir} is not a directory")
                    return Err(ERROR_MESSAGE_TARGET_NOT_DIRECTORY)

            # Check if target is within workspace
            if not str(target_path).startswith(str(self.workspace_path)):
                logger.error(
                    f"Error: cannot navigate outside workspace: Target: {target_path} Workspace: {self.workspace_path}"
                )
                return Err(ERROR_MESSAGE_NAVIGATE_OUTSIDE_WORKSPACE)

            if not target_path.exists():
                logger.error(f"Error: Directory does not exist: {target_path}")
                return Err(ERROR_MESSAGE_TARGET_DIRECTORY_NOT_EXIST)

            if not target_path.is_absolute():
                logger.error(f"Error: {target_path} is not an absolute path")
                return Err(ERROR_MESSAGE_WORKSPACE_NOT_ABSOLUTE)

            relative_path = target_path.relative_to(self.workspace_path)
            if relative_path == Path("."):
                relative_path = Path("/")

            self.set_current_dir(relative_path)
            return Ok(f"Successfully changed directory to {relative_path}")
        except Exception:
            logger.exception("Error changing directory")
            return Err(ERROR_MESSAGE_DIRECTORY_CHANGE_FAILED)

    def set_current_dir(self, value: Path):
        """Set the current directory and update the notes."""
        self.current_dir = value
        self.notes.set_item("current_dir", str(value))
        logger.info("Set current directory to: %(path)s", {"path": value})

    def write_note(self, note_key: str, note_value: str) -> str:
        """Write a note to the notes list."""
        self.notes.set_item(note_key, note_value)
        return "Successfully wrote note with key {note_key}"

    # ----------------

    async def go(
        self,
        task: str,
        acceptance_criteria: str | None = None,
    ) -> TaskResult:
        """Create an agent/executor, run the task and retry until successful or max retries is hit."""
        if task.strip() == "":
            return Err[TaskOutput, TaskOutput](
                TaskOutput(
                    output_message="Task failed: Task is empty", correlation_id=None
                )
            )

        # Generate a correlation ID and set up logging with it
        correlation_id = str(uuid.uuid4())
        log_filename = f"{correlation_id}.json"
        logger = get_logger(__name__, log_filename=log_filename)

        # Log the start of the task
        logger.debug(
            "Starting task: %(task_info)s",
            {
                "task_info": {
                    "correlation_id": correlation_id,
                    "task": task,
                    "acceptance_criteria": acceptance_criteria
                    if acceptance_criteria
                    else "Verify the objective was achieved in its entirety. Partial completeness is not acceptable.",
                }
            },
        )

        # Store task and acceptance criteria
        self.current_task = task

        # Create the agent and agent executor
        self.chain = self._create_agent_executor()

        # Prepare input data for logging and execution
        chain_input = {
            "input": task,
            "chat_history": self.chat_history.messages,
            "notes": self.notes.get_messages,
            "acceptance_criteria": acceptance_criteria
            if acceptance_criteria
            else "Verify the objective was achieved",
        }

        result = await self._invoke_agent(chain_input)

        match result:
            case Ok(value=output):
                logger.info(f"Task completed successfully: {output}")
                return Ok(
                    TaskOutput(correlation_id=correlation_id, output_message=output)
                )
            case Err(error=err):
                logger.error(f"Task failed with error: {err}")
                return Err(
                    TaskOutput(correlation_id=correlation_id, output_message=err)
                )

    async def _invoke_agent(self, chain_input) -> Result[str, str]:
        """Invoke the agent."""
        structured_input = {
            "input": chain_input.get("input", ""),
            "chat_history": [str(msg) for msg in chain_input.get("chat_history", [])],
            "notes": chain_input.get("notes", []),
            "acceptance_criteria": chain_input.get(
                "acceptance_criteria", "Verify the objective was achieved"
            ),
        }

        logger.info("Invoking Agent with input: %s", structured_input)

        # Execute the task
        if self.chain is None:
            return Err("Chain not initialized")

        result = await self.chain.ainvoke(structured_input)

        output = result.get("output", "")
        intermediate_steps = result.get("intermediate_steps", [])

        intermediate_step_message = []

        for tool_step, tool_result in intermediate_steps:
            if inspect.iscoroutine(tool_result):
                result = await tool_result
            else:
                result = str(tool_result)  # type:ignore[assignment]
            intermediate_step_message.append(
                {
                    "tool": tool_step.tool,
                    "input": tool_step.tool_input,
                    "result": result,
                }
            )

        logger.debug(
            "Agent invocation completed.\nSteps: %s\nOutput: %s",
            intermediate_step_message,
            output,
        )

        match output:
            case None:
                return Ok("")
            case str() if output.startswith("Task failed"):
                logger.error(f"Task failed with output: {output}")
                return Err(output)
            case str():
                return Ok(output)
            case _:
                logger.error(f"Unexpected result: {result}")
                return Err(f"Unexpected result: {result}")
