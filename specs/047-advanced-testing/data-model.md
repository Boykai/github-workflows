# Data Model: Advanced Testing for Deep Unknown Bugs

**Feature**: 047-advanced-testing  
**Date**: 2026-03-16

## Entities

### PollingState (Concurrency Test Target)

Module-level mutable dataclass in `copilot_polling/state.py`.

| Field | Type | Description |
|---|---|---|
| is_running | bool | Whether the polling loop is currently active |
| last_poll_time | datetime or None | Timestamp of last successful poll |
| poll_count | int | Total polls executed |
| errors_count | int | Total errors encountered |
| last_error | str or None | Last error message |
| processed_issues | BoundedDict[int, datetime] | Issue → last-processed timestamp (maxlen=2000) |

**Related module globals** (also unprotected):
- `_polling_task`: asyncio.Task reference — race target for duplicate loops
- `_processed_issue_prs`: BoundedSet[str] (maxlen=1000) — "issue:pr" dedup
- `_pending_agent_assignments`: BoundedDict[str, datetime] (maxlen=500) — assignment tracking
- `_claimed_child_prs`: BoundedSet[str] (maxlen=500) — agent PR attribution
- `_system_marked_ready_prs`: BoundedSet[int] (maxlen=500) — draft→ready tracking
- `_copilot_review_first_detected`: BoundedDict[int, datetime] (maxlen=200) — two-cycle confirmation
- `_copilot_review_requested_at`: BoundedDict[int, datetime] (maxlen=200) — review request timestamps
- `_recovery_last_attempt`: BoundedDict[int, datetime] (maxlen=200) — cooldown tracking
- `_consecutive_idle_polls`: int — adaptive interval counter

**Concurrency invariants to verify**:
1. Only one `_polling_task` is active at any time
2. `_polling_state.is_running` reflects actual task liveness
3. Bounded collections never exceed `maxlen` under concurrent access

### PipelineState (State Machine Test Target)

Write-through cache in `pipeline_state_store.py`, persisted to SQLite.

| Field | Type | Description |
|---|---|---|
| issue_number | int | Primary key — GitHub issue number |
| status | str | One of: idle, running, completed, failed, cancelled |
| current_agent_index | int | Index into the agent sequence |
| completed_agents | list[str] | Agent names that finished successfully |
| execution_mode | str | "sequential" or "parallel" |
| parallel_agent_statuses | dict | Agent name → status mapping for parallel mode |
| created_at | datetime | Pipeline creation timestamp |
| updated_at | datetime | Last state change timestamp |

**State machine invariants**:
1. `current_agent_index` ∈ [0, len(agents)]
2. `completed_agents` ⊆ all configured agents
3. Status transitions: idle → running → {completed, failed, cancelled}; no back-transitions
4. In parallel mode: pipeline completes only when all parallel agents complete

### BoundedDict / BoundedSet (Stateful Cache Test Target)

Generic data structures in `src/utils.py`.

**BoundedDict[K, V]**:
| Property | Type | Description |
|---|---|---|
| maxlen | int | Maximum capacity (> 0) |
| _data | OrderedDict[K, V] | Insertion-ordered storage |
| _on_evict | Callable or None | Callback fired on eviction |

**BoundedSet[T]**:
| Property | Type | Description |
|---|---|---|
| maxlen | int | Maximum capacity (> 0) |
| _data | OrderedDict[T, None] | Insertion-ordered storage |

**Stateful test invariants**:
1. `len(collection) <= maxlen` after every operation
2. Eviction removes the oldest (first-inserted) item
3. Adding an existing item moves it to the end (LRU refresh)
4. `on_evict` callback fires exactly once per evicted entry

### WebhookPayload (Runtime Validation Target — Backend)

Currently untyped `dict[str, Any]` in `webhooks.py`. Proposed typed models:

**PullRequestEvent**:
| Field | Type | Required | Description |
|---|---|---|---|
| action | str | Yes | Event action (opened, closed, ready_for_review, etc.) |
| pull_request | PullRequestData | Yes | PR details |
| repository | RepositoryData | Yes | Repository info |

**PullRequestData** (nested):
| Field | Type | Required | Description |
|---|---|---|---|
| number | int | Yes | PR number |
| draft | bool | Yes | Draft status |
| merged | bool | No | Whether PR was merged (on close) |
| user | UserData | Yes | Author info |
| head | BranchRef | No | Head branch info |
| body | str or None | No | PR description body |

**UserData** (nested):
| Field | Type | Required | Description |
|---|---|---|---|
| login | str | Yes | GitHub username |

**RepositoryData** (nested):
| Field | Type | Required | Description |
|---|---|---|---|
| name | str | Yes | Repository name |
| owner | OwnerData | Yes | Repository owner |

**OwnerData** (nested):
| Field | Type | Required | Description |
|---|---|---|---|
| login | str | Yes | Owner username |

### API Response (Runtime Validation Target — Frontend)

Top 5 API response shapes to be validated with Zod schemas:

1. **ProjectsListResponse**: `projectsApi.getUserProjects()` — array of project objects with `id`, `title`, `number`, `url`
2. **BoardDataResponse**: `boardApi.getBoardData()` — board columns with nested issue cards
3. **ChatMessagesResponse**: `chatApi.getMessages()` — array of chat messages with `id`, `role`, `content`, `timestamp`
4. **SettingsResponse**: `settingsApi.getUserSettings()` — user preferences object
5. **PipelineStateResponse**: `workflowApi.getPipelineState()` — pipeline configuration and execution state

## Relationships

```
PollingState ──reads/writes──▶ BoundedDict/BoundedSet (module globals)
                                      │
PipelineState ──persisted-via──▶ pipeline_state_store (write-through cache)
                                      │
                              uses BoundedDict as L1 cache
                                      │
WebhookPayload ──triggers──▶ PipelineState transitions (via orchestrator)
                                      │
API Response ──consumed-by──▶ Frontend (currently no runtime validation)
```

## Validation Rules

- **BoundedDict/BoundedSet**: `maxlen > 0` enforced at construction time (raises `ValueError`)
- **PipelineState**: Status must be one of the defined enum values; `current_agent_index` must be non-negative
- **WebhookPayload**: HMAC signature verified before parsing; required fields (`action`, `pull_request.number`, `repository.name`) must be present
- **API Response**: Required fields must be present and of correct type; optional fields may be null/missing

## State Transitions

### Pipeline Lifecycle

```
idle ──start──▶ running ──advance──▶ running (next agent)
                   │                    │
                   ├──fail──▶ failed    ├──complete──▶ completed
                   │                    │
                   └──cancel──▶ cancelled
```

Invalid transitions (to be caught by stateful tests):
- `completed → running` (no restart of completed pipelines)
- `failed → running` (failed pipelines require explicit reset)
- `cancelled → running` (cancelled pipelines require explicit reset)
- Any transition with `current_agent_index > len(agents)`
