# Data Model: Transcript Upload & Transcribe Agent — Entities, Validation, State Transitions

**Feature Branch**: `049-transcript-upload-transcribe` | **Date**: 2026-03-17

## Overview

This feature introduces one new entity (`TranscriptDetectionResult`) and reuses one existing entity (`IssueRecommendation`). No database migrations are required. The data model focuses on the detection result dataclass and the state transitions through the transcript processing pipeline.

## Entity Diagram

```text
┌─────────────────────────────────┐
│       Uploaded File             │
│  (filename, content, extension) │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│   TranscriptDetectionResult     │  ← NEW
│  is_transcript: bool            │
│  format: str | None             │
│  confidence: float              │
└──────────────┬──────────────────┘
               │
               ├── is_transcript = False → Fall through to normal flow
               │
               └── is_transcript = True
                        │
                        ▼
              ┌───────────────────┐
              │  Transcribe Agent │
              │  (AI Completion)  │
              └────────┬──────────┘
                       │
                       ▼
              ┌───────────────────────────┐
              │   IssueRecommendation     │  ← EXISTING (reused)
              │  title, user_story,       │
              │  functional_requirements, │
              │  metadata, file_urls      │
              └────────┬──────────────────┘
                       │
                       ▼
              ┌───────────────────────────┐
              │  Existing Pipeline Flow   │
              │  confirm → create issue   │
              │  → create sub-issues      │
              └───────────────────────────┘
```

## Entities

### TranscriptDetectionResult *(NEW)*

Represents the outcome of analyzing a file or content string for transcript patterns. This is a lightweight dataclass — not a database model — used as a return type from the `detect_transcript()` utility function.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `is_transcript` | `bool` | ✅ | Whether the content was identified as a meeting transcript |
| `format` | `str \| None` | ✅ | Detected format: `"vtt"`, `"srt"`, `"speaker_labeled"`, `"timestamped"`, or `None` |
| `confidence` | `float` | ✅ | Confidence score between 0.0 and 1.0 |

**Validation Rules**:
- `confidence` MUST be in range `[0.0, 1.0]`
- `format` MUST be `None` when `is_transcript` is `False`
- `format` MUST be one of the defined format strings when `is_transcript` is `True`
- `is_transcript` MUST be `True` when `confidence > 0.0`

**Implementation**:
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class TranscriptDetectionResult:
    is_transcript: bool
    format: str | None  # "vtt" | "srt" | "speaker_labeled" | "timestamped" | None
    confidence: float   # 0.0 to 1.0
```

**Format Values**:

| Format | Triggered By | Confidence |
|--------|-------------|------------|
| `"vtt"` | `.vtt` extension OR `WEBVTT` header in content | 1.0 (extension) / 0.95 (content) |
| `"srt"` | `.srt` extension OR `-->` arrows with numbered cue blocks | 1.0 (extension) / 0.95 (content) |
| `"speaker_labeled"` | ≥3 lines matching speaker label pattern in `.txt`/`.md` | 0.8 |
| `"timestamped"` | ≥5 lines matching timestamp pattern in `.txt`/`.md` | 0.7 |
| `None` | No transcript patterns detected | 0.0 |

---

### IssueRecommendation *(EXISTING — reused as-is)*

The existing `IssueRecommendation` model from `solune/backend/src/models/recommendation.py` is reused without modification. For transcript-generated recommendations, fields are populated as follows:

| Field | Type | Transcript-Specific Usage |
|-------|------|---------------------------|
| `recommendation_id` | `UUID` | Auto-generated |
| `session_id` | `UUID` | From current chat session or pipeline session |
| `original_input` | `str` | Truncated transcript excerpt (first 500 characters) per FR-014 |
| `original_context` | `str` | Full transcript content preserved verbatim |
| `title` | `str` | AI-generated summary title from transcript analysis |
| `user_story` | `str` | Synthesized "As a / I want / So that" from speaker discussions |
| `ui_ux_description` | `str` | UI/UX preferences mentioned in transcript |
| `functional_requirements` | `list[str]` | Requirements extracted from discussed needs |
| `technical_notes` | `str` | Technical constraints or decisions from transcript |
| `selected_pipeline_id` | `str \| None` | From user's pipeline selection |
| `metadata` | `IssueMetadata` | Priority based on discussion emphasis; labels from repo context |
| `status` | `RecommendationStatus` | `PENDING` on creation |
| `file_urls` | `list[str]` | URLs of uploaded transcript files |

---

## State Transitions

### Chat Path — Transcript Processing States

```text
[File Uploaded]
    │
    ▼
[Detecting] ──── is_transcript=False ──→ [Normal Chat Flow]
    │                                     (feature-request detection etc.)
    │ is_transcript=True
    ▼
[Analyzing] ──── AI completion error ──→ [Error Response]
    │                                     (ValueError with context)
    │ success
    ▼
[Recommendation Created]
    │ (status=PENDING, action_type=ISSUE_CREATE)
    │
    ▼
[Displayed in IssueRecommendationPreview]
    │
    ├── User confirms ──→ [execute_full_workflow]
    │                      ├── Create parent issue
    │                      ├── Create sub-issues
    │                      └── Assign agents
    │
    └── User declines ──→ [Recommendation Rejected]
                           (status=REJECTED)
```

### Pipeline Path — Transcript Processing States

```text
[Issue Description Submitted]
    │
    ▼
[Detecting] ──── is_transcript=False ──→ [Normal Pipeline Flow]
    │                                     (use description as-is)
    │ is_transcript=True
    ▼
[Analyzing] ──── AI completion error ──→ [Error Response]
    │                                     (WorkflowResult with error)
    │ success
    ▼
[Requirements Extracted]
    │ (title from AI, body from formatted requirements)
    ▼
[Create GitHub Issue with Structured Body]
    │
    ▼
[Normal Pipeline Continuation]
    ├── Add to project
    ├── Create sub-issues
    └── Assign first agent
```

### Detection Decision Tree

```text
Input: (filename, content)
    │
    ├── Extension is .vtt?
    │   └── YES → TranscriptDetectionResult(True, "vtt", 1.0)
    │
    ├── Extension is .srt?
    │   └── YES → TranscriptDetectionResult(True, "srt", 1.0)
    │
    ├── Extension is .txt or .md?
    │   │
    │   ├── Content has WEBVTT header?
    │   │   └── YES → TranscriptDetectionResult(True, "vtt", 0.95)
    │   │
    │   ├── Content has --> arrows?
    │   │   └── YES → TranscriptDetectionResult(True, "srt", 0.95)
    │   │
    │   ├── Speaker labels ≥ 3 lines?
    │   │   └── YES → TranscriptDetectionResult(True, "speaker_labeled", 0.8)
    │   │
    │   ├── Timestamps ≥ 5 lines?
    │   │   └── YES → TranscriptDetectionResult(True, "timestamped", 0.7)
    │   │
    │   └── None of the above
    │       └── TranscriptDetectionResult(False, None, 0.0)
    │
    └── Other extension?
        └── TranscriptDetectionResult(False, None, 0.0)
```

## Regex Patterns Reference

Concrete regex patterns for content-based detection:

```python
import re

# Speaker label pattern: "Name:", "[Name]:", "Speaker N:"
# Matches start of line, optional whitespace, optional brackets, word chars, colon
SPEAKER_LABEL_PATTERN = re.compile(
    r"^\s*(?:\[?\w[\w\s]{0,30}\]?\s*:\s)",
    re.MULTILINE,
)

# Timestamp pattern: "HH:MM:SS" or "H:MM:SS" with optional milliseconds
TIMESTAMP_PATTERN = re.compile(
    r"\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?",
)

# VTT header: "WEBVTT" at start of content
VTT_HEADER_PATTERN = re.compile(r"^WEBVTT\b", re.MULTILINE)

# SRT arrow: "-->" used in timestamp ranges
SRT_ARROW_PATTERN = re.compile(r"\d+:\d{2}:\d{2}[.,]?\d*\s*-->\s*\d+:\d{2}:\d{2}")
```

## No Database Migration Required

The feature does not introduce any new database tables, columns, or indexes:

- `TranscriptDetectionResult` is an in-memory dataclass, not a persisted model
- `IssueRecommendation` is reused as-is — already stored by `ChatStore._persist_recommendation()`
- `ChatMessage` with `action_type=ISSUE_CREATE` is already supported by the existing schema
- Pipeline `WorkflowResult` model is unchanged
