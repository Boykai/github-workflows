from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.services.metadata_service import MetadataService, RepositoryMetadataContext


class _SpyCache:
    def __init__(self, initial: dict[str, object] | None = None):
        self.data = dict(initial or {})
        self.set_calls: list[tuple[str, object, int | None]] = []
        self.deleted: list[str] = []

    def get(self, key: str):
        return self.data.get(key)

    def set(self, key: str, value: object, ttl_seconds: int | None = None, **_kwargs) -> None:
        self.data[key] = value
        self.set_calls.append((key, value, ttl_seconds))

    def delete(self, key: str) -> bool:
        self.deleted.append(key)
        return self.data.pop(key, None) is not None


@pytest.fixture
def metadata_service():
    cache = _SpyCache()
    with patch(
        "src.services.metadata_service.get_settings",
        return_value=SimpleNamespace(metadata_cache_ttl_seconds=300),
    ):
        return MetadataService(l1_cache=cache)


class TestGetOrFetch:
    @pytest.mark.asyncio
    async def test_returns_fresh_l1_cache_without_other_lookups(
        self, metadata_service: MetadataService
    ):
        ctx = RepositoryMetadataContext(
            repo_key="owner/repo",
            labels=[{"name": "bug"}],
            fetched_at="2026-03-16T12:00:00+00:00",
        )
        metadata_service._l1.data["metadata:owner/repo"] = ctx.model_dump()  # type: ignore[attr-defined]

        with (
            patch.object(metadata_service, "_is_stale", return_value=False),
            patch.object(
                metadata_service, "_read_from_sqlite", new_callable=AsyncMock
            ) as read_sqlite,
            patch.object(metadata_service, "fetch_metadata", new_callable=AsyncMock) as fetch,
        ):
            result = await metadata_service.get_or_fetch("token", "owner", "repo")

        assert result.repo_key == "owner/repo"
        assert result.source == "cache"
        assert result.is_stale is False
        read_sqlite.assert_not_awaited()
        fetch.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_uses_fresh_sqlite_cache_and_populates_l1(
        self, metadata_service: MetadataService
    ):
        ctx = RepositoryMetadataContext(
            repo_key="owner/repo", branches=[{"name": "main"}], fetched_at="fresh"
        )

        with (
            patch.object(metadata_service, "_is_stale", return_value=False),
            patch.object(
                metadata_service, "_read_from_sqlite", new_callable=AsyncMock, return_value=ctx
            ) as read_sqlite,
            patch.object(metadata_service, "fetch_metadata", new_callable=AsyncMock) as fetch,
        ):
            result = await metadata_service.get_or_fetch("token", "owner", "repo")

        assert result.source == "cache"
        assert result.is_stale is False
        read_sqlite.assert_awaited_once_with("owner/repo")
        fetch.assert_not_awaited()
        assert metadata_service._l1.set_calls[0][0] == "metadata:owner/repo"  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_falls_back_to_stale_sqlite_when_fetch_fails(
        self, metadata_service: MetadataService
    ):
        stale_ctx = RepositoryMetadataContext(
            repo_key="owner/repo", labels=[{"name": "cached"}], fetched_at="stale"
        )

        with (
            patch.object(metadata_service, "_is_stale", return_value=True),
            patch.object(
                metadata_service,
                "_read_from_sqlite",
                new_callable=AsyncMock,
                side_effect=[stale_ctx, stale_ctx],
            ),
            patch.object(
                metadata_service,
                "fetch_metadata",
                new_callable=AsyncMock,
                side_effect=RuntimeError("boom"),
            ),
        ):
            result = await metadata_service.get_or_fetch("token", "owner", "repo")

        assert result.repo_key == "owner/repo"
        assert result.source == "cache"
        assert result.is_stale is True

    @pytest.mark.asyncio
    async def test_uses_hardcoded_fallback_when_all_tiers_fail(
        self, metadata_service: MetadataService
    ):
        with (
            patch.object(
                metadata_service,
                "_read_from_sqlite",
                new_callable=AsyncMock,
                side_effect=RuntimeError("db"),
            ),
            patch.object(
                metadata_service,
                "fetch_metadata",
                new_callable=AsyncMock,
                side_effect=RuntimeError("api"),
            ),
        ):
            result = await metadata_service.get_or_fetch("token", "owner", "repo")

        assert result.repo_key == "owner/repo"
        assert result.source == "fallback"
        assert result.branches == [{"name": "main", "protected": True}]

    @pytest.mark.asyncio
    async def test_fetches_when_sqlite_cache_read_raises(self, metadata_service: MetadataService):
        fresh_ctx = RepositoryMetadataContext(
            repo_key="owner/repo", fetched_at="fresh", source="fresh"
        )

        with (
            patch.object(
                metadata_service,
                "_read_from_sqlite",
                new_callable=AsyncMock,
                side_effect=RuntimeError("db broke"),
            ),
            patch.object(
                metadata_service,
                "fetch_metadata",
                new_callable=AsyncMock,
                return_value=fresh_ctx,
            ) as fetch,
        ):
            result = await metadata_service.get_or_fetch("token", "owner", "repo")

        fetch.assert_awaited_once_with("token", "owner", "repo")
        assert result is fresh_ctx


class TestFetchMetadata:
    @pytest.mark.asyncio
    async def test_normalizes_api_data_and_persists_when_all_fetches_complete(
        self, metadata_service: MetadataService
    ):
        with (
            patch.object(
                metadata_service,
                "_fetch_paginated",
                new_callable=AsyncMock,
                side_effect=[
                    ([{"name": "bug", "color": "ff0000", "description": None}], True),
                    ([{"name": "main", "protected": True}], True),
                    ([{"number": 7, "title": "v1", "due_on": None, "state": "open"}], True),
                    ([{"login": "octocat", "avatar_url": "https://example.test/avatar"}], True),
                ],
            ) as fetch_paginated,
            patch.object(
                metadata_service, "_write_to_sqlite", new_callable=AsyncMock
            ) as write_sqlite,
        ):
            result = await metadata_service.fetch_metadata("token", "owner", "repo")

        assert result.source == "fresh"
        assert result.labels == [{"name": "bug", "color": "ff0000", "description": ""}]
        assert result.branches == [{"name": "main", "protected": True}]
        assert result.milestones == [{"number": 7, "title": "v1", "due_on": None, "state": "open"}]
        assert result.collaborators == [
            {"login": "octocat", "avatar_url": "https://example.test/avatar"}
        ]
        assert fetch_paginated.await_count == 4
        write_sqlite.assert_awaited_once()
        assert metadata_service._l1.set_calls[-1][0] == "metadata:owner/repo"  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_skips_sqlite_write_when_one_fetch_is_incomplete(
        self, metadata_service: MetadataService
    ):
        with (
            patch.object(
                metadata_service,
                "_fetch_paginated",
                new_callable=AsyncMock,
                side_effect=[([], True), ([], False), ([], True), ([], True)],
            ),
            patch.object(
                metadata_service, "_write_to_sqlite", new_callable=AsyncMock
            ) as write_sqlite,
        ):
            result = await metadata_service.fetch_metadata("token", "owner", "repo")

        assert result.source == "fresh"
        write_sqlite.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_continues_when_sqlite_write_fails(self, metadata_service: MetadataService):
        with (
            patch.object(
                metadata_service,
                "_fetch_paginated",
                new_callable=AsyncMock,
                side_effect=[([], True), ([], True), ([], True), ([], True)],
            ),
            patch.object(
                metadata_service,
                "_write_to_sqlite",
                new_callable=AsyncMock,
                side_effect=RuntimeError("disk full"),
            ),
        ):
            result = await metadata_service.fetch_metadata("token", "owner", "repo")

        assert result.source == "fresh"
        assert metadata_service._l1.set_calls[-1][0] == "metadata:owner/repo"  # type: ignore[attr-defined]


class TestGetMetadata:
    @pytest.mark.asyncio
    async def test_returns_l1_cached_metadata(self, metadata_service: MetadataService):
        metadata_service._l1.data["metadata:owner/repo"] = {  # type: ignore[attr-defined]
            "repo_key": "owner/repo",
            "labels": [{"name": "bug"}],
            "branches": [],
            "milestones": [],
            "collaborators": [],
            "fetched_at": "2026-03-16T12:00:00+00:00",
            "is_stale": False,
            "source": "fresh",
        }

        with patch.object(metadata_service, "_is_stale", return_value=False):
            result = await metadata_service.get_metadata("owner", "repo")

        assert result is not None
        assert result.source == "cache"
        assert result.is_stale is False

    @pytest.mark.asyncio
    async def test_returns_sqlite_cached_metadata_and_populates_l1(
        self, metadata_service: MetadataService
    ):
        ctx = RepositoryMetadataContext(repo_key="owner/repo", fetched_at="fresh")

        with (
            patch.object(metadata_service, "_is_stale", return_value=True),
            patch.object(
                metadata_service, "_read_from_sqlite", new_callable=AsyncMock, return_value=ctx
            ),
        ):
            result = await metadata_service.get_metadata("owner", "repo")

        assert result is not None
        assert result.source == "cache"
        assert result.is_stale is True
        assert metadata_service._l1.set_calls[-1][0] == "metadata:owner/repo"  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_returns_none_when_sqlite_read_fails(self, metadata_service: MetadataService):
        with patch.object(
            metadata_service,
            "_read_from_sqlite",
            new_callable=AsyncMock,
            side_effect=RuntimeError("db"),
        ):
            result = await metadata_service.get_metadata("owner", "repo")

        assert result is None


class TestFetchPaginated:
    @pytest.mark.asyncio
    async def test_fetches_multiple_pages_until_final_partial_page(
        self, metadata_service: MetadataService
    ):
        page1 = Mock()
        page1.status_code = 200
        page1.json.return_value = [{"name": f"label-{index}"} for index in range(100)]

        page2 = Mock()
        page2.status_code = 200
        page2.json.return_value = [{"name": "final"}]

        mock_svc = AsyncMock()
        mock_svc.rest_request = AsyncMock(side_effect=[page1, page2])
        metadata_service._github_service = mock_svc

        results, complete = await metadata_service._fetch_paginated(
            "token", "/repos/o/r/labels", {}
        )

        assert complete is True
        assert len(results) == 101
        assert mock_svc.rest_request.await_count == 2

    @pytest.mark.asyncio
    async def test_returns_partial_results_and_false_on_rate_limit(
        self, metadata_service: MetadataService
    ):
        ok_response = Mock()
        ok_response.status_code = 200
        ok_response.json.return_value = [{"name": f"label-{index}"} for index in range(100)]

        rate_limited = Mock()
        rate_limited.status_code = 429

        mock_svc = AsyncMock()
        mock_svc.rest_request = AsyncMock(side_effect=[ok_response, rate_limited])
        metadata_service._github_service = mock_svc

        results, complete = await metadata_service._fetch_paginated(
            "token", "/repos/o/r/labels", {}
        )

        assert len(results) == 100
        assert results[0] == {"name": "label-0"}
        assert complete is False

    @pytest.mark.asyncio
    async def test_handles_404_and_connect_errors(self, metadata_service: MetadataService):
        missing = Mock()
        missing.status_code = 404

        mock_svc_404 = AsyncMock()
        mock_svc_404.rest_request = AsyncMock(return_value=missing)
        metadata_service._github_service = mock_svc_404

        missing_results, missing_complete = await metadata_service._fetch_paginated(
            "token", "/repos/o/r/labels", {}
        )

        mock_svc_err = AsyncMock()
        mock_svc_err.rest_request = AsyncMock(side_effect=Exception("offline"))
        metadata_service._github_service = mock_svc_err

        connect_results, connect_complete = await metadata_service._fetch_paginated(
            "token", "/repos/o/r/labels", {}
        )

        assert missing_results == []
        assert missing_complete is False
        assert connect_results == []
        assert connect_complete is False

    @pytest.mark.asyncio
    async def test_stops_on_non_list_or_empty_payload(self, metadata_service: MetadataService):
        non_list = Mock()
        non_list.status_code = 200
        non_list.json.return_value = {"unexpected": True}

        empty = Mock()
        empty.status_code = 200
        empty.json.return_value = []

        mock_svc_non_list = AsyncMock()
        mock_svc_non_list.rest_request = AsyncMock(return_value=non_list)
        metadata_service._github_service = mock_svc_non_list

        non_list_results, non_list_complete = await metadata_service._fetch_paginated(
            "token", "/repos/o/r/labels", {}
        )

        mock_svc_empty = AsyncMock()
        mock_svc_empty.rest_request = AsyncMock(return_value=empty)
        metadata_service._github_service = mock_svc_empty

        empty_results, empty_complete = await metadata_service._fetch_paginated(
            "token", "/repos/o/r/labels", {}
        )

        assert non_list_results == []
        assert non_list_complete is True
        assert empty_results == []
        assert empty_complete is True


class TestSqliteHelpers:
    @pytest.mark.asyncio
    async def test_read_from_sqlite_returns_none_when_no_rows_exist(
        self, metadata_service: MetadataService, mock_db
    ):
        with patch("src.services.database.get_db", return_value=mock_db):
            result = await metadata_service._read_from_sqlite("owner/repo")

        assert result is None

    @pytest.mark.asyncio
    async def test_read_from_sqlite_groups_rows_by_field_type(
        self, metadata_service: MetadataService, mock_db
    ):
        await mock_db.execute(
            "INSERT INTO github_metadata_cache (repo_key, field_type, value, fetched_at) VALUES (?, ?, ?, ?)",
            ("owner/repo", "label", json.dumps({"name": "bug"}), "2026-03-16T12:00:00+00:00"),
        )
        await mock_db.execute(
            "INSERT INTO github_metadata_cache (repo_key, field_type, value, fetched_at) VALUES (?, ?, ?, ?)",
            ("owner/repo", "branch", json.dumps({"name": "main"}), "2026-03-16T12:00:01+00:00"),
        )
        await mock_db.execute(
            "INSERT INTO github_metadata_cache (repo_key, field_type, value, fetched_at) VALUES (?, ?, ?, ?)",
            ("owner/repo", "milestone", json.dumps({"title": "v1"}), "2026-03-16T12:00:01+00:00"),
        )
        await mock_db.execute(
            "INSERT INTO github_metadata_cache (repo_key, field_type, value, fetched_at) VALUES (?, ?, ?, ?)",
            (
                "owner/repo",
                "collaborator",
                json.dumps({"login": "octocat"}),
                "2026-03-16T12:00:01+00:00",
            ),
        )
        await mock_db.execute(
            "INSERT INTO github_metadata_cache (repo_key, field_type, value, fetched_at) VALUES (?, ?, ?, ?)",
            ("owner/repo", "label", "{invalid-json", "2026-03-16T12:00:02+00:00"),
        )
        await mock_db.commit()

        with patch("src.services.database.get_db", return_value=mock_db):
            result = await metadata_service._read_from_sqlite("owner/repo")

        assert result is not None
        assert result.labels == [{"name": "bug"}]
        assert result.branches == [{"name": "main"}]
        assert result.milestones == [{"title": "v1"}]
        assert result.collaborators == [{"login": "octocat"}]
        assert result.fetched_at == "2026-03-16T12:00:02+00:00"

    @pytest.mark.asyncio
    async def test_write_to_sqlite_replaces_existing_rows_and_invalidate_clears_them(
        self, metadata_service: MetadataService, mock_db
    ):
        await mock_db.execute(
            "INSERT INTO github_metadata_cache (repo_key, field_type, value, fetched_at) VALUES (?, ?, ?, ?)",
            ("owner/repo", "label", json.dumps({"name": "old"}), "2026-03-16T11:00:00+00:00"),
        )
        await mock_db.commit()

        ctx = RepositoryMetadataContext(
            repo_key="owner/repo",
            labels=[{"name": "bug"}],
            branches=[{"name": "main", "protected": True}],
            milestones=[],
            collaborators=[],
            fetched_at="2026-03-16T12:00:00+00:00",
        )

        with patch("src.services.database.get_db", return_value=mock_db):
            await metadata_service._write_to_sqlite(ctx)
            await metadata_service.invalidate("owner", "repo")

        assert metadata_service._l1.deleted == ["metadata:owner/repo"]  # type: ignore[attr-defined]
        rows = await mock_db.execute_fetchall(
            "SELECT repo_key, field_type, value FROM github_metadata_cache WHERE repo_key = ?",
            ("owner/repo",),
        )
        assert rows == []

    @pytest.mark.asyncio
    async def test_write_to_sqlite_commits_even_when_no_rows_exist(
        self, metadata_service: MetadataService, mock_db
    ):
        ctx = RepositoryMetadataContext(
            repo_key="owner/repo", fetched_at="2026-03-16T12:00:00+00:00"
        )

        with patch("src.services.database.get_db", return_value=mock_db):
            await metadata_service._write_to_sqlite(ctx)

        rows = await mock_db.execute_fetchall(
            "SELECT repo_key, field_type, value FROM github_metadata_cache WHERE repo_key = ?",
            ("owner/repo",),
        )
        assert rows == []

    @pytest.mark.asyncio
    async def test_invalidate_swallows_database_errors(self, metadata_service: MetadataService):
        failing_db = AsyncMock()
        failing_db.execute.side_effect = RuntimeError("locked")

        with patch("src.services.database.get_db", return_value=failing_db):
            await metadata_service.invalidate("owner", "repo")

        assert metadata_service._l1.deleted == ["metadata:owner/repo"]  # type: ignore[attr-defined]


class TestMiscHelpers:
    def test_is_stale_handles_empty_invalid_and_expired_timestamps(
        self, metadata_service: MetadataService
    ):
        assert metadata_service._is_stale("", 300) is True
        assert metadata_service._is_stale("not-a-date", 300) is True
        assert metadata_service._is_stale("2026-03-16T11:00:00+00:00", 60) is True

    def test_is_stale_handles_naive_and_fresh_timestamps(self, metadata_service: MetadataService):
        with patch(
            "src.services.metadata_service.utcnow",
            return_value=datetime(2026, 3, 16, 12, 0, 0, tzinfo=UTC),
        ):
            assert metadata_service._is_stale("2026-03-16T11:59:45", 60) is False

    def test_fallback_context_uses_default_labels(self, metadata_service: MetadataService):
        result = metadata_service._fallback_context("owner/repo")

        assert result.repo_key == "owner/repo"
        assert result.source == "fallback"
        assert result.labels
        assert result.branches == [{"name": "main", "protected": True}]
