"""Agent middleware for logging and security.

Provides two middleware classes for the Microsoft Agent Framework:

- ``LoggingAgentMiddleware`` — logs timing, token count, and tool invocations.
- ``SecurityMiddleware`` — detects prompt-injection patterns and validates
  tool arguments before execution.
"""

from __future__ import annotations

import re
import time
from typing import Any

from src.logging_utils import get_logger

logger = get_logger(__name__)

# ── Prompt injection detection ──────────────────────────────────────────

# Known prompt injection patterns (compiled once for performance)
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a\s+)?(?:DAN|evil|jailbreak)", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:your\s+)?(?:previous\s+)?(?:instructions|rules)", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are", re.IGNORECASE),
    re.compile(r"<\|(?:im_start|system)\|>", re.IGNORECASE),
    re.compile(r"reveal\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions)", re.IGNORECASE),
    re.compile(r"(?:print|show|output)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions)", re.IGNORECASE),
]


def detect_prompt_injection(text: str) -> bool:
    """Check if text contains known prompt-injection patterns.

    Args:
        text: User input to check.

    Returns:
        True if a prompt-injection pattern was detected.
    """
    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)


# ── Tool argument validation ────────────────────────────────────────────

# Maximum allowed lengths for tool arguments
_ARG_MAX_LENGTHS: dict[str, int] = {
    "title": 256,
    "description": 100_000,
    "user_story": 50_000,
    "task_reference": 500,
    "target_status": 100,
    "transcript_content": 500_000,
    "question": 10_000,
}


def validate_tool_arguments(tool_name: str, kwargs: dict[str, Any]) -> str | None:
    """Validate tool arguments against expected schemas.

    Args:
        tool_name: Name of the tool being invoked.
        kwargs: Arguments to validate.

    Returns:
        Error message if validation fails, None if valid.
    """
    for arg_name, max_len in _ARG_MAX_LENGTHS.items():
        if arg_name in kwargs:
            value = kwargs[arg_name]
            if isinstance(value, str) and len(value) > max_len:
                return (
                    f"Argument '{arg_name}' for tool '{tool_name}' "
                    f"exceeds maximum length ({len(value)} > {max_len})."
                )

    # Validate that required string args are not empty
    if tool_name == "create_task_proposal" and not kwargs.get("title", "").strip():
        return "Tool 'create_task_proposal' requires a non-empty 'title'."

    if tool_name == "update_task_status":
        if not kwargs.get("task_reference", "").strip():
            return "Tool 'update_task_status' requires a non-empty 'task_reference'."
        if not kwargs.get("target_status", "").strip():
            return "Tool 'update_task_status' requires a non-empty 'target_status'."

    return None


# ── Middleware classes ───────────────────────────────────────────────────
#
# These classes implement a simple middleware pattern.  When agent-framework
# middleware support is available they can be plugged in directly; otherwise
# the ChatAgentService invokes them manually around each run.


class LoggingAgentMiddleware:
    """Logs timing, token usage, and tool invocation details."""

    def on_request_start(self, message: str, context: dict[str, Any]) -> None:
        """Called before the agent processes a request."""
        self._start_time = time.monotonic()
        logger.info(
            "Agent request start — session=%s, message_length=%d",
            context.get("session_id", "unknown"),
            len(message),
        )

    def on_request_end(
        self,
        response_text: str,
        tools_invoked: list[str],
        context: dict[str, Any],
    ) -> None:
        """Called after the agent completes a request."""
        elapsed = time.monotonic() - getattr(self, "_start_time", time.monotonic())
        logger.info(
            "Agent request end — session=%s, elapsed=%.3fs, "
            "response_length=%d, tools=%s",
            context.get("session_id", "unknown"),
            elapsed,
            len(response_text),
            tools_invoked or "none",
        )

    def on_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> None:
        """Called when the agent invokes a tool."""
        # Redact potentially sensitive values
        safe_args = {
            k: (v[:50] + "..." if isinstance(v, str) and len(v) > 50 else v)
            for k, v in arguments.items()
            if k != "tool_context"
        }
        logger.info("Agent tool call — tool=%s, args=%s", tool_name, safe_args)


class SecurityMiddleware:
    """Detects prompt injections and validates tool arguments."""

    def check_input(self, message: str) -> str | None:
        """Check user input for prompt injection.

        Returns:
            Error message if injection detected, None if safe.
        """
        if detect_prompt_injection(message):
            logger.warning("Prompt injection detected in message: %.100s...", message)
            return (
                "I detected a potentially unsafe pattern in your message. "
                "Please rephrase your request."
            )
        return None

    def check_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> str | None:
        """Validate tool arguments before execution.

        Returns:
            Error message if validation fails, None if valid.
        """
        return validate_tool_arguments(tool_name, arguments)
