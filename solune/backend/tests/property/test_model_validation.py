"""Property tests: Pydantic model validation edge cases.

Verifies models handle unicode, empty strings, and extreme lengths correctly.
"""

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st
from pydantic import ValidationError

from src.models.agents import AgentCreate, AgentUpdate
from src.models.pipeline import (
    PipelineConfigCreate,
)
from src.models.tools import McpToolConfigCreate

# --- Strategies for edge-case inputs ---

unicode_text = st.text(
    alphabet=st.characters(categories=("L", "M", "N", "P", "S", "Z")),
    min_size=1,
    max_size=100,
)
empty_string = st.just("")
extreme_length = st.text(min_size=200, max_size=500)


class TestAgentCreateValidation:
    """Edge-case validation for AgentCreate."""

    @given(name=unicode_text)
    def test_unicode_names_accepted(self, name: str) -> None:
        """Unicode names should be accepted if within length bounds."""
        assume(1 <= len(name) <= 100)
        agent = AgentCreate(
            name=name,
            description="test",
            system_prompt="test prompt",
            tools=[],
            status_column="Backlog",
            default_model_id="gpt-4o",
            default_model_name="GPT-4o",
            raw=False,
        )
        assert agent.name == name

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AgentCreate(
                name="",
                description="test",
                system_prompt="test prompt",
                tools=[],
                status_column="Backlog",
                default_model_id="gpt-4o",
                default_model_name="GPT-4o",
                raw=False,
            )

    def test_empty_system_prompt_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AgentCreate(
                name="test",
                description="test",
                system_prompt="",
                tools=[],
                status_column="Backlog",
                default_model_id="gpt-4o",
                default_model_name="GPT-4o",
                raw=False,
            )

    @given(name=st.text(min_size=101, max_size=200))
    def test_name_exceeding_max_length_rejected(self, name: str) -> None:
        with pytest.raises(ValidationError):
            AgentCreate(
                name=name,
                description="test",
                system_prompt="test prompt",
                tools=[],
                status_column="Backlog",
                default_model_id="gpt-4o",
                default_model_name="GPT-4o",
                raw=False,
            )


class TestAgentUpdateValidation:
    """Edge-case validation for AgentUpdate (all-optional fields)."""

    @given(
        name=st.one_of(st.none(), unicode_text),
        description=st.one_of(st.none(), unicode_text),
    )
    def test_partial_updates_always_valid(self, name: str | None, description: str | None) -> None:
        """Partial updates with None or valid text should never raise."""
        update = AgentUpdate(name=name, description=description)
        assert update.name == name
        assert update.description == description


class TestMcpToolConfigCreateValidation:
    """Edge-case validation for McpToolConfigCreate."""

    def test_config_content_too_short_rejected(self) -> None:
        with pytest.raises(ValidationError):
            McpToolConfigCreate(
                name="test",
                description="test",
                config_content="x",  # min_length is 2
                github_repo_target="owner/repo",
            )

    @given(
        name=st.text(min_size=1, max_size=100, alphabet=st.characters(categories=("L", "N", "Z"))),
        config=st.text(min_size=2, max_size=100),
    )
    def test_valid_configs_accepted(self, name: str, config: str) -> None:
        tool = McpToolConfigCreate(
            name=name,
            description="test",
            config_content=config,
            github_repo_target="owner/repo",
        )
        assert tool.name == name
        assert tool.config_content == config


class TestPipelineConfigCreateValidation:
    """Edge-case validation for PipelineConfigCreate."""

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PipelineConfigCreate(name="", description="test", stages=[])

    @given(name=st.text(min_size=101, max_size=200))
    def test_name_exceeding_max_length_rejected(self, name: str) -> None:
        with pytest.raises(ValidationError):
            PipelineConfigCreate(name=name, description="test", stages=[])

    @given(
        name=st.text(min_size=1, max_size=100, alphabet=st.characters(categories=("L", "N", "Z")))
    )
    def test_valid_name_with_empty_stages_accepted(self, name: str) -> None:
        config = PipelineConfigCreate(name=name, description="test", stages=[])
        assert config.name == name
        assert config.stages == []
