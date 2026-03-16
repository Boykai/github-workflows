"""Property tests: Pydantic model serialization round-trips.

Verifies that model_dump → model_validate is identity for key API models.
"""

from uuid import uuid4

from hypothesis import given
from hypothesis import strategies as st

from src.models.agent import AgentAssignment, AgentSource, AvailableAgent
from src.models.agents import Agent, AgentCreate, AgentStatus
from src.models.agents import AgentSource as AgentsAgentSource
from src.models.pipeline import (
    ExecutionGroup,
    PipelineAgentNode,
    PipelineConfig,
    PipelineStage,
)
from src.models.tools import McpToolConfigCreate

# --- Strategies ---

slug_st = st.from_regex(r"[a-z][a-z0-9\-]{0,29}", fullmatch=True)
short_text = st.text(min_size=1, max_size=50, alphabet=st.characters(categories=("L", "N", "Z")))
optional_text = st.one_of(st.none(), short_text)
model_id_st = st.text(min_size=1, max_size=100, alphabet=st.characters(categories=("L", "N")))


@given(slug=slug_st, display_name=optional_text)
def test_agent_assignment_roundtrip(slug: str, display_name: str | None) -> None:
    original = AgentAssignment(slug=slug, display_name=display_name)
    dumped = original.model_dump(mode="json")
    restored = AgentAssignment.model_validate(dumped)
    assert restored.slug == original.slug
    assert restored.display_name == original.display_name


@given(
    slug=slug_st,
    display_name=short_text,
    source=st.sampled_from(list(AgentSource)),
)
def test_available_agent_roundtrip(slug: str, display_name: str, source: AgentSource) -> None:
    original = AvailableAgent(slug=slug, display_name=display_name, source=source)
    dumped = original.model_dump(mode="json")
    restored = AvailableAgent.model_validate(dumped)
    assert restored == original


@given(
    name=short_text,
    slug=slug_st,
    description=short_text,
    system_prompt=st.text(min_size=1, max_size=200),
    status=st.sampled_from(list(AgentStatus)),
    source=st.sampled_from(list(AgentsAgentSource)),
)
def test_agent_roundtrip(
    name: str,
    slug: str,
    description: str,
    system_prompt: str,
    status: AgentStatus,
    source: AgentsAgentSource,
) -> None:
    original = Agent(
        id=str(uuid4()),
        name=name,
        slug=slug,
        description=description,
        system_prompt=system_prompt,
        default_model_id="gpt-4o",
        default_model_name="GPT-4o",
        status=status,
        tools=[],
        source=source,
    )
    dumped = original.model_dump(mode="json")
    restored = Agent.model_validate(dumped)
    assert restored == original


@given(
    name=st.text(min_size=1, max_size=100, alphabet=st.characters(categories=("L", "N", "Z"))),
    description=st.text(min_size=0, max_size=200),
    system_prompt=st.text(min_size=1, max_size=500),
)
def test_agent_create_roundtrip(name: str, description: str, system_prompt: str) -> None:
    original = AgentCreate(
        name=name,
        description=description,
        system_prompt=system_prompt,
        tools=[],
        status_column="Backlog",
        default_model_id="gpt-4o",
        default_model_name="GPT-4o",
        raw=False,
    )
    dumped = original.model_dump(mode="json")
    restored = AgentCreate.model_validate(dumped)
    assert restored == original


@given(slug=slug_st, model_id=model_id_st)
def test_pipeline_agent_node_roundtrip(slug: str, model_id: str) -> None:
    original = PipelineAgentNode(
        id=str(uuid4()),
        agent_slug=slug,
        agent_display_name=slug,
        model_id=model_id,
        model_name=model_id,
        tool_ids=[],
        tool_count=0,
        config={},
    )
    dumped = original.model_dump(mode="json")
    restored = PipelineAgentNode.model_validate(dumped)
    assert restored == original


def test_pipeline_config_roundtrip_simple() -> None:
    """Roundtrip a minimal PipelineConfig with one stage and group."""
    node = PipelineAgentNode(
        id="n1",
        agent_slug="review",
        agent_display_name="Review",
        model_id="m1",
        model_name="Model",
        tool_ids=[],
        tool_count=0,
        config={},
    )
    group = ExecutionGroup(id="g1", order=0, execution_mode="sequential", agents=[node])
    stage = PipelineStage(
        id="s1", name="Stage 1", order=0, groups=[group], agents=[node], execution_mode="sequential"
    )
    original = PipelineConfig(
        id="p1",
        project_id="proj1",
        name="Test Pipeline",
        description="test",
        stages=[stage],
        is_preset=False,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    dumped = original.model_dump(mode="json")
    restored = PipelineConfig.model_validate(dumped)
    assert restored == original


@given(
    name=st.text(min_size=1, max_size=100, alphabet=st.characters(categories=("L", "N", "Z"))),
    description=st.text(min_size=0, max_size=200),
    config_content=st.text(min_size=2, max_size=500),
    repo_target=st.text(min_size=1, max_size=50, alphabet=st.characters(categories=("L", "N"))),
)
def test_mcp_tool_config_create_roundtrip(
    name: str,
    description: str,
    config_content: str,
    repo_target: str,
) -> None:
    original = McpToolConfigCreate(
        name=name,
        description=description,
        config_content=config_content,
        github_repo_target=repo_target,
    )
    dumped = original.model_dump(mode="json")
    restored = McpToolConfigCreate.model_validate(dumped)
    assert restored == original
