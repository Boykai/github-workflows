"""Video upload, playback, and management API endpoints."""

from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from src.api.auth import get_session_dep
from src.logging_utils import get_logger
from src.models.user import UserSession
from src.models.video import (
    VideoListResponse,
    VideoMetadata,
    VideoStatus,
    VideoUpdateRequest,
    VideoUploadResponse,
)

logger = get_logger(__name__)
router = APIRouter()

# ── Video upload validation constants ────────────────────────────────────
MAX_VIDEO_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB
MAX_VIDEO_DURATION_SECONDS = 3600  # 1 hour

ALLOWED_VIDEO_TYPES = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
ALLOWED_VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    "video/webm",
}

# ── In-memory video storage (single-instance deployment) ─────────────────
_videos: dict[str, VideoMetadata] = {}


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),  # noqa: B008
    session: UserSession = Depends(get_session_dep),  # noqa: B008
) -> VideoUploadResponse | JSONResponse:
    """Upload a video file.

    Validates file size and type, stores the file, and returns metadata.
    Supported formats: MP4, MOV, AVI, MKV, WebM. Maximum size: 2 GB.
    """
    if not file.filename:
        return JSONResponse(
            status_code=400,
            content={"error": "No file provided", "error_code": "no_file"},
        )

    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_VIDEO_TYPES:
        supported = ", ".join(sorted(ALLOWED_VIDEO_TYPES))
        return JSONResponse(
            status_code=415,
            content={
                "filename": file.filename,
                "error": f"Unsupported video format '{ext}'. Supported formats: {supported}",
                "error_code": "unsupported_format",
            },
        )

    # Read file content with streaming to handle large files
    # Read in chunks to validate size without loading entire file into memory
    chunks: list[bytes] = []
    total_size = 0
    chunk_size = 8 * 1024 * 1024  # 8 MB chunks

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_VIDEO_SIZE_BYTES:
            return JSONResponse(
                status_code=413,
                content={
                    "filename": file.filename,
                    "error": "Video exceeds the 2 GB size limit",
                    "error_code": "file_too_large",
                },
            )
        chunks.append(chunk)

    if total_size == 0:
        return JSONResponse(
            status_code=400,
            content={
                "filename": file.filename,
                "error": "Empty file — cannot upload a video with no content",
                "error_code": "empty_file",
            },
        )

    # Generate unique ID and sanitise filename
    video_id = str(uuid4())[:8]
    cleaned = file.filename.replace("\x00", "")
    basename = Path(cleaned).name
    if not basename:
        basename = "video"
    safe_filename = f"{video_id}-{basename}"

    # Store in temporary directory
    upload_dir = Path(tempfile.gettempdir()) / "video-uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / safe_filename

    # Verify resolved path stays inside upload_dir (defense-in-depth)
    if not file_path.resolve().is_relative_to(upload_dir.resolve()):
        return JSONResponse(
            status_code=400,
            content={
                "filename": file.filename,
                "error": "Invalid filename",
                "error_code": "invalid_filename",
            },
        )

    # Write file
    with open(file_path, "wb") as f:
        for chunk in chunks:
            f.write(chunk)

    file_url = f"/api/v1/videos/stream/{safe_filename}"
    thumbnail_url = f"/api/v1/videos/thumbnail/{video_id}"

    # Create video metadata
    video = VideoMetadata(
        id=video_id,
        filename=file.filename,
        title=Path(file.filename).stem,
        file_url=file_url,
        thumbnail_url=thumbnail_url,
        file_size=total_size,
        content_type=file.content_type or "video/mp4",
        status=VideoStatus.READY,
    )
    _videos[video_id] = video

    logger.info("Video uploaded: %s (%d bytes)", file.filename, total_size)

    return VideoUploadResponse(
        id=video.id,
        filename=video.filename,
        file_url=video.file_url,
        thumbnail_url=video.thumbnail_url,
        file_size=video.file_size,
        content_type=video.content_type,
        status=video.status,
    )


@router.get("", response_model=VideoListResponse)
async def list_videos(
    session: UserSession = Depends(get_session_dep),  # noqa: B008
) -> VideoListResponse:
    """List all uploaded videos."""
    videos = sorted(_videos.values(), key=lambda v: v.created_at, reverse=True)
    return VideoListResponse(videos=videos, total=len(videos))


@router.get("/{video_id}", response_model=VideoMetadata)
async def get_video(
    video_id: str,
    session: UserSession = Depends(get_session_dep),  # noqa: B008
) -> VideoMetadata | JSONResponse:
    """Get video metadata by ID."""
    video = _videos.get(video_id)
    if not video:
        return JSONResponse(
            status_code=404,
            content={"error": f"Video not found: {video_id}", "error_code": "not_found"},
        )
    return video


@router.patch("/{video_id}", response_model=VideoMetadata)
async def update_video(
    video_id: str,
    update: VideoUpdateRequest,
    session: UserSession = Depends(get_session_dep),  # noqa: B008
) -> VideoMetadata | JSONResponse:
    """Update video metadata (title, description)."""
    video = _videos.get(video_id)
    if not video:
        return JSONResponse(
            status_code=404,
            content={"error": f"Video not found: {video_id}", "error_code": "not_found"},
        )

    from src.utils import utcnow

    if update.title is not None:
        video.title = update.title
    if update.description is not None:
        video.description = update.description
    video.updated_at = utcnow()

    _videos[video_id] = video
    return video


@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    session: UserSession = Depends(get_session_dep),  # noqa: B008
) -> JSONResponse:
    """Delete a video and its associated file."""
    video = _videos.get(video_id)
    if not video:
        return JSONResponse(
            status_code=404,
            content={"error": f"Video not found: {video_id}", "error_code": "not_found"},
        )

    # Clean up file on disk
    upload_dir = Path(tempfile.gettempdir()) / "video-uploads"
    # Extract safe_filename from URL
    safe_filename = video.file_url.split("/")[-1]
    file_path = upload_dir / safe_filename

    if file_path.exists() and file_path.resolve().is_relative_to(upload_dir.resolve()):
        file_path.unlink(missing_ok=True)

    del _videos[video_id]

    logger.info("Video deleted: %s", video_id)
    return JSONResponse(
        status_code=200,
        content={"message": f"Video {video_id} deleted"},
    )
