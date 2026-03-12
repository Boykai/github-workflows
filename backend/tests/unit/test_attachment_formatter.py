"""Tests for attachment_formatter (src/attachment_formatter.py).

Covers:
- Empty input
- Single image file (inline image syntax)
- Single document file (standard link syntax)
- Mixed file types (image + document + archive)
- Filename prefix stripping (upload ID removal)
- All image extensions use ![name](url) syntax
- Chat session reference text
- Separator present
- Multi-file ordering preserved
"""

from src.attachment_formatter import format_attachments_markdown


class TestFormatAttachmentsMarkdownEmpty:
    """format_attachments_markdown returns empty string for no URLs."""

    def test_empty_list_returns_empty_string(self):
        assert format_attachments_markdown([]) == ""

    def test_none_coerced_empty(self):
        """Passing an explicitly empty list still returns empty."""
        assert format_attachments_markdown(list()) == ""


class TestFormatAttachmentsMarkdownSingleFile:
    """Single-file formatting for images and documents."""

    def test_single_image_file(self):
        result = format_attachments_markdown(["/chat/uploads/a1b2c3d4-screenshot.png"])
        assert "![screenshot.png](/chat/uploads/a1b2c3d4-screenshot.png)" in result

    def test_single_document_file(self):
        result = format_attachments_markdown(["/chat/uploads/e5f6a7b8-report.pdf"])
        assert "[report.pdf](/chat/uploads/e5f6a7b8-report.pdf)" in result
        assert "![" not in result  # should NOT be inline image


class TestFormatAttachmentsMarkdownMixedTypes:
    """Mixed file types produce correct syntax per type."""

    def test_mixed_file_types(self):
        urls = [
            "/chat/uploads/a1a1a1a1-screenshot.png",
            "/chat/uploads/b2b2b2b2-report.pdf",
            "/chat/uploads/c3c3c3c3-data.zip",
        ]
        result = format_attachments_markdown(urls)
        assert "![screenshot.png]" in result
        assert "[report.pdf]" in result
        assert "[data.zip]" in result

    def test_ordering_preserved(self):
        """Multi-file entries appear in the same order as input."""
        urls = [
            "/chat/uploads/00000001-first.png",
            "/chat/uploads/00000002-second.pdf",
            "/chat/uploads/00000003-third.csv",
        ]
        result = format_attachments_markdown(urls)
        lines = result.strip().split("\n")
        # Find file entry lines (skip header lines)
        file_lines = [ln for ln in lines if ln.startswith("[") or ln.startswith("!")]
        assert len(file_lines) == 3
        assert "first.png" in file_lines[0]
        assert "second.pdf" in file_lines[1]
        assert "third.csv" in file_lines[2]


class TestFormatAttachmentsMarkdownPrefixStripping:
    """Upload ID prefix is stripped from displayed filenames."""

    def test_filename_prefix_stripping(self):
        result = format_attachments_markdown(["/chat/uploads/a1b2c3d4-my-document.txt"])
        assert "[my-document.txt]" in result

    def test_no_prefix_filename(self):
        """Filename without an upload ID prefix is rendered as-is."""
        result = format_attachments_markdown(["/chat/uploads/nodash.png"])
        assert "![nodash.png]" in result

    def test_natural_hyphen_preserved(self):
        """Filenames with natural hyphens (not upload ID) are preserved."""
        result = format_attachments_markdown(["/chat/uploads/my-feature-spec.pdf"])
        assert "[my-feature-spec.pdf]" in result


class TestFormatAttachmentsMarkdownImageExtensions:
    """All image extensions use inline image syntax."""

    IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]

    def test_all_image_extensions(self):
        for ext in self.IMAGE_EXTS:
            url = f"/chat/uploads/abcd1234-photo{ext}"
            result = format_attachments_markdown([url])
            assert f"![photo{ext}]" in result, f"Expected inline image for {ext}"


class TestFormatAttachmentsMarkdownStructure:
    """Structural elements: separator, header, chat reference."""

    def test_separator_present(self):
        result = format_attachments_markdown(["/chat/uploads/abcd1234-file.png"])
        assert "---" in result

    def test_header_present(self):
        result = format_attachments_markdown(["/chat/uploads/abcd1234-file.png"])
        assert "## Attachments" in result

    def test_chat_session_reference(self):
        result = format_attachments_markdown(["/chat/uploads/abcd1234-file.png"])
        assert "📎 Files shared from chat session" in result
