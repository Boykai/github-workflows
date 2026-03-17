# Implementation Plan: Transcript Upload & Transcribe Agent

**Branch**: `049-transcript-upload-transcribe` | **Date**: 2026-03-17 | **Spec**: ./spec.md
**Input**: Feature specification from `/specs/049-transcript-upload-transcribe/spec.md`

## Summary

Add transcript file upload support (`.vtt`, `.srt`, `.txt`, `.md` with content detection) to both the Chat interface and Parent Issue Intake panel. When a transcript file is detected, automatically route it through a new **Transcribe agent** that extracts user requirements and user stories from multi-speaker meeting conversations. The agent outputs a structured `IssueRecommendation` — reusing the existing model — which feeds into the existing confirm → `execute_full_workflow` → `create_all_sub_issues` pipeline to create a GitHub Parent Issue with sub-issues.

The implementation spans three layers: (1) a backend transcript detection utility with regex-based content analysis, (2) a new Transcribe agent prompt following the existing `issue_generation.py` pattern, and (3) frontend file validation updates to accept `.vtt`/`.srt` extensions. No new data models, database migrations, or UI components are required.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x / React 19 (frontend)
**Primary Dependencies**: FastAPI, Pydantic, pytest (backend); Vite, Vitest, React Testing Library (frontend)
**Storage**: SQLite (existing `ChatStore` for message/recommendation persistence — no changes)
**Testing**: pytest with `asyncio_mode="auto"` (backend), Vitest + RTL (frontend)
**Target Platform**: Linux server (backend API), modern browsers (frontend SPA)
**Project Type**: Web application (backend + frontend under `solune/`)
**Performance Goals**: Transcript detection < 50ms for files up to 1MB; AI analysis response within 30 seconds (SC-001)
**Constraints**: Reuse existing `IssueRecommendation` model (no DB migrations); detection must produce zero false positives on standard prose (SC-004)
**Scale/Scope**: 4 user stories, ~8 files modified/created, ~3 new test files; no new UI components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | `spec.md` contains 4 prioritized user stories (P1–P3) with Given-When-Then acceptance scenarios, edge cases, 14 functional requirements, and clear out-of-scope declarations |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates (`plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`) |
| **III. Agent-Orchestrated** | ✅ PASS | Single-responsibility Transcribe agent with clear input (transcript content) → output (`IssueRecommendation`); integrates into existing dispatch chain |
| **IV. Test Optionality** | ✅ PASS | Tests are included per spec requirement (Phase 3 in issue); follows existing `test_ai_agent.py` and `test_api_chat.py` patterns |
| **V. Simplicity and DRY** | ✅ PASS | Reuses `IssueRecommendation` model, `_parse_recommendation_response()`, `_call_completion()`, and existing issue creation workflow. No new data models, DB migrations, or UI components. `TranscriptDetectionResult` is the only new entity |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

### Post-Phase 1 Re-Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All 4 user stories mapped to implementation steps; acceptance scenarios covered by test plan |
| **II. Template-Driven** | ✅ PASS | Plan, research, data-model, contracts, and quickstart all follow canonical templates |
| **III. Agent-Orchestrated** | ✅ PASS | Transcribe agent prompt follows `issue_generation.py` pattern exactly (system prompt + factory function); dispatch integrated at Priority 0.5 in Chat handler chain |
| **IV. Test Optionality** | ✅ PASS | 3 new test files specified: `test_transcript_detector.py`, `test_transcript_analysis_prompt.py`, `test_chat_transcript.py`; frontend test updates for file validation |
| **V. Simplicity and DRY** | ✅ PASS | Only 1 new entity (`TranscriptDetectionResult` dataclass). All AI completion, JSON parsing, and issue creation logic reused from existing services. No new abstractions |

**Gate Result**: ✅ ALL PASS — proceed to Phase 2 (tasks generation).

## Project Structure

### Documentation (this feature)

```text
specs/049-transcript-upload-transcribe/
├── plan.md              # This file
├── research.md          # Phase 0: Detection patterns, prompt design, integration strategy
├── data-model.md        # Phase 1: TranscriptDetectionResult entity, state transitions
├── quickstart.md        # Phase 1: Developer setup and verification guide
├── contracts/
│   └── transcript-api-contracts.md   # Phase 1: Backend API contracts for transcript flow
├── checklists/
│   └── requirements.md  # Spec phase requirements checklist
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/backend/
├── src/
│   ├── api/
│   │   ├── chat.py                          # MODIFY: add .vtt/.srt to ALLOWED_DOC_TYPES; Priority 0.5 transcript dispatch
│   │   └── pipelines.py                     # MODIFY: transcript detection in launch_pipeline_issue()
│   ├── prompts/
│   │   ├── issue_generation.py              # REFERENCE: prompt template pattern to follow
│   │   └── transcript_analysis.py           # CREATE: Transcribe agent system prompt + factory
│   ├── services/
│   │   ├── ai_agent.py                      # MODIFY: add analyze_transcript() method
│   │   ├── completion_providers.py          # REFERENCE: CompletionProvider interface (unchanged)
│   │   └── transcript_detector.py           # CREATE: detect_transcript() utility
│   └── models/
│       └── recommendation.py                # REFERENCE: IssueRecommendation model (unchanged)
└── tests/
    ├── unit/
    │   ├── test_ai_agent.py                 # REFERENCE: existing test pattern
    │   └── test_api_chat.py                 # REFERENCE: existing test pattern
    ├── test_transcript_detector.py          # CREATE: detection unit tests
    ├── test_transcript_analysis_prompt.py   # CREATE: prompt construction tests
    └── test_chat_transcript.py              # CREATE: Chat transcript integration tests

solune/frontend/
├── src/
│   ├── types/
│   │   └── index.ts                         # MODIFY: add .vtt/.srt to FILE_VALIDATION.allowedDocTypes
│   ├── components/
│   │   ├── chat/
│   │   │   └── ChatToolbar.tsx              # MODIFY: file input accept attribute
│   │   └── board/
│   │       └── ProjectIssueLaunchPanel.tsx   # MODIFY: isAcceptedIssueFile() + file input accept
│   └── components/chat/
│       └── IssueRecommendationPreview.tsx   # REFERENCE: renders recommendations (unchanged)
└── src/components/board/
    └── ProjectIssueLaunchPanel.test.tsx      # MODIFY: add .vtt/.srt extension tests
```

**Structure Decision**: Web application structure (Option 2). Feature spans `solune/backend/` (Python/FastAPI) and `solune/frontend/` (TypeScript/React). All new backend files are placed in existing directories following established conventions. No new directories created except `specs/049-transcript-upload-transcribe/contracts/`.

## Complexity Tracking

> No violations identified. The feature reuses existing models (`IssueRecommendation`), existing services (`_call_completion`, `_parse_recommendation_response`), and existing UI components (`IssueRecommendationPreview`). The only new entity is `TranscriptDetectionResult` — a simple dataclass with 3 fields. No new abstractions, patterns, or architectural changes are introduced.
