"""Shared CopilotClient caching keyed by token fingerprint.

Both :class:`CopilotCompletionProvider` and :class:`GitHubCopilotModelFetcher`
need to keep one ``CopilotClient`` instance per GitHub OAuth token.  This
module extracts the duplicate cache+hash logic into a single reusable helper.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)


class TokenClientCache:
    """Token-keyed cache for ``CopilotClient`` instances.

    Parameters
    ----------
    label:
        A human-readable label used in log messages to distinguish callers
        (e.g. ``"completion"`` or ``"model-fetching"``).
    """

    def __init__(self, label: str = "copilot") -> None:
        self._clients: dict[str, Any] = {}
        self._label = label

    @staticmethod
    def token_key(token: str) -> str:
        """Return a stable hash of *token* for use as a cache key.

        Avoids keeping raw tokens as dict keys where they could be
        exposed by debug tooling or log dumps.
        """
        return hashlib.sha256(token.encode()).hexdigest()[:16]

    async def get_or_create(self, github_token: str) -> Any:
        """Return a cached ``CopilotClient``, creating one if necessary."""
        key = self.token_key(github_token)
        if key not in self._clients:
            from copilot import CopilotClient  # type: ignore[reportMissingImports]
            from copilot.types import CopilotClientOptions  # type: ignore[reportMissingImports]

            options = CopilotClientOptions(github_token=github_token)
            client = CopilotClient(options=options)
            await client.start()
            self._clients[key] = client
            logger.info(
                "Created new CopilotClient [%s] (total cached: %d)",
                self._label,
                len(self._clients),
            )
        return self._clients[key]

    async def cleanup(self) -> None:
        """Stop all cached ``CopilotClient`` instances."""
        for _key, client in self._clients.items():
            try:
                await client.stop()
            except Exception as exc:
                logger.warning("Error stopping CopilotClient [%s]: %s", self._label, exc)
        self._clients.clear()
        logger.info("Cleaned up all CopilotClient instances [%s]", self._label)
