"""Pydantic models for the application."""

from src.models.agent import (
    AgentAssignment,
    AgentAssignmentInput,
    AgentSource,
    AvailableAgent,
    AvailableAgentsResponse,
)
from src.models.agent_creator import (
    AgentCreationState,
    AgentPreview,
    CreationStep,
    PipelineStepResult,
)
from src.models.agents import AgentMcpSyncResponse
from src.models.chat import (
    ActionType,
    ChatMessage,
    ChatMessageRequest,
    ChatMessagesResponse,
    SenderType,
)
from src.models.chores import ChoreDeleteResponse
from src.models.common import (
    DeleteResponse,
    MessageResponse,
    PipelineSeedPresetsResponse,
    SeedPresetsResponse,
)
from src.models.project import GitHubProject, StatusColumn
from src.models.recommendation import (
    AVAILABLE_LABELS,
    AITaskProposal,
    IssueLabel,
    IssueMetadata,
    IssuePriority,
    IssueRecommendation,
    IssueSize,
    ProposalConfirmRequest,
    ProposalStatus,
    RecommendationStatus,
)
from src.models.task import Task
from src.models.user import UserSession
from src.models.workflow import (
    PipelineRetryResponse,
    PipelineStateItem,
    PipelineStatesResponse,
    PollingCheckAllResponse,
    PollingCheckResult,
    PollingStartResponse,
    PollingStatusResponse,
    PollingStopResponse,
    TriggeredBy,
    WorkflowConfiguration,
    WorkflowResult,
    WorkflowTransition,
)

__all__ = [
    # recommendation
    "AVAILABLE_LABELS",
    "AITaskProposal",
    # chat
    "ActionType",
    # agent
    "AgentAssignment",
    "AgentAssignmentInput",
    # agent_creator
    "AgentCreationState",
    # agents
    "AgentMcpSyncResponse",
    "AgentPreview",
    "AgentSource",
    "AvailableAgent",
    "AvailableAgentsResponse",
    "ChatMessage",
    "ChatMessageRequest",
    "ChatMessagesResponse",
    # chores
    "ChoreDeleteResponse",
    "CreationStep",
    # common
    "DeleteResponse",
    # project
    "GitHubProject",
    "IssueLabel",
    "IssueMetadata",
    "IssuePriority",
    "IssueRecommendation",
    "IssueSize",
    "MessageResponse",
    "PipelineRetryResponse",
    "PipelineSeedPresetsResponse",
    "PipelineStateItem",
    "PipelineStatesResponse",
    "PipelineStepResult",
    "PollingCheckAllResponse",
    "PollingCheckResult",
    "PollingStartResponse",
    "PollingStatusResponse",
    "PollingStopResponse",
    "ProposalConfirmRequest",
    "ProposalStatus",
    "RecommendationStatus",
    "SeedPresetsResponse",
    "SenderType",
    "StatusColumn",
    # task
    "Task",
    # workflow
    "TriggeredBy",
    # user
    "UserSession",
    "WorkflowConfiguration",
    "WorkflowResult",
    "WorkflowTransition",
]
