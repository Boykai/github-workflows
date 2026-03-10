"""Unit tests for metadata service fallback logging."""

from unittest.mock import AsyncMock, patch

import aiosqlite
import pytest

from src.services.metadata_service import MetadataService


class TestMetadataServiceFallbacks:
    """Tests for metadata cache fallback behavior."""

    @pytest.mark.asyncio
    async def test_logs_warning_when_stale_sqlite_read_fails(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        service = MetadataService()

        with (
            patch.object(
                service,
                "_read_from_sqlite",
                new_callable=AsyncMock,
                side_effect=[None, aiosqlite.Error("database is locked")],
            ),
            patch.object(
                service,
                "fetch_metadata",
                new_callable=AsyncMock,
                side_effect=RuntimeError("api unavailable"),
            ),
            caplog.at_level("WARNING"),
        ):
            result = await service.get_or_fetch("token", "octo", "repo")

        assert result.source == "fallback"
        assert result.repo_key == "octo/repo"
        assert "SQLite metadata read failed for octo/repo, using defaults" in caplog.text
        assert "database is locked" in caplog.text
