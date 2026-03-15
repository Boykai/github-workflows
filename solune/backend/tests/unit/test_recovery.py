"""Tests for recovery helpers — AgentStepState enum (T100)."""

from src.models.agent import AgentStepState


class TestAgentStepState:
    """AgentStepState.from_markdown maps emoji prefixes to typed enum values."""

    def test_done(self):
        assert AgentStepState.from_markdown("✅ Done") == AgentStepState.DONE

    def test_active(self):
        assert AgentStepState.from_markdown("🔄 Active") == AgentStepState.ACTIVE

    def test_queued(self):
        assert AgentStepState.from_markdown("⏳ Queued") == AgentStepState.QUEUED

    def test_error(self):
        assert AgentStepState.from_markdown("❌ Error") == AgentStepState.ERROR

    def test_skipped(self):
        assert AgentStepState.from_markdown("⏭ Skipped") == AgentStepState.SKIPPED

    def test_unknown_fallback(self):
        assert AgentStepState.from_markdown("something else") == AgentStepState.UNKNOWN

    def test_empty_string(self):
        assert AgentStepState.from_markdown("") == AgentStepState.UNKNOWN

    def test_whitespace_stripped(self):
        assert AgentStepState.from_markdown("  ✅ Done  ") == AgentStepState.DONE

    def test_enum_values(self):
        assert AgentStepState.DONE == "done"
        assert AgentStepState.ACTIVE == "active"
        assert AgentStepState.QUEUED == "queued"
        assert AgentStepState.ERROR == "error"
        assert AgentStepState.SKIPPED == "skipped"
        assert AgentStepState.UNKNOWN == "unknown"
