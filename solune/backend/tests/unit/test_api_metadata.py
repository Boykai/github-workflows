"""Tests for metadata API routes (src/api/metadata.py).

Covers:
- GET  /api/v1/metadata/{owner}/{repo}          → get_metadata
- POST /api/v1/metadata/{owner}/{repo}/refresh   → refresh_metadata
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.metadata_service import RepositoryMetadataContext

# ── Helpers ─────────────────────────────────────────────────────────────────


def _metadata_context(**overrides) -> RepositoryMetadataContext:
    defaults = {
        "repo_key": "testowner/testrepo",
        "labels": [{"name": "bug", "color": "d73a4a"}],
        "branches": [{"name": "main"}],
        "milestones": [],
        "collaborators": [],
        "fetched_at": "2024-01-01T00:00:00",
        "is_stale": False,
        "source": "cache",
    }
    defaults.update(overrides)
    return RepositoryMetadataContext(**defaults)


# ── GET /metadata/{owner}/{repo} ──────────────────────────────────────────


class TestGetMetadata:
    @pytest.fixture(autouse=True)
    def _patch_service(self):
        with patch("src.api.metadata.MetadataService") as cls_mock:
            self.svc_instance = MagicMock()
            cls_mock.return_value = self.svc_instance
            self.svc_instance.get_or_fetch = AsyncMock()
            yield

    async def test_get_metadata_success(self, client):
        self.svc_instance.get_or_fetch.return_value = _metadata_context()
        resp = await client.get("/api/v1/metadata/testowner/testrepo")
        assert resp.status_code == 200
        data = resp.json()
        assert data["repo_key"] == "testowner/testrepo"
        assert len(data["labels"]) == 1

    async def test_get_metadata_stale_cache(self, client):
        self.svc_instance.get_or_fetch.return_value = _metadata_context(is_stale=True)
        resp = await client.get("/api/v1/metadata/testowner/testrepo")
        assert resp.status_code == 200
        assert resp.json()["is_stale"] is True

    async def test_get_metadata_empty_repo(self, client):
        self.svc_instance.get_or_fetch.return_value = _metadata_context(
            labels=[], branches=[], milestones=[], collaborators=[]
        )
        resp = await client.get("/api/v1/metadata/owner/repo")
        assert resp.status_code == 200
        assert resp.json()["labels"] == []


# ── POST /metadata/{owner}/{repo}/refresh ─────────────────────────────────


class TestRefreshMetadata:
    @pytest.fixture(autouse=True)
    def _patch_service(self):
        with patch("src.api.metadata.MetadataService") as cls_mock:
            self.svc_instance = MagicMock()
            cls_mock.return_value = self.svc_instance
            self.svc_instance.invalidate = AsyncMock()
            self.svc_instance.fetch_metadata = AsyncMock()
            yield

    async def test_refresh_metadata_success(self, client):
        self.svc_instance.fetch_metadata.return_value = _metadata_context(source="fresh")
        resp = await client.post("/api/v1/metadata/testowner/testrepo/refresh")
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "fresh"
        self.svc_instance.invalidate.assert_awaited_once_with("testowner", "testrepo")

    async def test_refresh_calls_invalidate_then_fetch(self, client):
        self.svc_instance.fetch_metadata.return_value = _metadata_context()
        await client.post("/api/v1/metadata/owner/repo/refresh")
        self.svc_instance.invalidate.assert_awaited_once()
        self.svc_instance.fetch_metadata.assert_awaited_once()
