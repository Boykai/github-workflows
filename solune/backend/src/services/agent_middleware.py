"""Middleware for the Microsoft Agent Framework agent.

Provides cross-cutting concerns:
- LoggingAgentMiddleware: timing, token count, request/response logging
- SecurityMiddleware: prompt injection detection, tool argument validation

v0.2.0 — Intelligent Chat Agent (Microsoft Agent Framework)
"""

from __future__ import annotations

import re
import time
from typing import Any

from src.logging_utils import get_logger

logger = get_logger(__name__)

# ── Prompt injection patterns ────────────────────────────────────────────

_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"forget\s+(?:all|everything)\s+(?:above|before)", re.IGNORECASE),
    re.compile(r"override\s+(?:your|the)\s+(?:instructions|prompt|rules)", re.IGNORECASE),
]

# Maximum allowed lengths for tool arguments
_MAX_TITLE_LENGTH = 256
_MAX_DESCRIPTION_LENGTH = 10_000
_MAX_TRANSCRIPT_LENGTH = 500_000


class LoggingAgentMiddleware:
    """Middleware that logs timing, token counts, and tool calls.

    Wraps agent invocations to provide observability without modifying
    the agent's behavior.
    """

    def __init__(self, name: str = "LoggingMiddleware") -> None:
        self.name = name

    async def on_request(self, message: str, session_id: str) -> str:
        """Log incoming request.

        Args:
            message: The user's message.
            session_id: Current session ID.

        Returns:
            The message (unmodified).
        """
        logger.info(
            "[%s] Request: session=%s, message_len=%d",
            self.name,
            session_id,
            len(message),
        )
        return message

    async def on_response(
        self,
        response: Any,
        session_id: str,
        elapsed_ms: float,
    ) -> Any:
        """Log outgoing response with timing.

        Args:
            response: The agent's response.
            session_id: Current session ID.
            elapsed_ms: Time taken in milliseconds.

        Returns:
            The response (unmodified).
        """
        logger.info(
            "[%s] Response: session=%s, elapsed_ms=%.1f",
            self.name,
            session_id,
            elapsed_ms,
        )
        return response

    async def on_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        session_id: str,
    ) -> dict[str, Any]:
        """Log tool invocation.

        Args:
            tool_name: Name of the tool being called.
            arguments: Tool arguments.
            session_id: Current session ID.

        Returns:
            The arguments (unmodified).
        """
        logger.info(
            "[%s] Tool call: session=%s, tool=%s",
            self.name,
            session_id,
            tool_name,
        )
        return arguments


class SecurityMiddleware:
    """Middleware that detects prompt injection and validates tool arguments.

    Checks user input against known injection patterns and validates
    tool argument lengths/types to prevent abuse.
    """

    def __init__(self, name: str = "SecurityMiddleware") -> None:
        self.name = name

    def detect_injection(self, message: str) -> bool:
        """Check if a message contains prompt injection patterns.

        Args:
            message: The user's message to check.

        Returns:
            True if a prompt injection pattern was detected.
        """
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(message):
                logger.warning(
                    "[%s] Prompt injection detected: pattern=%s",
                    self.name,
                    pattern.pattern[:50],
                )
                return True
        return False

    def validate_tool_arguments(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> list[str]:
        """Validate tool arguments for safety constraints.

        Args:
            tool_name: Name of the tool being called.
            arguments: Tool arguments to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: list[str] = []

        if tool_name in ("create_task_proposal", "create_issue_recommendation"):
            title = arguments.get("title", "")
            if isinstance(title, str) and len(title) > _MAX_TITLE_LENGTH:
                errors.append(f"Title exceeds maximum length ({len(title)} > {_MAX_TITLE_LENGTH})")

            description = arguments.get("description", "")
            if isinstance(description, str) and len(description) > _MAX_DESCRIPTION_LENGTH:
                errors.append(
                    f"Description exceeds maximum length "
                    f"({len(description)} > {_MAX_DESCRIPTION_LENGTH})"
                )

        if tool_name == "analyze_transcript":
            content = arguments.get("transcript_content", "")
            if isinstance(content, str) and len(content) > _MAX_TRANSCRIPT_LENGTH:
                errors.append(
                    f"Transcript exceeds maximum length ({len(content)} > {_MAX_TRANSCRIPT_LENGTH})"
                )

        return errors

    async def on_request(self, message: str, session_id: str) -> str:
        """Check incoming request for injection patterns.

        Args:
            message: The user's message.
            session_id: Current session ID.

        Returns:
            The message if safe.

        Raises:
            ValueError: If prompt injection is detected.
        """
        if self.detect_injection(message):
            raise ValueError(
                "Message blocked: potential prompt injection detected. "
                "Please rephrase your request."
            )
        return message

    async def on_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        session_id: str,
    ) -> dict[str, Any]:
        """Validate tool arguments before execution.

        Args:
            tool_name: Name of the tool being called.
            arguments: Tool arguments.
            session_id: Current session ID.

        Returns:
            The arguments if valid.

        Raises:
            ValueError: If validation fails.
        """
        errors = self.validate_tool_arguments(tool_name, arguments)
        if errors:
            raise ValueError(f"Tool argument validation failed: {'; '.join(errors)}")
        return arguments


def measure_elapsed_ms(start_time: float) -> float:
    """Calculate elapsed time in milliseconds.

    Args:
        start_time: Start time from time.monotonic().

    Returns:
        Elapsed time in milliseconds.
    """
    return (time.monotonic() - start_time) * 1000
