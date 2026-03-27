"""Unit tests for roadmap generator — AI response parsing and prompt building.

Covers:
- _parse_ai_response() with valid JSON, malformed JSON, empty arrays
- create_roadmap_generation_prompt() message structure
- Markdown fence stripping
"""

from __future__ import annotations

import json

import pytest

from src.models.roadmap import RoadmapItem
from src.prompts.roadmap_generation import create_roadmap_generation_prompt
from src.services.roadmap.generator import _parse_ai_response


# ── AI Response Parsing ──────────────────────────────────────────────


class TestParseAiResponse:
    def test_valid_json_array(self):
        response = json.dumps([
            {
                "title": "Feature A",
                "body": "## Feature A\nDetails...",
                "rationale": "Users need this",
                "priority": "P1",
                "size": "M",
            },
            {
                "title": "Feature B",
                "body": "## Feature B\nDetails...",
                "rationale": "Critical for growth",
                "priority": "P2",
                "size": "L",
            },
        ])
        items = _parse_ai_response(response)
        assert len(items) == 2
        assert items[0].title == "Feature A"
        assert items[1].priority == "P2"

    def test_single_item(self):
        response = json.dumps([{
            "title": "Solo Feature",
            "body": "body",
            "rationale": "reason",
            "priority": "P0",
            "size": "XS",
        }])
        items = _parse_ai_response(response)
        assert len(items) == 1
        assert items[0].size == "XS"

    def test_malformed_json_raises(self):
        with pytest.raises(ValueError, match="not valid JSON"):
            _parse_ai_response("this is not json")

    def test_non_array_json_raises(self):
        with pytest.raises(ValueError, match="must be a JSON array"):
            _parse_ai_response('{"title": "not an array"}')

    def test_empty_array_raises(self):
        with pytest.raises(ValueError, match="no valid items"):
            _parse_ai_response("[]")

    def test_missing_required_field_raises(self):
        response = json.dumps([{
            "title": "Feature",
            "body": "body",
            # missing rationale, priority, size
        }])
        with pytest.raises(Exception):
            _parse_ai_response(response)

    def test_strips_markdown_fences(self):
        inner = json.dumps([{
            "title": "Fenced Feature",
            "body": "body",
            "rationale": "reason",
            "priority": "P1",
            "size": "S",
        }])
        response = f"```json\n{inner}\n```"
        items = _parse_ai_response(response)
        assert len(items) == 1
        assert items[0].title == "Fenced Feature"

    def test_strips_plain_fences(self):
        inner = json.dumps([{
            "title": "Plain Fenced",
            "body": "body",
            "rationale": "reason",
            "priority": "P3",
            "size": "XL",
        }])
        response = f"```\n{inner}\n```"
        items = _parse_ai_response(response)
        assert len(items) == 1
        assert items[0].priority == "P3"

    def test_whitespace_around_json(self):
        inner = json.dumps([{
            "title": "Spaced",
            "body": "body",
            "rationale": "reason",
            "priority": "P2",
            "size": "M",
        }])
        response = f"\n  {inner}  \n"
        items = _parse_ai_response(response)
        assert len(items) == 1


# ── Prompt Building ──────────────────────────────────────────────────


class TestCreateRoadmapGenerationPrompt:
    def test_basic_prompt_structure(self):
        messages = create_roadmap_generation_prompt(
            seed="Build a great product",
            batch_size=3,
            codebase_context="Python backend with FastAPI",
            recent_titles=[],
        )
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "product engineering lead" in messages[0]["content"]
        assert "Build a great product" in messages[1]["content"]
        assert "exactly 3" in messages[1]["content"]

    def test_includes_dedup_titles(self):
        messages = create_roadmap_generation_prompt(
            seed="Vision",
            batch_size=2,
            codebase_context="context",
            recent_titles=["Feature A", "Feature B"],
        )
        user_msg = messages[1]["content"]
        assert "Feature A" in user_msg
        assert "Feature B" in user_msg
        assert "DO NOT duplicate" in user_msg

    def test_no_dedup_section_when_empty(self):
        messages = create_roadmap_generation_prompt(
            seed="Vision",
            batch_size=1,
            codebase_context="context",
            recent_titles=[],
        )
        user_msg = messages[1]["content"]
        assert "DO NOT duplicate" not in user_msg

    def test_codebase_context_included(self):
        messages = create_roadmap_generation_prompt(
            seed="Vision",
            batch_size=1,
            codebase_context="React frontend with TypeScript",
            recent_titles=[],
        )
        user_msg = messages[1]["content"]
        assert "React frontend with TypeScript" in user_msg
