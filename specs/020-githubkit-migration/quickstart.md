# Quickstart: Simplify GitHub Service with githubkit

**Date**: 2026-03-05  
**Branch**: `020-githubkit-migration`

## Prerequisites

- Python 3.11+
- The backend virtual environment activated: `source backend/.venv/bin/activate`
- githubkit installed: `pip install githubkit>=0.14.0`

## Key Concepts

### Before (current architecture)

```python
# Every method manually builds HTTP requests:
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
response = await self._client.post(url, json=body, headers=headers)
response.raise_for_status()
data = response.json()
```

### After (githubkit architecture)

```python
# SDK handles auth, retry, cache, pagination automatically:
client = self._client_factory.get_client(access_token)
resp = await client.rest.issues.async_create(owner, repo, title="Bug", body="Details")
issue = resp.parsed_data  # Pydantic-validated model
```

## Migration Patterns

### Pattern 1: Simple REST Call

```python
# BEFORE (create_issue)
url = f"https://api.github.com/repos/{owner}/{repo}/issues"
headers = self._build_headers(access_token)
response = await self._request_with_retry("POST", url, headers, json=body)
data = response.json()
return data

# AFTER
client = self._client_factory.get_client(access_token)
resp = await client.rest.issues.async_create(owner, repo, title=title, body=body, labels=labels)
return {"number": resp.parsed_data.number, "id": resp.parsed_data.id, "node_id": resp.parsed_data.node_id}
```

### Pattern 2: Standard GraphQL

```python
# BEFORE
data = await self._graphql(access_token, LIST_USER_PROJECTS_QUERY, {"login": username, "first": 20})

# AFTER (unchanged signature, simplified implementation)
data = await self._graphql(access_token, LIST_USER_PROJECTS_QUERY, {"login": username, "first": 20})
# _graphql() internally calls: client.async_graphql(query, variables)
```

### Pattern 3: GraphQL with Feature Flags

```python
# BEFORE
data = await self._graphql(
    access_token, ASSIGN_COPILOT_MUTATION, variables,
    graphql_features=["issues_copilot_assignment_api_support", "coding_agent_model_selection"],
)

# AFTER (_graphql detects graphql_features and routes to arequest)
data = await self._graphql(
    access_token, ASSIGN_COPILOT_MUTATION, variables,
    graphql_features=["issues_copilot_assignment_api_support", "coding_agent_model_selection"],
)
# Internal: uses client.arequest("POST", "/graphql", json=..., headers={"GraphQL-Features": "..."})
```

### Pattern 4: Preview API (no typed method)

```python
# BEFORE
url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/sub_issues"
headers = self._build_headers(access_token)
response = await self._request_with_retry("POST", url, headers, json={"sub_issue_id": sub_id})

# AFTER
client = self._client_factory.get_client(access_token)
resp = await client.arequest("POST", f"/repos/{owner}/{repo}/issues/{number}/sub_issues", json={"sub_issue_id": sub_id})
```

### Pattern 5: Exception Handling

```python
# BEFORE
from httpx import HTTPStatusError
try:
    response = await self._request_with_retry("GET", url, headers)
except HTTPStatusError as e:
    if e.response.status_code == 404:
        return None

# AFTER
from githubkit.exception import RequestFailed
try:
    resp = await client.rest.issues.async_get(owner, repo, number)
except RequestFailed as e:
    if e.response.status_code == 404:
        return None
```

## Verification

```bash
# Run all backend tests
cd backend && pytest

# Type check
pyright

# Lint
ruff check src/

# Verify no raw httpx imports in production code
grep -r "import httpx" src/ --include="*.py"
# Expected: zero matches (signal_bridge.py and signal_delivery.py are separate services)

# Check line count reduction
wc -l src/services/github_projects/service.py src/services/github_projects/graphql.py src/services/github_auth.py
# Target: ~5,100 LOC total (down from ~6,400)
```
