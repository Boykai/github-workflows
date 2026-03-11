"""Bot detection helpers for GitHub Copilot accounts."""

from __future__ import annotations


def is_copilot_author(login: str) -> bool:
    """Check if a login belongs to a Copilot agent.

    Matches both "copilot" (substring) and known bot logins
    like "copilot-swe-agent[bot]".
    """
    return "copilot" in (login or "").lower()


def is_copilot_swe_agent(login: str) -> bool:
    """Check if a login belongs specifically to the Copilot SWE coding agent.

    Unlike ``is_copilot_author``, this does NOT match other Copilot bots
    such as the pull-request-reviewer.  Used in completion detection
    to avoid treating auto-triggered code reviews as agent work finishing.
    """
    normalised = (login or "").lower().removesuffix("[bot]")
    return normalised == "copilot-swe-agent"


def is_copilot_reviewer_bot(login: str) -> bool:
    """Check if a login belongs to the Copilot pull-request reviewer bot."""
    normalised = (login or "").lower().removesuffix("[bot]")
    return normalised == "copilot-pull-request-reviewer"
