"""Transcript detection utility for uploaded files.

Detects whether a file contains a meeting transcript based on its extension
and content patterns. Supports VTT, SRT, speaker-labeled, and timestamped
transcript formats.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ── Compiled regex patterns for content-based detection ──────────────────

# Speaker labels: "Speaker 1:", "John:", "[Jane]:", "  Alice :"
_SPEAKER_LABEL_RE = re.compile(r"^\s*\[?\w[\w\s]{0,30}\]?\s*:\s", re.MULTILINE)

# Timestamps: "00:00:00", "1:23:45.678", "01:02:03,456"
_TIMESTAMP_RE = re.compile(r"\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?")

# VTT header marker
_VTT_HEADER_RE = re.compile(r"^WEBVTT\b", re.MULTILINE)

# SRT/VTT time-range arrows: "00:00:01,000 --> 00:00:04,000"
_ARROW_RE = re.compile(r"\d+:\d{2}:\d{2}[.,]?\d*\s*-->\s*\d+:\d{2}:\d{2}")

# ── Thresholds ───────────────────────────────────────────────────────────

_SPEAKER_LABEL_THRESHOLD = 3
_TIMESTAMP_THRESHOLD = 5


@dataclass(frozen=True)
class TranscriptDetectionResult:
    """Result of transcript detection analysis.

    Attributes:
        is_transcript: Whether the file is detected as a transcript.
        format: Detected format — ``"vtt"``, ``"srt"``, ``"speaker_labeled"``,
            ``"timestamped"``, or ``None`` if not a transcript.
        confidence: Confidence score between 0.0 and 1.0.
    """

    is_transcript: bool
    format: str | None
    confidence: float


_NOT_TRANSCRIPT = TranscriptDetectionResult(is_transcript=False, format=None, confidence=0.0)


def detect_transcript(filename: str, content: str) -> TranscriptDetectionResult:
    """Detect whether *filename* with *content* is a meeting transcript.

    Detection is priority-ordered:

    1. **Extension-based** (high confidence): ``.vtt`` and ``.srt`` are always
       treated as transcripts.
    2. **VTT structural markers**: ``WEBVTT`` header in content.
    3. **SRT structural markers**: Time-range arrows (``-->``) in content.
    4. **Speaker labels**: ≥3 lines matching the speaker-label pattern.
    5. **Timestamps**: ≥5 timestamp occurrences.

    Returns ``TranscriptDetectionResult`` with ``is_transcript=False`` for
    anything that doesn't match the above heuristics.
    """
    if not filename:
        return _NOT_TRANSCRIPT

    ext = _get_extension(filename)

    # 1. Extension-based — always transcript (even with empty content)
    if ext == ".vtt":
        return TranscriptDetectionResult(is_transcript=True, format="vtt", confidence=1.0)
    if ext == ".srt":
        return TranscriptDetectionResult(is_transcript=True, format="srt", confidence=1.0)

    # Content-based detection requires non-empty content
    if not content:
        return _NOT_TRANSCRIPT

    # Only analyse content for text-like extensions
    if ext not in (".txt", ".md"):
        return _NOT_TRANSCRIPT

    # 2. VTT structural markers in content
    if _VTT_HEADER_RE.search(content):
        return TranscriptDetectionResult(is_transcript=True, format="vtt", confidence=0.95)

    # 3. SRT arrow markers in content
    if _ARROW_RE.search(content):
        return TranscriptDetectionResult(is_transcript=True, format="srt", confidence=0.95)

    # 4. Speaker labels
    speaker_matches = _SPEAKER_LABEL_RE.findall(content)
    if len(speaker_matches) >= _SPEAKER_LABEL_THRESHOLD:
        return TranscriptDetectionResult(
            is_transcript=True, format="speaker_labeled", confidence=0.8
        )

    # 5. Timestamps
    timestamp_matches = _TIMESTAMP_RE.findall(content)
    if len(timestamp_matches) >= _TIMESTAMP_THRESHOLD:
        return TranscriptDetectionResult(is_transcript=True, format="timestamped", confidence=0.7)

    return _NOT_TRANSCRIPT


def _get_extension(filename: str) -> str:
    """Return the lowercase file extension (including leading dot)."""
    dot_pos = filename.rfind(".")
    if dot_pos == -1:
        return ""
    return filename[dot_pos:].lower()
