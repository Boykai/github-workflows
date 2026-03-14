# Contract: Admin Guard Middleware

**Feature**: `041-solune-rebrand-app-builder` | **Date**: 2026-03-14
**Source**: FR-027, FR-028, FR-029, FR-030

## Overview

The admin guard system protects platform core files from unintended modification by agents operating in app-building mode. It operates as middleware in the agent operation routing layer, evaluating each file path against a configuration of protection rules.

## Guard Levels

| Level | Behavior | Override |
|-------|----------|---------|
| `admin` | Blocks by default, prompts for elevated permission | User can approve via confirmation dialog |
| `adminlock` | Unconditionally blocks all agent modifications | No override — operation is rejected |
| `none` | No restriction, operations proceed freely | N/A |

## Configuration Format

**File**: `solune/guard-config.yml` (or embedded in platform configuration)

```yaml
# Guard rules — evaluated in order, most specific match wins
guard_rules:
  # Platform core — modification requires elevated permission
  - path_pattern: "solune/**"
    guard_level: admin
    description: "Platform core code and configuration"

  # Workflow and agent configs — fully locked
  - path_pattern: ".github/**"
    guard_level: adminlock
    description: "CI/CD workflows and agent definitions"

  # App directories — unrestricted for agents
  - path_pattern: "apps/**"
    guard_level: none
    description: "Generated application directories"

  # Root config files — admin protection
  - path_pattern: "docker-compose.yml"
    guard_level: admin
    description: "Root orchestration configuration"

  - path_pattern: "README.md"
    guard_level: admin
    description: "Root-level README"
```

## Evaluation Algorithm

```text
evaluate_guard(file_path, guard_config):
  1. Normalize file_path (resolve `.`, `..`, remove leading `/`)
  2. For each rule in guard_config (most specific first):
     a. If file_path matches rule.path_pattern:
        Return rule.guard_level
  3. Default: return "admin" (fail-closed)
```

**Specificity**: Rules are sorted by path depth (most nested first). For equal depth, explicit file matches beat glob patterns.

## API Integration

### Check Guard (internal, used by agent operations)

```python
async def check_guard(file_paths: list[str]) -> GuardResult:
    """
    Evaluate guard rules for a set of file paths.

    Returns:
        GuardResult with:
        - allowed: list of paths that can proceed
        - admin_blocked: list of paths needing elevation
        - locked: list of paths that are unconditionally blocked
    """
```

### Guard Result Shape

```python
class GuardResult(BaseModel):
    allowed: list[str]          # Paths with guard_level = none
    admin_blocked: list[str]    # Paths with guard_level = admin (need approval)
    locked: list[str]           # Paths with guard_level = adminlock (rejected)
```

### Agent Operation Flow

```text
Agent requests file operation (create/modify/delete)
  │
  ├─► Guard middleware intercepts
  │     │
  │     ├─► Evaluate each target file path
  │     │     │
  │     │     ├─► "none" → Add to allowed list
  │     │     ├─► "admin" → Add to admin_blocked list
  │     │     └─► "adminlock" → Add to locked list
  │     │
  │     ├─► If locked paths exist:
  │     │     Return 403 with explanation of locked paths
  │     │
  │     ├─► If admin_blocked paths exist (no locked):
  │     │     Return 403 with elevation prompt
  │     │     │
  │     │     └─► User approves → Retry with elevation flag
  │     │         │
  │     │         └─► Guard middleware allows admin paths with flag
  │     │
  │     └─► All paths allowed → Proceed
  │
  └─► File operation executes
```

## Error Responses

### Locked Path Rejection
```json
{
  "detail": "Operation blocked by @adminlock guard",
  "locked_paths": [".github/workflows/ci.yml"],
  "explanation": "CI/CD workflows and agent definitions are permanently protected"
}
```

### Admin Elevation Required
```json
{
  "detail": "Operation requires @admin elevation",
  "admin_paths": ["solune/backend/src/main.py"],
  "explanation": "Platform core code requires elevated permission to modify",
  "elevation_prompt": "This operation targets platform core files. Approve to proceed."
}
```
