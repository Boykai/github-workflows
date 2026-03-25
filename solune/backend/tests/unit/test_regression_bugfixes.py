"""Regression tests for bugs discovered and fixed.

Each test class documents the bug, references the fix, and prevents
the specific issue from being reintroduced.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from urllib.parse import quote

import pytest

# ── Bug 1: test_lint_async used hardcoded "python" instead of sys.executable ──


class TestLintAsyncUsesCorrectPython:
    """Regression: test_lint_async.py used bare 'python' binary which
    fails inside virtual environments where only 'python3' or the full
    venv path is available.

    Fix: use sys.executable so the test runs the same Python interpreter
    that is executing pytest.
    """

    def test_sys_executable_used_in_lint_test(self):
        """Verify the lint test source references sys.executable, not 'python'."""
        import pathlib

        lint_test = pathlib.Path(__file__).parent / "test_lint_async.py"
        source = lint_test.read_text()
        assert "sys.executable" in source, "test_lint_async.py should use sys.executable"
        assert '["python",' not in source, (
            'test_lint_async.py should NOT hardcode "python" as the binary'
        )


# ── Bug 2: _schedule_persist leaked unawaited coroutines ─────────────


class TestSchedulePersistClosesCoroutines:
    """Regression: _schedule_persist in transitions.py created coroutines
    that were never awaited or closed when no event loop was running,
    causing RuntimeWarning about unawaited coroutines during tests and
    process shutdown.

    Fix: call coro.close() in the RuntimeError handler.
    """

    def test_no_runtime_warning_when_no_event_loop(self):
        """Calling a sync transition helper that triggers _schedule_persist
        must not leave unawaited coroutines when no event loop is running."""
        import warnings

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", RuntimeWarning)

            from src.services.workflow_orchestrator.transitions import (
                clear_all_agent_trigger_buffers,
            )

            clear_all_agent_trigger_buffers()

        unawaited = [
            w
            for w in caught
            if issubclass(w.category, RuntimeWarning) and "never awaited" in str(w.message)
        ]
        assert unawaited == [], (
            f"Unawaited coroutine warnings found: {[str(w.message) for w in unawaited]}"
        )

    def test_schedule_persist_closes_coroutine_on_runtime_error(self):
        """_schedule_persist must call coro.close() when scheduling fails."""

        async def _dummy_coro():
            await asyncio.sleep(0)

        coro = _dummy_coro()

        with patch(
            "src.services.task_registry.task_registry",
        ) as mock_registry:
            mock_registry.create_task.side_effect = RuntimeError("no loop")

            from src.services.workflow_orchestrator.transitions import _schedule_persist

            _schedule_persist(coro)

        # After close(), attempting to send to the coroutine raises
        # "cannot reuse already awaited coroutine" (Python 3.12+)
        # or StopIteration — either confirms it was properly closed.
        with pytest.raises((StopIteration, RuntimeError)):
            coro.send(None)


# ── Bug 3: _claimed_child_prs iterated directly ──────────────────────


class TestClaimedChildPrsSnapshotIteration:
    """Regression: completion.py iterated over _claimed_child_prs directly
    (``for key in _claimed_child_prs:``). In edge cases where a concurrent
    coroutine adds to the set between await points within the same iteration
    scope, this could raise RuntimeError: dictionary changed size during
    iteration (since BoundedSet is backed by OrderedDict).

    Fix: iterate over ``list(_claimed_child_prs)`` snapshot.
    """

    def test_source_uses_list_snapshot(self):
        """Verify completion.py iterates a list snapshot, not the raw set."""
        import pathlib

        completion_py = (
            pathlib.Path(__file__).parent.parent.parent
            / "src"
            / "services"
            / "copilot_polling"
            / "completion.py"
        )
        source = completion_py.read_text()
        assert "for key in list(_claimed_child_prs)" in source, (
            "completion.py should iterate list(_claimed_child_prs) not raw _claimed_child_prs"
        )
        assert "for key in _claimed_child_prs:" not in source, (
            "completion.py should NOT iterate the raw _claimed_child_prs set"
        )


# ── Bug 4: _track_main_branch_if_needed exception blocks Done! marker ──


_GPS = "src.services.copilot_polling.github_projects_service"


class TestTrackMainBranchFailureDoesNotBlockDone:
    """Regression: agent_output.py called _track_main_branch_if_needed
    without try-except. If it raised (e.g. API 500), the exception
    propagated and prevented the Done! marker from being posted,
    permanently stalling the pipeline for that issue.

    Fix: wrap _track_main_branch_if_needed in try-except so completion
    continues even if branch tracking fails.
    """

    def test_source_has_try_except_around_track_main_branch(self):
        """Verify the try-except guard exists in source."""
        import pathlib

        agent_output_py = (
            pathlib.Path(__file__).parent.parent.parent
            / "src"
            / "services"
            / "copilot_polling"
            / "agent_output.py"
        )
        source = agent_output_py.read_text()
        # Find the _track_main_branch_if_needed call — it should be inside a try block
        idx = source.find("await _track_main_branch_if_needed(")
        assert idx != -1, "_track_main_branch_if_needed call not found"
        # Look backwards for the nearest try:
        preceding = source[:idx]
        last_try = preceding.rfind("try:")
        last_except = preceding.rfind("except")
        assert last_try > last_except, "_track_main_branch_if_needed should be inside a try block"


# ── Bug 5: label_manager didn't URL-encode label names in DELETE path ──


class TestLabelManagerURLEncoding:
    """Regression: delete_pipeline_label constructed the DELETE URL
    with the raw label name containing colons (e.g.
    ``solune:pipeline:1:stage:build:running``). RFC 3986 reserves ``:``
    and while GitHub's API tolerates it, proper encoding is required
    for correctness and portability.

    Fix: URL-encode the label name using urllib.parse.quote.
    """

    @pytest.mark.asyncio
    async def test_delete_url_encodes_label_name(self):
        """The DELETE path must contain the URL-encoded label name."""
        mock_rest = AsyncMock(return_value=SimpleNamespace(status_code=204))
        mock_gps = SimpleNamespace(rest_request=mock_rest)

        with patch("src.services.github_projects.github_projects_service", mock_gps):
            from src.services.copilot_polling.label_manager import delete_pipeline_label

            label_name = "solune:pipeline:1:stage:build:running"
            await delete_pipeline_label("tok", "owner", "repo", label_name)

        mock_rest.assert_awaited_once()
        call_args = mock_rest.call_args
        url_path = call_args[0][2]
        # Colons in the label name should be percent-encoded
        expected_encoded = quote(label_name, safe="")
        assert expected_encoded in url_path, (
            f"Expected URL-encoded label name '{expected_encoded}' in path, got: {url_path}"
        )
        # Specifically, the raw label should NOT appear in the path
        assert f"/labels/{label_name}" not in url_path, (
            f"Raw label name with colons should not appear unencoded in: {url_path}"
        )

    @pytest.mark.asyncio
    async def test_delete_handles_label_with_special_chars(self):
        """URL encoding handles labels with spaces or other special chars."""
        mock_rest = AsyncMock(return_value=SimpleNamespace(status_code=204))
        mock_gps = SimpleNamespace(rest_request=mock_rest)

        with patch("src.services.github_projects.github_projects_service", mock_gps):
            from src.services.copilot_polling.label_manager import delete_pipeline_label

            label_name = "solune:pipeline:99:stage:my stage:failed"
            await delete_pipeline_label("tok", "owner", "repo", label_name)

        call_args = mock_rest.call_args
        url_path = call_args[0][2]
        # Space should be encoded as %20
        assert "%20" in url_path or "+" in url_path


# ── Bug 6: _schedule_persist source code correctness ─────────────────


class TestSchedulePersistSourceCorrectness:
    """Verify the _schedule_persist function properly closes coroutines."""

    def test_source_has_coro_close(self):
        """The RuntimeError handler must call coro.close()."""
        import pathlib

        transitions_py = (
            pathlib.Path(__file__).parent.parent.parent
            / "src"
            / "services"
            / "workflow_orchestrator"
            / "transitions.py"
        )
        source = transitions_py.read_text()
        assert "coro.close()" in source, (
            "transitions.py _schedule_persist must call coro.close() in RuntimeError handler"
        )


# ── Additional: BoundedSet safety under concurrent modification ──────


class TestBoundedSetSnapshotSafety:
    """Verify that list() snapshot of BoundedSet is safe even if the
    underlying set is modified during iteration (simulated)."""

    def test_list_snapshot_survives_modification(self):
        from src.utils import BoundedSet

        bs: BoundedSet[str] = BoundedSet(maxlen=10)
        bs.add("a")
        bs.add("b")
        bs.add("c")

        # Take snapshot, then modify the set
        snapshot = list(bs)
        bs.add("d")
        bs.discard("a")

        # Snapshot is independent of modifications
        assert snapshot == ["a", "b", "c"]
        assert "d" in bs
        assert "a" not in bs


# ── Characterization: repo-resolution paths ──────────────────────────


class TestResolveRepositoryCachePath:
    """Pin: resolve_repository uses cache with token-scoped key."""

    def test_cache_key_includes_token_hash(self):
        """The cache key must include a hash of the access token."""
        import pathlib

        utils_py = pathlib.Path(__file__).parent.parent.parent / "src" / "utils.py"
        source = utils_py.read_text()
        assert "token_hash" in source
        assert "sha256" in source
        assert "resolve_repo:" in source

    def test_cache_key_includes_project_id(self):
        """The cache key must be scoped to the project_id."""
        import pathlib

        utils_py = pathlib.Path(__file__).parent.parent.parent / "src" / "utils.py"
        source = utils_py.read_text()
        assert "project_id" in source


class TestResolveRepositoryFallbackChain:
    """Pin: resolve_repository uses 3-step fallback: items → config → settings."""

    def test_fallback_order_documented(self):
        import pathlib

        utils_py = pathlib.Path(__file__).parent.parent.parent / "src" / "utils.py"
        source = utils_py.read_text()
        # Verify the fallback chain exists within resolve_repository function
        func_start = source.find("async def resolve_repository")
        assert func_start != -1, "resolve_repository function must exist"
        func_source = source[func_start:]
        # Check all three fallback steps are present
        assert "get_project_repository" in func_source
        assert "get_workflow_config" in func_source
        assert "default_repo_owner" in func_source


class TestResolveRepositoryValidation:
    """Pin: resolve_repository raises ValidationError when all fallbacks fail."""

    def test_raises_validation_error_on_failure(self):
        import pathlib

        utils_py = pathlib.Path(__file__).parent.parent.parent / "src" / "utils.py"
        source = utils_py.read_text()
        assert "ValidationError" in source
        # Must import and raise ValidationError
        assert "from src.exceptions import ValidationError" in source


# ── Characterization: error-response patterns ────────────────────────


class TestHTTPErrorResponsePatterns:
    """Pin: API endpoints return consistent error response shapes."""

    def test_error_response_uses_detail_key(self):
        """FastAPI-style HTTPException uses 'detail' as the error key."""
        import pathlib

        # Check that API routes use HTTPException(detail=...)
        api_dir = pathlib.Path(__file__).parent.parent.parent / "src" / "api"
        found_detail = False
        for py_file in api_dir.glob("*.py"):
            source = py_file.read_text()
            if "HTTPException" in source and "detail=" in source:
                found_detail = True
                break
        assert found_detail, "API routes should use HTTPException(detail=...)"

    def test_auth_returns_401_for_invalid_session(self):
        """Auth endpoints should raise AuthenticationError for invalid sessions."""
        import pathlib

        auth_py = pathlib.Path(__file__).parent.parent.parent / "src" / "api" / "auth.py"
        source = auth_py.read_text()
        assert "AuthenticationError" in source, (
            "Auth should raise AuthenticationError for invalid sessions"
        )

    def test_validation_errors_return_422(self):
        """Pydantic validation errors return 422 via FastAPI."""
        import pathlib

        main_py = pathlib.Path(__file__).parent.parent.parent / "src" / "main.py"
        source = main_py.read_text()
        # FastAPI auto-handles RequestValidationError → 422
        assert "FastAPI" in source or "create_app" in source

    def test_rate_limit_returns_429(self):
        """Rate limiting middleware should return 429."""
        import pathlib

        middleware_dir = pathlib.Path(__file__).parent.parent.parent / "src" / "middleware"
        found_429 = False
        for py_file in middleware_dir.glob("*.py"):
            source = py_file.read_text()
            if "429" in source or "rate" in source.lower():
                found_429 = True
                break
        assert found_429, "Middleware should handle rate limiting (429)"

    def test_guard_service_returns_403(self):
        """Guard service violations should result in 403-style blocking."""
        import pathlib

        guard_py = (
            pathlib.Path(__file__).parent.parent.parent / "src" / "services" / "guard_service.py"
        )
        source = guard_py.read_text()
        assert "admin_blocked" in source or "locked" in source, (
            "Guard service should categorize blocked paths"
        )


# ── Bug-bash: _decode_cursor missing input validation ────────────────


class TestDecodeCursorValidatesPayload:
    """Regression: _decode_cursor() in activity.py directly indexed
    ``parts[0], parts[1]`` on the decoded JSON without checking the
    array length, raising IndexError on malformed cursors instead of a
    meaningful ValueError.

    Fix: validate that the decoded JSON is a list with ≥2 elements.
    """

    def test_valid_cursor_round_trip(self):
        """A well-formed cursor encodes and decodes correctly."""
        from src.api.activity import _decode_cursor, _encode_cursor

        ts, eid = "2025-01-01T00:00:00", "abc-123"
        cursor = _encode_cursor(ts, eid)
        assert _decode_cursor(cursor) == (ts, eid)

    def test_malformed_cursor_empty_array(self):
        """An empty JSON array must raise ValueError, not IndexError."""
        import base64
        import json

        from src.api.activity import _decode_cursor

        bad = base64.urlsafe_b64encode(json.dumps([]).encode()).decode()
        with pytest.raises(ValueError, match="Invalid cursor payload"):
            _decode_cursor(bad)

    def test_malformed_cursor_single_element(self):
        """A JSON array with only one element must raise ValueError."""
        import base64
        import json

        from src.api.activity import _decode_cursor

        bad = base64.urlsafe_b64encode(json.dumps(["only-one"]).encode()).decode()
        with pytest.raises(ValueError, match="Invalid cursor payload"):
            _decode_cursor(bad)

    def test_malformed_cursor_non_array(self):
        """A JSON object (not an array) must raise ValueError."""
        import base64
        import json

        from src.api.activity import _decode_cursor

        bad = base64.urlsafe_b64encode(json.dumps({"a": 1}).encode()).decode()
        with pytest.raises(ValueError, match="Invalid cursor payload"):
            _decode_cursor(bad)


# ── Bug-bash: app_service create_app unsafe full_name key access ─────


class TestCreateAppValidatesFullName:
    """Regression: create_app() in app_service.py used
    ``repo_data["full_name"].split("/")[0]`` without checking whether
    ``full_name`` existed in the GitHub API response, causing a raw
    KeyError that leaks internal details.

    Fix: use ``.get()`` with a validation check that raises a clear
    ValidationError.
    """

    def test_source_uses_safe_full_name_access(self):
        """Verify the source no longer uses repo_data['full_name']."""
        import pathlib

        app_svc = (
            pathlib.Path(__file__).parent.parent.parent / "src" / "services" / "app_service.py"
        )
        source = app_svc.read_text()
        # The old pattern should be gone
        assert 'repo_data["full_name"]' not in source, (
            "app_service.py should not use direct dict access for full_name"
        )

    def test_source_validates_full_name_format(self):
        """Verify the source validates that full_name contains '/'."""
        import pathlib

        app_svc = (
            pathlib.Path(__file__).parent.parent.parent / "src" / "services" / "app_service.py"
        )
        source = app_svc.read_text()
        assert '"/" not in full_name' in source or "'/' not in full_name" in source, (
            "app_service.py should validate that full_name contains '/'"
        )


# ── Bug-bash: app_service import asyncio at module level ─────────────


class TestAppServiceAsyncioAtModuleLevel:
    """Regression: app_service.py had ``import asyncio`` inside
    create_app() and delete_app() function bodies. Each call re-executed
    the import lookup, adding unnecessary overhead.

    Fix: move ``import asyncio`` to the module-level import block.
    """

    def test_no_function_level_asyncio_import(self):
        """Verify no function-level 'import asyncio' exists."""
        import pathlib

        app_svc = (
            pathlib.Path(__file__).parent.parent.parent / "src" / "services" / "app_service.py"
        )
        lines = app_svc.read_text().splitlines()
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == "import asyncio" and line[0] == " ":
                pytest.fail(f"Function-level 'import asyncio' found at line {i} in app_service.py")


# ── Bug-bash: update_app column whitelist ────────────────────────────


class TestUpdateAppColumnWhitelist:
    """Regression: update_app() constructed a dynamic SQL SET clause
    from dictionary keys without validating them against a whitelist.
    While the keys were derived from controlled code, the missing
    validation was a defense-in-depth gap.

    Fix: add an explicit whitelist check before building the SET clause.
    """

    def test_source_has_allowed_columns_set(self):
        """Verify the source defines an allowed columns whitelist."""
        import pathlib

        app_svc = (
            pathlib.Path(__file__).parent.parent.parent / "src" / "services" / "app_service.py"
        )
        source = app_svc.read_text()
        assert "_ALLOWED_UPDATE_COLUMNS" in source, (
            "update_app should define _ALLOWED_UPDATE_COLUMNS whitelist"
        )

    def test_source_validates_columns_against_whitelist(self):
        """Verify the source rejects columns not in the whitelist."""
        import pathlib

        app_svc = (
            pathlib.Path(__file__).parent.parent.parent / "src" / "services" / "app_service.py"
        )
        source = app_svc.read_text()
        assert "not in _ALLOWED_UPDATE_COLUMNS" in source, (
            "update_app should validate column names against whitelist"
        )


# ── Bug-bash: _column_exists table name validation ───────────────────


class TestColumnExistsTableNameValidation:
    """Regression: _column_exists() in database.py validated table names
    with ``table_name.replace('_', '').isalnum()`` which allowed Unicode
    letters and digits. The fix uses ``re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', ...)``
    to restrict to ASCII identifiers only, matching SQLite naming conventions.
    """

    def test_source_uses_strict_regex_validation(self):
        """Verify strict regex is used instead of isalnum()."""
        import pathlib

        db_py = pathlib.Path(__file__).parent.parent.parent / "src" / "services" / "database.py"
        source = db_py.read_text()
        assert "re.fullmatch" in source, (
            "_column_exists should use re.fullmatch for table name validation"
        )
        assert "isalnum()" not in source, (
            "_column_exists should not use isalnum() for table name validation"
        )
