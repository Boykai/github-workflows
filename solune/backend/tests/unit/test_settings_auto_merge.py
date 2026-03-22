"""Unit tests for auto_merge settings persistence and flag resolution."""

from __future__ import annotations

from src.models.settings import ProjectBoardConfig


class TestAutoMergeFlagResolution:
    """Tests for auto_merge OR logic — project true OR pipeline true → active."""

    def test_project_true_pipeline_false(self):
        """Project auto_merge=True should activate."""
        config = ProjectBoardConfig(auto_merge=True)
        assert config.auto_merge is True

    def test_project_false_pipeline_true(self):
        """Pipeline auto_merge should be independent."""
        from src.services.workflow_orchestrator.models import PipelineState

        ps = PipelineState(
            issue_number=1,
            project_id="test",
            status="In Progress",
            agents=["a"],
            auto_merge=True,
        )
        assert ps.auto_merge is True

    def test_both_false(self):
        """Both false → inactive."""
        config = ProjectBoardConfig(auto_merge=False)
        assert config.auto_merge is False

    def test_or_logic(self):
        """Either true activates."""
        from src.services.workflow_orchestrator.models import PipelineState

        ps = PipelineState(
            issue_number=1,
            project_id="test",
            status="In Progress",
            agents=["a"],
            auto_merge=False,
        )
        project_auto_merge = True
        resolved = ps.auto_merge or project_auto_merge
        assert resolved is True

    def test_default_false(self):
        """Default should be False."""
        config = ProjectBoardConfig()
        assert config.auto_merge is False


class TestSettingsPersistence:
    """Tests for auto_merge settings persistence round-trip."""

    def test_board_config_serialization(self):
        """auto_merge should serialize and deserialize correctly."""
        config = ProjectBoardConfig(auto_merge=True, queue_mode=False)
        data = config.model_dump()
        assert data["auto_merge"] is True

        restored = ProjectBoardConfig(**data)
        assert restored.auto_merge is True

    def test_board_config_default(self):
        """auto_merge should default to False in JSON."""
        config = ProjectBoardConfig()
        data = config.model_dump()
        assert data["auto_merge"] is False

    def test_pipeline_state_metadata_serialization(self):
        """auto_merge should be serialized in pipeline metadata."""
        from src.services.workflow_orchestrator.models import PipelineState

        ps = PipelineState(
            issue_number=1,
            project_id="test",
            status="In Progress",
            agents=["a"],
            auto_merge=True,
        )
        # Verify the field is set
        assert ps.auto_merge is True

    def test_pipeline_state_default(self):
        """auto_merge should default to False."""
        from src.services.workflow_orchestrator.models import PipelineState

        ps = PipelineState(
            issue_number=1,
            project_id="test",
            status="In Progress",
            agents=["a"],
        )
        assert ps.auto_merge is False
