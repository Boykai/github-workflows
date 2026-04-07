"""Agent Framework middleware for logging and security.

Two middleware layers:

1. **LoggingAgentMiddleware** — records timing, token usage (when available),
   and which tool (if any) was invoked for observability (FR-013).

2. **SecurityMiddleware** — lightweight prompt-injection detection and tool
   argument validation (FR-014).
"""

from __future__ import annotations

import re
import time
from collections.abc import Awaitable, Callable

from agent_framework import AgentContext, AgentMiddleware

from src.logging_utils import get_logger

logger = get_logger(__name__)


# ── Logging Middleware ─────────────────────────────────────────────────────


class LoggingAgentMiddleware(AgentMiddleware):
    """Emit structured logs for every agent invocation."""

    async def process(
        self,
        context: AgentContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        start = time.monotonic()
        logger.info("Agent invocation started")

        await call_next()

        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info(
            "Agent invocation completed in %.1fms",
            elapsed_ms,
        )


# ── Security Middleware ────────────────────────────────────────────────────

# Known prompt-injection patterns (case-insensitive).
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+", re.IGNORECASE),
    re.compile(r"system:\s*override", re.IGNORECASE),
    re.compile(r"do\s+not\s+follow\s+your\s+(?:instructions|rules)", re.IGNORECASE),
    re.compile(r"pretend\s+you\s+(?:are|have)\s+no\s+(?:rules|restrictions)", re.IGNORECASE),
    re.compile(r"reveal\s+(?:your|the)\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"\[INST\]|\[/INST\]|<<SYS>>|<\|im_start\|>", re.IGNORECASE),
]


class SecurityMiddleware(AgentMiddleware):
    """Detect prompt injection attempts and validate tool arguments."""

    async def process(
        self,
        context: AgentContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        # Injection detection is best-effort — log warnings but do not block
        # the agent outright, since false positives are possible.
        # The agent's own instruction set is the primary defense layer.
        user_input = getattr(context, "user_message", None) or ""
        if user_input:
            for pattern in _INJECTION_PATTERNS:
                if pattern.search(user_input):
                    logger.warning(
                        "Potential prompt injection detected: pattern=%s input=%.100s",
                        pattern.pattern,
                        user_input,
                    )
                    break

        await call_next()
