"""Unit tests for admin guard rule loading and evaluation."""

from __future__ import annotations

import pytest

from src.services import guard_service


@pytest.fixture(autouse=True)
def reset_guard_cache():
    """Keep guard rule cache isolated across tests."""
    guard_service.reset_cache()
    yield
    guard_service.reset_cache()


class TestLoadRules:
    def test_missing_guard_rules_defaults_to_empty_list(self, tmp_path):
        config_path = tmp_path / "guard-config.yml"
        config_path.write_text("version: 1\n", encoding="utf-8")

        assert guard_service._load_rules(config_path) == []

    def test_invalid_guard_rules_shape_defaults_to_empty_list(self, tmp_path):
        config_path = tmp_path / "guard-config.yml"
        config_path.write_text("guard_rules: invalid\n", encoding="utf-8")

        assert guard_service._load_rules(config_path) == []


class TestCheckGuard:
    def test_more_specific_pattern_wins(self, tmp_path):
        config_path = tmp_path / "guard-config.yml"
        config_path.write_text(
            "\n".join(
                [
                    "guard_rules:",
                    "  - path_pattern: apps/**",
                    "    guard_level: none",
                    "  - path_pattern: apps/secret/**",
                    "    guard_level: adminlock",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = guard_service.check_guard(
            ["apps/public/readme.md", "apps/secret/config.yml"],
            config_path=config_path,
        )

        assert result.allowed == ["apps/public/readme.md"]
        assert result.locked == ["apps/secret/config.yml"]
        assert result.admin_blocked == []

    def test_elevated_requests_still_block_adminlock(self, tmp_path):
        config_path = tmp_path / "guard-config.yml"
        config_path.write_text(
            "\n".join(
                [
                    "guard_rules:",
                    "  - path_pattern: solune/**",
                    "    guard_level: admin",
                    "  - path_pattern: solune/backend/src/services/**",
                    "    guard_level: adminlock",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = guard_service.check_guard(
            ["solune/frontend/src/App.tsx", "solune/backend/src/services/guard_service.py"],
            elevated=True,
            config_path=config_path,
        )

        assert result.allowed == ["solune/frontend/src/App.tsx"]
        assert result.locked == ["solune/backend/src/services/guard_service.py"]
