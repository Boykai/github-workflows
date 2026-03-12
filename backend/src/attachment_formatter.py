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


def format_attachments_markdown(file_urls: list[str]) -> str:
    """Convert file URLs to a markdown attachments section.

    Image files use inline image syntax (![name](url));
    other files use standard link syntax ([name](url)).
    Returns empty string if no URLs provided.
    """
    if not file_urls:
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

    for url in file_urls:
        filename = PurePosixPath(url).name
        # Strip upload ID prefix (e.g., "a1b2c3d4-screenshot.png" → "screenshot.png")
        filename = _UPLOAD_ID_PREFIX.sub("", filename)
        ext = PurePosixPath(filename).suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            lines.append(f"![{filename}]({url})")
        else:
            lines.append(f"[{filename}]({url})")

    return "\n".join(lines)
