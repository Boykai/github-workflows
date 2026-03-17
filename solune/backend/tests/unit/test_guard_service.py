"""Unit tests for guard_service — file-path protection rules."""

import os
from pathlib import Path

import pytest
import yaml

from src.services.guard_service import (
    GuardResult,
    _load_rules,
    _match_guard_level,
    check_guard,
    reset_cache,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    """Reset cached rules before and after each test."""
    reset_cache()
    yield
    reset_cache()


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    """Write a sample guard-config.yml and return its path."""
    rules = {
        "guard_rules": [
            {"path_pattern": "solune/backend/*", "guard_level": "admin"},
            {"path_pattern": "solune/backend/src/services/*", "guard_level": "none"},
            {"path_pattern": "solune/backend/src/core/*", "guard_level": "adminlock"},
            {"path_pattern": "apps/*", "guard_level": "none"},
        ]
    }
    p = tmp_path / "guard-config.yml"
    p.write_text(yaml.dump(rules), encoding="utf-8")
    return p


# ── _load_rules ─────────────────────────────────────────────────────────────


class TestLoadRules:
    def test_loads_rules_from_config(self, config_file: Path):
        rules = _load_rules(config_file)
        assert len(rules) == 4

    def test_missing_config_returns_empty(self, tmp_path: Path):
        rules = _load_rules(tmp_path / "nonexistent.yml")
        assert rules == []

    def test_caching_returns_same_list(self, config_file: Path):
        r1 = _load_rules(config_file)
        r2 = _load_rules(config_file)
        assert r1 is r2  # same object ⇒ cached

    def test_cache_invalidated_by_mtime_change(self, config_file: Path):
        r1 = _load_rules(config_file)
        # Rewrite with extra rule and bump mtime to guarantee cache miss
        data = yaml.safe_load(config_file.read_text(encoding="utf-8"))
        data["guard_rules"].append({"path_pattern": "docs/*", "guard_level": "none"})
        config_file.write_text(yaml.dump(data), encoding="utf-8")
        st = config_file.stat()
        os.utime(config_file, (st.st_atime, st.st_mtime + 1))
        r2 = _load_rules(config_file)
        assert len(r2) == 5
        assert r1 is not r2


# ── _match_guard_level ──────────────────────────────────────────────────────


class TestMatchGuardLevel:
    def test_unmatched_defaults_to_admin(self):
        assert _match_guard_level("random/file.py", []) == "admin"

    def test_matched_returns_level(self):
        rules = [{"path_pattern": "apps/*", "guard_level": "none"}]
        assert _match_guard_level("apps/web/index.html", rules) == "none"

    def test_longest_pattern_wins(self):
        rules = [
            {"path_pattern": "solune/backend/*", "guard_level": "admin"},
            {"path_pattern": "solune/backend/src/services/*", "guard_level": "none"},
        ]
        # The more specific pattern should win
        assert _match_guard_level("solune/backend/src/services/foo.py", rules) == "none"

    def test_shorter_pattern_used_when_specific_not_matched(self):
        rules = [
            {"path_pattern": "solune/backend/*", "guard_level": "admin"},
            {"path_pattern": "solune/backend/src/services/*", "guard_level": "none"},
        ]
        assert _match_guard_level("solune/backend/other.py", rules) == "admin"


# ── check_guard (non-elevated) ──────────────────────────────────────────────


class TestCheckGuardNonElevated:
    def test_allowed_paths(self, config_file: Path):
        result = check_guard(["apps/web/page.tsx"], config_path=config_file)
        assert isinstance(result, GuardResult)
        assert result.allowed == ["apps/web/page.tsx"]
        assert result.admin_blocked == []
        assert result.locked == []

    def test_admin_blocked_paths(self, config_file: Path):
        result = check_guard(["solune/backend/setup.py"], config_path=config_file)
        assert result.admin_blocked == ["solune/backend/setup.py"]
        assert result.allowed == []

    def test_adminlock_paths(self, config_file: Path):
        result = check_guard(["solune/backend/src/core/secret.py"], config_path=config_file)
        assert result.locked == ["solune/backend/src/core/secret.py"]

    def test_mixed_paths(self, config_file: Path):
        paths = [
            "apps/web/page.tsx",
            "solune/backend/setup.py",
            "solune/backend/src/core/secret.py",
            "solune/backend/src/services/svc.py",
        ]
        result = check_guard(paths, config_path=config_file)
        assert "apps/web/page.tsx" in result.allowed
        assert "solune/backend/src/services/svc.py" in result.allowed
        assert "solune/backend/setup.py" in result.admin_blocked
        assert "solune/backend/src/core/secret.py" in result.locked


# ── check_guard (elevated) ──────────────────────────────────────────────────


class TestCheckGuardElevated:
    def test_elevated_bypasses_admin(self, config_file: Path):
        result = check_guard(["solune/backend/setup.py"], elevated=True, config_path=config_file)
        assert result.allowed == ["solune/backend/setup.py"]
        assert result.admin_blocked == []

    def test_elevated_does_not_bypass_adminlock(self, config_file: Path):
        result = check_guard(
            ["solune/backend/src/core/secret.py"],
            elevated=True,
            config_path=config_file,
        )
        assert result.locked == ["solune/backend/src/core/secret.py"]
        assert result.allowed == []


# ── Missing config → fail-closed ────────────────────────────────────────────


class TestMissingConfig:
    def test_no_config_file_fails_closed(self, tmp_path: Path):
        """When config is missing, _load_rules returns [] so every path
        defaults to 'admin' (fail-closed) via _match_guard_level."""
        result = check_guard(
            ["apps/anything.ts"],
            config_path=tmp_path / "missing.yml",
        )
        assert result.admin_blocked == ["apps/anything.ts"]
        assert result.allowed == []

    def test_no_config_elevated_allows(self, tmp_path: Path):
        """Even with missing config, elevated still bypasses admin."""
        result = check_guard(
            ["apps/anything.ts"],
            elevated=True,
            config_path=tmp_path / "missing.yml",
        )
        assert result.allowed == ["apps/anything.ts"]


# ── reset_cache ─────────────────────────────────────────────────────────────


class TestResetCache:
    def test_reset_clears_mtime_tracking(self, config_file: Path):
        """After reset_cache, a subsequent _load_rules must re-read the file."""
        r1 = _load_rules(config_file)
        reset_cache()
        r2 = _load_rules(config_file)
        # After reset, a fresh list is built (different object identity)
        assert r1 is not r2
        # But same content
        assert r1 == r2
