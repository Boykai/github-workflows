"""Regression tests for PipelineService — json.loads robustness."""

from src.services.pipelines.service import PipelineService


class TestRowToConfig:
    """Verify _row_to_config handles malformed JSON gracefully."""

    def test_malformed_stages_json_does_not_crash(self):
        """_row_to_config should return empty stages for invalid JSON, not crash."""
        row = {
            "id": "pipe-1",
            "project_id": "proj-1",
            "name": "Test Pipeline",
            "description": "",
            "stages": "{not valid json",
            "is_preset": 0,
            "preset_id": "",
            "blocking": 0,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        config = PipelineService._row_to_config(row)
        assert config.stages == []
        assert config.name == "Test Pipeline"

    def test_valid_stages_json_parses_correctly(self):
        """_row_to_config should parse valid stages JSON into PipelineStage objects."""
        row = {
            "id": "pipe-1",
            "project_id": "proj-1",
            "name": "Test Pipeline",
            "description": "",
            "stages": '[{"id": "s1", "name": "Review", "order": 0, "agents": []}]',
            "is_preset": 0,
            "preset_id": "",
            "blocking": 0,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        config = PipelineService._row_to_config(row)
        assert len(config.stages) == 1
        assert config.stages[0].name == "Review"

    def test_missing_stages_key_defaults_to_empty(self):
        """_row_to_config should default to empty stages when key is missing."""
        row = {
            "id": "pipe-1",
            "project_id": "proj-1",
            "name": "Test Pipeline",
            "description": "",
            "is_preset": 0,
            "preset_id": "",
            "blocking": 0,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        config = PipelineService._row_to_config(row)
        assert config.stages == []
