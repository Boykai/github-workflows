"""Unit tests for #block detection and stripping in chat messages."""

from __future__ import annotations

import re

# The regex pattern used in chat.py for #block detection (no \s* — avoids ReDoS)
_BLOCK_PATTERN = re.compile(r"#block\b", re.IGNORECASE)


def _detect_and_strip(content: str) -> tuple[bool, str]:
    """Detect and strip #block from content, matching chat.py logic."""
    is_blocking = bool(_BLOCK_PATTERN.search(content))
    if is_blocking:
        content = " ".join(_BLOCK_PATTERN.sub("", content).split())
    return is_blocking, content


class TestBlockDetection:
    """Tests for #block detection and stripping."""

    def test_block_at_end(self):
        """#block at end of message is detected and stripped."""
        is_blocking, content = _detect_and_strip("Fix the login page #block")
        assert is_blocking is True
        assert content == "Fix the login page"

    def test_block_at_beginning(self):
        """#block at beginning of message is detected and stripped."""
        is_blocking, content = _detect_and_strip("#block Fix the login page")
        assert is_blocking is True
        assert content == "Fix the login page"

    def test_block_in_middle(self):
        """#block in middle of message is detected and stripped."""
        is_blocking, content = _detect_and_strip("Fix the #block login page")
        assert is_blocking is True
        assert content == "Fix the login page"

    def test_multiple_block_occurrences(self):
        """Multiple #block occurrences are all stripped."""
        is_blocking, content = _detect_and_strip("#block Fix #block the page #block")
        assert is_blocking is True
        assert content == "Fix the page"

    def test_case_insensitive_block(self):
        """#Block and #BLOCK are detected case-insensitively."""
        is_blocking, content = _detect_and_strip("Fix the login page #Block")
        assert is_blocking is True
        assert content == "Fix the login page"

        is_blocking2, content2 = _detect_and_strip("Fix page #BLOCK")
        assert is_blocking2 is True
        assert content2 == "Fix page"

    def test_no_block_present(self):
        """No #block in message → is_blocking=False, content unchanged."""
        is_blocking, content = _detect_and_strip("Fix the login page")
        assert is_blocking is False
        assert content == "Fix the login page"

    def test_blockchain_not_matched(self):
        """#blockchain should NOT match (word boundary)."""
        is_blocking, content = _detect_and_strip("Add #blockchain support")
        assert is_blocking is False
        assert content == "Add #blockchain support"

    def test_empty_after_strip(self):
        """Message that is only #block → empty string after strip."""
        is_blocking, content = _detect_and_strip("#block")
        assert is_blocking is True
        assert content == ""

    def test_block_with_extra_spaces(self):
        """#block with extra whitespace is handled correctly."""
        is_blocking, content = _detect_and_strip("Fix bug   #block  ")
        assert is_blocking is True
        assert "Fix bug" in content
