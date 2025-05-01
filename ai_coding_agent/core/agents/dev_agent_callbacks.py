"""Callback handlers for the agent."""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.documents import Document
from langchain_core.outputs import LLMResult
from tenacity import RetryCallState

from ai_coding_agent.core.logger import get_logger

# Configure our logger
logger = get_logger(__name__)


def format_kwargs(kwargs: dict[str, object]) -> str:
    """Format kwargs for logging."""
    return "\n".join(f"{key}: {value}" for key, value in kwargs.items())


class LLMDebugHandler(BaseCallbackHandler):
    """Callback handler that logs the exact messages being sent to the LLM."""

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run when LLM starts running."""
        logger.info(
            "LLM Started.\nSerialized: %s\nPrompts: %s\nRun ID: %s\nParent Run ID: %s\nTags: %s\nMetadata: %s\nKwargs: %s",
            serialized,
            prompts,
            run_id,
            parent_run_id,
            tags,
            metadata,
            kwargs,
        )

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list],  # type: ignore
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run when a chat model starts running."""
        logger.debug(
            "Chat Model Started.\nSerialized: %s\nMessages: %s\nRun ID: %s\nParent Run ID: %s\nTags: %s\nMetadata: %s\nKwargs: %s",
            serialized,
            messages,
            run_id,
            parent_run_id,
            tags,
            metadata,
            kwargs,
        )

    # Too verbose right now: async def on_llm_new_token

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run when LLM ends running."""
        logger.debug(
            "LLM Ended.\nResponse: %s\nRun ID: %s\nParent Run ID: %s\nKwargs: %s",
            response,
            run_id,
            parent_run_id,
            kwargs,
        )

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run when LLM errors."""
        logger.error(
            "LLM Error: %s\nRun ID: %s\nParent Run ID: %s\nKwargs: %s",
            error,
            run_id,
            parent_run_id,
            kwargs,
        )

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run when chain starts running."""
        log_data = {
            "event": "chain_start",
            "serialized": serialized,
            "run_id": str(run_id),
            "parent_run_id": str(parent_run_id) if parent_run_id else None,
            "tags": tags,
            "metadata": metadata,
            "kwargs": kwargs,
            "agent_planning": None,
            "agent_input": None,
        }

        if "intermediate_steps" in inputs:
            log_data["agent_planning"] = [
                str(step) for step in inputs["intermediate_steps"]
            ]

        if "input" in inputs:
            log_data["agent_input"] = inputs["input"]

        logger.debug("Chain started: %s", log_data)

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run when chain ends running."""
        logger.info(
            "Chain ended.\nOutputs: %s\nRun ID: %s\nParent Run ID: %s\nKwargs: %s",
            outputs,
            run_id,
            parent_run_id,
            kwargs,
        )

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run when chain errors."""
        logger.error(
            "Chain Error: %s\nRun ID: %s\nParent Run ID: %s\nKwargs: %s",
            error,
            run_id,
            parent_run_id,
            kwargs,
        )

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run when tool starts running."""
        logger.info(
            "Tool Start.\nName: %s\nInput: %s\nRun ID: %s\nParent Run ID: %s\nTags: %s\nMetadata: %s\nInputs: %s\nKwargs: %s",
            serialized.get("name", "unknown"),
            input_str,
            run_id,
            parent_run_id,
            tags,
            metadata,
            inputs,
            kwargs,
        )

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run when tool ends running."""
        logger.info(
            "Tool Output: %s\nRun ID: %s\nParent Run ID: %s\nKwargs: %s",
            output,
            run_id,
            parent_run_id,
            kwargs,
        )

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run when tool errors."""
        logger.error(
            "Tool Error: %s\nRun ID: %s\nParent Run ID: %s\nKwargs: %s",
            error,
            run_id,
            parent_run_id,
            kwargs,
        )

    def on_text(
        self,
        text: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run on arbitrary text."""
        logger.info(
            "Text: %s\nRun ID: %s\nParent Run ID: %s\nKwargs: %s",
            text,
            run_id,
            parent_run_id,
            kwargs,
        )

    def on_retry(
        self,
        retry_state: RetryCallState,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run on a retry event."""
        logger.info(
            "Retry: %s\nRun ID: %s\nParent Run ID: %s\nKwargs: %s",
            retry_state,
            run_id,
            parent_run_id,
            kwargs,
        )

    async def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Run on agent action."""
        logger.debug(
            "Agent Action: %s\nRun ID: %s\nParent Run ID: %s\nTags: %s\nKwargs: %s",
            action,
            run_id,
            parent_run_id,
            tags,
            kwargs,
        )

    async def on_agent_finish(
        self,
        finish: AgentFinish,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Run on agent end."""
        logger.debug(
            "Agent Finish: %s\nRun ID: %s\nParent Run ID: %s\nTags: %s\nKwargs: %s",
            finish,
            run_id,
            parent_run_id,
            tags,
            kwargs,
        )

    def on_retriever_start(
        self,
        serialized: dict[str, Any],
        query: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run when Retriever starts running."""
        logger.info(
            "Retriever Start.\nSerialized: %s\nQuery: %s\nRun ID: %s\nParent Run ID: %s\nTags: %s\nMetadata: %s\nKwargs: %s",
            serialized,
            query,
            run_id,
            parent_run_id,
            tags,
            metadata,
            kwargs,
        )

    def on_retriever_end(
        self,
        documents: Sequence[Document],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run when Retriever ends running."""
        logger.info(
            "Retriever End.\nDocuments: %s\nRun ID: %s\nParent Run ID: %s\nKwargs: %s",
            documents,
            run_id,
            parent_run_id,
            kwargs,
        )

    def on_retriever_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run when Retriever errors."""
        logger.error(
            "Retriever Error: %s\nRun ID: %s\nParent Run ID: %s\nKwargs: %s",
            error,
            run_id,
            parent_run_id,
            kwargs,
        )
