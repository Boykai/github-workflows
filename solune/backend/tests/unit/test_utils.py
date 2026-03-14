"""Unit tests for src.utils module."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils import BoundedDict, BoundedSet, resolve_repository, utcnow

# =============================================================================
# BoundedSet
# =============================================================================


class TestBoundedSet:
    """Tests for BoundedSet."""

    def test_add_and_contains(self):
        """Should add items and report membership correctly."""
        bs = BoundedSet(maxlen=5)
        bs.add("a")
        bs.add("b")

        assert "a" in bs
        assert "b" in bs
        assert "c" not in bs

    def test_len(self):
        """Should report the correct number of items."""
        bs = BoundedSet(maxlen=5)
        bs.add("a")
        bs.add("b")

        assert len(bs) == 2

    def test_discard_existing(self):
        """Should remove an existing item."""
        bs = BoundedSet(maxlen=5)
        bs.add("a")
        bs.discard("a")

        assert "a" not in bs
        assert len(bs) == 0

    def test_discard_missing_is_noop(self):
        """Should silently ignore discarding a missing item."""
        bs = BoundedSet(maxlen=5)
        bs.discard("missing")  # should not raise

    def test_iter(self):
        """Should iterate over items in insertion order."""
        bs = BoundedSet(maxlen=5)
        bs.add("a")
        bs.add("b")
        bs.add("c")

        assert list(bs) == ["a", "b", "c"]

    def test_clear(self):
        """Should remove all items."""
        bs = BoundedSet(maxlen=5)
        bs.add("a")
        bs.add("b")
        bs.clear()

        assert len(bs) == 0

    def test_repr(self):
        """Should return a descriptive repr string."""
        bs = BoundedSet(maxlen=3)
        bs.add("x")

        assert repr(bs) == "BoundedSet(maxlen=3, size=1)"

    def test_maxlen_property(self):
        """Should expose the configured maxlen."""
        bs = BoundedSet(maxlen=7)

        assert bs.maxlen == 7

    def test_maxlen_zero_raises(self):
        """Should raise ValueError when maxlen is 0."""
        with pytest.raises(ValueError, match="maxlen must be > 0"):
            BoundedSet(maxlen=0)

    def test_maxlen_negative_raises(self):
        """Should raise ValueError when maxlen is negative."""
        with pytest.raises(ValueError, match="maxlen must be > 0"):
            BoundedSet(maxlen=-1)

    def test_eviction_fifo(self):
        """Should evict the oldest item when capacity is exceeded."""
        bs = BoundedSet(maxlen=3)
        bs.add("a")
        bs.add("b")
        bs.add("c")
        bs.add("d")  # should evict "a"

        assert "a" not in bs
        assert list(bs) == ["b", "c", "d"]

    def test_eviction_multiple(self):
        """Should evict oldest items progressively."""
        bs = BoundedSet(maxlen=2)
        bs.add(1)
        bs.add(2)
        bs.add(3)  # evicts 1
        bs.add(4)  # evicts 2

        assert list(bs) == [3, 4]

    def test_add_existing_moves_to_end(self):
        """Re-adding an existing item should move it to the end."""
        bs = BoundedSet(maxlen=3)
        bs.add("a")
        bs.add("b")
        bs.add("c")

        bs.add("a")  # move "a" to end
        bs.add("d")  # should evict "b" (now the oldest)

        assert "b" not in bs
        assert list(bs) == ["c", "a", "d"]


# =============================================================================
# BoundedDict
# =============================================================================


class TestBoundedDict:
    """Tests for BoundedDict."""

    def test_setitem_and_getitem(self):
        """Should set and get items by key."""
        bd = BoundedDict(maxlen=5)
        bd["a"] = 1
        bd["b"] = 2

        assert bd["a"] == 1
        assert bd["b"] == 2

    def test_getitem_missing_raises(self):
        """Should raise KeyError for a missing key."""
        bd = BoundedDict(maxlen=5)

        with pytest.raises(KeyError):
            _ = bd["missing"]

    def test_delitem(self):
        """Should delete an existing key."""
        bd = BoundedDict(maxlen=5)
        bd["a"] = 1
        del bd["a"]

        assert "a" not in bd

    def test_delitem_missing_raises(self):
        """Should raise KeyError when deleting a missing key."""
        bd = BoundedDict(maxlen=5)

        with pytest.raises(KeyError):
            del bd["missing"]

    def test_contains(self):
        """Should report membership correctly."""
        bd = BoundedDict(maxlen=5)
        bd["a"] = 1

        assert "a" in bd
        assert "z" not in bd

    def test_len(self):
        """Should report the correct number of items."""
        bd = BoundedDict(maxlen=5)
        bd["a"] = 1
        bd["b"] = 2

        assert len(bd) == 2

    def test_iter(self):
        """Should iterate over keys in insertion order."""
        bd = BoundedDict(maxlen=5)
        bd["a"] = 1
        bd["b"] = 2
        bd["c"] = 3

        assert list(bd) == ["a", "b", "c"]

    def test_get_existing(self):
        """Should return value for existing key."""
        bd = BoundedDict(maxlen=5)
        bd["a"] = 1

        assert bd.get("a") == 1

    def test_get_missing_default(self):
        """Should return default for missing key."""
        bd = BoundedDict(maxlen=5)

        assert bd.get("missing") is None
        assert bd.get("missing", 42) == 42

    def test_pop_existing(self):
        """Should pop and return value for existing key."""
        bd = BoundedDict(maxlen=5)
        bd["a"] = 1

        result = bd.pop("a")

        assert result == 1
        assert "a" not in bd

    def test_pop_missing_with_default(self):
        """Should return default when popping a missing key."""
        bd = BoundedDict(maxlen=5)

        assert bd.pop("missing", 99) == 99

    def test_pop_missing_raises(self):
        """Should raise KeyError when popping a missing key without default."""
        bd = BoundedDict(maxlen=5)

        with pytest.raises(KeyError):
            bd.pop("missing")

    def test_keys(self):
        """Should return a view of keys."""
        bd = BoundedDict(maxlen=5)
        bd["a"] = 1
        bd["b"] = 2

        assert list(bd.keys()) == ["a", "b"]

    def test_values(self):
        """Should return a view of values."""
        bd = BoundedDict(maxlen=5)
        bd["a"] = 1
        bd["b"] = 2

        assert list(bd.values()) == [1, 2]

    def test_items(self):
        """Should return a view of key-value pairs."""
        bd = BoundedDict(maxlen=5)
        bd["a"] = 1
        bd["b"] = 2

        assert list(bd.items()) == [("a", 1), ("b", 2)]

    def test_clear(self):
        """Should remove all items."""
        bd = BoundedDict(maxlen=5)
        bd["a"] = 1
        bd["b"] = 2
        bd.clear()

        assert len(bd) == 0

    def test_repr(self):
        """Should return a descriptive repr string."""
        bd = BoundedDict(maxlen=3)
        bd["x"] = 10

        assert repr(bd) == "BoundedDict(maxlen=3, size=1)"

    def test_maxlen_property(self):
        """Should expose the configured maxlen."""
        bd = BoundedDict(maxlen=7)

        assert bd.maxlen == 7

    def test_maxlen_zero_raises(self):
        """Should raise ValueError when maxlen is 0."""
        with pytest.raises(ValueError, match="maxlen must be > 0"):
            BoundedDict(maxlen=0)

    def test_maxlen_negative_raises(self):
        """Should raise ValueError when maxlen is negative."""
        with pytest.raises(ValueError, match="maxlen must be > 0"):
            BoundedDict(maxlen=-1)

    def test_eviction_fifo(self):
        """Should evict the oldest entry when capacity is exceeded."""
        bd = BoundedDict(maxlen=3)
        bd["a"] = 1
        bd["b"] = 2
        bd["c"] = 3
        bd["d"] = 4  # should evict "a"

        assert "a" not in bd
        assert list(bd.keys()) == ["b", "c", "d"]

    def test_eviction_multiple(self):
        """Should evict oldest entries progressively."""
        bd = BoundedDict(maxlen=2)
        bd[1] = "x"
        bd[2] = "y"
        bd[3] = "z"  # evicts 1
        bd[4] = "w"  # evicts 2

        assert list(bd.items()) == [(3, "z"), (4, "w")]

    def test_update_existing_key_moves_to_end(self):
        """Updating an existing key should move it to the end."""
        bd = BoundedDict(maxlen=3)
        bd["a"] = 1
        bd["b"] = 2
        bd["c"] = 3

        bd["a"] = 99  # move "a" to end with new value
        bd["d"] = 4  # should evict "b" (now the oldest)

        assert "b" not in bd
        assert list(bd.keys()) == ["c", "a", "d"]
        assert bd["a"] == 99


# =============================================================================
# utcnow
# =============================================================================


class TestUtcnow:
    """Tests for utcnow()."""

    def test_returns_timezone_aware_utc(self):
        """Should return a datetime with UTC timezone."""
        result = utcnow()

        assert result.tzinfo is UTC

    def test_returns_close_to_current_time(self):
        """Should return a datetime within 1 second of now."""
        before = datetime.now(UTC)
        result = utcnow()
        after = datetime.now(UTC)

        assert before - timedelta(seconds=1) <= result <= after + timedelta(seconds=1)


# =============================================================================
# resolve_repository
# =============================================================================


class TestResolveRepository:
    """Tests for resolve_repository()."""

    @pytest.mark.asyncio
    async def test_step1_returns_from_github_projects_service(self):
        """Should return repo info from github_projects_service when available."""
        mock_service = AsyncMock()
        mock_service.get_project_repository.return_value = ("owner1", "repo1")

        with patch(
            "src.services.github_projects.github_projects_service",
            mock_service,
        ):
            result = await resolve_repository("token", "proj-id")

        assert result == ("owner1", "repo1")
        mock_service.get_project_repository.assert_awaited_once_with("token", "proj-id")

    @pytest.mark.asyncio
    async def test_step2_falls_back_to_workflow_config(self):
        """Should fall back to workflow config when step 1 returns None."""
        mock_service = AsyncMock()
        mock_service.get_project_repository.return_value = None

        mock_config = MagicMock()
        mock_config.repository_owner = "owner2"
        mock_config.repository_name = "repo2"

        with (
            patch(
                "src.services.github_projects.github_projects_service",
                mock_service,
            ),
            patch(
                "src.services.workflow_orchestrator.get_workflow_config",
                AsyncMock(return_value=mock_config),
            ),
        ):
            result = await resolve_repository("token", "proj-id")

        assert result == ("owner2", "repo2")

    @pytest.mark.asyncio
    async def test_step3_falls_back_to_settings(self):
        """Should fall back to settings when steps 1 and 2 return None."""
        mock_service = AsyncMock()
        mock_service.get_project_repository.return_value = None

        mock_settings = MagicMock()
        mock_settings.default_repo_owner = "owner3"
        mock_settings.default_repo_name = "repo3"

        with (
            patch(
                "src.services.github_projects.github_projects_service",
                mock_service,
            ),
            patch(
                "src.services.workflow_orchestrator.get_workflow_config",
                AsyncMock(return_value=None),
            ),
            patch(
                "src.config.get_settings",
                return_value=mock_settings,
            ),
        ):
            result = await resolve_repository("token", "proj-id")

        assert result == ("owner3", "repo3")

    @pytest.mark.asyncio
    async def test_raises_validation_error_when_all_steps_fail(self):
        """Should raise ValidationError when no repository is resolved."""
        from src.exceptions import ValidationError

        mock_service = AsyncMock()
        mock_service.get_project_repository.return_value = None

        mock_settings = MagicMock()
        mock_settings.default_repo_owner = None
        mock_settings.default_repo_name = None

        with (
            patch(
                "src.services.github_projects.github_projects_service",
                mock_service,
            ),
            patch(
                "src.services.workflow_orchestrator.get_workflow_config",
                AsyncMock(return_value=None),
            ),
            patch(
                "src.config.get_settings",
                return_value=mock_settings,
            ),
        ):
            with pytest.raises(ValidationError, match="No repository found"):
                await resolve_repository("token", "proj-id")
