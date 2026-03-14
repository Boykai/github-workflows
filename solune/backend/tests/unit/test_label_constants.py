"""Unit tests for pipeline label constants, parsing, building, and query utilities."""

import pytest

from src.constants import (
    ACTIVE_LABEL,
    ACTIVE_LABEL_COLOR,
    AGENT_LABEL_COLOR,
    AGENT_LABEL_PREFIX,
    PIPELINE_LABEL_COLOR,
    PIPELINE_LABEL_PREFIX,
    STALLED_LABEL,
    STALLED_LABEL_COLOR,
    build_agent_label,
    build_pipeline_label,
    extract_agent_slug,
    extract_pipeline_config,
    find_agent_label,
    find_pipeline_label,
    has_stalled_label,
)

# ── Constants ────────────────────────────────────────────────────────────────


class TestConstants:
    def test_pipeline_label_prefix(self):
        assert PIPELINE_LABEL_PREFIX == "pipeline:"

    def test_agent_label_prefix(self):
        assert AGENT_LABEL_PREFIX == "agent:"

    def test_active_label(self):
        assert ACTIVE_LABEL == "active"

    def test_stalled_label(self):
        assert STALLED_LABEL == "stalled"

    def test_color_constants_are_hex_without_hash(self):
        for color in (
            PIPELINE_LABEL_COLOR,
            AGENT_LABEL_COLOR,
            ACTIVE_LABEL_COLOR,
            STALLED_LABEL_COLOR,
        ):
            assert "#" not in color
            assert len(color) == 6
            int(color, 16)  # must be valid hex


# ── extract_pipeline_config / extract_agent_slug ─────────────────────────────


class TestExtractPipelineConfig:
    def test_valid_label(self):
        assert extract_pipeline_config("pipeline:speckit-full") == "speckit-full"

    def test_non_matching_label(self):
        assert extract_pipeline_config("agent:speckit.plan") is None

    def test_empty_string(self):
        assert extract_pipeline_config("") is None

    def test_prefix_only(self):
        assert extract_pipeline_config("pipeline:") == ""


class TestExtractAgentSlug:
    def test_valid_label(self):
        assert extract_agent_slug("agent:speckit.plan") == "speckit.plan"

    def test_non_matching_label(self):
        assert extract_agent_slug("pipeline:x") is None

    def test_empty_string(self):
        assert extract_agent_slug("") is None

    def test_prefix_only(self):
        assert extract_agent_slug("agent:") == ""


# ── Round-trip invariants ────────────────────────────────────────────────────


class TestRoundTrip:
    @pytest.mark.parametrize("config_name", ["speckit-full", "custom-pipeline", "x"])
    def test_pipeline_round_trip(self, config_name):
        assert extract_pipeline_config(build_pipeline_label(config_name)) == config_name

    @pytest.mark.parametrize("slug", ["speckit.plan", "copilot-review", "human"])
    def test_agent_round_trip(self, slug):
        assert extract_agent_slug(build_agent_label(slug)) == slug


# ── build_pipeline_label / build_agent_label ─────────────────────────────────


class TestBuildPipelineLabel:
    def test_builds_correct_label(self):
        assert build_pipeline_label("speckit-full") == "pipeline:speckit-full"


class TestBuildAgentLabel:
    def test_builds_correct_label(self):
        assert build_agent_label("speckit.plan") == "agent:speckit.plan"


# ── find_pipeline_label / find_agent_label / has_stalled_label ───────────────


class TestFindPipelineLabel:
    def test_from_dict_list(self):
        labels = [
            {"name": "ai-generated", "color": "000"},
            {"name": "pipeline:speckit-full", "color": "0052cc"},
        ]
        assert find_pipeline_label(labels) == "speckit-full"

    def test_from_object_list(self):
        class FakeLabel:
            def __init__(self, name):
                self.name = name

        labels = [FakeLabel("bug"), FakeLabel("pipeline:custom")]
        assert find_pipeline_label(labels) == "custom"

    def test_returns_none_when_absent(self):
        labels = [{"name": "bug"}, {"name": "agent:x"}]
        assert find_pipeline_label(labels) is None

    def test_empty_list(self):
        assert find_pipeline_label([]) is None


class TestFindAgentLabel:
    def test_from_dict_list(self):
        labels = [{"name": "agent:speckit.plan", "color": "7057ff"}]
        assert find_agent_label(labels) == "speckit.plan"

    def test_returns_first_match(self):
        labels = [
            {"name": "agent:first"},
            {"name": "agent:second"},
        ]
        assert find_agent_label(labels) == "first"

    def test_returns_none_when_absent(self):
        assert find_agent_label([{"name": "pipeline:x"}]) is None

    def test_empty_list(self):
        assert find_agent_label([]) is None


class TestHasStalledLabel:
    def test_true_when_present(self):
        labels = [{"name": "stalled"}, {"name": "bug"}]
        assert has_stalled_label(labels) is True

    def test_false_when_absent(self):
        labels = [{"name": "bug"}, {"name": "agent:x"}]
        assert has_stalled_label(labels) is False

    def test_empty_list(self):
        assert has_stalled_label([]) is False

    def test_with_object_labels(self):
        class FakeLabel:
            def __init__(self, name):
                self.name = name

        assert has_stalled_label([FakeLabel("stalled")]) is True
        assert has_stalled_label([FakeLabel("bug")]) is False
