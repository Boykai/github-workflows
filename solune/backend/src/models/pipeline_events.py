"""Internal event dataclasses for pipeline state changes.

These events are emitted within the service layer to coordinate
between the pipeline orchestrator, WebSocket notifier, and label
manager per contracts/events.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PipelineRunStateChanged:
    """Emitted when a pipeline run transitions between states.

    Consumers:
    - Pipeline orchestrator: triggers next group execution or completes run
    - WebSocket notifier: pushes state update to connected frontends
    - Label manager: creates/updates GitHub labels for state tracking (FR-015)
    """

    run_id: int
    pipeline_config_id: str
    project_id: str
    previous_status: str  # 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
    new_status: str
    timestamp: str  # ISO 8601
    error_message: str | None = None


@dataclass
class PipelineStageStateChanged:
    """Emitted when an individual stage transitions between states.

    Consumers:
    - Group executor: determines if group is complete → triggers next group
    - Pipeline run manager: checks if all groups complete → transitions run
    - WebSocket notifier: pushes stage update to connected frontends
    - Label manager: updates GitHub label for this stage
    """

    stage_state_id: int
    pipeline_run_id: int
    stage_id: str
    group_id: int | None
    previous_status: str  # 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
    new_status: str
    agent_id: str | None
    timestamp: str  # ISO 8601


@dataclass
class MCPConfigUpdated:
    """Emitted when MCP tool configuration is updated for a project.

    Consumer: Agent file writer — propagates tools to all agent config files.
    """

    project_id: str
    owner: str
    repo: str
    tools: list[str] = field(default_factory=list)
    timestamp: str = ""
