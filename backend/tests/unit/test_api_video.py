"""Tests for video API routes (src/api/video.py).

Covers:
- POST   /api/v1/videos/upload            → upload_video
- GET    /api/v1/videos                    → list_videos
- GET    /api/v1/videos/{video_id}         → get_video
- PATCH  /api/v1/videos/{video_id}         → update_video
- DELETE /api/v1/videos/{video_id}         → delete_video
"""

import io

import pytest


# ── POST /videos/upload ────────────────────────────────────────────────────


class TestUploadVideo:
    async def test_upload_mp4_success(self, client):
        """A valid MP4 file should be accepted and return metadata."""
        content = b"\x00\x00\x00\x1c" + b"\x00" * 100  # minimal bytes
        resp = await client.post(
            "/api/v1/videos/upload",
            files={"file": ("test_video.mp4", io.BytesIO(content), "video/mp4")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["filename"] == "test_video.mp4"
        assert body["content_type"] == "video/mp4"
        assert body["status"] == "ready"
        assert "file_url" in body
        assert body["file_size"] == len(content)

    async def test_upload_webm_success(self, client):
        """WebM files should be accepted."""
        content = b"\x1a\x45\xdf\xa3" + b"\x00" * 50
        resp = await client.post(
            "/api/v1/videos/upload",
            files={"file": ("clip.webm", io.BytesIO(content), "video/webm")},
        )
        assert resp.status_code == 200
        assert resp.json()["filename"] == "clip.webm"

    async def test_upload_mov_success(self, client):
        """MOV files should be accepted."""
        resp = await client.post(
            "/api/v1/videos/upload",
            files={"file": ("movie.mov", io.BytesIO(b"\x00" * 64), "video/quicktime")},
        )
        assert resp.status_code == 200

    async def test_upload_avi_success(self, client):
        """AVI files should be accepted."""
        resp = await client.post(
            "/api/v1/videos/upload",
            files={"file": ("clip.avi", io.BytesIO(b"\x00" * 64), "video/x-msvideo")},
        )
        assert resp.status_code == 200

    async def test_upload_mkv_success(self, client):
        """MKV files should be accepted."""
        resp = await client.post(
            "/api/v1/videos/upload",
            files={"file": ("movie.mkv", io.BytesIO(b"\x00" * 64), "video/x-matroska")},
        )
        assert resp.status_code == 200

    async def test_unsupported_format_rejected(self, client):
        """Non-video file extensions should be rejected."""
        resp = await client.post(
            "/api/v1/videos/upload",
            files={"file": ("document.pdf", io.BytesIO(b"\x00" * 10), "application/pdf")},
        )
        assert resp.status_code == 415
        body = resp.json()
        assert body["error_code"] == "unsupported_format"
        assert ".pdf" in body["error"]

    async def test_empty_file_rejected(self, client):
        """Empty files should be rejected."""
        resp = await client.post(
            "/api/v1/videos/upload",
            files={"file": ("empty.mp4", io.BytesIO(b""), "video/mp4")},
        )
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "empty_file"

    async def test_no_filename_rejected(self, client):
        """Uploads without a filename should be rejected."""
        resp = await client.post(
            "/api/v1/videos/upload",
            files={"file": ("", io.BytesIO(b"\x00"), "video/mp4")},
        )
        # FastAPI may return 400 or 422 depending on form validation
        assert resp.status_code in (400, 422)

    async def test_path_traversal_sanitised(self, client):
        """Path traversal attempts should be neutralised."""
        resp = await client.post(
            "/api/v1/videos/upload",
            files={
                "file": (
                    "../../etc/shadow.mp4",
                    io.BytesIO(b"\x00" * 32),
                    "video/mp4",
                )
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "../" not in body["file_url"]
        assert "shadow.mp4" in body["file_url"]


# ── GET /videos ────────────────────────────────────────────────────────────


class TestListVideos:
    async def test_empty_list(self, client):
        """Listing videos with no uploads returns empty list."""
        # Clear in-memory store
        from src.api.video import _videos

        _videos.clear()

        resp = await client.get("/api/v1/videos")
        assert resp.status_code == 200
        body = resp.json()
        assert body["videos"] == []
        assert body["total"] == 0

    async def test_list_after_upload(self, client):
        """Uploaded videos appear in the listing."""
        from src.api.video import _videos

        _videos.clear()

        # Upload a video
        await client.post(
            "/api/v1/videos/upload",
            files={"file": ("listed.mp4", io.BytesIO(b"\x00" * 64), "video/mp4")},
        )

        resp = await client.get("/api/v1/videos")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["videos"][0]["filename"] == "listed.mp4"


# ── GET /videos/{video_id} ─────────────────────────────────────────────────


class TestGetVideo:
    async def test_get_existing_video(self, client):
        """Getting an uploaded video returns its metadata."""
        from src.api.video import _videos

        _videos.clear()

        upload_resp = await client.post(
            "/api/v1/videos/upload",
            files={"file": ("detail.mp4", io.BytesIO(b"\x00" * 64), "video/mp4")},
        )
        video_id = upload_resp.json()["id"]

        resp = await client.get(f"/api/v1/videos/{video_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == video_id
        assert resp.json()["filename"] == "detail.mp4"

    async def test_get_nonexistent_video(self, client):
        """Requesting a missing video returns 404."""
        resp = await client.get("/api/v1/videos/nonexistent")
        assert resp.status_code == 404
        assert resp.json()["error_code"] == "not_found"


# ── PATCH /videos/{video_id} ───────────────────────────────────────────────


class TestUpdateVideo:
    async def test_update_title_and_description(self, client):
        """Updating metadata should persist changes."""
        from src.api.video import _videos

        _videos.clear()

        upload_resp = await client.post(
            "/api/v1/videos/upload",
            files={"file": ("editable.mp4", io.BytesIO(b"\x00" * 64), "video/mp4")},
        )
        video_id = upload_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/videos/{video_id}",
            json={"title": "My Video", "description": "A test video"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "My Video"
        assert body["description"] == "A test video"

    async def test_partial_update(self, client):
        """Updating only the title should not change description."""
        from src.api.video import _videos

        _videos.clear()

        upload_resp = await client.post(
            "/api/v1/videos/upload",
            files={"file": ("partial.mp4", io.BytesIO(b"\x00" * 64), "video/mp4")},
        )
        video_id = upload_resp.json()["id"]

        # Set description first
        await client.patch(
            f"/api/v1/videos/{video_id}",
            json={"description": "Initial description"},
        )

        # Update only title
        resp = await client.patch(
            f"/api/v1/videos/{video_id}",
            json={"title": "Updated Title"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Updated Title"
        assert body["description"] == "Initial description"

    async def test_update_nonexistent_video(self, client):
        """Updating a missing video returns 404."""
        resp = await client.patch(
            "/api/v1/videos/nonexistent",
            json={"title": "Nope"},
        )
        assert resp.status_code == 404


# ── DELETE /videos/{video_id} ──────────────────────────────────────────────


class TestDeleteVideo:
    async def test_delete_existing_video(self, client):
        """Deleting a video should remove it from the listing."""
        from src.api.video import _videos

        _videos.clear()

        upload_resp = await client.post(
            "/api/v1/videos/upload",
            files={"file": ("deletable.mp4", io.BytesIO(b"\x00" * 64), "video/mp4")},
        )
        video_id = upload_resp.json()["id"]

        resp = await client.delete(f"/api/v1/videos/{video_id}")
        assert resp.status_code == 200

        # Verify it's gone
        list_resp = await client.get("/api/v1/videos")
        assert list_resp.json()["total"] == 0

    async def test_delete_nonexistent_video(self, client):
        """Deleting a missing video returns 404."""
        resp = await client.delete("/api/v1/videos/nonexistent")
        assert resp.status_code == 404
        assert resp.json()["error_code"] == "not_found"


# ── Chat upload with video formats ─────────────────────────────────────────


class TestChatUploadVideoFormats:
    """Verify that the chat file upload endpoint accepts video formats."""

    @pytest.mark.parametrize("ext", [".mp4", ".mov", ".webm", ".avi", ".mkv"])
    async def test_chat_upload_accepts_video_formats(self, client, ext):
        """Video formats should be accepted by the chat upload endpoint."""
        filename = f"test{ext}"
        content = b"\x00" * 64
        resp = await client.post(
            "/api/v1/chat/upload",
            files={"file": (filename, io.BytesIO(content), "video/mp4")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["filename"] == filename
