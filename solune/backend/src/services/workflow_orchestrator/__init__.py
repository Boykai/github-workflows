"""
GitHub Issue Workflow Orchestrator Package

Decomposed from a single 2048-line file into focused sub-modules:
- models.py: Data classes, enums, and pure helper functions (leaf dependency)
- config.py: Workflow configuration load/persist/defaults and transition audit log
- transitions.py: Pipeline state, branch tracking, and sub-issue map management
- orchestrator.py: WorkflowOrchestrator class and singleton factory

All public names are re-exported here for backward compatibility.
Existing ``from src.services.workflow_orchestrator import X`` imports continue to work.
"""

from .config import (
    _load_workflow_config_from_db,
    _persist_workflow_config_to_db,
    _transitions,
    _workflow_configs,
    deduplicate_agent_mappings,
    get_transitions,
    get_workflow_config,
    load_user_agent_mappings,
    set_workflow_config,
)
from .models import (
    MainBranchInfo,
    PipelineGroupInfo,
    PipelineState,
    WorkflowContext,
    WorkflowState,
    _ci_get,
    find_next_actionable_status,
    get_agent_slugs,
    get_next_status,
    get_status_order,
)
from .orchestrator import (
    WorkflowOrchestrator,
    get_workflow_orchestrator,
)
from .transitions import (
    _issue_main_branches,
    _issue_sub_issue_map,
    _pipeline_states,
    clear_agent_trigger_buffer,
    clear_all_agent_trigger_buffers,
    clear_issue_main_branch,
    clear_issue_sub_issues,
    count_active_pipelines_for_project,
    get_all_pipeline_states,
    get_issue_main_branch,
    get_issue_sub_issues,
    get_pipeline_state,
    get_project_launch_lock,
    get_queued_pipelines_for_project,
    remove_pipeline_state,
    set_issue_main_branch,
    set_issue_sub_issues,
    set_pipeline_state,
    should_skip_agent_trigger,
    update_issue_main_branch_sha,
)

__all__ = [
    "MainBranchInfo",
    "PipelineGroupInfo",
    "PipelineState",
    "WorkflowContext",
    # orchestrator
    "WorkflowOrchestrator",
    # models
    "WorkflowState",
    "_ci_get",
    "_issue_main_branches",
    "_issue_sub_issue_map",
    "_load_workflow_config_from_db",
    "_persist_workflow_config_to_db",
    "_pipeline_states",
    "_transitions",
    "_workflow_configs",
    "clear_agent_trigger_buffer",
    "clear_all_agent_trigger_buffers",
    "clear_issue_main_branch",
    "clear_issue_sub_issues",
    "count_active_pipelines_for_project",
    "deduplicate_agent_mappings",
    "find_next_actionable_status",
    "get_agent_slugs",
    "get_all_pipeline_states",
    "get_issue_main_branch",
    "get_issue_sub_issues",
    "get_next_status",
    # transitions
    "get_pipeline_state",
    "get_project_launch_lock",
    "get_queued_pipelines_for_project",
    "get_status_order",
    "get_transitions",
    # config
    "get_workflow_config",
    "get_workflow_orchestrator",
    "load_user_agent_mappings",
    "remove_pipeline_state",
    "set_issue_main_branch",
    "set_issue_sub_issues",
    "set_pipeline_state",
    "set_workflow_config",
    "should_skip_agent_trigger",
    "update_issue_main_branch_sha",
]
