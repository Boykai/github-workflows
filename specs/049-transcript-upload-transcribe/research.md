# Research: Transcript Upload & Transcribe Agent — Detection Patterns, Prompt Design, Integration Strategy

**Feature Branch**: `049-transcript-upload-transcribe` | **Date**: 2026-03-17

## Research Tasks

### R1: Transcript Detection Patterns and Thresholds

**Decision**: Use a tiered detection strategy — extension-based (high confidence) for `.vtt`/`.srt`, and regex-based content analysis for `.txt`/`.md` with configurable thresholds.

**Rationale**: The codebase already validates file extensions in both backend (`ALLOWED_DOC_TYPES` in `chat.py`) and frontend (`FILE_VALIDATION.allowedDocTypes` in `types/index.ts`). Extension-based detection for `.vtt`/`.srt` is deterministic and requires no content parsing. Content-based detection for `.txt`/`.md` needs pattern matching because these extensions are ambiguous — they could contain transcripts or regular documents.

**Alternatives Considered**:
- **ML-based classification** — Rejected because it introduces a heavy dependency (model loading, inference latency) for a problem that can be solved with simple regex patterns. Violates Constitution Principle V (Simplicity and DRY).
- **NLP sentence structure analysis** — Rejected because speaker-label and timestamp patterns are structurally distinctive enough for regex. NLP libraries (spaCy, NLTK) would add significant dependency weight for marginal accuracy improvement.
- **User-explicit toggle ("this is a transcript")** — Rejected because the spec mandates fully automatic detection (FR-013). A manual toggle could be added later but is out of scope.

**Proposed Detection Patterns**:

| Pattern | Regex | Example Matches | Threshold |
|---------|-------|-----------------|-----------|
| Speaker labels | `^\s*(?:\[?\w[\w\s]*\]?\s*:\s)` | `Alice:`, `Speaker 1:`, `[Jane]:` | ≥3 lines |
| Timestamps (HH:MM:SS) | `\d{1,2}:\d{2}:\d{2}` | `00:01:23`, `1:45:00.678` | ≥5 lines |
| VTT markers | `^WEBVTT` | `WEBVTT` header | Any occurrence |
| SRT arrows | `-->` | `00:00:01,000 --> 00:00:04,000` | Any occurrence |
| Numbered cue blocks | `^\d+\s*$` followed by timestamp | `1\n00:00:01,000 --> ...` | Combined with arrows |

**Confidence Scoring**:
- Extension `.vtt`/`.srt` → confidence 1.0
- Speaker labels ≥3 → confidence 0.8
- Timestamps ≥5 → confidence 0.7
- VTT/SRT structural markers → confidence 0.95
- Multiple patterns match → highest confidence wins

---

### R2: Transcribe Agent Prompt Design

**Decision**: Follow the existing `issue_generation.py` pattern — a comprehensive system prompt constant plus a factory function that injects transcript content and project context.

**Rationale**: The codebase has a well-established prompt engineering pattern in `solune/backend/src/prompts/issue_generation.py`. The system prompt (`ISSUE_GENERATION_SYSTEM_PROMPT`) provides behavioral instructions and output schema, while the factory function (`create_issue_generation_prompt()`) injects dynamic context (date, project name, metadata). Reusing this exact pattern ensures consistency, testability, and familiarity for developers.

**Alternatives Considered**:
- **LangChain prompt templates** — Rejected because the codebase doesn't use LangChain. Adding it would violate DRY (existing pattern works) and introduce unnecessary dependency.
- **Few-shot prompting with example transcripts** — Rejected for initial implementation. The system prompt provides enough structural guidance. Few-shot examples could be added later if quality is insufficient, but would significantly increase token usage.
- **Multi-step pipeline (summarize → extract → format)** — Rejected because a single-pass prompt is simpler and the existing `_call_completion()` infrastructure handles single completions. Multi-step adds latency and complexity without proven benefit for this use case.

**Proposed Prompt Structure**:
```
System Prompt:
  ├── Role definition: "You are a meeting transcript analyst..."
  ├── Task description: Identify speakers, extract requirements, synthesize user stories
  ├── Output schema: JSON matching IssueRecommendation fields
  │   ├── title, user_story, ui_ux_description
  │   ├── functional_requirements (list of strings)
  │   ├── technical_notes, metadata
  │   └── metadata.priority, metadata.size, metadata.labels
  └── Quality guidelines: prioritize by discussion emphasis, deduplicate, assign priorities

User Message:
  ├── Project name
  ├── Current date
  ├── Metadata context (labels, branches, milestones, collaborators)
  └── Full transcript content
```

**Temperature & Token Config**: 0.7 temperature, 8000 max_tokens — identical to `create_issue_generation_prompt()` usage in `AIAgentService.generate_issue_recommendation()`.

---

### R3: Chat Dispatch Integration Point

**Decision**: Insert transcript detection as **Priority 0.5** in the `send_message()` dispatch chain — after agent command handling (Priority 0) but before feature-request detection (Priority 1).

**Rationale**: The existing dispatch chain in `chat.py` uses a priority-based handler pattern:
- Priority 0: `_handle_agent_command()` — explicit user commands take precedence
- Priority 1: `_handle_feature_request()` — AI-detected feature requests
- Priority 2: `_handle_status_change()` — status change proposals
- Priority 3: `_handle_task_generation()` — task proposals

Transcript detection should happen before feature-request detection because:
1. A transcript file is a strong, unambiguous signal (file extension or content patterns)
2. Without Priority 0.5, a transcript would be processed as a generic feature request, losing the specialized extraction
3. If detection returns false (not a transcript), the file falls through to normal processing

**Alternatives Considered**:
- **Priority 1 (replace feature-request detection)** — Rejected because both can coexist. Non-transcript files should still go through feature-request detection.
- **Separate endpoint (`/chat/transcript`)** — Rejected because the spec requires automatic detection without user action (FR-013). A separate endpoint would require frontend routing logic.
- **Middleware/decorator approach** — Rejected because the dispatch chain pattern is already established and readable. Adding middleware would break the pattern.

**Proposed Integration Flow**:
```
send_message() receives ChatMessageRequest with file_urls
    │
    ▼
Priority 0: _handle_agent_command()
    │ (returns None if not agent command)
    ▼
Priority 0.5: _handle_transcript_upload()  ← NEW
    │ ├── Check file_urls for uploaded files
    │ ├── For each file: read content, run detect_transcript()
    │ ├── If transcript detected: analyze_transcript() → IssueRecommendation
    │ └── Return ChatMessage with action_type=ISSUE_CREATE
    │ (returns None if no transcript detected)
    ▼
Priority 1: _handle_feature_request()
    │ (continues existing flow)
    ▼
Priority 2–3: existing handlers
```

---

### R4: Pipeline Issue-Launch Integration

**Decision**: Add transcript detection at the start of `launch_pipeline_issue()` before GitHub issue creation. When detected, replace the raw transcript body with structured requirements from the Transcribe agent.

**Rationale**: The `launch_pipeline_issue()` endpoint in `pipelines.py` receives `PipelineIssueLaunchRequest` with an `issue_description` field. Currently, this description is used as-is for the GitHub issue body. For transcript content, we should extract structured requirements first, then use those as the issue body. The rest of the pipeline flow (tracking table, sub-issues, agent assignment) proceeds unchanged.

**Alternatives Considered**:
- **Frontend-side detection and separate request** — Rejected because it duplicates detection logic and the backend already has access to the content. Backend detection is authoritative.
- **Always run through AI (even for non-transcripts)** — Rejected because it would add latency to all pipeline launches and change existing behavior for non-transcript content.

**Proposed Integration Flow**:
```
launch_pipeline_issue() receives PipelineIssueLaunchRequest
    │
    ▼
detect_transcript(filename="inline", content=issue_description)
    │
    ├── IS transcript → analyze_transcript()
    │   ├── Use generated title (replace extracted heading)
    │   └── Use formatted requirements body (replace raw transcript)
    │
    └── NOT transcript → existing behavior unchanged
    │
    ▼
Create GitHub issue → add to project → create sub-issues → assign agent
```

---

### R5: File Type Extension Support (Frontend + Backend)

**Decision**: Add `.vtt` and `.srt` to both backend `ALLOWED_DOC_TYPES` and frontend `FILE_VALIDATION.allowedDocTypes`. Update file input `accept` attributes in ChatToolbar and ProjectIssueLaunchPanel.

**Rationale**: Backend and frontend maintain parallel file validation constants. The backend `ALLOWED_DOC_TYPES` in `chat.py` (line 68) controls server-side validation. The frontend `FILE_VALIDATION.allowedDocTypes` in `types/index.ts` (line 204) controls client-side UX (file picker filtering). Both must be updated in sync to allow `.vtt`/`.srt` files through the full upload pipeline.

**Alternatives Considered**:
- **New "transcript types" category** — Rejected because `.vtt`/`.srt` are text-based document formats. Adding them to `allowedDocTypes` is the simplest approach and doesn't require new validation categories.
- **Accept all file types and validate server-side only** — Rejected because the frontend file picker UX depends on the `accept` attribute to filter visible files. Users should see `.vtt`/`.srt` in the file picker.

**MIME Types for `accept` attributes**:
- `.vtt` → `text/vtt`
- `.srt` → `application/x-subrip` (no standard MIME; use extension-based acceptance `.srt`)
- For `ChatToolbar.tsx`: append `text/vtt,.srt,.vtt` to existing accept string
- For `ProjectIssueLaunchPanel.tsx`: append `.vtt,.srt` to existing `.md,.txt` accept

---

### R6: Reusing IssueRecommendation Model

**Decision**: Reuse the existing `IssueRecommendation` model as-is for transcript analysis output. No new models or fields required.

**Rationale**: `IssueRecommendation` (in `solune/backend/src/models/recommendation.py`) already contains all fields needed for transcript analysis output: `title`, `user_story`, `ui_ux_description`, `functional_requirements`, `technical_notes`, `metadata`, and `file_urls`. The existing issue recommendation preview UI (`IssueRecommendationPreview.tsx`) renders these fields, and the confirm → `execute_full_workflow` → `create_all_sub_issues` pipeline creates the parent issue and sub-issues from them.

**Alternatives Considered**:
- **New `TranscriptAnalysisResult` model** — Rejected because it would duplicate `IssueRecommendation` fields and require a new preview component and creation workflow. Violates DRY.
- **Extended `IssueRecommendation` with transcript-specific fields** — Rejected because no additional fields are needed. The `original_input` field stores the truncated transcript excerpt (first 500 chars) per FR-014, and `file_urls` stores the uploaded file references.

---

## Research Summary

| Topic | Status | Key Finding |
|-------|--------|-------------|
| R1: Detection patterns | ✅ Resolved | Tiered strategy: extension-based (.vtt/.srt → always transcript) + regex content analysis (.txt/.md → speaker labels ≥3, timestamps ≥5, structural markers) |
| R2: Prompt design | ✅ Resolved | Follow `issue_generation.py` pattern exactly: system prompt constant + factory function; output IssueRecommendation JSON schema |
| R3: Chat dispatch | ✅ Resolved | Priority 0.5 insertion between agent commands (P0) and feature-request detection (P1); returns None to fall through if no transcript |
| R4: Pipeline integration | ✅ Resolved | Detect-then-replace at start of `launch_pipeline_issue()`; non-transcripts pass through unchanged |
| R5: File type support | ✅ Resolved | Add `.vtt`/`.srt` to backend `ALLOWED_DOC_TYPES` and frontend `FILE_VALIDATION.allowedDocTypes`; update `accept` attributes in ChatToolbar and ProjectIssueLaunchPanel |
| R6: Model reuse | ✅ Resolved | Reuse `IssueRecommendation` as-is; no new models, fields, or DB migrations needed |

All NEEDS CLARIFICATION items have been resolved through codebase analysis and comparison with existing patterns.
