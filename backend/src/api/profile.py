"""Profile API endpoints for user profile management."""

import re
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Response, UploadFile
from fastapi.responses import JSONResponse

from src.api.auth import get_session_dep
from src.config import get_settings
from src.dependencies import get_database
from src.models.user import UserProfile, UserProfileResponse, UserProfileUpdate, UserSession
from src.services import profile_store

router = APIRouter()

MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_AVATAR_TYPES = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_AVATAR_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}

CONTENT_TYPE_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

AVATAR_FILENAME_RE = re.compile(
    r"^[0-9a-f]{8}_[A-Za-z0-9][A-Za-z0-9._-]{0,127}\.(?:png|jpg|jpeg|webp)$"
)


def _get_avatar_dir() -> Path:
    """Return the avatar storage directory, creating it if needed."""
    settings = get_settings()
    db_path = Path(settings.database_path)
    avatar_dir = db_path.parent / "profile-avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    return avatar_dir


def _sanitize_avatar_basename(filename: str, ext: str) -> str:
    """Return a filesystem-safe avatar basename with an allowed extension."""
    cleaned = filename.replace("\x00", "")
    stem = Path(cleaned).stem
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-")
    if not sanitized:
        sanitized = "avatar"
    return f"{sanitized}{ext}"


def _resolve_avatar_path(filename: str) -> Path | None:
    """Resolve a validated avatar filename to an on-disk path under avatar_dir."""
    if not AVATAR_FILENAME_RE.fullmatch(filename):
        return None

    avatar_dir = _get_avatar_dir().resolve()
    resolved = (avatar_dir / filename).resolve()
    if resolved.parent != avatar_dir:
        return None

    return resolved


def _build_profile_response(
    session: UserSession, profile: UserProfile | None
) -> UserProfileResponse:
    """Build a composite profile response from session + profile data."""
    if profile is None:
        return UserProfileResponse(
            github_user_id=session.github_user_id,
            github_username=session.github_username,
            github_avatar_url=session.github_avatar_url,
            display_name=None,
            bio=None,
            avatar_url=session.github_avatar_url,
            account_created_at=None,
            role="member",
        )

    # Resolve avatar URL: custom upload takes precedence over GitHub avatar
    if profile.avatar_path and AVATAR_FILENAME_RE.fullmatch(profile.avatar_path):
        avatar_filename = profile.avatar_path
        avatar_url = f"/api/v1/users/profile/avatar/{avatar_filename}"
    else:
        avatar_url = session.github_avatar_url

    return UserProfileResponse(
        github_user_id=session.github_user_id,
        github_username=session.github_username,
        github_avatar_url=session.github_avatar_url,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=avatar_url,
        account_created_at=profile.created_at.isoformat(),
        role="member",
    )


@router.get("", response_model=UserProfileResponse)
async def get_profile(
    session: UserSession = Depends(get_session_dep),  # noqa: B008
    db=Depends(get_database),  # noqa: B008
) -> UserProfileResponse:
    """Fetch the authenticated user's composite profile."""
    profile = await profile_store.get_profile(db, session.github_user_id)
    return _build_profile_response(session, profile)


@router.patch("", response_model=UserProfileResponse)
async def update_profile(
    update: UserProfileUpdate,
    session: UserSession = Depends(get_session_dep),  # noqa: B008
    db=Depends(get_database),  # noqa: B008
) -> UserProfileResponse | Response:
    """Update the authenticated user's profile fields."""
    # Validate display_name if provided
    if update.display_name is not None:
        stripped = update.display_name.strip()
        if not stripped:
            return JSONResponse(
                status_code=422,
                content={"error": "Display name cannot be empty"},
            )
        if len(stripped) > 100:
            return JSONResponse(
                status_code=422,
                content={"error": "Display name must be 100 characters or fewer"},
            )
        update.display_name = stripped

    # Validate bio if provided
    if update.bio is not None and len(update.bio) > 500:
        return JSONResponse(
            status_code=422,
            content={"error": "Bio must be 500 characters or fewer"},
        )

    profile = await profile_store.upsert_profile(db, session.github_user_id, update)
    return _build_profile_response(session, profile)


@router.post("/avatar", response_model=UserProfileResponse)
async def upload_avatar(
    file: UploadFile = File(...),  # noqa: B008
    session: UserSession = Depends(get_session_dep),  # noqa: B008
    db=Depends(get_database),  # noqa: B008
) -> UserProfileResponse | Response:
    """Upload a new avatar image for the authenticated user."""
    if not file.filename:
        return JSONResponse(
            status_code=400,
            content={"error": "No file provided"},
        )

    # Validate file type by extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_AVATAR_TYPES:
        return JSONResponse(
            status_code=422,
            content={"error": "Please select a PNG, JPG, or WebP image"},
        )

    # Validate content type
    if file.content_type and file.content_type not in ALLOWED_AVATAR_CONTENT_TYPES:
        return JSONResponse(
            status_code=422,
            content={"error": "Please select a PNG, JPG, or WebP image"},
        )

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_AVATAR_SIZE:
        return JSONResponse(
            status_code=413,
            content={"error": "Image must be smaller than 5 MB"},
        )

    # Generate safe filename
    upload_id = str(uuid4())[:8]
    safe_basename = _sanitize_avatar_basename(file.filename, ext)
    safe_filename = f"{upload_id}_{safe_basename}"
    file_path = _resolve_avatar_path(safe_filename)
    if file_path is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid filename"},
        )

    # Delete previous avatar if exists
    existing_profile = await profile_store.get_profile(db, session.github_user_id)
    if existing_profile and existing_profile.avatar_path:
        old_path = _resolve_avatar_path(existing_profile.avatar_path)
        if old_path and old_path.exists():
            old_path.unlink(missing_ok=True)

    # Save new avatar
    file_path.write_bytes(content)

    # Update profile with new avatar path
    await profile_store.update_avatar_path(db, session.github_user_id, safe_filename)

    # Fetch updated profile for response
    profile = await profile_store.get_profile(db, session.github_user_id)
    return _build_profile_response(session, profile)


@router.get("/avatar/{filename}", response_model=None)
async def get_avatar(filename: str) -> Response:
    """Serve an uploaded avatar file."""
    file_path = _resolve_avatar_path(filename)
    if file_path is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid filename"},
        )

    if not file_path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "Avatar not found"},
        )

    ext = file_path.suffix.lower()
    content_type = CONTENT_TYPE_MAP.get(ext, "application/octet-stream")
    return Response(content=file_path.read_bytes(), media_type=content_type)
