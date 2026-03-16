# Contract: Webhook Payload Models

**Feature**: 047-advanced-testing  
**Purpose**: Define the Pydantic 2 models that replace untyped `dict[str, Any]` parsing in `webhooks.py`.

## Scope

Only fields **actually accessed** in the codebase are modeled. GitHub sends many more fields — unmodeled fields are silently ignored via `model_config = ConfigDict(extra="ignore")`.

## Models

### PullRequestEvent

```python
class UserData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    login: str

class OwnerData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    login: str

class RepositoryData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    owner: OwnerData

class BranchRef(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ref: str = ""

class PullRequestData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    number: int
    draft: bool = False
    merged: bool = False
    user: UserData
    head: BranchRef = BranchRef()
    body: str | None = None

class PullRequestEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    action: str
    pull_request: PullRequestData
    repository: RepositoryData
```

### IssuesEvent (future extensibility)

```python
class IssuesEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    action: str
    issue: IssueData
    repository: RepositoryData
```

### PingEvent

```python
class PingEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    zen: str = ""
    hook_id: int | None = None
```

## Integration Point

In `webhooks.py` `github_webhook()` handler:

```python
# Before (current):
payload = await request.json()

# After:
raw = await request.json()
if x_github_event == "pull_request":
    payload = PullRequestEvent.model_validate(raw)
elif x_github_event == "issues":
    payload = IssuesEvent.model_validate(raw)
elif x_github_event == "ping":
    payload = PingEvent.model_validate(raw)
else:
    payload = raw  # unknown events pass through untyped
```

## Validation Behavior

- **Missing required field**: Pydantic raises `ValidationError` with field path and missing-field detail
- **Wrong type**: Pydantic raises `ValidationError` with expected vs actual type
- **Extra fields**: Silently ignored (GitHub evolves its API frequently; strict rejection would break on new fields)
- **HMAC verification**: Still happens before payload parsing (no change)
