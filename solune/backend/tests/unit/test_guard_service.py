from __future__ import annotations

import os
from pathlib import Path

import yaml

from src.services import guard_service
from src.services.guard_service import _load_rules, _match_guard_level, check_guard, reset_cache


def _write_config(path: Path, rules: list[dict[str, str]]) -> None:
    path.write_text(yaml.safe_dump({"guard_rules": rules}), encoding="utf-8")


class TestLoadRules:
    def setup_method(self) -> None:
        reset_cache()

    def teardown_method(self) -> None:
        reset_cache()

    def test_missing_config_fails_closed_with_empty_rules(self, tmp_path: Path) -> None:
        config_path = tmp_path / "missing.yml"

        assert _load_rules(config_path) == []

    def test_reuses_cached_rules_when_file_is_unchanged(self, tmp_path: Path, monkeypatch) -> None:
        config_path = tmp_path / "guard.yml"
        rules = [{"path_pattern": "solune/**", "guard_level": "admin"}]
        _write_config(config_path, rules)

        load_count = 0
        original_safe_load = guard_service.yaml.safe_load

        def counting_safe_load(stream):
            nonlocal load_count
            load_count += 1
            return original_safe_load(stream)

        monkeypatch.setattr(guard_service.yaml, "safe_load", counting_safe_load)

        first = _load_rules(config_path)
        second = _load_rules(config_path)

        assert first == rules
        assert second == rules
        assert load_count == 1

    def test_reload_picks_up_updated_rules_after_mtime_changes(self, tmp_path: Path) -> None:
        config_path = tmp_path / "guard.yml"
        _write_config(config_path, [{"path_pattern": "solune/**", "guard_level": "admin"}])

        first = _load_rules(config_path)

        stat = config_path.stat()
        _write_config(config_path, [{"path_pattern": "apps/**", "guard_level": "none"}])
        os.utime(config_path, (stat.st_atime, stat.st_mtime + 1))

        second = _load_rules(config_path)

        assert first == [{"path_pattern": "solune/**", "guard_level": "admin"}]
        assert second == [{"path_pattern": "apps/**", "guard_level": "none"}]


class TestMatchGuardLevel:
    def test_defaults_to_admin_when_no_rules_match(self) -> None:
        assert _match_guard_level("unmatched/file.py", []) == "admin"

    def test_uses_most_specific_matching_pattern(self) -> None:
        rules = [
            {"path_pattern": "solune/**", "guard_level": "admin"},
            {"path_pattern": "solune/docs/**", "guard_level": "none"},
            {"path_pattern": "solune/docs/OWNERS.md", "guard_level": "adminlock"},
        ]

        assert _match_guard_level("solune/backend/src/main.py", rules) == "admin"
        assert _match_guard_level("solune/docs/setup.md", rules) == "none"
        assert _match_guard_level("solune/docs/OWNERS.md", rules) == "adminlock"


class TestCheckGuard:
    def setup_method(self) -> None:
        reset_cache()

    def teardown_method(self) -> None:
        reset_cache()

    def test_categorizes_allowed_admin_and_locked_paths(self, tmp_path: Path) -> None:
        config_path = tmp_path / "guard.yml"
        _write_config(
            config_path,
            [
                {"path_pattern": "apps/**", "guard_level": "none"},
                {"path_pattern": ".github/**", "guard_level": "adminlock"},
                {"path_pattern": "solune/**", "guard_level": "admin"},
            ],
        )

        result = check_guard(
            ["apps/test-app/README.md", ".github/workflows/ci.yml", "solune/backend/src/main.py"],
            config_path=config_path,
        )

        assert result.allowed == ["apps/test-app/README.md"]
        assert result.locked == [".github/workflows/ci.yml"]
        assert result.admin_blocked == ["solune/backend/src/main.py"]

    def test_elevation_bypasses_admin_but_not_adminlock(self, tmp_path: Path) -> None:
        config_path = tmp_path / "guard.yml"
        _write_config(
            config_path,
            [
                {"path_pattern": ".github/**", "guard_level": "adminlock"},
                {"path_pattern": "solune/**", "guard_level": "admin"},
            ],
        )

        result = check_guard(
            [".github/workflows/ci.yml", "solune/backend/src/main.py"],
            elevated=True,
            config_path=config_path,
        )

        assert result.allowed == ["solune/backend/src/main.py"]
        assert result.locked == [".github/workflows/ci.yml"]
        assert result.admin_blocked == []

    def test_unknown_guard_levels_are_treated_as_allowed(self, tmp_path: Path) -> None:
        config_path = tmp_path / "guard.yml"
        _write_config(config_path, [{"path_pattern": "custom/**", "guard_level": "weird"}])

        result = check_guard(["custom/file.txt"], config_path=config_path)

        assert result.allowed == ["custom/file.txt"]
        assert result.admin_blocked == []
        assert result.locked == []
