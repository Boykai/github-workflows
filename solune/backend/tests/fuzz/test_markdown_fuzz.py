from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from src.services.agent_tracking import AgentStep, render_tracking_markdown


@given(
    agent_name=st.text(max_size=40),
    model_name=st.text(max_size=40),
    state=st.sampled_from(["⏳ Pending", "🔄 Active", "✅ Done"]),
)
def test_render_tracking_markdown_preserves_table_structure(
    agent_name: str,
    model_name: str,
    state: str,
) -> None:
    steps = [
        AgentStep(
            index=1,
            status="Ready",
            agent_name=agent_name,
            model=model_name,
            state=state,
        )
    ]

    markdown = render_tracking_markdown(steps)
    table_lines = [line for line in markdown.splitlines() if line.startswith("|")]

    assert "| # | Status | Agent | Model | State |" in markdown
    assert len(table_lines) == 3
    assert all(line.startswith("|") and line.endswith("|") for line in table_lines)
    assert table_lines[-1].startswith("| 1 | Ready |")
