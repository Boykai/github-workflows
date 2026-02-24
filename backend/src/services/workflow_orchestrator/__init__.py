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
    get_transitions,
    get_workflow_config,
    set_workflow_config,
)
from .models import (
    MainBranchInfo,
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
    clear_issue_main_branch,
    clear_issue_sub_issues,
    get_all_pipeline_states,
    get_issue_main_branch,
    get_issue_sub_issues,
    get_pipeline_state,
    remove_pipeline_state,
    set_issue_main_branch,
    set_issue_sub_issues,
    set_pipeline_state,
    update_issue_main_branch_sha,
)

__all__ = [
    # models
    "WorkflowState",
    "WorkflowContext",
    "PipelineState",
    "MainBranchInfo",
    "_ci_get",
    "get_agent_slugs",
    "get_status_order",
    "get_next_status",
    "find_next_actionable_status",
    # config
    "get_workflow_config",
    "set_workflow_config",
    "get_transitions",
    "_workflow_configs",
    "_transitions",
    "_load_workflow_config_from_db",
    "_persist_workflow_config_to_db",
    # transitions
    "get_pipeline_state",
    "get_all_pipeline_states",
    "set_pipeline_state",
    "remove_pipeline_state",
    "get_issue_main_branch",
    "get_issue_sub_issues",
    "set_issue_sub_issues",
    "set_issue_main_branch",
    "clear_issue_main_branch",
    "clear_issue_sub_issues",
    "update_issue_main_branch_sha",
    "_pipeline_states",
    "_issue_main_branches",
    "_issue_sub_issue_map",
    # orchestrator
    "WorkflowOrchestrator",
    "get_workflow_orchestrator",
]
