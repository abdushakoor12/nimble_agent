"""Functions used to create agents."""

import platform
import sys
from typing import Any

from langchain.agents import (
    AgentExecutor,
    create_openai_functions_agent,  # type: ignore
)
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

# Get detailed system information
SYSTEM_INFO = f"""Operating System: {platform.system()}\n
OS Version: {platform.version()}\n
OS Release: {platform.release()}\n
Architecture: {platform.machine()}\n
Python Version: {platform.python_version()}\n
Platform: {sys.platform}\n
"""

TASK_MESSAGE = """You are an agent that assists with software development tasks. This prompt is in importance order. The most important directives are at the top, and the bottom is informational content.

Objective: {input}

Note: the objective may already be complete. Perform checks to determine if you need to do anything.

Acceptance Criteria:
{acceptance_criteria}

Critical Rules:
- Don't stop until the objective is complete in its entirety, even if you encounter errors
- If there is acceptance criteria, you must verify it and not stop until it passes
- You MUST include the results of the step you used to verify the acceptance criteria in the last step

Critical Path Navigation Rules
1. ALWAYS use full paths relative to workspace root (e.g. 'app/src/lib')
2. NEVER use '..' or '.' in paths
Remember, paths are virtual paths relative to the workspace root that you can't see.

Example: If you're in 'lib/src' and want to go to 'lib/test':
   - WRONG: cd ../test
   - RIGHT: cd lib/test

Example: If you're in 'lib/src' and want to go to root:
   - WRONG: cd ../..
   - RIGHT: cd /

Example: When given multiple directory steps, you MUST use the full path. Example:
   - Task: "Go to folder1 then folder2"
   - WRONG: First cd folder1, then cd folder2
   - RIGHT: cd folder1/folder2

Guidelines:
1. Don't include unnecessary information in your responses, particularly large slabs of code. Keep responses concise and to the point.
2. Use the toolkit's standard CLI tool to create the project. Don't try to create the project by writing all files manually.
3. If you're running a command, give it at least 20 seconds to finish before timeout.
"""


def get_prompt_template() -> ChatPromptTemplate:
    """Get the prompt template for the agent.

    Args:
        system_message: The system message to use in the prompt.

    Returns:
        The prompt template.
    """
    return ChatPromptTemplate.from_messages(
        [
            HumanMessagePromptTemplate.from_template(
                TASK_MESSAGE,
            ),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            SystemMessage(content=SYSTEM_INFO),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            MessagesPlaceholder(variable_name="notes"),
        ],
    )


def create_agent(
    llm: ChatOpenAI,
    prompt: ChatPromptTemplate,
    tools: list[BaseTool],
) -> Any:
    """Create the tools capable agent. Currently only OpenAI, but will be extended to other providers in the future.

    Args:
        llm: The language model to use.
        prompt: The prompt template.
        tools: The tools available to the agent.

    Returns:
        The OpenAI functions agent.
    """
    return create_openai_functions_agent(
        llm=llm,
        prompt=prompt,
        tools=tools,
    )


def create_agent_executor(
    agent: Any,
    tools: list[BaseTool],
    max_iterations: int,
    callbacks: list[BaseCallbackHandler],
) -> AgentExecutor:
    """Create the agent executor.

    Args:
        agent: The agent to execute.
        tools: The tools available to the agent.
        max_iterations: Maximum number of iterations.
        callbacks: Callback handlers.

    Returns:
        The agent executor.
    """
    return AgentExecutor(
        agent=agent,
        tools=tools,
        handle_parsing_errors=True,
        max_iterations=max_iterations,
        return_intermediate_steps=True,
        verbose=True,
        max_execution_time=300,  # 5 minutes max per attempt
        early_stopping_method="force",
        callbacks=callbacks,
    )
