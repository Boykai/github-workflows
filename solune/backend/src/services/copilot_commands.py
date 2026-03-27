"""Copilot slash-command service.

Detects and executes the 9 GitHub Copilot slash commands by building
intent-specific system prompts and delegating to CopilotCompletionProvider.
"""

from __future__ import annotations

import re

from src.logging_utils import get_logger

logger = get_logger(__name__)

# ── Command set ─────────────────────────────────────────────────────────────

COPILOT_COMMANDS: set[str] = {
    "explain",
    "fix",
    "doc",
    "tests",
    "setuptests",
    "new",
    "newnotebook",
    "search",
    "startdebugging",
}

# ── Intent-specific system prompts ──────────────────────────────────────────

COPILOT_COMMAND_PROMPTS: dict[str, str] = {
    "explain": (
        "You are a helpful coding assistant. Explain the given code or concept "
        "clearly and concisely. Include practical examples where appropriate. "
        "Break down complex ideas into understandable parts."
    ),
    "fix": (
        "You are a helpful coding assistant. Identify issues in the provided code, "
        "explain what is wrong, and provide the corrected code with a clear "
        "explanation of each fix."
    ),
    "doc": (
        "You are a helpful coding assistant. Generate idiomatic documentation "
        "comments for the provided code. Follow the language's standard "
        "documentation conventions (JSDoc, docstrings, Javadoc, etc.)."
    ),
    "tests": (
        "You are a helpful coding assistant. Generate comprehensive unit tests "
        "for the provided code. Include edge cases, error scenarios, and boundary "
        "conditions. Use the appropriate testing framework for the language."
    ),
    "setuptests": (
        "You are a helpful coding assistant. Recommend the best test framework "
        "for the described project and provide step-by-step setup instructions, "
        "configuration files, and example tests to get started."
    ),
    "new": (
        "You are a helpful coding assistant. Generate a project scaffold for the "
        "described project. Include the directory structure, essential "
        "configuration files, and starter code."
    ),
    "newnotebook": (
        "You are a helpful coding assistant. Generate a Jupyter notebook outline "
        "for the described topic. Include markdown cells for explanations and "
        "code cells with starter code for each section."
    ),
    "search": (
        "You are a helpful coding assistant. Generate effective code search "
        "queries and regex patterns to help find the described code construct. "
        "Include grep, ripgrep, and IDE search patterns."
    ),
    "startdebugging": (
        "You are a helpful coding assistant. Generate a debug launch.json "
        "configuration for the described project setup. Include the appropriate "
        "debugger settings, environment variables, and common breakpoint suggestions."
    ),
}

# Pre-compiled pattern for matching copilot commands at the start of a message.
_COMMAND_RE = re.compile(
    r"^/(" + "|".join(re.escape(c) for c in sorted(COPILOT_COMMANDS)) + r")(?:\s+(.*))?$",
    re.IGNORECASE | re.DOTALL,
)


def is_copilot_command(content: str) -> tuple[str, str] | None:
    """Detect whether *content* is a Copilot slash command.

    Returns ``(command, args)`` when detected, ``None`` otherwise.
    ``command`` is normalised to lowercase; ``args`` is the remaining
    text after the command name (may be empty).
    """
    m = _COMMAND_RE.match(content.strip())
    if not m:
        return None
    return m.group(1).lower(), (m.group(2) or "").strip()


async def execute_copilot_command(
    command: str,
    args: str,
    github_token: str,
) -> str:
    """Execute a Copilot command and return the assistant response text.

    Builds the intent-specific system prompt and calls
    ``CopilotCompletionProvider.complete()`` using the caller's GitHub token.
    """
    from src.services.completion_providers import CopilotCompletionProvider

    system_prompt = COPILOT_COMMAND_PROMPTS.get(command)
    if not system_prompt:
        return f"Unknown Copilot command: /{command}"

    user_content = args or f"/{command}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    provider = CopilotCompletionProvider()
    try:
        return await provider.complete(messages, github_token=github_token)
    except Exception as exc:
        logger.error("Copilot /%s command failed: %s", command, exc)
        return (
            f"**Error:** The `/{command}` command encountered an unexpected error. "
            "Please try again."
        )
