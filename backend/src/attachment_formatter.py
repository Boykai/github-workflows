"""Shared markdown attachment formatter for GitHub issue bodies.

Converts a list of file URLs into a formatted markdown attachments section
that is appended to the GitHub issue body when a proposal or recommendation
is confirmed.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}

# Matches the 8-char hex upload ID prefix added by upload_file() (e.g., "a1b2c3d4-")
_UPLOAD_ID_PREFIX = re.compile(r"^[0-9a-f]{8}-")

# Expected URL prefix for internally uploaded files.
_ALLOWED_URL_PREFIX = "/api/v1/chat/uploads/"

# Characters that break markdown link/image syntax (including backslash to
# prevent escape-sequence injection).
_MD_ESCAPE_RE = re.compile(r"([\[\]\(\)\\])")


def _escape_markdown(text: str) -> str:
    """Escape markdown-sensitive characters in link/alt text."""
    return _MD_ESCAPE_RE.sub(r"\\\1", text)


def _is_valid_upload_url(url: str) -> bool:
    """Return True if *url* matches the expected internal uploads prefix.

    Rejects URLs containing path-traversal sequences (``..``) even if the
    prefix is correct.
    """
    return isinstance(url, str) and url.startswith(_ALLOWED_URL_PREFIX) and ".." not in url


def format_attachments_markdown(file_urls: list[str]) -> str:
    """Convert file URLs to a markdown attachments section.

    Only URLs originating from the server's upload endpoint are included;
    external or malformed URLs are silently skipped.

    Image files use inline image syntax (![name](url));
    other files use standard link syntax ([name](url)).
    Returns empty string if no URLs provided or none are valid.
    """
    if not file_urls:
        return ""

    valid_urls = [u for u in file_urls if _is_valid_upload_url(u)]
    if not valid_urls:
        return ""

    lines = [
        "",
        "---",
        "",
        "## Attachments",
        "",
        "> 📎 Files shared from chat session",
        "",
    ]

    for url in valid_urls:
        filename = PurePosixPath(url).name
        # Strip upload ID prefix (e.g., "a1b2c3d4-screenshot.png" → "screenshot.png")
        filename = _UPLOAD_ID_PREFIX.sub("", filename)
        safe_name = _escape_markdown(filename)
        ext = PurePosixPath(filename).suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            lines.append(f"![{safe_name}]({url})")
        else:
            lines.append(f"[{safe_name}]({url})")

    return "\n".join(lines)
