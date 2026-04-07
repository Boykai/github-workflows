"""Agent middleware for logging, timing, and security.

Middleware classes wrap each agent ``run()`` call with cross-cutting
concerns:

* :class:`LoggingAgentMiddleware` — timing, token counts, structured logging.
* :class:`SecurityMiddleware` — prompt-injection detection and tool-argument
  validation.

These are designed to be composable: you can stack multiple middleware
by nesting ``wrap()`` calls or by using a middleware chain.
"""

from __future__ import annotations

import re
import time
from typing import Any

from src.logging_utils import get_logger

logger = get_logger(__name__)


class LoggingAgentMiddleware:
    """Wraps an agent run with structured logging.

    Logs:
    - Request start with session/project context.
    - Elapsed wall-clock time.
    - Approximate token counts (based on whitespace splitting).
    """

    async def wrap(
        self,
        run_fn,
        *,
        message: str,
        session_id: str,
        project_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute *run_fn* and log timing + token metrics.

        Args:
            run_fn: The async callable to wrap (e.g. ``AgentProvider.run``).
            message: User message text.
            session_id: Current session ID.
            project_id: Active project ID.
            **kwargs: Additional keyword arguments forwarded to *run_fn*.

        Returns:
            The dict returned by *run_fn*.
        """
        start = time.monotonic()
        logger.info(
            "Agent run start — session=%s, project=%s, input_tokens≈%d",
            session_id,
            project_id,
            len(message.split()),
        )

        try:
            result = await run_fn(message, session_id=session_id, **kwargs)
        except Exception:
            elapsed = time.monotonic() - start
            logger.error(
                "Agent run failed — session=%s, elapsed=%.2fs",
                session_id,
                elapsed,
                exc_info=True,
            )
            raise

        elapsed = time.monotonic() - start
        output_tokens = len(str(result.get("content", "")).split())
        logger.info(
            "Agent run complete — session=%s, elapsed=%.2fs, output_tokens≈%d",
            session_id,
            elapsed,
            output_tokens,
        )
        return result


# ── Prompt injection detection patterns ───────────────────────────────────

_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\|(?:im_start|system|endoftext)\|>", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
]


class SecurityMiddleware:
    """Validates user input and tool arguments for safety.

    Checks:
    - Prompt injection detection via regex patterns.
    - Tool argument length limits.
    - Disallowed characters in tool arguments.
    """

    def __init__(
        self,
        *,
        max_input_length: int = 100_000,
        max_arg_length: int = 65_536,
    ) -> None:
        self.max_input_length = max_input_length
        self.max_arg_length = max_arg_length

    def check_input(self, message: str) -> list[str]:
        """Check *message* for prompt injection patterns.

        Returns:
            A list of warning strings (empty if clean).
        """
        warnings: list[str] = []

        if len(message) > self.max_input_length:
            warnings.append(
                f"Input exceeds maximum length ({len(message)} > {self.max_input_length})"
            )

        warnings.extend(
            f"Potential prompt injection detected: {pattern.pattern}"
            for pattern in _INJECTION_PATTERNS
            if pattern.search(message)
        )

        return warnings

    def validate_tool_args(self, tool_name: str, args: dict[str, Any]) -> list[str]:
        """Validate tool arguments for safety.

        Args:
            tool_name: Name of the tool being called.
            args: Dict of argument name → value.

        Returns:
            A list of validation error strings (empty if all args are valid).
        """
        errors: list[str] = []

        for key, value in args.items():
            if isinstance(value, str) and len(value) > self.max_arg_length:
                errors.append(
                    f"Tool '{tool_name}' arg '{key}' exceeds max length "
                    f"({len(value)} > {self.max_arg_length})"
                )
            # Check for null bytes
            if isinstance(value, str) and "\x00" in value:
                errors.append(f"Tool '{tool_name}' arg '{key}' contains null bytes")

        return errors

    async def wrap(
        self,
        run_fn,
        *,
        message: str,
        session_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Check input then delegate to *run_fn*.

        If prompt-injection patterns are detected, the run is still allowed
        but warnings are logged.  The caller decides whether to block.
        """
        warnings = self.check_input(message)
        if warnings:
            logger.warning(
                "Security warnings for session=%s: %s",
                session_id,
                "; ".join(warnings),
            )

        return await run_fn(message, session_id=session_id, **kwargs)
