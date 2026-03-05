# Contract: Header Builder

**Module**: `backend/src/services/github_projects/service.py`
**Type**: Enhancement to existing `_build_headers()` static method

---

## Purpose

Consolidate all header construction into a single entry point. Currently, `_build_headers()` returns base REST headers, while GraphQL and Copilot-specific headers are added inline at various call sites. The enhanced builder accepts optional parameters to merge extra headers and GraphQL feature flags.

## Interface

```python
@staticmethod
def _build_headers(
    access_token: str,
    *,
    extra_headers: dict[str, str] | None = None,
    graphql_features: list[str] | None = None,
) -> dict[str, str]:
    """Build request headers for GitHub API calls.
    
    Args:
        access_token: GitHub bearer token.
        extra_headers: Additional headers to merge (overrides base headers
                       if keys conflict).
        graphql_features: List of GraphQL feature flag names. If provided,
                          adds a 'GraphQL-Features' header with comma-
                          separated values.
    
    Returns:
        Complete headers dict ready for use in HTTP requests.
    """
    ...
```

## Output Examples

### Base REST headers (no optional params)

```python
_build_headers("ghp_xxx")
# → {
#     "Authorization": "Bearer ghp_xxx",
#     "Accept": "application/vnd.github+json",
#     "X-GitHub-Api-Version": "2022-11-28",
# }
```

### With GraphQL feature flags

```python
_build_headers(
    "ghp_xxx",
    graphql_features=["issues_copilot_assignment_api_support", "coding_agent_model_selection"],
)
# → {
#     "Authorization": "Bearer ghp_xxx",
#     "Accept": "application/vnd.github+json",
#     "X-GitHub-Api-Version": "2022-11-28",
#     "GraphQL-Features": "issues_copilot_assignment_api_support,coding_agent_model_selection",
# }
```

### With extra headers

```python
_build_headers(
    "ghp_xxx",
    extra_headers={"X-Custom": "value"},
)
# → {
#     "Authorization": "Bearer ghp_xxx",
#     "Accept": "application/vnd.github+json",
#     "X-GitHub-Api-Version": "2022-11-28",
#     "X-Custom": "value",
# }
```

## Behavioral Contract

- **Base headers always present**: Authorization, Accept, X-GitHub-Api-Version
- **Extra headers merge**: `extra_headers` values override base headers on key conflict
- **GraphQL features**: Comma-joined into a single `GraphQL-Features` header value
- **Order**: Base → GraphQL features → extra headers (last wins on conflict)
- **Static method**: No instance state required
- **Backward compatible**: Existing callers passing only `access_token` get identical behavior

## Consumers

All methods in `GitHubProjectsService` that currently call `_build_headers()`:
- `_graphql()` — add `extra_headers` passthrough
- `_request_with_retry()` — base headers only
- `_assign_copilot_graphql()` — uses `graphql_features` parameter
- `_request_copilot_review_graphql()` — may use `graphql_features`
- Various REST methods — base headers only
