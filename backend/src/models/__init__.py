"""Pydantic models for the application."""

from src.models.agent import (
    AgentAssignment,
    AgentAssignmentInput,
    AgentSource,
    AvailableAgent,
    AvailableAgentsResponse,
)
from src.models.chat import (
    ActionType,
    ChatMessage,
    ChatMessageRequest,
    ChatMessagesResponse,
    SenderType,
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
    TriggeredBy,
    WorkflowConfiguration,
    WorkflowResult,
    WorkflowTransition,
)

__all__ = [
    # agent
    "AgentAssignment",
    "AgentAssignmentInput",
    "AgentSource",
    "AvailableAgent",
    "AvailableAgentsResponse",
    # chat
    "ActionType",
    "ChatMessage",
    "ChatMessageRequest",
    "ChatMessagesResponse",
    "SenderType",
    # project
    "GitHubProject",
    "StatusColumn",
    # recommendation
    "AVAILABLE_LABELS",
    "AITaskProposal",
    "IssueLabel",
    "IssueMetadata",
    "IssuePriority",
    "IssueRecommendation",
    "IssueSize",
    "ProposalConfirmRequest",
    "ProposalStatus",
    "RecommendationStatus",
    # task
    "Task",
    # user
    "UserSession",
    # workflow
    "TriggeredBy",
    "WorkflowConfiguration",
    "WorkflowResult",
    "WorkflowTransition",
]
