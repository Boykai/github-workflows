"""AI task proposal and issue recommendation models."""

from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.constants import LABELS
from src.utils import utcnow


class ProposalStatus(StrEnum):
    """Status of an AI task proposal."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    EDITED = "edited"
    CANCELLED = "cancelled"


class RecommendationStatus(StrEnum):
    """Status of an AI issue recommendation."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class AITaskProposal(BaseModel):
    """Temporary entity for AI-generated tasks awaiting user confirmation."""

    proposal_id: UUID = Field(default_factory=uuid4, description="Unique proposal identifier")
    session_id: UUID = Field(..., description="Parent session ID (FK)")
    original_input: str = Field(..., description="User's original natural language input")
    proposed_title: str = Field(..., max_length=256, description="AI-generated task title")
    proposed_description: str = Field(
        ..., max_length=65535, description="AI-generated task description"
    )
    status: ProposalStatus = Field(default=ProposalStatus.PENDING, description="Proposal status")
    edited_title: str | None = Field(default=None, description="User-modified title")
    edited_description: str | None = Field(default=None, description="User-modified description")
    created_at: datetime = Field(default_factory=utcnow, description="Proposal creation time")
    expires_at: datetime = Field(
        default_factory=lambda: utcnow() + timedelta(minutes=10),
        description="Auto-expiration time",
    )

    @property
    def is_expired(self) -> bool:
        """Check if proposal has expired."""
        return utcnow() > self.expires_at

    @property
    def final_title(self) -> str:
        """Get final title (edited or proposed)."""
        return self.edited_title or self.proposed_title

    @property
    def final_description(self) -> str:
        """Get final description (edited or proposed)."""
        return self.edited_description or self.proposed_description

    model_config = {
        "json_schema_extra": {
            "example": {
                "proposal_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "550e8400-e29b-41d4-a716-446655440001",
                "original_input": "Add authentication so users can log in with their GitHub accounts",
                "proposed_title": "Add OAuth2 authentication flow",
                "proposed_description": "## Overview\\nImplement GitHub OAuth2...",
                "status": "pending",
                "edited_title": None,
                "edited_description": None,
                "created_at": "2026-01-30T10:00:00Z",
                "expires_at": "2026-01-30T10:10:00Z",
            }
        }
    }


class ProposalConfirmRequest(BaseModel):
    """Request to confirm an AI task proposal."""

    edited_title: str | None = Field(default=None, max_length=256, description="Edited title")
    edited_description: str | None = Field(
        default=None, max_length=65535, description="Edited description"
    )


# ============================================================================
# Issue Recommendation Models
# ============================================================================


class IssuePriority(StrEnum):
    """Priority levels for issues."""

    P0 = "P0"  # Critical - immediate attention
    P1 = "P1"  # High - complete ASAP
    P2 = "P2"  # Medium - standard priority
    P3 = "P3"  # Low - nice to have


class IssueSize(StrEnum):
    """Size estimates for issues (T-shirt sizing)."""

    XS = "XS"  # < 1 hour
    S = "S"  # 1-4 hours
    M = "M"  # 4-8 hours (1 day)
    L = "L"  # 1-3 days
    XL = "XL"  # 3-5 days


class IssueLabel(StrEnum):
    """Pre-defined labels for GitHub Issues."""

    # Type labels
    FEATURE = "feature"  # New functionality
    BUG = "bug"  # Bug fix
    ENHANCEMENT = "enhancement"  # Improvement to existing feature
    REFACTOR = "refactor"  # Code refactoring
    DOCUMENTATION = "documentation"  # Documentation updates
    TESTING = "testing"  # Test-related work
    INFRASTRUCTURE = "infrastructure"  # DevOps, CI/CD, config

    # Scope labels
    FRONTEND = "frontend"  # Frontend/UI work
    BACKEND = "backend"  # Backend/API work
    DATABASE = "database"  # Database changes
    API = "api"  # API changes

    # Status labels
    AI_GENERATED = "ai-generated"  # Created by AI
    GOOD_FIRST_ISSUE = "good first issue"  # Simple issue
    HELP_WANTED = "help wanted"  # Needs assistance

    # Domain labels
    SECURITY = "security"  # Security-related
    PERFORMANCE = "performance"  # Performance optimization
    ACCESSIBILITY = "accessibility"  # A11y improvements
    UX = "ux"  # User experience


# List of all available labels for AI reference — re-exported alias.
AVAILABLE_LABELS = LABELS


class IssueMetadata(BaseModel):
    """AI-generated metadata for GitHub Issues."""

    priority: IssuePriority = Field(
        default=IssuePriority.P2,
        description="Issue priority (P0=Critical, P1=High, P2=Medium, P3=Low)",
    )
    size: IssueSize = Field(
        default=IssueSize.M,
        description="Estimated size (XS=<1hr, S=1-4hrs, M=1day, L=1-3days, XL=3-5days)",
    )
    estimate_hours: float = Field(
        default=4.0, ge=0.5, le=40.0, description="Estimated hours to complete (0.5-40)"
    )
    start_date: str = Field(default="", description="Suggested start date (ISO format YYYY-MM-DD)")
    target_date: str = Field(
        default="", description="Target completion date (ISO format YYYY-MM-DD)"
    )
    labels: list[str] = Field(
        default_factory=lambda: ["ai-generated"],
        description="Suggested labels for the issue",
    )


class IssueRecommendation(BaseModel):
    """AI-generated issue recommendation awaiting user confirmation."""

    recommendation_id: UUID = Field(default_factory=uuid4, description="Unique recommendation ID")
    session_id: UUID = Field(..., description="Parent session ID")
    original_input: str = Field(..., description="User's original feature request text")
    original_context: str = Field(
        default="", description="User's complete input preserved verbatim by the AI"
    )
    title: str = Field(..., max_length=256, description="AI-generated issue title")
    user_story: str = Field(..., description="User story in As a/I want/So that format")
    ui_ux_description: str = Field(..., description="UI/UX guidance for implementation")
    functional_requirements: list[str] = Field(..., description="List of testable requirements")
    technical_notes: str = Field(
        default="", description="Implementation hints and architecture considerations"
    )
    metadata: IssueMetadata = Field(
        default_factory=IssueMetadata,
        description="AI-generated issue metadata (priority, size, dates, labels)",
    )
    status: RecommendationStatus = Field(
        default=RecommendationStatus.PENDING, description="Recommendation status"
    )
    created_at: datetime = Field(default_factory=utcnow, description="Creation timestamp")
    confirmed_at: datetime | None = Field(default=None, description="Confirmation timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "recommendation_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "550e8400-e29b-41d4-a716-446655440001",
                "original_input": "Add CSV export functionality for user data",
                "original_context": "I need to be able to export my user data as CSV. It should include all profile fields and timestamps. Files could be up to 10MB.",
                "title": "Add CSV export functionality for user data",
                "user_story": "As a user, I want to export my data as CSV so that I can analyze it.",
                "ui_ux_description": "Add an Export button in the user profile section.",
                "functional_requirements": [
                    "System MUST generate CSV with all user profile fields",
                    "System MUST include timestamps in ISO 8601 format",
                ],
                "technical_notes": "Use streaming CSV response for large datasets. Rate-limit exports to 5 per minute per user.",
                "metadata": {
                    "priority": "P2",
                    "size": "M",
                    "estimate_hours": 4.0,
                    "start_date": "2026-02-03",
                    "target_date": "2026-02-04",
                    "labels": ["ai-generated", "feature", "export"],
                },
                "status": "pending",
                "created_at": "2026-02-02T10:00:00Z",
                "confirmed_at": None,
            }
        }
    }


__all__ = [
    "ProposalStatus",
    "RecommendationStatus",
    "AITaskProposal",
    "ProposalConfirmRequest",
    "IssuePriority",
    "IssueSize",
    "IssueLabel",
    "AVAILABLE_LABELS",
    "IssueMetadata",
    "IssueRecommendation",
]
