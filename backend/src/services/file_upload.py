"""File upload service for chat attachments.

Handles validation (size, MIME type), UUID-based local filesystem storage,
and in-memory metadata registry.
"""

import logging
import os
import re
import shutil
from uuid import uuid4

from fastapi import UploadFile

from src.models.chat import (
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE,
    FileAttachment,
    FileAttachmentResponse,
    UploadStatus,
)

logger = logging.getLogger(__name__)

# In-memory file metadata registry (MVP)
_file_registry: dict[str, FileAttachment] = {}

# Upload directory — relative to backend working directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")


def _sanitize_filename(filename: str) -> str:
    """Sanitize original filename: strip path components, limit length."""
    # Strip directory components
    filename = os.path.basename(filename)
    # Remove null bytes and control characters
    filename = re.sub(r"[\x00-\x1f]", "", filename)
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[: 255 - len(ext)] + ext
    return filename or "unnamed"


def _ensure_upload_dir() -> None:
    """Create upload directory if it doesn't exist."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_file_attachment(file_id: str) -> FileAttachment | None:
    """Get file metadata by ID."""
    return _file_registry.get(file_id)


def to_response(attachment: FileAttachment) -> FileAttachmentResponse:
    """Convert internal FileAttachment to API response."""
    return FileAttachmentResponse(
        id=attachment.id,
        original_filename=attachment.original_filename,
        mime_type=attachment.mime_type,
        file_size=attachment.file_size,
        upload_status=attachment.upload_status.value,
        url=f"/api/v1/chat/upload/{attachment.id}",
    )


async def upload_file(file: UploadFile) -> FileAttachment:
    """Validate and store an uploaded file.

    Raises ValueError with descriptive message on validation failure.
    """
    _ensure_upload_dir()

    # Validate filename
    original_filename = _sanitize_filename(file.filename or "unnamed")

    # Validate MIME type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            "File type not supported. Accepted formats: JPG, PNG, GIF, WEBP, PDF, DOCX, TXT"
        )

    # Read file content and validate size
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise ValueError("File exceeds the maximum size of 25 MB")

    if file_size == 0:
        raise ValueError("File is empty")

    # Generate UUID-based storage filename
    file_id = str(uuid4())
    _, ext = os.path.splitext(original_filename)
    storage_filename = f"{file_id}{ext}"
    storage_path = os.path.join(UPLOAD_DIR, storage_filename)

    # Write file to disk
    with open(storage_path, "wb") as f:
        f.write(content)

    # Create metadata entry
    attachment = FileAttachment(
        id=file_id,
        original_filename=original_filename,
        mime_type=content_type,
        file_size=file_size,
        storage_path=storage_path,
        upload_status=UploadStatus.UPLOADED,
    )

    # Register in memory
    _file_registry[file_id] = attachment

    logger.info(
        "File uploaded: id=%s name=%s type=%s size=%d",
        file_id,
        original_filename,
        content_type,
        file_size,
    )

    return attachment


def delete_file(file_id: str) -> bool:
    """Delete an uploaded file and its metadata.

    Returns True if the file was found and deleted, False otherwise.
    """
    attachment = _file_registry.pop(file_id, None)
    if not attachment:
        return False

    # Remove from filesystem
    if os.path.exists(attachment.storage_path):
        os.remove(attachment.storage_path)
        logger.info("File deleted: id=%s name=%s", file_id, attachment.original_filename)

    return True


def get_attachment_responses(attachment_ids: list[str]) -> list[FileAttachmentResponse]:
    """Get FileAttachmentResponse objects for a list of IDs.

    Silently skips missing IDs.
    """
    responses = []
    for aid in attachment_ids:
        attachment = _file_registry.get(aid)
        if attachment and attachment.upload_status == UploadStatus.UPLOADED:
            responses.append(to_response(attachment))
    return responses


def cleanup_uploads() -> None:
    """Remove all uploaded files and clear registry. Used for testing/reset."""
    for attachment in _file_registry.values():
        if os.path.exists(attachment.storage_path):
            os.remove(attachment.storage_path)
    _file_registry.clear()
    if os.path.exists(UPLOAD_DIR):
        shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
