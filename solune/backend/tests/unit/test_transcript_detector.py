"""Unit tests for the transcript detection utility."""

import pytest

from src.services.transcript_detector import detect_transcript

# ── Extension-based detection ────────────────────────────────────────────


class TestExtensionBasedDetection:
    """Files with .vtt or .srt extensions are always detected as transcripts."""

    def test_vtt_extension_detected(self):
        result = detect_transcript("meeting.vtt", "WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nHello")
        assert result.is_transcript is True
        assert result.format == "vtt"
        assert result.confidence == 1.0

    def test_srt_extension_detected(self):
        result = detect_transcript("meeting.srt", "1\n00:00:01,000 --> 00:00:04,000\nHello")
        assert result.is_transcript is True
        assert result.format == "srt"
        assert result.confidence == 1.0

    def test_vtt_extension_case_insensitive(self):
        result = detect_transcript("MEETING.VTT", "some content")
        assert result.is_transcript is True
        assert result.format == "vtt"

    def test_srt_extension_case_insensitive(self):
        result = detect_transcript("recap.SRT", "some content")
        assert result.is_transcript is True
        assert result.format == "srt"

    def test_vtt_extension_minimal_content(self):
        """Even with minimal content, .vtt extension wins."""
        result = detect_transcript("notes.vtt", "just text")
        assert result.is_transcript is True
        assert result.format == "vtt"
        assert result.confidence == 1.0

    def test_vtt_extension_empty_content(self):
        """Extension-based detection classifies .vtt even with empty content."""
        result = detect_transcript("empty.vtt", "")
        assert result.is_transcript is True
        assert result.format == "vtt"
        assert result.confidence == 1.0

    def test_srt_extension_empty_content(self):
        """Extension-based detection classifies .srt even with empty content."""
        result = detect_transcript("empty.srt", "")
        assert result.is_transcript is True
        assert result.format == "srt"
        assert result.confidence == 1.0


# ── Content-based detection (VTT markers) ────────────────────────────────


class TestVTTMarkerDetection:
    """VTT structural markers in .txt/.md files."""

    def test_webvtt_header_in_txt(self):
        content = "WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nHello everyone"
        result = detect_transcript("transcript.txt", content)
        assert result.is_transcript is True
        assert result.format == "vtt"
        assert result.confidence == 0.95

    def test_webvtt_header_in_md(self):
        content = "WEBVTT\n\nSome content"
        result = detect_transcript("notes.md", content)
        assert result.is_transcript is True
        assert result.format == "vtt"
        assert result.confidence == 0.95


# ── Content-based detection (SRT arrows) ─────────────────────────────────


class TestSRTArrowDetection:
    """SRT time-range arrow markers in .txt/.md files."""

    def test_srt_arrows_in_txt(self):
        content = "1\n00:00:01,000 --> 00:00:04,000\nHello world"
        result = detect_transcript("caption.txt", content)
        assert result.is_transcript is True
        assert result.format == "srt"
        assert result.confidence == 0.95

    def test_srt_arrows_in_md(self):
        content = "1\n00:00:01.000 --> 00:00:04.000\nHi"
        result = detect_transcript("recap.md", content)
        assert result.is_transcript is True
        assert result.format == "srt"
        assert result.confidence == 0.95


# ── Content-based detection (speaker labels) ─────────────────────────────


class TestSpeakerLabelDetection:
    """Speaker-labeled transcripts in .txt/.md files."""

    def test_speaker_labels_txt(self):
        content = (
            "Alice: I think we should add dark mode.\n"
            "Bob: Agreed, let me check the design.\n"
            "Alice: Also we need responsive layout.\n"
            "Charlie: I'll handle the CSS changes.\n"
        )
        result = detect_transcript("meeting.txt", content)
        assert result.is_transcript is True
        assert result.format == "speaker_labeled"
        assert result.confidence == 0.8

    def test_speaker_labels_md(self):
        content = (
            "Speaker 1: Welcome everyone.\n"
            "Speaker 2: Thanks for joining.\n"
            "Speaker 1: Let's discuss the roadmap.\n"
        )
        result = detect_transcript("notes.md", content)
        assert result.is_transcript is True
        assert result.format == "speaker_labeled"

    def test_bracketed_speaker_labels(self):
        content = (
            "[Jane]: Let's start the standup.\n"
            "[Mike]: I finished the API work.\n"
            "[Jane]: Great, what's next?\n"
        )
        result = detect_transcript("standup.txt", content)
        assert result.is_transcript is True
        assert result.format == "speaker_labeled"

    def test_speaker_labels_below_threshold(self):
        """Only 2 speaker labels — below the threshold of 3."""
        content = "Alice: Hello\nBob: Hi there\nJust regular notes about the project.\n"
        result = detect_transcript("notes.txt", content)
        assert result.is_transcript is False


# ── Content-based detection (timestamps) ─────────────────────────────────


class TestTimestampDetection:
    """Timestamped content in .txt/.md files."""

    def test_timestamps_in_txt(self):
        content = (
            "00:00:10 Meeting starts\n"
            "00:01:30 Alice introduces the topic\n"
            "00:05:00 Bob presents the design\n"
            "00:10:15 Discussion about implementation\n"
            "00:15:45 Action items reviewed\n"
        )
        result = detect_transcript("meeting.txt", content)
        assert result.is_transcript is True
        assert result.format == "timestamped"
        assert result.confidence == 0.7

    def test_timestamps_below_threshold(self):
        """Only 4 timestamps — below the threshold of 5."""
        content = "00:00:10 Start\n00:01:30 Topic 1\n00:05:00 Topic 2\n00:10:15 End\n"
        result = detect_transcript("notes.txt", content)
        assert result.is_transcript is False


# ── Non-transcript detection (passthrough) ───────────────────────────────


class TestNonTranscriptDetection:
    """Regular files that should NOT be detected as transcripts."""

    def test_plain_prose_txt(self):
        content = (
            "This is a regular document about our project.\n"
            "We should consider adding new features.\n"
            "The deadline is next Friday.\n"
        )
        result = detect_transcript("notes.txt", content)
        assert result.is_transcript is False
        assert result.format is None
        assert result.confidence == 0.0

    def test_standard_markdown(self):
        content = (
            "# Project Plan\n\n"
            "## Phase 1\n\n"
            "- Add authentication\n"
            "- Create dashboard\n"
            "- Set up CI/CD\n"
        )
        result = detect_transcript("plan.md", content)
        assert result.is_transcript is False

    def test_empty_content(self):
        result = detect_transcript("empty.txt", "")
        assert result.is_transcript is False

    def test_empty_filename(self):
        result = detect_transcript("", "some content")
        assert result.is_transcript is False

    def test_none_like_empty(self):
        """Both filename and content empty."""
        result = detect_transcript("", "")
        assert result.is_transcript is False

    def test_non_text_extension(self):
        """Non-text extensions are not analysed."""
        content = "Alice: Hello\nBob: Hi\nCharlie: Hey"
        result = detect_transcript("image.png", content)
        assert result.is_transcript is False

    def test_csv_extension_not_analysed(self):
        content = "Speaker: data\nAnother: row\nThird: entry"
        result = detect_transcript("data.csv", content)
        assert result.is_transcript is False

    def test_json_extension_not_analysed(self):
        content = '{"speaker": "Alice", "text": "Hello"}'
        result = detect_transcript("data.json", content)
        assert result.is_transcript is False


# ── Edge cases ───────────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases and mixed format content."""

    def test_mixed_vtt_and_speakers_vtt_wins(self):
        """VTT header takes priority over speaker labels."""
        content = "WEBVTT\n\nAlice: Hello\nBob: Hi\nCharlie: Hey\n"
        result = detect_transcript("mixed.txt", content)
        assert result.is_transcript is True
        assert result.format == "vtt"  # VTT marker has higher priority

    def test_mixed_srt_arrows_and_speakers(self):
        """SRT arrows take priority over speaker labels."""
        content = (
            "1\n00:00:01,000 --> 00:00:04,000\nAlice: Hello everyone\nBob: Hi\nCharlie: Welcome\n"
        )
        result = detect_transcript("mixed.txt", content)
        assert result.is_transcript is True
        assert result.format == "srt"  # Arrow marker has higher priority

    def test_transcript_detection_result_is_frozen(self):
        result = detect_transcript("test.vtt", "content")
        with pytest.raises(AttributeError):
            result.is_transcript = False  # type: ignore[misc]
