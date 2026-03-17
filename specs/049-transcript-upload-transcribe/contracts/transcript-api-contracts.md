# Transcript API Contracts

**Feature**: `049-transcript-upload-transcribe` | **Date**: 2026-03-17

## Contract: Transcript Detection Utility

The `detect_transcript()` function MUST provide deterministic, stateless transcript detection from a filename and content string.

### Function Signature

```python
def detect_transcript(filename: str, content: str) -> TranscriptDetectionResult:
    """Detect whether file content is a meeting transcript.

    Args:
        filename: Original filename with extension (e.g., "meeting.vtt").
        content: Full text content of the file.

    Returns:
        TranscriptDetectionResult with detection outcome, format, and confidence.
    """
```

### Behavioral Contracts

**Extension-Based Detection**:

| Input Extension | Expected Result |
|----------------|-----------------|
| `.vtt` | `TranscriptDetectionResult(is_transcript=True, format="vtt", confidence=1.0)` |
| `.srt` | `TranscriptDetectionResult(is_transcript=True, format="srt", confidence=1.0)` |
| `.txt` | Content-based analysis (see below) |
| `.md` | Content-based analysis (see below) |
| Any other | `TranscriptDetectionResult(is_transcript=False, format=None, confidence=0.0)` |

**Content-Based Detection** (for `.txt` and `.md` only):

The function MUST check content patterns in this priority order:
1. VTT structural markers (`WEBVTT` header) → `format="vtt"`, `confidence=0.95`
2. SRT structural markers (`-->` timestamp arrows) → `format="srt"`, `confidence=0.95`
3. Speaker labels (≥3 matching lines) → `format="speaker_labeled"`, `confidence=0.8`
4. Timestamps (≥5 matching lines) → `format="timestamped"`, `confidence=0.7`
5. None matched → `TranscriptDetectionResult(is_transcript=False, format=None, confidence=0.0)`

**Edge Cases**:
- Empty content (`""`) with `.txt`/`.md` extension → NOT a transcript
- Empty filename (`""`) → NOT a transcript (no extension to check)
- Content with exactly 2 speaker labels → NOT a transcript (below threshold of 3)
- Content with exactly 4 timestamps → NOT a transcript (below threshold of 5)
- Content matching multiple patterns → first match wins (highest priority)

---

## Contract: Transcribe Agent Prompt Factory

The `create_transcript_analysis_prompt()` function MUST produce a message list compatible with the `CompletionProvider.complete()` interface.

### Function Signature

```python
def create_transcript_analysis_prompt(
    transcript_content: str,
    project_name: str,
    metadata_context: dict | None = None,
) -> list[dict[str, str]]:
    """Create prompt messages for transcript analysis.

    Args:
        transcript_content: Full text of the transcript to analyze.
        project_name: Name of the project for context.
        metadata_context: Optional dict with 'labels', 'branches', 'milestones', 'collaborators'.

    Returns:
        List of message dicts with 'role' and 'content' keys.
    """
```

### Message Format Contract

The returned list MUST contain exactly 2 messages:

```python
[
    {"role": "system", "content": TRANSCRIPT_ANALYSIS_SYSTEM_PROMPT},
    {"role": "user", "content": "<dynamic prompt with transcript and context>"},
]
```

**System Prompt MUST instruct the AI to**:
- Identify speakers and their roles/perspectives
- Extract application features discussed
- Synthesize into user stories ("As a … I want … So that …")
- Derive functional requirements from discussed needs
- Capture UI/UX preferences mentioned
- Note technical constraints or decisions
- Assign priority based on discussion emphasis/frequency

**System Prompt MUST specify output JSON schema**:
```json
{
  "title": "string (max 256 chars)",
  "user_story": "string (As a/I want/So that format)",
  "ui_ux_description": "string",
  "functional_requirements": ["string", "..."],
  "technical_notes": "string",
  "metadata": {
    "priority": "P0|P1|P2|P3",
    "size": "XS|S|M|L|XL",
    "estimate_hours": "number (0.5-40)",
    "labels": ["string"],
    "assignees": ["string"]
  }
}
```

**User Message MUST include**:
- Current date (ISO 8601)
- Project name
- Available labels, milestones, collaborators (from metadata_context if provided)
- Full transcript content

---

## Contract: AIAgentService.analyze_transcript()

The `analyze_transcript()` method MUST follow the same pattern as `generate_issue_recommendation()`.

### Method Signature

```python
async def analyze_transcript(
    self,
    transcript_content: str,
    project_name: str,
    session_id: str,
    github_token: str,
    metadata_context: dict | None = None,
) -> IssueRecommendation:
    """Analyze a meeting transcript and generate an issue recommendation.

    Args:
        transcript_content: Full text of the transcript.
        project_name: Name of the project.
        session_id: Current session UUID.
        github_token: GitHub OAuth token for completion provider.
        metadata_context: Optional repo metadata (labels, branches, etc.).

    Returns:
        IssueRecommendation populated from AI analysis.

    Raises:
        ValueError: If AI completion fails or response cannot be parsed.
    """
```

### Behavioral Contracts

- MUST call `create_transcript_analysis_prompt()` to build messages
- MUST call `self._call_completion()` with `temperature=0.7`, `max_tokens=8000`
- MUST call `self._parse_issue_recommendation_response()` to parse the AI response
- MUST set `original_input` to `transcript_content[:500]` (first 500 characters)
- MUST propagate `ValueError` on AI completion failure or invalid JSON
- MUST NOT modify the transcript content before passing to the prompt factory

---

## Contract: Chat Flow Integration

The `send_message()` function in `chat.py` MUST insert transcript handling at Priority 0.5.

### Dispatch Order Contract

```
Priority 0:   _handle_agent_command()        # Explicit agent commands
Priority 0.5: _handle_transcript_upload()    # NEW — transcript file detection
Priority 1:   _handle_feature_request()      # Feature request detection
Priority 2:   _handle_status_change()        # Status change proposals
Priority 3:   _handle_task_generation()       # Task proposals
```

### _handle_transcript_upload() Contract

```python
async def _handle_transcript_upload(
    chat_request: ChatMessageRequest,
    session: UserSession,
    user_message: ChatMessage,
    ai_service: AIAgentService,
) -> ChatMessage | None:
    """Handle transcript file uploads in chat.

    Returns:
        ChatMessage with action_type=ISSUE_CREATE if transcript detected,
        None if no transcript found (falls through to next priority).
    """
```

**Behavioral Contracts**:
- MUST check `chat_request.file_urls` for uploaded files
- MUST read file content from the stored file path for each URL
- MUST call `detect_transcript(filename, content)` for each file
- If ANY file is detected as transcript:
  - MUST call `ai_service.analyze_transcript()` with the transcript content
  - MUST store the resulting `IssueRecommendation` via `_persist_recommendation()`
  - MUST return a `ChatMessage` with `action_type="ISSUE_CREATE"`
- If NO files are transcripts:
  - MUST return `None` to allow fallthrough to Priority 1

---

## Contract: Pipeline Launch Integration

The `launch_pipeline_issue()` endpoint in `pipelines.py` MUST detect transcripts in the issue description before creating the GitHub issue.

### Behavioral Contracts

- MUST call `detect_transcript("inline", issue_description)` before issue creation
- If transcript detected:
  - MUST call `ai_service.analyze_transcript()` with the description content
  - MUST use the generated `title` as the GitHub issue title (replacing heading extraction)
  - MUST format the `IssueRecommendation` fields as the issue body (user_story + functional_requirements + technical_notes)
  - MUST continue with normal pipeline flow (tracking table, sub-issues, agent assignment)
- If NOT transcript:
  - MUST NOT alter existing behavior
  - MUST use existing title extraction (heading or first line)
  - MUST use `issue_description` as-is for the issue body

---

## Contract: Frontend File Validation

### FILE_VALIDATION Update

```typescript
export const FILE_VALIDATION = {
  // ... existing fields unchanged ...
  allowedDocTypes: ['.pdf', '.txt', '.md', '.csv', '.json', '.yaml', '.yml', '.vtt', '.srt'],
  // ... rest unchanged ...
} as const;
```

### ChatToolbar Accept Attribute

The file input `accept` attribute MUST include `.vtt` and `.srt` MIME types/extensions:
```
"image/png,...existing types...,text/vtt,.srt,.vtt"
```

### ProjectIssueLaunchPanel Updates

**ACCEPTED_FILE_EXTENSIONS** MUST include `.vtt` and `.srt`:
```typescript
const ACCEPTED_FILE_EXTENSIONS = ['.md', '.txt', '.vtt', '.srt'];
```

**isAcceptedIssueFile()** MUST accept `.vtt` and `.srt` files.

**File input accept attribute** MUST include `.vtt` and `.srt`:
```
".md,.txt,.vtt,.srt,text/plain,text/markdown,text/vtt"
```

**Error message** MUST be updated to include transcript formats:
```
"Only Markdown (.md), plain-text (.txt), and transcript (.vtt, .srt) files are supported."
```
