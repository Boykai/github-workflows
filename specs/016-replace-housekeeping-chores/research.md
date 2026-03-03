# Research: Replace Housekeeping with Chores

**Feature**: 016-replace-housekeeping-chores  
**Date**: 2026-03-02  
**Status**: Complete — all unknowns resolved

## Research 1: GitHub Issue Template Format

**Decision**: Use Markdown templates (`.md`) with YAML front matter in `.github/ISSUE_TEMPLATE/`

**Rationale**: User explicitly chose `.md` templates over `.yml` issue forms. The `.md` format is simpler, supports free-form body content (essential for rich user input like Bug Bash), and uses straightforward YAML front matter for metadata.

**Template structure**:
```markdown
---
name: Template Name
about: Description shown in template chooser
title: '[PREFIX] Default title'
labels: label1, label2
assignees: username1
---

Body content here (markdown)
```

**Required front matter**: `name`, `about`  
**Optional front matter**: `title`, `labels`, `assignees`, `type`

**Alternatives considered**: `.yml` issue forms (structured web form fields); rejected because user specified `.md` format and the chore templates need free-form markdown bodies.

**Key finding**: No existing `.github/ISSUE_TEMPLATE/` directory in the repo. The chore creation flow will create this directory as part of the first template commit.

## Research 2: Workflow Orchestrator Integration for Trigger Execution

**Decision**: At trigger time, create a GitHub Issue directly (not via `IssueRecommendation`), then invoke `create_all_sub_issues()` from the orchestrator for sub-issue creation and agent assignment.

**Rationale**: The orchestrator's `create_issue_from_recommendation()` expects an `IssueRecommendation` object (with AI-generated fields like `user_story`, `functional_requirements`, etc.). Chore-triggered issues use template content directly as the body, so we bypass the recommendation flow and create the issue via `github_service.create_issue()` directly. However, sub-issue creation and agent assignment should reuse `WorkflowOrchestrator.create_all_sub_issues()` which handles: iterating agents from config, tailoring body per agent, creating sub-issues, adding to project, handling branching strategy.

**Key methods to reuse**:
- `github_service.create_issue(access_token, owner, repo, title, body, labels)` — create parent issue
- `github_service.add_issue_to_project(access_token, project_id, issue_node_id)` — add to project board
- `WorkflowOrchestrator.create_all_sub_issues(ctx)` — create sub-issues per agent pipeline config
- `get_workflow_config(project_id)` — load agent pipeline configuration

**WorkflowContext inputs needed**: `access_token`, `repository_owner`, `repository_name`, `project_id`, `config`, `issue_id`, `issue_number`, `issue_url`, `issue_title`

**Alternatives considered**: Creating a synthetic `IssueRecommendation` to feed through `create_issue_from_recommendation()`; rejected because it adds unnecessary transformation and the body format would not match template content.

## Research 3: GitHub API Methods for Template Commit Workflow

**Decision**: Use existing `github_service` methods for the branch+commit+PR flow.

**Rationale**: All required GitHub API operations already exist in the service. No new API calls needed.

**Workflow sequence**:
1. `github_service.create_branch(access_token, repository_id, branch_name, from_oid)` — create branch from `main` HEAD
2. `github_service.commit_files(access_token, owner, repo, branch_name, head_oid, files, message)` — commit template file; `files=[{"path": ".github/ISSUE_TEMPLATE/chore-name.md", "content": "template content"}]`
3. `github_service.create_pull_request(access_token, repository_id, title, body, head_branch, base_branch)` — open PR targeting `main`
4. `github_service.create_issue(access_token, owner, repo, title, body, labels)` — create tracking issue
5. `github_service.add_issue_to_project(access_token, project_id, issue_node_id)` — add to project
6. `github_service.update_item_status(access_token, project_id, item_id, field_id, option_id)` — set "In review" status

**Key detail**: Need to obtain `from_oid` (the HEAD SHA of `main`) and `repository_id` (GraphQL node ID) before creating the branch. The service already handles these via existing internal methods.

**Alternatives considered**: Using REST API for file creation (PUT `/repos/{owner}/{repo}/contents/{path}`); rejected because the existing `commit_files` GraphQL approach supports multi-file commits atomically.

## Research 4: Chat Agent Integration for Sparse Input

**Decision**: Create a new chat endpoint (`POST /api/v1/chores/chat`) that leverages the existing `AIAgentService` for generating template content through multi-turn conversation, using the same in-memory message pattern as the existing chat.

**Rationale**: The existing chat system (`/api/v1/chat/messages`) is tightly coupled to feature request detection, status change, and task creation flows. Chore template generation is a distinct concern. A dedicated endpoint avoids polluting the main chat flow while reusing the same AI service infrastructure.

**Integration pattern**:
- Backend: New endpoint receives user messages in a chore-specific conversation thread. Uses `AIAgentService.generate_completion()` with a system prompt tailored for GitHub Issue Template generation. Maintains conversation state in memory (keyed by session + chore creation flow ID).
- Frontend: `ChoreChatFlow.tsx` component embeds a mini-chat interface within the `AddChoreModal`. Uses the existing chat UI patterns (message list, input box) but routes messages to the chores-specific endpoint.

**Alternatives considered**: 
1. Reusing the main `/chat/messages` endpoint with a special prefix/flag; rejected because it would require adding chore-specific branching logic to an already complex handler.
2. Opening the full `ChatPopup` for chore creation; rejected because the user flow requires the chat to be scoped within the add-chore modal context.

## Research 5: Trigger Evaluation / Scheduler Pattern

**Decision**: Follow the existing housekeeping pattern — trigger evaluation via HTTP endpoint called by external cron (GitHub Actions), not a background asyncio loop.

**Rationale**: The existing housekeeping system uses `POST /api/v1/housekeeping/evaluate-triggers` called by GitHub Actions cron. This pattern:
- Avoids long-running background tasks in the web server
- Prevents double-firing via atomic CAS (compare-and-swap) UPDATE queries
- Is observable (GitHub Actions logs show invocation history)
- Survives container restarts without missing triggers

The chore equivalent will be `POST /api/v1/chores/evaluate-triggers` with the same pattern. The existing CAS technique (`UPDATE ... WHERE last_triggered_at = {old_value}`) prevents concurrent evaluators from double-triggering.

**Alternatives considered**: 
1. In-process asyncio background task (`asyncio.create_task` in lifespan); rejected because the housekeeping pattern already works and an in-process scheduler would not survive container restarts, could double-fire in multi-instance deployments.
2. APScheduler or Celery; rejected because it adds dependencies and complexity for a simple periodic check.

## Research 6: Sparse Input Detection Heuristic

**Decision**: Classify input as "sparse" when it has ≤15 words without markdown structure, or ≤40 words with no headings, lists, or multi-line structure.

**Rationale**: Simple, deterministic heuristic that correctly handles extreme cases while providing reasonable defaults for the tweener range.

**Heuristic logic**:
```
rich indicators: markdown headings (##), list markers (- *), ≥3 newlines
if any rich indicator present → RICH
if word_count ≤ 15 → SPARSE
if word_count ≤ 40 AND single-line → SPARSE
else → RICH
```

**Test cases**:
- "create refactor chore" (3 words) → SPARSE ✓
- "bug bash review all code for security issues" (8 words) → SPARSE ✓
- Multi-paragraph detailed markdown with `##` headings → RICH ✓
- 30-word single sentence without structure → SPARSE ✓ (benefits from chat refinement)
- 50-word text without headings → RICH ✓ (likely intentional)

**Alternatives considered**: LLM-based classification; rejected because it adds latency, cost, and a dependency on AI for a UX routing decision that should be instant and deterministic.

## Research 7: Migration Numbering

**Decision**: Use `010_chores.sql` as the migration file name.

**Rationale**: Existing migrations go from `001` through `009_housekeeping.sql`. The next sequential number is `010`.

**Migration content**: Will DROP the three housekeeping tables (`housekeeping_templates`, `housekeeping_tasks`, `housekeeping_trigger_history`) and CREATE the new `chores` table.

**Alternatives considered**: Separate drop and create migrations (010 + 011); rejected because a single migration file is simpler and the feature atomically replaces housekeeping with chores.

## Research 8: API Router Registration

**Decision**: Add chores router and remove housekeeping router in `backend/src/api/__init__.py`.

**Rationale**: Straightforward replacement — same pattern as all other routers.

**Changes**:
1. Remove: `from src.api.housekeeping import router as housekeeping_router` and `router.include_router(housekeeping_router, ...)`
2. Add: `from src.api.chores import router as chores_router` and `router.include_router(chores_router, prefix="/chores", tags=["chores"])`
3. In `main.py`: Remove `HousekeepingService.initialize()` from lifespan, add any chores-specific initialization if needed.

**Alternatives considered**: None — the pattern is established and clear.
