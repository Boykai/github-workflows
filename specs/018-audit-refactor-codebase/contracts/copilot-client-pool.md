# Contract: CopilotClientPool

**Module**: `backend/src/services/completion_providers.py`
**Type**: Internal Python class (not an HTTP API)

---

## Purpose

Shared pool for caching `CopilotClient` instances keyed by GitHub token fingerprint. Eliminates duplicate client-caching logic in `CopilotCompletionProvider` and `GitHubCopilotModelFetcher`.

## Interface

```python
class CopilotClientPool:
    """Thread-safe pool of CopilotClient instances keyed by token fingerprint."""

    @staticmethod
    def token_key(github_token: str) -> str:
        """Return SHA-256 hash of token, truncated to 16 hex chars."""
        ...

    async def get_or_create(self, github_token: str) -> CopilotClient:
        """Return cached client or create + cache a new one.
        
        Args:
            github_token: GitHub personal access token or app token.
            
        Returns:
            Initialized CopilotClient instance.
            
        Raises:
            CopilotSDKError: If client creation or startup fails.
        """
        ...

    def remove(self, github_token: str) -> None:
        """Remove a cached client by token (e.g., on auth failure)."""
        ...

    def clear(self) -> None:
        """Remove all cached clients."""
        ...
```

## Consumers

1. `CopilotCompletionProvider._get_or_create_client()` → delegates to `pool.get_or_create()`
2. `GitHubCopilotModelFetcher._get_or_create_client()` → delegates to `pool.get_or_create()`

## Behavioral Contract

- **Idempotent**: Multiple calls with the same token return the same client instance
- **Lazy**: Client is created and started only on first access for a given token
- **Cache key**: SHA-256 of raw token, truncated to 16 hex chars (64-bit collision space)
- **Lifecycle**: Clients remain cached until explicitly removed or pool is cleared
- **Logging**: Logs client creation count at INFO level

## Migration Path

Both `CopilotCompletionProvider` and `GitHubCopilotModelFetcher` replace their internal `_clients` dict and `_token_key`/`_get_or_create_client` methods with a shared `CopilotClientPool` instance (module-level singleton or injected).
