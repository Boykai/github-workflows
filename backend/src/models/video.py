"""Video metadata models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from src.utils import utcnow


class VideoStatus(StrEnum):
    """Processing status for uploaded videos."""

    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class VideoMetadata(BaseModel):
    """Represents metadata for an uploaded video."""

    id: str = Field(..., description="Unique video identifier")
    filename: str = Field(..., description="Original filename")
    title: str = Field(default="", description="User-editable title")
    description: str = Field(default="", description="User-editable description")
    file_url: str = Field(..., description="URL to access the video file")
    thumbnail_url: str | None = Field(default=None, description="URL to video thumbnail")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type of the video")
    duration: float | None = Field(default=None, description="Duration in seconds")
    width: int | None = Field(default=None, description="Video width in pixels")
    height: int | None = Field(default=None, description="Video height in pixels")
    status: VideoStatus = Field(default=VideoStatus.READY, description="Processing status")
    error_message: str | None = Field(default=None, description="Error message if processing failed")
    created_at: datetime = Field(default_factory=utcnow, description="Upload timestamp")
    updated_at: datetime = Field(default_factory=utcnow, description="Last update timestamp")


class VideoUploadResponse(BaseModel):
    """Response returned after a video upload."""

    id: str
    filename: str
    file_url: str
    thumbnail_url: str | None = None
    file_size: int
    content_type: str
    status: VideoStatus


class VideoUpdateRequest(BaseModel):
    """Request to update video metadata."""

    title: str | None = Field(default=None, max_length=200, description="Video title")
    description: str | None = Field(
        default=None, max_length=2000, description="Video description"
    )


class VideoListResponse(BaseModel):
    """Response for listing videos."""

    videos: list[VideoMetadata]
    total: int
