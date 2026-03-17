# Quickstart: Transcript Upload & Transcribe Agent

**Feature Branch**: `049-transcript-upload-transcribe` | **Date**: 2026-03-17

## Prerequisites

- Python 3.11+ with pip
- Node.js 22+ with npm
- GitHub OAuth token (for Copilot completion provider)
- Repository cloned and on feature branch

## Setup

```bash
# Clone and checkout feature branch
git checkout 049-transcript-upload-transcribe

# Backend setup
cd solune/backend
pip install -e ".[dev]"

# Frontend setup
cd ../frontend
npm install
```

## Development Workflow

### 1. Backend — Transcript Detection Utility

Create `solune/backend/src/services/transcript_detector.py`:

- [ ] Define `TranscriptDetectionResult` dataclass (3 fields: `is_transcript`, `format`, `confidence`)
- [ ] Implement extension-based detection (`.vtt` → always transcript, `.srt` → always transcript)
- [ ] Implement content-based regex patterns:
  - [ ] Speaker label pattern: `^\s*(?:\[?\w[\w\s]{0,30}\]?\s*:\s)` (threshold: ≥3 lines)
  - [ ] Timestamp pattern: `\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?` (threshold: ≥5 lines)
  - [ ] VTT header pattern: `^WEBVTT\b`
  - [ ] SRT arrow pattern: `\d+:\d{2}:\d{2}[.,]?\d*\s*-->\s*\d+:\d{2}:\d{2}`
- [ ] Implement `detect_transcript(filename, content)` with priority-ordered checks

### 2. Backend — Transcribe Agent Prompt

Create `solune/backend/src/prompts/transcript_analysis.py`:

- [ ] Define `TRANSCRIPT_ANALYSIS_SYSTEM_PROMPT` constant (follow `issue_generation.py` pattern)
- [ ] Implement `create_transcript_analysis_prompt(transcript_content, project_name, metadata_context)` factory
- [ ] Ensure output JSON schema matches `IssueRecommendation` fields

### 3. Backend — AIAgentService Integration

Modify `solune/backend/src/services/ai_agent.py`:

- [ ] Add `analyze_transcript()` method to `AIAgentService`
- [ ] Call `create_transcript_analysis_prompt()` → `self._call_completion(temperature=0.7, max_tokens=8000)` → `self._parse_issue_recommendation_response()`
- [ ] Set `original_input` to `transcript_content[:500]`

### 4. Backend — Chat API Integration

Modify `solune/backend/src/api/chat.py`:

- [ ] Add `.vtt` and `.srt` to `ALLOWED_DOC_TYPES` set
- [ ] Create `_handle_transcript_upload()` handler function
- [ ] Insert at Priority 0.5 in `send_message()` dispatch chain (after agent commands, before feature-request)
- [ ] Handle: check `file_urls` → read file content → `detect_transcript()` → `analyze_transcript()` → return `ChatMessage` with `action_type=ISSUE_CREATE`

### 5. Backend — Pipeline Integration

Modify `solune/backend/src/api/pipelines.py`:

- [ ] Add transcript detection at start of `launch_pipeline_issue()`
- [ ] If transcript: call `analyze_transcript()`, use generated title + formatted body
- [ ] If not transcript: existing behavior unchanged

### 6. Frontend — File Validation Updates

Modify `solune/frontend/src/types/index.ts`:

- [ ] Add `'.vtt'`, `'.srt'` to `FILE_VALIDATION.allowedDocTypes` array

Modify `solune/frontend/src/components/chat/ChatToolbar.tsx`:

- [ ] Add `text/vtt,.srt,.vtt` to file input `accept` attribute

Modify `solune/frontend/src/components/board/ProjectIssueLaunchPanel.tsx`:

- [ ] Add `'.vtt'`, `'.srt'` to `ACCEPTED_FILE_EXTENSIONS` array
- [ ] Update file input `accept` attribute to include `.vtt,.srt`
- [ ] Update error message to mention transcript formats

## Running Tests

```bash
# Backend — transcript detection unit tests
cd solune/backend
pytest tests/test_transcript_detector.py -v

# Backend — prompt construction tests
pytest tests/test_transcript_analysis_prompt.py -v

# Backend — Chat transcript integration tests
pytest tests/test_chat_transcript.py -v

# Backend — full regression suite
pytest --cov=src --cov-report=term-missing --durations=20

# Backend — linting
ruff check src tests
ruff format --check src tests
bandit -r src/ -ll -ii --skip B104,B608

# Frontend — type check
cd ../frontend
npm run type-check

# Frontend — linting
npm run lint

# Frontend — tests (if applicable)
npm run test
```

## Key Files Reference

| Priority | File | Action | Description |
|----------|------|--------|-------------|
| HIGH | `solune/backend/src/services/transcript_detector.py` | CREATE | Core detection utility — no external dependencies |
| HIGH | `solune/backend/src/prompts/transcript_analysis.py` | CREATE | Transcribe agent prompt — follow `issue_generation.py` pattern |
| HIGH | `solune/backend/src/services/ai_agent.py` | MODIFY | Add `analyze_transcript()` method |
| HIGH | `solune/backend/src/api/chat.py` | MODIFY | Priority 0.5 transcript dispatch + `.vtt`/`.srt` extensions |
| MEDIUM | `solune/backend/src/api/pipelines.py` | MODIFY | Transcript detection in pipeline launch |
| MEDIUM | `solune/frontend/src/types/index.ts` | MODIFY | Add `.vtt`/`.srt` to `allowedDocTypes` |
| MEDIUM | `solune/frontend/src/components/chat/ChatToolbar.tsx` | MODIFY | File input accept attribute |
| MEDIUM | `solune/frontend/src/components/board/ProjectIssueLaunchPanel.tsx` | MODIFY | Accept transcript files in intake |
| LOW | `solune/backend/tests/test_transcript_detector.py` | CREATE | Detection unit tests |
| LOW | `solune/backend/tests/test_transcript_analysis_prompt.py` | CREATE | Prompt tests |
| LOW | `solune/backend/tests/test_chat_transcript.py` | CREATE | Integration tests |

## Reference Files (read-only)

| File | Why |
|------|-----|
| `solune/backend/src/prompts/issue_generation.py` | Prompt template pattern to follow |
| `solune/backend/src/models/recommendation.py` | `IssueRecommendation` model (reused) |
| `solune/backend/src/services/completion_providers.py` | `CompletionProvider` interface |
| `solune/backend/tests/unit/test_ai_agent.py` | Test pattern with `MockCompletionProvider` |
| `solune/backend/tests/unit/test_api_chat.py` | Chat API test patterns |

## Verification Checklist

- [ ] Upload `.vtt` file in Chat → `IssueRecommendationPreview` appears with extracted requirements
- [ ] Confirm recommendation → parent issue + sub-issues created per pipeline
- [ ] Upload `.srt` file in Chat → same behavior as `.vtt`
- [ ] Upload speaker-labeled `.txt` in Chat → detected as transcript → recommendation appears
- [ ] Upload plain `.txt` (no speaker labels) in Chat → falls through to normal chat flow
- [ ] Upload transcript in Parent Issue Intake → structured requirements in created issue body
- [ ] Upload plain text in Parent Issue Intake → existing behavior unchanged
- [ ] `.vtt` and `.srt` visible in file pickers (both Chat and Intake)
- [ ] `ruff check solune/backend/src/` passes
- [ ] `npm run lint` passes (frontend)
- [ ] All existing tests pass (no regressions)

## Output

After completing all steps, the feature should:

1. Accept `.vtt`, `.srt`, `.txt`, and `.md` transcript files through both Chat and Parent Issue Intake
2. Automatically detect transcripts using extension + content analysis
3. Route detected transcripts through the Transcribe agent for requirement extraction
4. Present structured `IssueRecommendation` via existing preview UI
5. Create GitHub Parent Issues with structured requirements bodies and sub-issues via pipelines
6. Preserve all existing behavior for non-transcript files
