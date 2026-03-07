# Implementation Plan: Fix — Use Exact User Input + Chat Agent Metadata When AI Enhance Is Disabled

**Branch**: `029-fix-ai-enhance-disabled` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/029-fix-ai-enhance-disabled/spec.md`

## Summary

When users disable the AI Enhance toggle and submit a chat message, the system throws a generic error ("I couldn't generate a task from your description. Please try again with more detail.") because the issue creation pipeline unconditionally calls the AI enhancement step. The fix requires branching the pipeline into two explicit paths: (1) full AI pipeline when AI Enhance is enabled, and (2) metadata-only fallback when AI Enhance is disabled — using the user's verbatim chat input as the GitHub issue description while still invoking the Chat Agent to generate metadata (title, labels, estimates, priority, assignees) and appending Agent Pipeline configuration.

**Root Cause**: `backend/src/api/chat.py` line 432 — `generate_task_from_description()` is called unconditionally for non-feature-request, non-status-change messages. When AI Enhance is disabled, this call either fails or produces unwanted results, and the catch-all exception handler at line 465 returns the generic error message. The `ai_enhance` flag from the request is only passed through to `action_data` for feature requests (line 329) but never checked in the task generation fallback path (lines 430–476).

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/Node.js 20 (frontend)
**Primary Dependencies**: FastAPI (backend API), React (frontend UI), Pydantic (models)
**Storage**: In-memory dictionaries (`_proposals`, `_recommendations`) — lost on restart
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Linux server (backend), Web browser (frontend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Issue creation flow completes within same time threshold as AI Enhance–enabled flow
**Constraints**: Must not break existing AI Enhance–enabled behavior; structurally identical issues regardless of toggle state
**Scale/Scope**: Single API endpoint modification (`send_message`), single service method addition, minor frontend changes for error handling

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md complete with 4 prioritized user stories, Given-When-Then acceptance scenarios, edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | This is a bug fix within the existing agent pipeline; no new agents needed |
| IV. Test Optionality with Clarity | ✅ PASS | Tests not explicitly requested in spec; will be included only if existing test infrastructure covers the modified paths |
| V. Simplicity and DRY | ✅ PASS | Fix adds a conditional branch, not a new abstraction; reuses existing `generate_issue_recommendation()` for metadata |

**Gate result**: ✅ PASS — No violations. Proceed to Phase 0.

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | All user stories have corresponding implementation tasks mapped |
| II. Template-Driven Workflow | ✅ PASS | All artifacts generated from canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | No new agents; existing pipeline preserved |
| IV. Test Optionality with Clarity | ✅ PASS | Existing pytest tests for `send_message` and `ai_agent` should be extended to cover the new branch |
| V. Simplicity and DRY | ✅ PASS | Reuses existing metadata generation; single conditional branch in `send_message()` |

**Gate result**: ✅ PASS — No violations post-design.

## Project Structure

### Documentation (this feature)

```text
specs/029-fix-ai-enhance-disabled/
├── plan.md              # This file
├── research.md          # Phase 0 output — research decisions
├── data-model.md        # Phase 1 output — entity changes
├── quickstart.md        # Phase 1 output — developer guide
├── contracts/
│   ├── api.md           # Phase 1 output — API behavior contract changes
│   └── components.md    # Phase 1 output — frontend component behavior changes
├── checklists/
│   └── requirements.md  # Specification quality checklist (already exists)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── chat.py              # PRIMARY: send_message() pipeline branching
│   ├── models/
│   │   ├── chat.py              # ChatMessageRequest (no changes needed)
│   │   └── recommendation.py    # AITaskProposal, IssueRecommendation (no changes needed)
│   ├── services/
│   │   ├── ai_agent.py          # generate_task_from_description(), generate_issue_recommendation()
│   │   └── agent_tracking.py    # append_tracking_to_body() — Agent Pipeline config block
│   └── prompts/
│       ├── issue_generation.py  # Prompt for metadata generation
│       └── task_generation.py   # Prompt for task generation
└── tests/

frontend/
├── src/
│   ├── components/
│   │   └── chat/
│   │       ├── ChatInterface.tsx  # ai_enhance state management, sendMessage call
│   │       └── ChatToolbar.tsx    # AI Enhance toggle UI
│   └── types/
│       └── index.ts               # TypeScript interfaces
└── tests/
```

**Structure Decision**: Web application structure (Option 2). Changes are primarily in `backend/src/api/chat.py` (the `send_message()` function, lines 430–476) with potential minor adjustments to `backend/src/services/ai_agent.py` for a metadata-only generation method. Frontend changes are minimal — only error handling adjustments if needed.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.
