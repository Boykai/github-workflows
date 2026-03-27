"""Unit tests for roadmap Pydantic models.

Covers:
- RoadmapItem validation (title length, priority/size enums)
- RoadmapBatch validation (min/max items, required fields)
- RoadmapCycleLog status enum and batch deserialization
- ProjectBoardConfig roadmap field defaults and validation
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.models.roadmap import RoadmapBatch, RoadmapCycleLog, RoadmapCycleStatus, RoadmapItem
from src.models.settings import ProjectBoardConfig


# ── RoadmapItem ──────────────────────────────────────────────────────


class TestRoadmapItem:
    def test_valid_item(self):
        item = RoadmapItem(
            title="Add user dashboard",
            body="## Dashboard\nAs a user...",
            rationale="Users need visibility into metrics",
            priority="P1",
            size="M",
        )
        assert item.title == "Add user dashboard"
        assert item.priority == "P1"
        assert item.size == "M"

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            RoadmapItem(
                title="",
                body="body",
                rationale="rationale",
                priority="P1",
                size="M",
            )

    def test_title_max_length(self):
        with pytest.raises(ValidationError):
            RoadmapItem(
                title="x" * 257,
                body="body",
                rationale="rationale",
                priority="P1",
                size="M",
            )

    def test_title_at_max_length(self):
        item = RoadmapItem(
            title="x" * 256,
            body="body",
            rationale="rationale",
            priority="P1",
            size="M",
        )
        assert len(item.title) == 256

    def test_invalid_priority_rejected(self):
        with pytest.raises(ValidationError):
            RoadmapItem(
                title="Feature",
                body="body",
                rationale="rationale",
                priority="P5",
                size="M",
            )

    def test_invalid_size_rejected(self):
        with pytest.raises(ValidationError):
            RoadmapItem(
                title="Feature",
                body="body",
                rationale="rationale",
                priority="P1",
                size="XXL",
            )

    def test_all_valid_priorities(self):
        for p in ["P0", "P1", "P2", "P3"]:
            item = RoadmapItem(
                title="Feature", body="body", rationale="r", priority=p, size="M"
            )
            assert item.priority == p

    def test_all_valid_sizes(self):
        for s in ["XS", "S", "M", "L", "XL"]:
            item = RoadmapItem(
                title="Feature", body="body", rationale="r", priority="P1", size=s
            )
            assert item.size == s


# ── RoadmapBatch ─────────────────────────────────────────────────────


def _make_item(**overrides) -> RoadmapItem:
    defaults = {
        "title": "Feature",
        "body": "body text",
        "rationale": "good reason",
        "priority": "P1",
        "size": "M",
    }
    defaults.update(overrides)
    return RoadmapItem(**defaults)


class TestRoadmapBatch:
    def test_valid_batch(self):
        batch = RoadmapBatch(
            items=[_make_item()],
            project_id="PVT_test",
            user_id="user_1",
        )
        assert len(batch.items) == 1
        assert batch.project_id == "PVT_test"
        assert isinstance(batch.generated_at, datetime)

    def test_empty_items_rejected(self):
        with pytest.raises(ValidationError):
            RoadmapBatch(
                items=[],
                project_id="PVT_test",
                user_id="user_1",
            )

    def test_max_10_items(self):
        batch = RoadmapBatch(
            items=[_make_item(title=f"Feature {i}") for i in range(10)],
            project_id="PVT_test",
            user_id="user_1",
        )
        assert len(batch.items) == 10

    def test_over_10_items_rejected(self):
        with pytest.raises(ValidationError):
            RoadmapBatch(
                items=[_make_item(title=f"Feature {i}") for i in range(11)],
                project_id="PVT_test",
                user_id="user_1",
            )

    def test_empty_project_id_rejected(self):
        with pytest.raises(ValidationError):
            RoadmapBatch(
                items=[_make_item()],
                project_id="",
                user_id="user_1",
            )

    def test_serialization_roundtrip(self):
        batch = RoadmapBatch(
            items=[_make_item(), _make_item(title="Second")],
            project_id="PVT_test",
            user_id="user_1",
        )
        json_str = batch.model_dump_json()
        restored = RoadmapBatch.model_validate_json(json_str)
        assert len(restored.items) == 2
        assert restored.project_id == "PVT_test"


# ── RoadmapCycleLog ─────────────────────────────────────────────────


class TestRoadmapCycleLog:
    def test_valid_cycle_log(self):
        batch = RoadmapBatch(
            items=[_make_item()],
            project_id="PVT_test",
            user_id="user_1",
        )
        log = RoadmapCycleLog(
            id=1,
            project_id="PVT_test",
            user_id="user_1",
            batch_json=batch.model_dump_json(),
            status=RoadmapCycleStatus.COMPLETED,
            created_at="2026-03-27T12:00:00Z",
        )
        assert log.status == RoadmapCycleStatus.COMPLETED
        assert log.batch.items[0].title == "Feature"

    def test_status_enum_values(self):
        assert RoadmapCycleStatus.PENDING == "pending"
        assert RoadmapCycleStatus.COMPLETED == "completed"
        assert RoadmapCycleStatus.FAILED == "failed"

    def test_batch_property_deserializes(self):
        batch = RoadmapBatch(
            items=[_make_item(title="Test Title")],
            project_id="PVT_proj",
            user_id="u1",
        )
        log = RoadmapCycleLog(
            id=42,
            project_id="PVT_proj",
            user_id="u1",
            batch_json=batch.model_dump_json(),
            status=RoadmapCycleStatus.PENDING,
            created_at="2026-03-27T12:00:00Z",
        )
        deserialized = log.batch
        assert deserialized.items[0].title == "Test Title"
        assert deserialized.project_id == "PVT_proj"


# ── ProjectBoardConfig roadmap defaults ──────────────────────────────


class TestProjectBoardConfigRoadmap:
    def test_default_values(self):
        config = ProjectBoardConfig()
        assert config.roadmap_enabled is False
        assert config.roadmap_seed == ""
        assert config.roadmap_batch_size == 3
        assert config.roadmap_pipeline_id is None
        assert config.roadmap_auto_launch is False
        assert config.roadmap_grace_minutes == 0

    def test_batch_size_range(self):
        config = ProjectBoardConfig(roadmap_batch_size=1)
        assert config.roadmap_batch_size == 1

        config = ProjectBoardConfig(roadmap_batch_size=10)
        assert config.roadmap_batch_size == 10

    def test_batch_size_below_range(self):
        with pytest.raises(ValidationError):
            ProjectBoardConfig(roadmap_batch_size=0)

    def test_batch_size_above_range(self):
        with pytest.raises(ValidationError):
            ProjectBoardConfig(roadmap_batch_size=11)

    def test_grace_minutes_range(self):
        config = ProjectBoardConfig(roadmap_grace_minutes=0)
        assert config.roadmap_grace_minutes == 0

        config = ProjectBoardConfig(roadmap_grace_minutes=1440)
        assert config.roadmap_grace_minutes == 1440

    def test_grace_minutes_above_range(self):
        with pytest.raises(ValidationError):
            ProjectBoardConfig(roadmap_grace_minutes=1441)

    def test_json_roundtrip(self):
        config = ProjectBoardConfig(
            roadmap_enabled=True,
            roadmap_seed="Build the best product",
            roadmap_batch_size=5,
            roadmap_pipeline_id="pipe_123",
            roadmap_auto_launch=True,
            roadmap_grace_minutes=15,
        )
        data = json.loads(config.model_dump_json())
        restored = ProjectBoardConfig(**data)
        assert restored.roadmap_enabled is True
        assert restored.roadmap_seed == "Build the best product"
        assert restored.roadmap_batch_size == 5
        assert restored.roadmap_pipeline_id == "pipe_123"
        assert restored.roadmap_auto_launch is True
        assert restored.roadmap_grace_minutes == 15

    def test_preserves_existing_fields(self):
        """Ensure adding roadmap fields doesn't break existing board config."""
        config = ProjectBoardConfig(
            column_order=["Backlog", "Done"],
            queue_mode=True,
            auto_merge=True,
            roadmap_enabled=True,
        )
        assert config.column_order == ["Backlog", "Done"]
        assert config.queue_mode is True
        assert config.auto_merge is True
        assert config.roadmap_enabled is True
