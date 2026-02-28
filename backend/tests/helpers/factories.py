"""Reusable test data factories for backend tests.

Provides factory functions that create valid model instances with sensible
defaults.  Override any field via keyword arguments.
"""

from src.models.board import (
    BoardColumn,
    BoardDataResponse,
    BoardItem,
    BoardProject,
    ContentType,
    StatusColor,
    StatusField,
    StatusOption,
)
from src.models.chat import ChatMessage, SenderType
from src.models.project import GitHubProject, ProjectType, StatusColumn
from src.models.recommendation import AITaskProposal, IssueRecommendation
from src.models.settings import GlobalSettingsRow, ProjectSettingsRow, UserPreferencesRow
from src.models.task import Task
from src.models.user import UserSession

# ── Identity ────────────────────────────────────────────────────────────────


def make_user_session(**overrides) -> UserSession:
    """Create a UserSession with sensible test defaults."""
    defaults: dict = {
        "github_user_id": "12345",
        "github_username": "testuser",
        "access_token": "test-token",
    }
    defaults.update(overrides)
    return UserSession(**defaults)


# ── Tasks ───────────────────────────────────────────────────────────────────


def make_task(**overrides) -> Task:
    """Create a Task with sensible test defaults."""
    defaults: dict = {
        "project_id": "PVT_abc",
        "github_item_id": "PVTI_1",
        "title": "Test task",
        "status": "Todo",
        "status_option_id": "opt1",
    }
    defaults.update(overrides)
    return Task(**defaults)


# ── Projects ────────────────────────────────────────────────────────────────


def make_status_column(**overrides) -> StatusColumn:
    """Create a StatusColumn with sensible test defaults."""
    defaults: dict = {
        "field_id": "PVTSSF_1",
        "name": "Todo",
        "option_id": "opt1",
        "color": "GRAY",
    }
    defaults.update(overrides)
    return StatusColumn(**defaults)


def make_project(**overrides) -> GitHubProject:
    """Create a GitHubProject with sensible test defaults."""
    defaults: dict = {
        "project_id": "PVT_abc",
        "owner_id": "O_123",
        "owner_login": "testuser",
        "name": "Test Project",
        "type": ProjectType.USER,
        "url": "https://github.com/users/testuser/projects/1",
        "status_columns": [
            make_status_column(),
            make_status_column(name="Done", option_id="opt2", color="GREEN"),
        ],
    }
    defaults.update(overrides)
    return GitHubProject(**defaults)


# ── Board ───────────────────────────────────────────────────────────────────


def make_board_project(**overrides) -> BoardProject:
    """Create a BoardProject with sensible test defaults."""
    defaults: dict = {
        "project_id": "PVT_abc",
        "name": "Test Board",
        "url": "https://github.com/users/testuser/projects/1",
        "owner_login": "testuser",
        "status_field": StatusField(
            field_id="SF_1",
            options=[
                StatusOption(option_id="opt1", name="Todo", color=StatusColor.GRAY),
                StatusOption(option_id="opt2", name="Done", color=StatusColor.GREEN),
            ],
        ),
    }
    defaults.update(overrides)
    return BoardProject(**defaults)


def make_board_column(**overrides) -> BoardColumn:
    """Create a BoardColumn with sensible test defaults."""
    defaults: dict = {
        "status": StatusOption(option_id="opt1", name="Todo", color=StatusColor.GRAY),
        "items": [],
        "item_count": 0,
    }
    defaults.update(overrides)
    return BoardColumn(**defaults)


def make_board_item(**overrides) -> BoardItem:
    """Create a BoardItem with sensible test defaults."""
    defaults: dict = {
        "item_id": "PVTI_1",
        "content_type": ContentType.ISSUE,
        "title": "Fix bug",
        "status": "Todo",
        "status_option_id": "opt1",
    }
    defaults.update(overrides)
    return BoardItem(**defaults)


def make_board_data(**overrides) -> BoardDataResponse:
    """Create a BoardDataResponse with sensible test defaults."""
    project = overrides.pop("project", make_board_project())
    defaults: dict = {
        "project": project,
        "columns": [
            make_board_column(
                status=project.status_field.options[0],
                items=[make_board_item()],
                item_count=1,
            ),
            make_board_column(
                status=project.status_field.options[1],
            ),
        ],
    }
    defaults.update(overrides)
    return BoardDataResponse(**defaults)


# ── Chat / Recommendations ──────────────────────────────────────────────────


def make_chat_message(**overrides) -> ChatMessage:
    """Create a ChatMessage with sensible test defaults."""
    defaults: dict = {
        "content": "Hello, world!",
        "sender": SenderType.USER,
    }
    defaults.update(overrides)
    return ChatMessage(**defaults)


def make_issue_recommendation(session_id=None, **overrides) -> IssueRecommendation:
    """Create an IssueRecommendation with sensible test defaults."""
    from uuid import uuid4

    defaults: dict = {
        "session_id": session_id or str(uuid4()),
        "original_input": "add dark mode",
        "title": "Add dark mode",
        "user_story": "As a user I want dark mode",
        "ui_ux_description": "Toggle in header",
        "functional_requirements": ["Must toggle theme"],
    }
    defaults.update(overrides)
    return IssueRecommendation(**defaults)


def make_task_proposal(session_id=None, **overrides) -> AITaskProposal:
    """Create an AITaskProposal with sensible test defaults."""
    from uuid import uuid4

    defaults: dict = {
        "session_id": session_id or str(uuid4()),
        "original_input": "fix login bug",
        "proposed_title": "Fix login bug",
        "proposed_description": "Fix the login flow",
    }
    defaults.update(overrides)
    return AITaskProposal(**defaults)


# ── Settings ────────────────────────────────────────────────────────────────


def make_user_preferences_row(**overrides) -> UserPreferencesRow:
    """Create a UserPreferencesRow with sensible test defaults."""
    defaults: dict = {
        "github_user_id": "12345",
        "preferences_json": "{}",
    }
    defaults.update(overrides)
    return UserPreferencesRow(**defaults)


def make_global_settings_row(**overrides) -> GlobalSettingsRow:
    """Create a GlobalSettingsRow with sensible test defaults."""
    defaults: dict = {
        "settings_json": "{}",
    }
    defaults.update(overrides)
    return GlobalSettingsRow(**defaults)


def make_project_settings_row(**overrides) -> ProjectSettingsRow:
    """Create a ProjectSettingsRow with sensible test defaults."""
    defaults: dict = {
        "project_id": "PVT_abc",
        "settings_json": "{}",
    }
    defaults.update(overrides)
    return ProjectSettingsRow(**defaults)
