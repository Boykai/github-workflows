"""Shared markdown attachment formatter for GitHub issue bodies.

Converts a list of file URLs into a formatted markdown attachments section
that is appended to the GitHub issue body when a proposal or recommendation
is confirmed.
"""

from __future__ import annotations

from pathlib import PurePosixPath

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


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
        # Strip upload ID prefix (e.g., "abc123-screenshot.png" → "screenshot.png")
        if "-" in filename:
            filename = filename.split("-", 1)[1]
        ext = PurePosixPath(filename).suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            lines.append(f"![{filename}]({url})")
        else:
            lines.append(f"[{filename}]({url})")

    return "\n".join(lines)
