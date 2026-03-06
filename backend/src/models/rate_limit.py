"""Rate limit state model for GitHub API quota tracking."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RateLimitState:
    """Immutable snapshot of GitHub API rate limit status.

    Replaces the ``dict[str, int]`` returned by the previous
    ``get_last_rate_limit()`` method.  Provides the same data
    with type safety and immutability.

    Attributes:
        limit: Maximum requests allowed per rate limit window.
        remaining: Requests remaining in the current window.
        reset_at: Unix timestamp when the window resets.
        used: Requests consumed (computed as ``limit - remaining``).
        resource: Rate limit resource category (default: ``"core"``).
    """

    limit: int
    remaining: int
    reset_at: int
    used: int
    resource: str = "core"
