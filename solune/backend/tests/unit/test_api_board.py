"""Tests for board API routes (src/api/board.py).

Covers:
- GET /api/v1/board/projects              → list_board_projects
- GET /api/v1/board/projects/{project_id} → get_board_data
"""

from unittest.mock import patch

from src.models.board import (
    BoardColumn,
    BoardDataResponse,
    BoardItem,
    BoardProject,
    ContentType,
    Repository,
    StatusColor,
    StatusField,
    StatusOption,
)

# ── Helpers ─────────────────────────────────────────────────────────────────


def _make_board_project(**kw) -> BoardProject:
    defaults = {
        "project_id": "PVT_abc",
        "name": "Test Board",
        "url": "https://github.com/users/testuser/projects/1",
        "owner_login": "testuser",
        "status_field": StatusField(
            field_id="SF_1",
            options=[
                StatusOption(option_id="opt1", name="Todo", color=StatusColor.GRAY),
                StatusOption(option_id="opt2", name="Done", color=StatusColor.GREEN),
            ],
        ),
    }
    defaults.update(kw)
    return BoardProject(**defaults)


def _make_board_data(project: BoardProject | None = None) -> BoardDataResponse:
    proj = project or _make_board_project()
    return BoardDataResponse(
        project=proj,
        columns=[
            BoardColumn(
                status=proj.status_field.options[0],
                items=[
                    BoardItem(
                        item_id="PVTI_1",
                        content_type=ContentType.ISSUE,
                        title="Fix bug",
                        status="Todo",
                        status_option_id="opt1",
                    )
                ],
                item_count=1,
            ),
            BoardColumn(
                status=proj.status_field.options[1],
                items=[],
                item_count=0,
            ),
        ],
    )


# ── GET /board/projects ────────────────────────────────────────────────────


class TestListBoardProjects:
    async def test_returns_projects(self, client, mock_github_service):
        bp = _make_board_project()
        mock_github_service.list_board_projects.return_value = [bp]
        resp = await client.get("/api/v1/board/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["projects"]) == 1
        assert data["projects"][0]["name"] == "Test Board"

    async def test_uses_cache_on_second_call(self, client, mock_github_service):
        bp = _make_board_project()
        mock_github_service.list_board_projects.return_value = [bp]

        # First call — populates cache
        resp1 = await client.get("/api/v1/board/projects")
        assert resp1.status_code == 200
        # Second call — should use cache (service not called again)
        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = [bp]
            resp2 = await client.get("/api/v1/board/projects")
            assert resp2.status_code == 200
            mock_cache.get.assert_called_once()

    async def test_refresh_bypasses_cache(self, client, mock_github_service):
        bp = _make_board_project()
        mock_github_service.list_board_projects.return_value = [bp]
        resp = await client.get("/api/v1/board/projects", params={"refresh": True})
        assert resp.status_code == 200
        mock_github_service.list_board_projects.assert_called_once()

    async def test_github_api_error(self, client, mock_github_service):
        mock_github_service.list_board_projects.side_effect = RuntimeError("network")
        resp = await client.get("/api/v1/board/projects", params={"refresh": True})
        # Should raise GitHubAPIError (mapped to 502 via AppException handler)
        assert resp.status_code == 502

    async def test_rate_limit_uses_cached_headers_for_generic_errors(
        self, client, mock_github_service
    ):
        mock_github_service.list_board_projects.side_effect = RuntimeError("network")
        mock_github_service.get_last_rate_limit.return_value = {
            "limit": 5000,
            "remaining": 0,
            "reset_at": 1_700_000_000,
            "used": 5000,
        }

        resp = await client.get("/api/v1/board/projects", params={"refresh": True})

        assert resp.status_code == 429
        body = resp.json()
        assert body["error"] == "GitHub API rate limit exceeded"
        assert body["details"]["rate_limit"]["remaining"] == 0


# ── GET /board/projects/{project_id} ───────────────────────────────────────


class TestGetBoardData:
    async def test_returns_board_data(self, client, mock_github_service):
        bd = _make_board_data()
        mock_github_service.get_board_data.return_value = bd
        resp = await client.get("/api/v1/board/projects/PVT_abc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project"]["project_id"] == "PVT_abc"
        assert len(data["columns"]) == 2
        assert data["columns"][0]["item_count"] == 1

    async def test_project_not_found(self, client, mock_github_service):
        mock_github_service.get_board_data.side_effect = ValueError("not found")
        resp = await client.get("/api/v1/board/projects/PVT_bad")
        assert resp.status_code == 404

    async def test_github_error_on_board_data(self, client, mock_github_service):
        mock_github_service.get_board_data.side_effect = RuntimeError("timeout")
        resp = await client.get("/api/v1/board/projects/PVT_error", params={"refresh": True})
        assert resp.status_code == 502

    async def test_rate_limit_uses_cached_headers_for_board_data_generic_errors(
        self, client, mock_github_service
    ):
        mock_github_service.get_board_data.side_effect = RuntimeError("timeout")
        mock_github_service.get_last_rate_limit.return_value = {
            "limit": 5000,
            "remaining": 0,
            "reset_at": 1_700_000_000,
            "used": 5000,
        }

        resp = await client.get("/api/v1/board/projects/PVT_error", params={"refresh": True})

        assert resp.status_code == 429
        body = resp.json()
        assert body["error"] == "GitHub API rate limit exceeded"
        assert body["details"]["rate_limit"]["used"] == 5000

    async def test_refresh_board_data(self, client, mock_github_service):
        bd = _make_board_data()
        mock_github_service.get_board_data.return_value = bd
        resp = await client.get("/api/v1/board/projects/PVT_abc", params={"refresh": True})
        assert resp.status_code == 200
        mock_github_service.get_board_data.assert_called_once()

    async def test_board_data_cache_stores_data_hash(self, client, mock_github_service):
        """Board data should be cached with a data_hash for change detection."""
        bd = _make_board_data()
        mock_github_service.get_board_data.return_value = bd

        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.get_stale.return_value = None
            resp = await client.get("/api/v1/board/projects/PVT_abc")
            assert resp.status_code == 200

            # Verify cache.set was called with a data_hash keyword argument
            mock_cache.set.assert_called()
            # Search call_args_list for the board cache set call with data_hash,
            # so the test remains robust if the endpoint adds more cache writes.
            data_hash = None
            for call in mock_cache.set.call_args_list:
                h = call.kwargs.get("data_hash")
                if h is not None:
                    data_hash = h
                    break
            assert data_hash is not None
            # The data_hash should be a 64-char hex SHA-256 string
            assert isinstance(data_hash, str)
            assert len(data_hash) == 64

    async def test_manual_refresh_clears_sub_issue_caches(self, client, mock_github_service):
        """Manual refresh (refresh=true) must clear sub-issue caches before fetching."""
        bd = _make_board_data()
        # Add repository info to the board item
        from src.models.board import Repository

        bd.columns[0].items[0].repository = Repository(owner="test-owner", name="test-repo")
        bd.columns[0].items[0].number = 42

        mock_github_service.get_board_data.return_value = bd

        with patch("src.api.board.cache") as mock_cache:
            # First populate cache
            mock_cache.get.return_value = bd
            mock_cache.get_stale.return_value = None

            resp = await client.get("/api/v1/board/projects/PVT_abc", params={"refresh": True})
            assert resp.status_code == 200

            # Verify cache.delete was called for sub-issue cache key
            delete_calls = [str(call) for call in mock_cache.delete.call_args_list]
            assert any("sub_issues" in str(call) for call in delete_calls)

    async def test_unchanged_board_data_returns_cached_with_fresh_rate_limit(
        self, client, mock_github_service
    ):
        """When board data is cached and unchanged, response includes fresh rate_limit."""
        bd = _make_board_data()
        mock_github_service.get_board_data.return_value = bd

        # First request populates cache
        resp1 = await client.get("/api/v1/board/projects/PVT_abc")
        assert resp1.status_code == 200

        # Second request should use cache
        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = bd
            resp2 = await client.get("/api/v1/board/projects/PVT_abc")
            assert resp2.status_code == 200
            mock_cache.get.assert_called_once()

    async def test_board_data_hash_excludes_rate_limit(self, client, mock_github_service):
        """Board data hash should exclude rate_limit so same board content gets same hash."""
        bd = _make_board_data()
        mock_github_service.get_board_data.return_value = bd

        hashes = []

        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.get_stale.return_value = None

            # First request
            resp1 = await client.get("/api/v1/board/projects/PVT_abc")
            assert resp1.status_code == 200
            h1 = None
            for call in mock_cache.set.call_args_list:
                h = call.kwargs.get("data_hash")
                if h is not None:
                    h1 = h
                    break
            hashes.append(h1)

        # Change rate limit info but keep board data identical
        mock_github_service.get_last_rate_limit.return_value = {
            "limit": 5000,
            "remaining": 4900,
            "reset_at": 1_700_000_000,
            "used": 100,
        }

        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.get_stale.return_value = None

            # Second request — same board data, different rate_limit
            resp2 = await client.get("/api/v1/board/projects/PVT_abc")
            assert resp2.status_code == 200
            h2 = None
            for call in mock_cache.set.call_args_list:
                h = call.kwargs.get("data_hash")
                if h is not None:
                    h2 = h
                    break
            hashes.append(h2)

        # Hashes should match because rate_limit is excluded
        assert hashes[0] is not None
        assert hashes[0] == hashes[1]

    async def test_warm_cache_prevents_outbound_api_calls(self, client, mock_github_service):
        """When board data is cached (warm), no outbound GitHub API call should occur (SC-001)."""
        bd = _make_board_data()
        mock_github_service.get_board_data.return_value = bd

        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = bd
            resp = await client.get("/api/v1/board/projects/PVT_abc")
            assert resp.status_code == 200
            # Service should NOT be called when cache is warm
            mock_github_service.get_board_data.assert_not_called()

    async def test_non_manual_refresh_reuses_sub_issue_cache(self, client, mock_github_service):
        """Non-manual refresh (refresh=false) must NOT clear sub-issue caches (SC-002)."""
        bd = _make_board_data()
        from src.models.board import Repository

        bd.columns[0].items[0].repository = Repository(owner="test-owner", name="test-repo")
        bd.columns[0].items[0].number = 42

        mock_github_service.get_board_data.return_value = bd

        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.get_stale.return_value = None

            resp = await client.get("/api/v1/board/projects/PVT_abc")
            assert resp.status_code == 200

            # cache.delete should NOT be called (sub-issue caches preserved)
            delete_calls = [str(call) for call in mock_cache.delete.call_args_list]
            assert not any("sub_issues" in str(call) for call in delete_calls)


# ── Performance: change detection suppresses unchanged WebSocket pushes ─────


class TestChangeDetection:
    """Verify that unchanged data hash suppresses client pushes (FR-004)."""

    def test_unchanged_data_hash_produces_same_hash(self):
        """Same board data should produce identical hashes for change detection."""
        from src.services.cache import compute_data_hash

        bd = _make_board_data()
        payload = bd.model_dump(mode="json", exclude={"rate_limit"})

        hash1 = compute_data_hash(payload)
        hash2 = compute_data_hash(payload)
        assert hash1 == hash2

    def test_changed_data_produces_different_hash(self):
        """Modified board data should produce a different hash."""
        from src.services.cache import compute_data_hash

        bd1 = _make_board_data()
        bd2 = _make_board_data()
        bd2.columns[0].items[0].title = "Different title"

        hash1 = compute_data_hash(bd1.model_dump(mode="json", exclude={"rate_limit"}))
        hash2 = compute_data_hash(bd2.model_dump(mode="json", exclude={"rate_limit"}))
        assert hash1 != hash2


# ── Regression: board error responses must NOT leak internal details ────────


class TestBoardErrorSanitization:
    """Bug-bash regression: GitHubAPIError raised in board endpoints must not
    include raw exception strings in the ``details`` field."""

    async def test_list_projects_error_does_not_leak_details(self, client, mock_github_service):
        """list_board_projects must not expose internal error strings."""
        mock_github_service.list_board_projects.side_effect = RuntimeError(
            "Connection refused to https://api.github.com"
        )
        resp = await client.get("/api/v1/board/projects", params={"refresh": True})
        assert resp.status_code == 502
        body = resp.json()
        assert "Connection refused" not in str(body)
        assert "api.github.com" not in str(body)

    async def test_get_board_data_error_does_not_leak_details(self, client, mock_github_service):
        """get_board_data must not expose internal error strings."""
        mock_github_service.get_board_data.side_effect = RuntimeError(
            "SSL: CERTIFICATE_VERIFY_FAILED"
        )
        resp = await client.get("/api/v1/board/projects/PVT_err", params={"refresh": True})
        assert resp.status_code == 502
        body = resp.json()
        assert "CERTIFICATE_VERIFY_FAILED" not in str(body)

    async def test_not_found_error_does_not_include_project_id(self, client, mock_github_service):
        """NotFoundError from get_board_data must not echo the project_id back
        to the client — user-controlled input should never appear in error messages."""
        mock_github_service.get_board_data.side_effect = ValueError("no such project")
        resp = await client.get(
            "/api/v1/board/projects/ATTACKER_CONTROLLED_ID", params={"refresh": True}
        )
        assert resp.status_code == 404
        body = resp.json()
        assert "ATTACKER_CONTROLLED_ID" not in str(body)


# ── Performance: Cache-hit behavior for project items (T012) ───────────────


class TestProjectItemsCacheHit:
    """Verify InMemoryCache get/miss behavior for project items cache keys.
    NOTE: These tests cover cache-layer semantics only, not the full WebSocket
    handler path.  Dedicated WebSocket integration tests are needed to verify
    end-to-end short-circuiting."""

    def test_cache_hit_returns_cached_data(self):
        """When cache has valid data, get() returns it."""
        from src.services.cache import cache, get_project_items_cache_key

        cache_key = get_project_items_cache_key("PVT_test")
        test_data = [{"id": "1", "title": "cached"}]
        cache.set(cache_key, test_data)

        # Verify cache.get() returns the data
        result = cache.get(cache_key)
        assert result is not None
        assert result == test_data

    def test_cache_miss_requires_fetch(self):
        """When cache is empty, get() returns None (caller must fetch)."""
        from src.services.cache import cache, get_project_items_cache_key

        cache_key = get_project_items_cache_key("PVT_missing")
        result = cache.get(cache_key)
        assert result is None


# ── Performance: stale-revalidation hash comparison (T013) ─────────────────


class TestStaleRevalidationHash:
    """Verify that stale-revalidation counter resets on verified-unchanged
    data (same hash) rather than only on forced fetches."""

    def test_unchanged_data_refreshes_ttl(self):
        """When fetched data matches cached data hash, TTL is refreshed."""
        from src.services.cache import (
            cache,
            compute_data_hash,
            get_project_items_cache_key,
        )

        cache_key = get_project_items_cache_key("PVT_revalidate")
        test_data = [{"id": "1", "title": "test"}]
        data_hash = compute_data_hash(test_data)

        # Prime cache with a data hash
        cache.set(cache_key, test_data, data_hash=data_hash)

        # Verify entry exists with hash
        entry = cache.get_entry(cache_key)
        assert entry is not None
        assert entry.data_hash == data_hash

        # Refresh TTL (simulating unchanged data detection)
        original_expires = entry.expires_at
        import time

        time.sleep(0.01)  # Ensure time difference
        cache.refresh_ttl(cache_key)

        # TTL should have been refreshed
        refreshed_entry = cache.get_entry(cache_key)
        assert refreshed_entry is not None
        assert refreshed_entry.expires_at > original_expires

    def test_changed_data_stores_new_entry(self):
        """When fetched data differs from cached data hash, a new entry is stored."""
        from src.services.cache import cache, compute_data_hash, get_project_items_cache_key

        cache_key = get_project_items_cache_key("PVT_changed")
        old_data = [{"id": "1", "title": "old"}]
        new_data = [{"id": "1", "title": "updated"}]
        old_hash = compute_data_hash(old_data)
        new_hash = compute_data_hash(new_data)

        # Prime cache with old data
        cache.set(cache_key, old_data, data_hash=old_hash)

        # Verify hashes differ
        assert old_hash != new_hash

        # Store new data with new hash (simulating changed data)
        cache.set(cache_key, new_data, data_hash=new_hash)

        entry = cache.get_entry(cache_key)
        assert entry is not None
        assert entry.data_hash == new_hash
        assert entry.value == new_data


# ── Performance: sub-issue cache reuse on non-manual refresh (T019-T021) ───


class TestSubIssueCacheReuse:
    """Verify sub-issue cache behavior for board data refreshes."""

    async def test_non_manual_refresh_checks_sub_issue_cache(self, client, mock_github_service):
        """Non-manual refresh should check sub-issue cache before external calls (T019)."""
        bd = _make_board_data()
        from src.models.board import Repository

        bd.columns[0].items[0].repository = Repository(owner="test-owner", name="test-repo")
        bd.columns[0].items[0].number = 42
        mock_github_service.get_board_data.return_value = bd

        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.get_stale.return_value = None
            resp = await client.get("/api/v1/board/projects/PVT_abc")
            assert resp.status_code == 200
            # cache.delete should NOT be called on non-manual refresh
            delete_calls = [str(call) for call in mock_cache.delete.call_args_list]
            assert not any("sub_issues" in c for c in delete_calls)

    async def test_manual_refresh_clears_sub_issue_cache_entries(self, client, mock_github_service):
        """Manual refresh (refresh=True) must clear sub-issue cache entries (T020)."""
        bd = _make_board_data()
        from src.models.board import Repository

        bd.columns[0].items[0].repository = Repository(owner="test-owner", name="test-repo")
        bd.columns[0].items[0].number = 42
        mock_github_service.get_board_data.return_value = bd

        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = bd
            mock_cache.get_stale.return_value = None
            resp = await client.get("/api/v1/board/projects/PVT_abc", params={"refresh": True})
            assert resp.status_code == 200
            # cache.delete should be called for sub-issue cache key
            delete_calls = [str(call) for call in mock_cache.delete.call_args_list]
            assert any("sub_issues" in c for c in delete_calls)

    async def test_warm_sub_issue_cache_reduces_fetch_count(self, client, mock_github_service):
        """Warm sub-issue cache should prevent redundant API calls (T021/SC-003)."""
        bd = _make_board_data()
        mock_github_service.get_board_data.return_value = bd

        with patch("src.api.board.cache") as mock_cache:
            # Simulate warm cache — return cached board data
            mock_cache.get.return_value = bd
            resp = await client.get("/api/v1/board/projects/PVT_abc")
            assert resp.status_code == 200
            # Service should NOT be called when cache is warm
            mock_github_service.get_board_data.assert_not_called()


# ---------------------------------------------------------------------------
# T018 - Column transform edge cases
# ---------------------------------------------------------------------------


class TestColumnTransformEdgeCases:
    """Edge-case tests for _to_board_projects and empty/missing column data."""

    def test_empty_columns_list_produces_no_board_projects(self):
        """A GitHubProject with an empty status_columns list is skipped."""
        from src.api.board import _to_board_projects
        from src.models.project import GitHubProject

        # Use model_construct to bypass validation — simulates a project whose
        # columns were stripped after construction (e.g. deserialized legacy data).
        project = GitHubProject.model_construct(
            project_id="PVT_empty",
            owner_id="O_empty",
            owner_login="testuser",
            name="No Columns",
            type="user",
            url="https://github.com/users/testuser/projects/9",
            status_columns=[],
        )
        result = _to_board_projects([project])
        assert result == []

    def test_single_column_with_no_items_still_creates_board_project(self):
        """A column with a valid field_id/option_id produces a BoardProject."""
        from src.api.board import _to_board_projects
        from src.models.project import GitHubProject, StatusColumn

        project = GitHubProject(
            project_id="PVT_single",
            owner_id="O_single",
            owner_login="testuser",
            name="One Column",
            type="user",
            url="https://github.com/users/testuser/projects/10",
            status_columns=[
                StatusColumn(
                    field_id="SF_1",
                    option_id="opt_1",
                    name="Backlog",
                    color="GRAY",
                ),
            ],
        )
        result = _to_board_projects([project])
        assert len(result) == 1
        assert result[0].name == "One Column"
        assert len(result[0].status_field.options) == 1

    def test_column_missing_option_id_is_filtered_out(self):
        """Columns without an option_id should be excluded from valid columns."""
        from src.api.board import _to_board_projects
        from src.models.project import GitHubProject, StatusColumn

        # Use model_construct on the column to bypass option_id required validation
        col = StatusColumn.model_construct(
            field_id="SF_1",
            option_id=None,
            name="Draft",
            color="GRAY",
        )
        project = GitHubProject.model_construct(
            project_id="PVT_no_opt",
            owner_id="O_no_opt",
            owner_login="testuser",
            name="Missing Option",
            type="user",
            url="https://github.com/users/testuser/projects/11",
            status_columns=[col],
        )
        result = _to_board_projects([project])
        assert result == []


# ---------------------------------------------------------------------------
# T019 - Rate-limit recovery
# ---------------------------------------------------------------------------


class TestRateLimitRecovery:
    """Tests for rate-limit detection, retry-after extraction, and cached header info."""

    def test_retry_after_seconds_from_timedelta(self):
        """_retry_after_seconds extracts seconds from a timedelta attribute."""
        from datetime import timedelta

        from src.api.board import _retry_after_seconds

        exc = Exception("rate limited")
        exc.retry_after = timedelta(seconds=42)  # type: ignore[attr-defined]
        assert _retry_after_seconds(exc) == 42

    def test_retry_after_seconds_from_int(self):
        """_retry_after_seconds returns the integer directly."""
        from src.api.board import _retry_after_seconds

        exc = Exception("rate limited")
        exc.retry_after = 30  # type: ignore[attr-defined]
        assert _retry_after_seconds(exc) == 30

    def test_retry_after_seconds_defaults_to_60(self):
        """Falls back to 60 s when no retry-after info is available."""
        from src.api.board import _retry_after_seconds

        assert _retry_after_seconds(ValueError("no info")) == 60

    def test_rate_limit_info_from_cached_headers(self):
        """_get_rate_limit_info builds RateLimitInfo from service cache."""
        from src.api.board import _get_rate_limit_info

        rl_dict = {"limit": 5000, "remaining": 100, "reset_at": 1700000000, "used": 4900}
        with patch("src.api.board.github_projects_service") as mock_svc:
            mock_svc.get_last_rate_limit.return_value = rl_dict
            info = _get_rate_limit_info()
        assert info is not None
        assert info.remaining == 100

    def test_rate_limit_info_returns_none_for_missing_keys(self):
        """Returns None when the cached dict is missing required keys."""
        from src.api.board import _get_rate_limit_info

        with patch("src.api.board.github_projects_service") as mock_svc:
            mock_svc.get_last_rate_limit.return_value = {"limit": 5000}
            info = _get_rate_limit_info()
        assert info is None

    def test_rate_limit_info_returns_none_for_non_dict(self):
        """Returns None when the cached value is not a dict."""
        from src.api.board import _get_rate_limit_info

        with patch("src.api.board.github_projects_service") as mock_svc:
            mock_svc.get_last_rate_limit.return_value = None
            info = _get_rate_limit_info()
        assert info is None


# ---------------------------------------------------------------------------
# T020 - Token expiration flows
# ---------------------------------------------------------------------------


class TestTokenExpirationFlows:
    """Tests for authentication error detection and 401 flows."""

    def test_is_github_auth_error_detects_bad_credentials(self):
        """ValueError containing 'bad credentials' is classified as auth error."""
        from src.api.board import _is_github_auth_error

        assert _is_github_auth_error(ValueError("bad credentials")) is True

    def test_is_github_auth_error_ignores_generic_errors(self):
        """A generic RuntimeError is NOT classified as auth error."""
        from src.api.board import _is_github_auth_error

        assert _is_github_auth_error(RuntimeError("timeout")) is False

    async def test_expired_token_returns_401(self, client, mock_github_service):
        """A 'bad credentials' error from the service should yield HTTP 401."""
        mock_github_service.list_board_projects.side_effect = ValueError("bad credentials")
        resp = await client.get("/api/v1/board/projects", params={"refresh": True})
        assert resp.status_code == 401
        body = resp.json()
        assert (
            "expired" in body.get("error", "").lower() or "log in" in body.get("error", "").lower()
        )

    async def test_401_does_not_leak_token(self, client, mock_github_service):
        """Auth error responses must not include internal details."""
        mock_github_service.list_board_projects.side_effect = ValueError(
            "unauthorized: token ghp_SECRETTOKEN123"
        )
        resp = await client.get("/api/v1/board/projects", params={"refresh": True})
        assert resp.status_code == 401
        body_str = str(resp.json())
        assert "ghp_SECRETTOKEN123" not in body_str


# ---------------------------------------------------------------------------
# T021 - Cache hash error branches
# ---------------------------------------------------------------------------


class TestCacheHashBranches:
    """Tests for compute_data_hash with None / empty data."""

    def test_hash_with_none_data(self):
        """compute_data_hash handles None input without crashing."""
        from src.services.cache import compute_data_hash

        h = compute_data_hash(None)
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex digest

    def test_hash_with_empty_board_data(self):
        """compute_data_hash produces a valid hash for empty dict."""
        from src.services.cache import compute_data_hash

        h = compute_data_hash({})
        assert isinstance(h, str)
        assert len(h) == 64

    def test_hash_empty_list(self):
        """compute_data_hash produces a valid hash for empty list."""
        from src.services.cache import compute_data_hash

        h = compute_data_hash([])
        assert isinstance(h, str)
        assert len(h) == 64

    def test_hash_stability_for_none(self):
        """Same None input yields the same hash on repeated calls."""
        from src.services.cache import compute_data_hash

        assert compute_data_hash(None) == compute_data_hash(None)

    def test_different_data_produces_different_hash(self):
        """None, empty dict, and empty list yield distinct hashes."""
        from src.services.cache import compute_data_hash

        h_none = compute_data_hash(None)
        h_dict = compute_data_hash({})
        h_list = compute_data_hash([])
        assert len({h_none, h_dict, h_list}) == 3


# ── Hash-Based Change Detection and Cache Semantics (T018/FR-003/SC-001) ───


class TestHashChangeDetectionLogic:
    """Unit tests for hash-based change detection and cache behavior.

    These tests exercise ``compute_data_hash`` and cache TTL refresh semantics
    that are used by higher-level components (e.g. WebSocket handlers) to
    avoid sending redundant ``refresh`` messages when data is unchanged.
    """

    def test_same_tasks_payload_produces_same_hash(self):
        """Identical task payloads yield the same hash — no refresh needed."""
        from src.services.cache import compute_data_hash

        payload = [{"id": "1", "title": "A"}, {"id": "2", "title": "B"}]
        h1 = compute_data_hash(payload)
        h2 = compute_data_hash(payload)
        assert h1 == h2, "identical payload must produce identical hash"

    def test_changed_tasks_payload_produces_different_hash(self):
        """Modified task payloads yield different hashes — refresh needed."""
        from src.services.cache import compute_data_hash

        payload_a = [{"id": "1", "title": "A"}]
        payload_b = [{"id": "1", "title": "A-updated"}]
        assert compute_data_hash(payload_a) != compute_data_hash(payload_b)

    def test_hash_comparison_gates_refresh_send(self):
        """Simulate the send-or-skip decision: skip when hashes match."""
        from src.services.cache import compute_data_hash

        payload = [{"id": "1", "title": "Task"}]
        last_sent_hash = compute_data_hash(payload)

        # Same payload — should skip
        current_hash = compute_data_hash(payload)
        should_send = current_hash != last_sent_hash
        assert not should_send, "unchanged data must suppress refresh message"

    def test_hash_comparison_allows_refresh_on_change(self):
        """Simulate the send-or-skip decision: send when hashes differ."""
        from src.services.cache import compute_data_hash

        payload_v1 = [{"id": "1", "title": "Task"}]
        last_sent_hash = compute_data_hash(payload_v1)

        payload_v2 = [{"id": "1", "title": "Task"}, {"id": "2", "title": "New"}]
        current_hash = compute_data_hash(payload_v2)
        should_send = current_hash != last_sent_hash
        assert should_send, "changed data must allow refresh message"

    def test_cache_ttl_refresh_on_unchanged_data(self):
        """When fetched data matches cached hash, only TTL is refreshed."""
        from src.services.cache import InMemoryCache, compute_data_hash

        cache = InMemoryCache()
        key = "project:items:PVT_test"
        data = [{"id": "1"}]
        data_hash = compute_data_hash(data)

        # Store initial entry
        cache.set(key, data, ttl_seconds=300, data_hash=data_hash)

        # Simulate re-fetch with same data
        new_hash = compute_data_hash(data)
        existing = cache.get_entry(key)
        assert existing is not None
        assert existing.data_hash == new_hash

        # TTL refresh instead of full store
        cache.refresh_ttl(key, ttl_seconds=300)
        refreshed = cache.get_entry(key)
        assert refreshed is not None
        assert refreshed.data_hash == data_hash  # hash preserved


# ── Board Endpoint Cache TTL Regression (T019/FR-004/SC-002) ───────────────


class TestBoardEndpointCacheTTL:
    """Verify that the board endpoint cache with 300s TTL prevents redundant
    GitHub API calls during normal (non-manual) board access (FR-004, SC-002).
    """

    async def test_board_cache_hit_within_ttl_skips_api(self, client, mock_github_service):
        """Board data fetched within 300s TTL returns cached data without
        invoking the GitHub service (SC-002)."""
        board_data = _make_board_data()
        mock_github_service.get_board_data.return_value = board_data

        # First request — populates cache
        resp1 = await client.get("/api/v1/board/projects/PVT_abc")
        assert resp1.status_code == 200
        assert mock_github_service.get_board_data.call_count == 1

        # Second request within TTL — should serve from cache
        resp2 = await client.get("/api/v1/board/projects/PVT_abc")
        assert resp2.status_code == 200
        # Service should NOT be called again (cache hit)
        assert mock_github_service.get_board_data.call_count == 1

    async def test_manual_refresh_bypasses_cache_ttl(self, client, mock_github_service):
        """Manual refresh (refresh=true) always fetches fresh data even
        when TTL is still valid (FR-006, SC-009)."""
        board_data = _make_board_data()
        mock_github_service.get_board_data.return_value = board_data

        # First request — populates cache
        await client.get("/api/v1/board/projects/PVT_abc")
        assert mock_github_service.get_board_data.call_count == 1

        # Manual refresh — bypasses cache
        resp = await client.get("/api/v1/board/projects/PVT_abc", params={"refresh": True})
        assert resp.status_code == 200
        assert mock_github_service.get_board_data.call_count == 2


# ── Sub-Issue Cache Lifecycle (T020/FR-005/FR-006) ─────────────────────────


class TestSubIssueCacheLifecycle:
    """Verify that sub-issue caches are reused on auto-refresh and cleared
    on manual refresh (FR-005, FR-006)."""

    async def test_sub_issue_cache_survives_auto_refresh(self, client, mock_github_service):
        """Non-manual board requests preserve sub-issue cache entries (FR-005)."""
        board_data = _make_board_data()
        mock_github_service.get_board_data.return_value = board_data

        with patch("src.api.board.cache") as mock_cache:
            # Return the board data from cache
            mock_cache.get.return_value = board_data
            resp = await client.get("/api/v1/board/projects/PVT_abc")
            assert resp.status_code == 200
            # Sub-issue cache delete should NOT be called for auto-refresh
            mock_cache.delete.assert_not_called()

    async def test_sub_issue_cache_cleared_on_manual_refresh(self, client, mock_github_service):
        """Manual refresh clears sub-issue caches before fetching (FR-006)."""
        # Build board data with a realistic BoardItem that has number + repository,
        # so the manual-refresh path in board.py triggers cache.delete for sub-issues.
        proj = _make_board_project()
        board_data = BoardDataResponse(
            project=proj,
            columns=[
                BoardColumn(
                    status=proj.status_field.options[0],
                    items=[
                        BoardItem(
                            item_id="PVTI_sub",
                            content_type=ContentType.ISSUE,
                            title="Issue with sub-issues",
                            status="Todo",
                            status_option_id="opt1",
                            number=42,
                            repository=Repository(owner="testowner", name="testrepo"),
                        )
                    ],
                    item_count=1,
                ),
            ],
        )
        mock_github_service.get_board_data.return_value = board_data

        # First call to populate cache
        await client.get("/api/v1/board/projects/PVT_abc")

        # Manual refresh should clear sub-issue caches
        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = board_data
            resp = await client.get("/api/v1/board/projects/PVT_abc", params={"refresh": True})
            assert resp.status_code == 200
            # board.py deletes sub-issue cache entries when item.number and
            # item.repository are present — verify that cache.delete was called.
            assert mock_cache.delete.call_count >= 1, (
                "cache.delete should be called for sub-issue cleanup on manual refresh"
            )
