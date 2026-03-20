from __future__ import annotations

from collections.abc import Iterator
from contextlib import ExitStack, asynccontextmanager
from unittest.mock import patch

import aiosqlite
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.models.board import (
    BoardColumn,
    BoardDataResponse,
    BoardItem,
    BoardProject,
    ContentType,
    Repository,
    StatusColor,
    StatusField,
    StatusOption,
)
from src.models.project import GitHubProject, ProjectType, StatusColumn
from src.models.user import UserSession
from src.services.websocket import ConnectionManager
from src.services.workflow_orchestrator import (
    _issue_main_branches,
    _issue_sub_issue_map,
    _pipeline_states,
    _transitions,
    _workflow_configs,
)
from src.services.workflow_orchestrator.orchestrator import WorkflowOrchestrator
from src.services.workflow_orchestrator.transitions import _agent_trigger_inflight


def _build_project(project_id: str) -> GitHubProject:
    return GitHubProject(
        project_id=project_id,
        owner_id="OWNER_1",
        owner_login="octocat",
        name="Integration Project",
        type=ProjectType.ORGANIZATION,
        url="https://github.com/orgs/octocat/projects/1",
        description="Thin-mock integration test project",
        status_columns=[
            StatusColumn(field_id="status-field", name="Backlog", option_id="opt-backlog"),
            StatusColumn(field_id="status-field", name="Ready", option_id="opt-ready"),
            StatusColumn(
                field_id="status-field",
                name="In Progress",
                option_id="opt-progress",
            ),
            StatusColumn(
                field_id="status-field",
                name="In Review",
                option_id="opt-review",
            ),
        ],
        item_count=3,
    )


def _build_board_data(project_id: str) -> BoardDataResponse:
    backlog = StatusOption(option_id="opt-backlog", name="Backlog", color=StatusColor.GRAY)
    return BoardDataResponse(
        project=BoardProject(
            project_id=project_id,
            name="Integration Project",
            description="Thin-mock board",
            url="https://github.com/orgs/octocat/projects/1",
            owner_login="octocat",
            status_field=StatusField(field_id="status-field", options=[backlog]),
        ),
        columns=[
            BoardColumn(
                status=backlog,
                items=[
                    BoardItem(
                        item_id="ITEM_1",
                        content_id="ISSUE_1",
                        content_type=ContentType.ISSUE,
                        title="Existing backlog task",
                        number=7,
                        repository=Repository(owner="octocat", name="demo-repo"),
                        url="https://github.com/octocat/demo-repo/issues/7",
                        status="Backlog",
                        status_option_id="opt-backlog",
                    )
                ],
                item_count=1,
            )
        ],
    )


@asynccontextmanager
async def _noop_lifespan(_app):
    yield


async def _create_integration_db() -> aiosqlite.Connection:
    from src.services.database import _run_migrations
    from src.services.done_items_store import init_done_items_store
    from src.services.pipeline_state_store import init_pipeline_state_store

    db = await aiosqlite.connect(":memory:")
    db.row_factory = aiosqlite.Row
    await _run_migrations(db)
    await init_pipeline_state_store(db)
    await init_done_items_store(db)
    return db


@pytest.fixture
def thin_mock_connection_manager() -> ConnectionManager:
    return ConnectionManager()


@pytest.fixture(autouse=True)
def _reset_integration_state() -> Iterator[None]:
    from src.api.chat import _locks, _messages, _proposals, _recommendations
    from src.services import pipeline_state_store, websocket
    from src.services.cache import cache as _cache

    _cache.clear()
    _messages.clear()
    _proposals.clear()
    _recommendations.clear()
    _locks.clear()
    _pipeline_states.clear()
    _issue_main_branches.clear()
    _issue_sub_issue_map.clear()
    _workflow_configs.clear()
    _transitions.clear()
    _agent_trigger_inflight.clear()
    import src.services.workflow_orchestrator.orchestrator as orch_mod

    orch_mod._orchestrator_instance = None
    pipeline_state_store._store_lock = None
    websocket._ws_lock = None

    yield

    _cache.clear()
    _messages.clear()
    _proposals.clear()
    _recommendations.clear()
    _locks.clear()
    _pipeline_states.clear()
    _issue_main_branches.clear()
    _issue_sub_issue_map.clear()
    _workflow_configs.clear()
    _transitions.clear()
    _agent_trigger_inflight.clear()
    import src.services.workflow_orchestrator.orchestrator as orch_mod

    orch_mod._orchestrator_instance = None
    pipeline_state_store._store_lock = None
    websocket._ws_lock = None


@pytest.fixture
def integration_session() -> UserSession:
    return UserSession(
        github_user_id="12345",
        github_username="octocat",
        access_token="gho_test_token",
    )


@pytest_asyncio.fixture
async def thin_mock_client(
    integration_session: UserSession,
    thin_mock_connection_manager: ConnectionManager,
) -> AsyncClient:
    from src.main import create_app

    project_id = "PVT_integration"
    project = _build_project(project_id)
    board_data = _build_board_data(project_id)
    active_session = integration_session.model_copy(deep=True)

    class _GitHubAuthStub:
        async def create_session_from_token(self, _token: str) -> UserSession:
            return await _create_session_from_token(_token)

        async def get_session(self, session_id: str) -> UserSession | None:
            return await _get_session(session_id)

        async def update_session(self, session: UserSession) -> None:
            await _update_session(session)

        async def revoke_session(self, session_id: str) -> None:
            await _revoke_session(session_id)

    class _AIAgentStub:
        async def detect_feature_request_intent(self, *_args, **_kwargs) -> bool:
            return False

        async def parse_status_change_request(self, *_args, **_kwargs):
            return None

        async def generate_title_from_description(self, *_args, **_kwargs) -> str:
            return "Generated task title"

    class _GitHubProjectsStub:
        async def list_user_projects(self, *_args, **_kwargs) -> list[GitHubProject]:
            return [project]

        async def get_project_repository(self, *_args, **_kwargs) -> tuple[str, str]:
            return ("octocat", "demo-repo")

        async def get_board_data(self, *_args, **_kwargs) -> BoardDataResponse:
            return board_data

        async def create_issue(self, *_args, **_kwargs) -> dict[str, str | int]:
            return {
                "id": "DB_101",
                "node_id": "ISSUE_101",
                "number": 101,
                "html_url": "https://github.com/octocat/demo-repo/issues/101",
            }

        async def add_issue_to_project(self, *_args, **kwargs) -> str:
            return f"ITEM_{kwargs['issue_node_id']}"

        async def update_item_status_by_name(self, *_args, **_kwargs) -> bool:
            return True

        async def get_issue_with_comments(self, *_args, **_kwargs) -> dict[str, object]:
            return {
                "title": "Launch human review",
                "body": "Parent issue body",
                "user": {"login": active_session.github_username},
            }

        def tailor_body_for_agent(self, *_args, **kwargs) -> str:
            return f"Sub-issue body for {kwargs['agent_name']}"

        async def create_sub_issue(self, *_args, **_kwargs) -> dict[str, str | int]:
            return {
                "id": "DB_201",
                "node_id": "ISSUE_SUB_201",
                "number": 201,
                "html_url": "https://github.com/octocat/demo-repo/issues/201",
            }

        async def assign_issue(self, *_args, **_kwargs) -> bool:
            return True

        async def create_issue_comment(self, *_args, **_kwargs) -> bool:
            return True

        async def request_copilot_review(self, *_args, **_kwargs) -> bool:
            return True

        async def has_copilot_reviewed_pr(self, *_args, **_kwargs) -> bool:
            return False

        async def delete_issue_comment(self, *_args, **_kwargs) -> bool:
            return True

        async def find_existing_pr_for_issue(self, *_args, **_kwargs):
            return None

        async def update_issue_state(self, *_args, **_kwargs) -> bool:
            return True

        async def update_sub_issue_project_status(self, *_args, **_kwargs) -> bool:
            return True

        def get_last_rate_limit(self) -> None:
            return None

    auth_service = _GitHubAuthStub()
    ai_service = _AIAgentStub()
    github_service = _GitHubProjectsStub()

    async def _create_session_from_token(_token: str) -> UserSession:
        return active_session

    async def _get_session(session_id: str) -> UserSession | None:
        if session_id == str(active_session.session_id):
            return active_session
        return None

    async def _update_session(session: UserSession) -> None:
        active_session.selected_project_id = session.selected_project_id
        active_session.active_app_name = session.active_app_name

    async def _revoke_session(_session_id: str) -> None:
        return None

    async def _ensure_polling_started(**_kwargs) -> bool:
        return True

    db = await _create_integration_db()
    orchestrator = WorkflowOrchestrator(ai_service, github_service)
    app = create_app()
    app.router.lifespan_context = _noop_lifespan
    app.state.db = db
    app.state.github_service = github_service
    app.state.connection_manager = thin_mock_connection_manager
    transport = ASGITransport(app=app)

    with ExitStack() as stack:
        stack.enter_context(patch("src.services.database.get_db", return_value=db))
        stack.enter_context(patch("src.services.database._connection", db))
        stack.enter_context(patch("src.api.chat.get_db", return_value=db))
        stack.enter_context(patch("src.api.settings.get_db", return_value=db))
        stack.enter_context(patch("src.api.mcp.get_db", return_value=db))
        stack.enter_context(patch("src.api.tools.get_db", return_value=db))
        stack.enter_context(patch("src.api.auth.github_auth_service", auth_service))
        stack.enter_context(patch("src.api.projects.github_auth_service", auth_service))
        stack.enter_context(
            patch("src.services.github_projects.github_projects_service", github_service)
        )
        stack.enter_context(patch("src.api.projects.github_projects_service", github_service))
        stack.enter_context(patch("src.api.board.github_projects_service", github_service))
        stack.enter_context(patch("src.api.pipelines.github_projects_service", github_service))
        stack.enter_context(patch("src.api.workflow.github_projects_service", github_service))
        stack.enter_context(patch("src.api.chat.get_ai_agent_service", return_value=ai_service))
        stack.enter_context(patch("src.api.chat._trigger_signal_delivery", lambda *_a, **_k: None))
        stack.enter_context(
            patch(
                "src.services.copilot_polling.ensure_polling_started",
                _ensure_polling_started,
            )
        )
        stack.enter_context(
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False, "errors_count": 0, "last_error": None},
            )
        )
        stack.enter_context(
            patch("src.api.pipelines.get_workflow_orchestrator", return_value=orchestrator)
        )
        stack.enter_context(
            patch("src.api.workflow.connection_manager", thin_mock_connection_manager)
        )
        stack.enter_context(
            patch("src.api.projects.connection_manager", thin_mock_connection_manager)
        )

        try:
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                yield client
        finally:
            await thin_mock_connection_manager.shutdown()
            await transport.aclose()

    await db.close()
