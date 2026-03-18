"""Tests for the label manager — pipeline state label parsing and building."""

from src.services.copilot_polling.label_manager import (
    build_label_name,
    parse_label,
)


class TestBuildLabelName:
    def test_builds_standard_label(self):
        result = build_label_name(42, "build", "running")
        assert result == "solune:pipeline:42:stage:build:running"

    def test_builds_label_with_different_status(self):
        result = build_label_name(1, "deploy", "completed")
        assert result == "solune:pipeline:1:stage:deploy:completed"


class TestParseLabel:
    def test_parses_valid_label(self):
        result = parse_label("solune:pipeline:42:stage:build:running")
        assert result is not None
        assert result.run_id == 42
        assert result.stage_id == "build"
        assert result.status == "running"
        assert result.full_name == "solune:pipeline:42:stage:build:running"

    def test_parses_completed_label(self):
        result = parse_label("solune:pipeline:100:stage:test:completed")
        assert result is not None
        assert result.run_id == 100
        assert result.stage_id == "test"
        assert result.status == "completed"

    def test_returns_none_for_non_pipeline_label(self):
        result = parse_label("bug")
        assert result is None

    def test_returns_none_for_malformed_label(self):
        result = parse_label("solune:pipeline:invalid:stage:build:running")
        assert result is None

    def test_returns_none_for_empty_string(self):
        result = parse_label("")
        assert result is None

    def test_roundtrip(self):
        """Build a label and parse it back."""
        name = build_label_name(7, "lint", "failed")
        parsed = parse_label(name)
        assert parsed is not None
        assert parsed.run_id == 7
        assert parsed.stage_id == "lint"
        assert parsed.status == "failed"
