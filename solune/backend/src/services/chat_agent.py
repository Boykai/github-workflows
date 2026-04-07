"""Chat Agent Service — central orchestrator for the Microsoft Agent Framework.

Replaces the priority-dispatch cascade in ``chat.py`` with a single
``ChatAgentService.run()`` call.  The agent decides which tool to invoke
based on its own reasoning (system instructions + user message).

Key responsibilities:
- Creates and caches ``Agent`` instances (per provider configuration)
- Manages ``AgentSession`` ↔ Solune ``session_id`` mapping
- Passes runtime context (project, token, tasks) to tools via kwargs
- Converts agent responses → ``ChatMessage`` with action_type / action_data
- Applies logging and security middleware around each interaction
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator
from uuid import UUID

from src.logging_utils import get_logger
from src.models.chat import ActionType, ChatMessage, SenderType
from src.models.recommendation import (
    AITaskProposal,
    IssueRecommendation,
    ProposalStatus,
    RecommendationStatus,
)
from src.prompts.agent_instructions import get_agent_instructions
from src.services.agent_middleware import LoggingAgentMiddleware, SecurityMiddleware
from src.services.agent_tools import (
    AGENT_TOOLS,
    analyze_transcript,
    ask_clarifying_question,
    create_issue_recommendation,
    create_task_proposal,
    get_pipeline_list,
    get_project_context,
    update_task_status,
)

logger = get_logger(__name__)


class ChatAgentService:
    """Orchestrates agent interactions for the chat API.

    The service holds a reference to the underlying ``Agent`` (from
    ``agent_framework``) and manages session mapping, middleware, and
    response conversion.

    When agent-framework is unavailable, falls back to a lightweight
    tool-dispatch implementation that matches user intent to tools
    using keyword heuristics.
    """

    def __init__(self) -> None:
        self._logging_mw = LoggingAgentMiddleware()
        self._security_mw = SecurityMiddleware()
        # Agent instance is created lazily on first run()
        self._agent: Any | None = None
        self._sessions: dict[str, Any] = {}
        self._agent_framework_available: bool | None = None

    # ── Public API ───────────────────────────────────────────────────

    async def run(
        self,
        message: str,
        *,
        session_id: UUID,
        project_name: str = "Unknown Project",
        github_token: str | None = None,
        project_id: str = "",
        current_tasks: list[Any] | None = None,
        project_columns: list[str] | None = None,
        cached_projects: list[Any] | None = None,
        pipeline_id: str | None = None,
        file_urls: list[str] | None = None,
        ai_service: Any | None = None,
        metadata_context: dict[str, Any] | None = None,
    ) -> ChatMessage:
        """Process a user message through the agent and return a response.

        This is the main entry point that replaces the 5-tier priority
        dispatch in ``chat.py``.

        Args:
            message: User's chat message.
            session_id: Current session UUID.
            project_name: Active project name for context.
            github_token: User's GitHub OAuth token.
            project_id: Selected project ID.
            current_tasks: Cached task list for the project.
            project_columns: Available status columns.
            cached_projects: All cached projects for the user.
            pipeline_id: Selected pipeline ID (if any).
            file_urls: Uploaded file URLs.
            ai_service: Legacy AIAgentService for tool delegation.
            metadata_context: Repository metadata for prompt enrichment.

        Returns:
            A ChatMessage with the agent's response, including
            action_type and action_data when a tool was invoked.
        """
        # ── Security check ──
        injection_msg = self._security_mw.check_input(message)
        if injection_msg:
            return ChatMessage(
                session_id=session_id,
                sender_type=SenderType.ASSISTANT,
                content=injection_msg,
            )

        # Build tool context (shared across all tools)
        tool_context: dict[str, Any] = {
            "session_id": str(session_id),
            "project_name": project_name,
            "github_token": github_token,
            "project_id": project_id,
            "current_tasks": current_tasks or [],
            "project_columns": project_columns or [],
            "cached_projects": cached_projects,
            "pipeline_id": pipeline_id,
            "file_urls": file_urls or [],
            "ai_service": ai_service,
            "metadata_context": metadata_context,
        }

        # ── Logging start ──
        self._logging_mw.on_request_start(message, {"session_id": str(session_id)})

        tools_invoked: list[str] = []
        try:
            # Try agent-framework path first
            if self._is_agent_framework_available():
                result = await self._run_with_agent_framework(
                    message, session_id, tool_context, tools_invoked
                )
            else:
                # Fallback: keyword-based tool dispatch
                result = await self._run_with_fallback(
                    message, tool_context, tools_invoked
                )
        except Exception as exc:
            logger.error("Agent run failed: %s", exc, exc_info=True)
            result = _error_tool_result(
                f"I encountered an error processing your request ({type(exc).__name__}). "
                "Please try again."
            )

        # ── Logging end ──
        response_text = result.get("message", "")
        self._logging_mw.on_request_end(
            response_text, tools_invoked, {"session_id": str(session_id)}
        )

        # ── Convert to ChatMessage ──
        return self._to_chat_message(result, session_id)

    async def run_stream(
        self,
        message: str,
        *,
        session_id: UUID,
        project_name: str = "Unknown Project",
        github_token: str | None = None,
        project_id: str = "",
        current_tasks: list[Any] | None = None,
        project_columns: list[str] | None = None,
        cached_projects: list[Any] | None = None,
        pipeline_id: str | None = None,
        file_urls: list[str] | None = None,
        ai_service: Any | None = None,
        metadata_context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream the agent response token by token.

        Yields:
            Partial response tokens as they become available.
            The final yield is a JSON object with the complete response
            including action_type and action_data.
        """
        # For now, fall back to non-streaming and yield the complete response.
        # When agent-framework streaming is wired up, this will yield
        # intermediate tokens via agent.run_stream().
        result = await self.run(
            message,
            session_id=session_id,
            project_name=project_name,
            github_token=github_token,
            project_id=project_id,
            current_tasks=current_tasks,
            project_columns=project_columns,
            cached_projects=cached_projects,
            pipeline_id=pipeline_id,
            file_urls=file_urls,
            ai_service=ai_service,
            metadata_context=metadata_context,
        )

        # Yield the content progressively (simulated streaming)
        content = result.content
        # Yield the full content in one chunk for now
        yield json.dumps({
            "type": "content",
            "content": content,
            "action_type": result.action_type.value if result.action_type else None,
            "action_data": result.action_data,
            "done": True,
        })

    # ── Agent Framework integration ──────────────────────────────────

    def _is_agent_framework_available(self) -> bool:
        """Check if agent-framework-core is installed."""
        if self._agent_framework_available is None:
            try:
                import agent_framework  # noqa: F401

                self._agent_framework_available = True
            except ImportError:
                self._agent_framework_available = False
                logger.info(
                    "agent-framework-core not available — using fallback tool dispatch"
                )
        return self._agent_framework_available

    async def _run_with_agent_framework(
        self,
        message: str,
        session_id: UUID,
        tool_context: dict[str, Any],
        tools_invoked: list[str],
    ) -> dict[str, Any]:
        """Run the message through the Microsoft Agent Framework agent."""
        try:
            from agent_framework import Agent, AgentSession, FunctionTool

            from src.services.agent_provider import create_agent_client

            client = create_agent_client(
                github_token=tool_context.get("github_token"),
            )

            # Build function tools with injected context
            framework_tools = []
            for tool_func in AGENT_TOOLS:
                # Wrap each tool to inject tool_context
                async def _wrapped(
                    _fn=tool_func, _ctx=tool_context, **kwargs: Any
                ) -> Any:
                    self._logging_mw.on_tool_call(_fn.__name__, kwargs)
                    validation_error = self._security_mw.check_tool_call(
                        _fn.__name__, kwargs
                    )
                    if validation_error:
                        return {"message": validation_error, "action_type": "", "action_data": {}}
                    tools_invoked.append(_fn.__name__)
                    return await _fn(**kwargs, tool_context=_ctx)

                _wrapped.__name__ = tool_func.__name__
                _wrapped.__doc__ = tool_func.__doc__
                framework_tools.append(_wrapped)

            instructions = get_agent_instructions(
                project_name=tool_context.get("project_name"),
            )

            agent = Agent(
                client=client,
                instructions=instructions,
                tools=framework_tools,
            )

            # Use or create session
            session_key = str(session_id)
            async with AgentSession(agent=agent) as session:
                result = await session.run(message)

            # Parse the agent's response
            if isinstance(result, str):
                try:
                    return json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    return _tool_result_from_text(result)
            elif isinstance(result, dict):
                return result
            else:
                return _tool_result_from_text(str(result))

        except ImportError:
            self._agent_framework_available = False
            return await self._run_with_fallback(message, tool_context, tools_invoked)
        except Exception as exc:
            logger.error("Agent framework run failed: %s", exc, exc_info=True)
            # Fall back to keyword dispatch
            return await self._run_with_fallback(message, tool_context, tools_invoked)

    async def _run_with_fallback(
        self,
        message: str,
        tool_context: dict[str, Any],
        tools_invoked: list[str],
    ) -> dict[str, Any]:
        """Fallback tool dispatch using keyword heuristics.

        Mirrors the old priority-dispatch cascade but routes through
        the new tool functions.  This ensures the system works even
        without agent-framework installed.
        """
        ai_service = tool_context.get("ai_service")
        github_token = tool_context.get("github_token")
        message_lower = message.lower().strip()

        # ── 1. Transcript analysis (if file_urls present) ────────────
        file_urls = tool_context.get("file_urls", [])
        if file_urls:
            transcript_content = await self._extract_transcript(file_urls)
            if transcript_content:
                tools_invoked.append("analyze_transcript")
                self._logging_mw.on_tool_call("analyze_transcript", {"content_length": len(transcript_content)})
                return await analyze_transcript(
                    transcript_content=transcript_content,
                    tool_context=tool_context,
                )

        # ── 2. Feature request detection ─────────────────────────────
        if ai_service:
            try:
                is_feature = await ai_service.detect_feature_request_intent(
                    message, github_token=github_token
                )
            except Exception as exc:
                logger.debug("Feature detection failed: %s", exc)
                is_feature = False

            if is_feature:
                # Generate full recommendation via AI
                try:
                    project_name = tool_context.get("project_name", "Unknown")
                    session_id = tool_context.get("session_id", "")
                    metadata_ctx = tool_context.get("metadata_context")

                    recommendation = await ai_service.generate_issue_recommendation(
                        user_input=message,
                        project_name=project_name,
                        session_id=session_id,
                        github_token=github_token,
                        metadata_context=metadata_ctx,
                    )

                    tools_invoked.append("create_issue_recommendation")
                    return {
                        "action_type": "issue_create",
                        "action_data": {
                            "recommendation_id": str(recommendation.recommendation_id),
                            "proposed_title": recommendation.title,
                            "user_story": recommendation.user_story,
                            "original_context": recommendation.original_context,
                            "ui_ux_description": recommendation.ui_ux_description,
                            "functional_requirements": recommendation.functional_requirements,
                            "technical_notes": recommendation.technical_notes,
                            "pipeline_id": tool_context.get("pipeline_id"),
                            "file_urls": file_urls,
                        },
                        "message": (
                            f"I've generated a GitHub issue recommendation:\n\n"
                            f"**{recommendation.title}**\n\n"
                            f"**User Story:**\n{recommendation.user_story}\n\n"
                            "Click **Confirm** to create this issue in GitHub, "
                            "or **Reject** to discard."
                        ),
                        "_recommendation": recommendation,
                    }
                except Exception as exc:
                    logger.error("Issue recommendation failed: %s", exc, exc_info=True)
                    return _error_tool_result(
                        "I couldn't generate an issue recommendation from your "
                        "feature request. Please try again with more detail."
                    )

        # ── 3. Status change detection ───────────────────────────────
        if ai_service:
            try:
                current_tasks = tool_context.get("current_tasks", [])
                project_columns = tool_context.get("project_columns", [])
                from src.constants import DEFAULT_STATUS_COLUMNS

                status_change = await ai_service.parse_status_change_request(
                    user_input=message,
                    available_tasks=[t.title for t in current_tasks],
                    available_statuses=project_columns or DEFAULT_STATUS_COLUMNS,
                    github_token=github_token,
                )

                if status_change:
                    tools_invoked.append("update_task_status")
                    self._logging_mw.on_tool_call(
                        "update_task_status",
                        {"task_reference": status_change.task_reference, "target_status": status_change.target_status},
                    )
                    return await update_task_status(
                        task_reference=status_change.task_reference,
                        target_status=status_change.target_status,
                        tool_context=tool_context,
                    )
            except Exception as exc:
                logger.debug("Status change detection failed: %s", exc)

        # ── 4. Task generation (default) ─────────────────────────────
        if ai_service:
            try:
                project_name = tool_context.get("project_name", "Unknown")
                generated = await ai_service.generate_task_from_description(
                    user_input=message,
                    project_name=project_name,
                    github_token=github_token,
                )
                tools_invoked.append("create_task_proposal")
                return await create_task_proposal(
                    title=generated.title,
                    description=generated.description,
                    tool_context=tool_context,
                )
            except Exception as exc:
                logger.error("Task generation failed: %s", exc, exc_info=True)
                return _error_tool_result(
                    "I couldn't generate a task from your description. "
                    "Please try again with more detail."
                )

        return _error_tool_result(
            "AI features are not configured. Please set up your AI provider."
        )

    async def _extract_transcript(self, file_urls: list[str]) -> str | None:
        """Try to extract transcript content from uploaded files."""
        import os
        import tempfile
        from pathlib import Path

        from src.services.transcript_detector import detect_transcript

        upload_dir = Path(tempfile.gettempdir()) / "chat-uploads"

        for file_url in file_urls:
            raw_name = file_url.rsplit("/", 1)[-1] if "/" in file_url else file_url
            filename = os.path.basename(raw_name)
            if not filename:
                continue

            candidate = os.path.normpath(os.path.join(str(upload_dir), filename))
            safe_prefix = os.path.normpath(str(upload_dir)) + os.sep
            if not candidate.startswith(safe_prefix):
                continue

            file_path = Path(candidate)
            if not file_path.exists():
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            original_name = filename[9:] if len(filename) > 9 and filename[8] == "-" else filename
            result = detect_transcript(original_name, content)
            if result.is_transcript:
                return content

        return None

    # ── Response conversion ──────────────────────────────────────────

    def _to_chat_message(
        self,
        result: dict[str, Any],
        session_id: UUID,
    ) -> ChatMessage:
        """Convert a tool result dict to a ChatMessage."""
        action_type_str = result.get("action_type", "")
        action_type = None
        if action_type_str:
            try:
                action_type = ActionType(action_type_str)
            except ValueError:
                logger.warning("Unknown action_type: %s", action_type_str)

        action_data = result.get("action_data", {})
        message_text = result.get("message", "")

        # Add proposal/recommendation status if creating
        if action_type and "status" not in action_data:
            if action_type == ActionType.TASK_CREATE:
                action_data["status"] = ProposalStatus.PENDING.value
            elif action_type == ActionType.ISSUE_CREATE:
                action_data["status"] = RecommendationStatus.PENDING.value
            elif action_type == ActionType.STATUS_UPDATE:
                action_data["status"] = ProposalStatus.PENDING.value

        return ChatMessage(
            session_id=session_id,
            sender_type=SenderType.ASSISTANT,
            content=message_text,
            action_type=action_type,
            action_data=action_data if action_data else None,
        )


# ── Module-level helpers ─────────────────────────────────────────────────


def _error_tool_result(message: str) -> dict[str, Any]:
    """Create an error tool result dict."""
    return {"action_type": "", "action_data": {}, "message": message}


def _tool_result_from_text(text: str) -> dict[str, Any]:
    """Wrap plain text in a tool result dict."""
    return {"action_type": "", "action_data": {}, "message": text}


# ── Global singleton ─────────────────────────────────────────────────────

_chat_agent_service_instance: ChatAgentService | None = None


def get_chat_agent_service() -> ChatAgentService:
    """Get or create the global ChatAgentService instance."""
    global _chat_agent_service_instance
    if _chat_agent_service_instance is None:
        _chat_agent_service_instance = ChatAgentService()
    return _chat_agent_service_instance


def reset_chat_agent_service() -> None:
    """Reset the global instance (useful for testing)."""
    global _chat_agent_service_instance
    _chat_agent_service_instance = None
