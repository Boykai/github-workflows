# Quickstart: githubkit Migration

**Feature**: `019-githubkit-migration`
**Date**: 2026-03-06
**Audience**: Backend engineers implementing or reviewing this migration

---

## Prerequisites

- Python 3.11+
- Existing backend development environment (`pip install -e ".[dev]"`)
- GitHub OAuth app credentials (existing `.env` configuration)

## Setup

### 1. Install New Dependency

```bash
cd backend
pip install "githubkit>=0.14.0,<0.15.0"
```

After pyproject.toml is updated:
```bash
pip install -e ".[dev]"
```

### 2. Verify Installation

```python
from githubkit import GitHub, TokenAuthStrategy
from githubkit.retry import RetryOption
from githubkit.throttling import LocalThrottler

# Should not raise ImportError
print(f"githubkit installed: {GitHub}")
```

## Key Concepts

### Client Factory Pattern

```python
from src.services.github_projects.client_factory import GitHubClientFactory

# Create factory (once, at app startup)
factory = GitHubClientFactory(max_pool_size=50)

# Get a client for a specific user token
github = factory.get_client(access_token)

# Use typed REST methods
resp = await github.rest.issues.async_create(
    owner="Boykai", repo="github-workflows",
    title="Test Issue", body="Created via githubkit"
)
issue = resp.parsed_data

# Use GraphQL
data = await github.async_graphql(query_string, variables={"login": "user"})

# Use generic request for preview APIs
resp = await github.arequest(
    "POST",
    f"/repos/{owner}/{repo}/issues/{issue_number}/sub_issues",
    json={"sub_issue_id": sub_id}
)
```

### Rate Limit Monitoring

```python
from src.models.rate_limit import RateLimitState

# Check rate limit (populated after any API call)
rl: RateLimitState | None = factory.get_rate_limit()
if rl:
    print(f"Remaining: {rl.remaining}/{rl.limit}, Resets: {rl.reset_at}")

# Clear stale data
factory.clear_rate_limit()
```

## Migration Cheat Sheet

### REST API Call Migration

| Before (httpx) | After (githubkit) |
|----------------|-------------------|
| `await self._client.post(url, json=..., headers=...)` | `await github.rest.issues.async_create(owner, repo, ...)` |
| `await self._client.patch(url, json=..., headers=...)` | `await github.rest.issues.async_update(owner, repo, issue_number, ...)` |
| `await self._client.get(url, headers=...)` | `await github.rest.pulls.async_list_files(owner, repo, pull_number)` |
| `await self._request_with_retry("POST", url, headers, json)` | `await github.rest.issues.async_create(...)` (retry built-in) |
| `await self._request_with_retry("DELETE", url, headers)` | `await github.rest.git.async_delete_ref(owner, repo, ref)` |

### GraphQL Migration

| Before | After |
|--------|-------|
| `await self._graphql(token, query, variables)` | `github = factory.get_client(token); await github.async_graphql(query, variables=variables)` |
| `headers["If-None-Match"] = etag` | Automatic (http_cache=True) |
| `if response.status_code == 304:` | Automatic (handled by Hishel) |

### Preview API Migration

```python
# Sub-Issues (preview API)
resp = await github.arequest(
    "POST",
    f"/repos/{owner}/{repo}/issues/{issue_number}/sub_issues",
    json={"sub_issue_id": child_issue_id},
)

# Copilot assignment (preview API)
resp = await github.arequest(
    "POST",
    f"/repos/{owner}/{repo}/issues/{issue_number}/assignees",
    json={"assignees": ["copilot-swe-agent"]},
)
```

## Verification Commands

```bash
# Run all tests
cd backend && python -m pytest tests/ -x --timeout=120

# Type checking
cd backend && pyright src/

# Linting
cd backend && ruff check src/

# Formatting check
cd backend && ruff format --check src/

# Verify no direct httpx imports in GitHub service code
grep -rn "import httpx" backend/src/services/github_projects/

# Count LOC reduction
wc -l backend/src/services/github_projects/service.py
# Target: ~3,200–3,700 lines (down from 5,179)
```

## Troubleshooting

### Common Issues

1. **`ImportError: cannot import name 'LocalThrottler'`**
   - Ensure githubkit >= 0.14.0 is installed
   - Run `pip install "githubkit>=0.14.0,<0.15.0"`

2. **`TypeError: unexpected keyword argument 'http_cache'`**
   - githubkit < 0.14.0 doesn't support http_cache
   - Upgrade: `pip install --upgrade githubkit`

3. **Tests fail with `AttributeError: 'GitHub' object has no attribute 'rest'`**
   - Test mocks may not be updated for the new githubkit client
   - Update mock to use `AsyncMock(spec=GitHub)` or mock at the transport level

4. **Rate limit data is `None` in polling loop**
   - Verify event hooks are registered on the githubkit client
   - Check that at least one API call has been made before reading rate limit

## File Reference

| File | Role | LOC Before → After |
|------|------|--------------------|
| `pyproject.toml` | Dependency manifest | ~70 → ~70 |
| `service.py` | GitHub Projects service | 5,179 → ~3,200–3,700 |
| `graphql.py` | GraphQL query strings | 927 → ~900 |
| `github_auth.py` | OAuth authentication | 313 → ~270 |
| `client_factory.py` | **NEW** Client pool factory | 0 → ~80 |
| `rate_limit.py` | **NEW** Rate limit model | 0 → ~30 |
| `dependencies.py` | FastAPI DI | 137 → ~145 |
| `polling_loop.py` | Copilot polling | ~500 → ~500 (minor changes) |
