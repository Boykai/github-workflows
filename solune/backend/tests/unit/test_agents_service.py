from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.models.agents import AgentSource, AgentStatus
from src.services.agents.service import AgentsService
from src.services.cache import cache

PROJECT_ID = "project-123"
OWNER = "octo"
REPO = "widgets"
ACCESS_TOKEN = "token"
GITHUB_USER_ID = "user-123"

AGENT_FILE_CONTENT = """---
name: Reviewer
description: Reviews pull requests
tools:
  - read
  - comment
---
Review pull requests carefully.
"""


async def _insert_mcp_tool(
    db,
    *,
    tool_id: str,
    project_id: str = PROJECT_ID,
    github_user_id: str = GITHUB_USER_ID,
    name: str = "Context7",
    config_content: str = '{"mcpServers":{"context7":{"type":"http","url":"https://example.com/mcp","tools":["*"]}}}',
) -> None:
    await db.execute(
        """INSERT INTO mcp_configurations
           (id, github_user_id, project_id, name, description, endpoint_url, config_content,
            sync_status, sync_error, synced_at, github_repo_target, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'synced', '', NULL, ?, 1, datetime('now'), datetime('now'))""",
        (
            tool_id,
            github_user_id,
            project_id,
            name,
            "Shared MCP server",
            "https://example.com/mcp",
            config_content,
            f"{OWNER}/{REPO}",
        ),
    )
    await db.commit()


async def _insert_agent_row(
    db,
    *,
    agent_id: str,
    name: str = "Reviewer",
    slug: str,
    lifecycle_status: str = "pending_pr",
    github_issue_number: int | None = None,
    github_pr_number: int | None = None,
    branch_name: str | None = None,
) -> None:
    await db.execute(
        """INSERT INTO agent_configs
           (id, name, slug, description, system_prompt, status_column,
            tools, project_id, owner, repo, created_by,
            github_issue_number, github_pr_number, branch_name, created_at, lifecycle_status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)""",
        (
            agent_id,
            name,
            slug,
            "Reviews pull requests",
            "Review pull requests carefully.",
            "",
            '["read","comment"]',
            PROJECT_ID,
            OWNER,
            REPO,
            GITHUB_USER_ID,
            github_issue_number,
            github_pr_number,
            branch_name,
            lifecycle_status,
        ),
    )
    await db.commit()


def _workflow_result(pr_number: int = 91, issue_number: int = 44) -> SimpleNamespace:
    return SimpleNamespace(
        success=True,
        pr_url=f"https://github.com/{OWNER}/{REPO}/pull/{pr_number}",
        pr_number=pr_number,
        issue_number=issue_number,
        errors=[],
    )


def _repo_entry(slug: str) -> dict[str, str]:
    return {
        "name": f"{slug}.agent.md",
        "content": AGENT_FILE_CONTENT,
    }


class TestAgentsServiceDeletion:
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        cache.clear()
        yield
        cache.clear()

    async def test_delete_marks_shared_agent_pending_deletion(self, mock_db):
        await _insert_agent_row(mock_db, agent_id="agent-1", slug="reviewer")
        service = AgentsService(mock_db)
        mock_github_service = AsyncMock()
        mock_github_service.get_directory_contents.return_value = [_repo_entry("reviewer")]

        with (
            patch("src.services.agents.service.github_projects_service", mock_github_service),
            patch(
                "src.services.agents.service.commit_files_workflow",
                AsyncMock(return_value=_workflow_result(pr_number=77, issue_number=55)),
            ),
        ):
            result = await service.delete_agent(
                project_id=PROJECT_ID,
                owner=OWNER,
                repo=REPO,
                agent_id="agent-1",
                access_token=ACCESS_TOKEN,
                github_user_id=GITHUB_USER_ID,
            )
            agents = await service.list_agents(
                project_id=PROJECT_ID,
                owner=OWNER,
                repo=REPO,
                access_token=ACCESS_TOKEN,
            )

        assert result.success is True
        assert result.pr_number == 77
        assert len(agents) == 1
        assert agents[0].id == "repo:reviewer"
        assert agents[0].source == AgentSource.REPO
        assert agents[0].status == AgentStatus.ACTIVE
        assert agents[0].github_pr_number is None

        cursor = await mock_db.execute(
            "SELECT lifecycle_status, github_pr_number, github_issue_number, branch_name "
            "FROM agent_configs WHERE id = ?",
            ("agent-1",),
        )
        row = await cursor.fetchone()
        assert row["lifecycle_status"] == AgentStatus.PENDING_DELETION.value
        assert row["github_pr_number"] == 77
        assert row["github_issue_number"] == 55
        assert row["branch_name"] == "agent/delete-reviewer"

    async def test_delete_allows_repo_only_agent_and_creates_tombstone(self, mock_db):
        service = AgentsService(mock_db)
        mock_github_service = AsyncMock()
        mock_github_service.get_directory_contents.return_value = [_repo_entry("reviewer")]

        with (
            patch("src.services.agents.service.github_projects_service", mock_github_service),
            patch(
                "src.services.agents.service.commit_files_workflow",
                AsyncMock(return_value=_workflow_result(pr_number=82, issue_number=63)),
            ),
        ):
            result = await service.delete_agent(
                project_id=PROJECT_ID,
                owner=OWNER,
                repo=REPO,
                agent_id="repo:reviewer",
                access_token=ACCESS_TOKEN,
                github_user_id=GITHUB_USER_ID,
            )
            agents = await service.list_agents(
                project_id=PROJECT_ID,
                owner=OWNER,
                repo=REPO,
                access_token=ACCESS_TOKEN,
            )

        assert result.success is True
        assert len(agents) == 1
        assert agents[0].source == AgentSource.REPO
        assert agents[0].status == AgentStatus.ACTIVE
        assert agents[0].id == "repo:reviewer"
        assert agents[0].github_pr_number is None

        cursor = await mock_db.execute(
            "SELECT id, lifecycle_status, github_pr_number FROM agent_configs WHERE slug = ?",
            ("reviewer",),
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row["id"] != "repo:reviewer"
        assert row["lifecycle_status"] == AgentStatus.PENDING_DELETION.value
        assert row["github_pr_number"] == 82

    async def test_list_agents_removes_pending_deletion_tombstone_after_repo_file_is_gone(
        self,
        mock_db,
    ):
        await _insert_agent_row(
            mock_db,
            agent_id="agent-1",
            slug="reviewer",
            lifecycle_status=AgentStatus.PENDING_DELETION.value,
        )
        service = AgentsService(mock_db)
        mock_github_service = AsyncMock()
        mock_github_service.get_directory_contents.return_value = []

        with patch("src.services.agents.service.github_projects_service", mock_github_service):
            agents = await service.list_agents(
                project_id=PROJECT_ID,
                owner=OWNER,
                repo=REPO,
                access_token=ACCESS_TOKEN,
            )

        assert agents == []

        cursor = await mock_db.execute(
            "SELECT COUNT(*) AS count FROM agent_configs WHERE id = ?", ("agent-1",)
        )
        row = await cursor.fetchone()
        assert row["count"] == 0

    async def test_list_agents_uses_cached_repo_results(self, mock_db):
        service = AgentsService(mock_db)
        mock_github_service = AsyncMock()
        mock_github_service.get_directory_contents.return_value = [_repo_entry("reviewer")]

        with patch("src.services.agents.service.github_projects_service", mock_github_service):
            first = await service.list_agents(
                project_id=PROJECT_ID,
                owner=OWNER,
                repo=REPO,
                access_token=ACCESS_TOKEN,
            )
            second = await service.list_agents(
                project_id=PROJECT_ID,
                owner=OWNER,
                repo=REPO,
                access_token=ACCESS_TOKEN,
            )

        assert len(first) == 1
        assert len(second) == 1
        mock_github_service.get_directory_contents.assert_awaited_once()

    async def test_list_pending_agents_exposes_unmerged_creation_prs(self, mock_db):
        await _insert_agent_row(
            mock_db,
            agent_id="agent-1",
            slug="reviewer",
            lifecycle_status=AgentStatus.PENDING_PR.value,
            github_pr_number=55,
        )
        service = AgentsService(mock_db)
        mock_github_service = AsyncMock()
        mock_github_service.get_directory_contents.return_value = []

        with patch("src.services.agents.service.github_projects_service", mock_github_service):
            pending = await service.list_pending_agents(
                project_id=PROJECT_ID,
                owner=OWNER,
                repo=REPO,
                access_token=ACCESS_TOKEN,
            )

        assert len(pending) == 1
        assert pending[0].id == "agent-1"
        assert pending[0].status == AgentStatus.PENDING_PR
        assert pending[0].source == AgentSource.LOCAL

    async def test_list_pending_agents_cleans_up_after_merge_to_main(self, mock_db):
        await _insert_agent_row(
            mock_db,
            agent_id="agent-1",
            slug="reviewer",
            lifecycle_status=AgentStatus.PENDING_PR.value,
            github_pr_number=55,
        )
        service = AgentsService(mock_db)
        mock_github_service = AsyncMock()
        mock_github_service.get_directory_contents.return_value = [_repo_entry("reviewer")]

        with patch("src.services.agents.service.github_projects_service", mock_github_service):
            pending = await service.list_pending_agents(
                project_id=PROJECT_ID,
                owner=OWNER,
                repo=REPO,
                access_token=ACCESS_TOKEN,
            )

        assert pending == []
        cursor = await mock_db.execute(
            "SELECT COUNT(*) AS count FROM agent_configs WHERE id = ?",
            ("agent-1",),
        )
        row = await cursor.fetchone()
        assert row["count"] == 0

    async def test_purge_pending_agents_deletes_only_non_active_rows(self, mock_db):
        await _insert_agent_row(
            mock_db,
            agent_id="pending-create",
            name="Reviewer Create",
            slug="reviewer",
            lifecycle_status=AgentStatus.PENDING_PR.value,
        )
        await _insert_agent_row(
            mock_db,
            agent_id="pending-delete",
            name="Reviewer Delete",
            slug="reviewer-delete",
            lifecycle_status=AgentStatus.PENDING_DELETION.value,
        )
        await _insert_agent_row(
            mock_db,
            agent_id="active-local",
            name="Reviewer Active",
            slug="reviewer-active",
            lifecycle_status=AgentStatus.ACTIVE.value,
        )

        service = AgentsService(mock_db)

        result = await service.purge_pending_agents(project_id=PROJECT_ID)

        assert result.success is True
        assert result.deleted_count == 2

        cursor = await mock_db.execute("SELECT id, lifecycle_status FROM agent_configs ORDER BY id")
        rows = await cursor.fetchall()
        assert len(rows) == 1
        assert rows[0]["id"] == "active-local"
        assert rows[0]["lifecycle_status"] == AgentStatus.ACTIVE.value


class TestAgentsServiceBulkModelUpdate:
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        cache.clear()
        yield
        cache.clear()

    async def test_bulk_update_models_includes_pending_pr_agents_and_skips_pending_deletions(
        self,
        mock_db,
    ):
        service = AgentsService(mock_db)
        active_agent = SimpleNamespace(
            id="repo:reviewer",
            slug="reviewer",
            icon_name=None,
            default_model_id="old-model",
            default_model_name="Old Model",
            status=AgentStatus.ACTIVE,
        )
        pending_agent = SimpleNamespace(
            id="pending-1",
            slug="writer",
            icon_name=None,
            default_model_id="old-model",
            default_model_name="Old Model",
            status=AgentStatus.PENDING_PR,
        )
        deleting_agent = SimpleNamespace(
            id="pending-2",
            slug="legacy",
            icon_name=None,
            default_model_id="old-model",
            default_model_name="Old Model",
            status=AgentStatus.PENDING_DELETION,
        )
        body = SimpleNamespace(target_model_id="model-1", target_model_name="GPT-5")

        with (
            patch.object(service, "list_agents", AsyncMock(return_value=[active_agent])),
            patch.object(
                service,
                "list_pending_agents",
                AsyncMock(return_value=[pending_agent, deleting_agent]),
            ),
            patch.object(service, "_save_runtime_preferences", AsyncMock()) as save_preferences,
        ):
            result = await service.bulk_update_models(
                project_id=PROJECT_ID,
                owner=OWNER,
                repo=REPO,
                github_user_id=GITHUB_USER_ID,
                body=body,
                access_token=ACCESS_TOKEN,
            )

        assert result.success is True
        assert result.updated_count == 2
        assert result.failed_count == 0
        assert result.updated_agents == ["reviewer", "writer"]
        assert result.failed_agents == []
        assert save_preferences.await_count == 2
        awaited_agents = [call.kwargs["agent"].slug for call in save_preferences.await_args_list]
        assert awaited_agents == ["reviewer", "writer"]


class TestAgentsServiceUpdate:
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        cache.clear()
        yield
        cache.clear()

    async def test_update_agent_allows_repo_only_agent_and_persists_pending_row(self, mock_db):
        service = AgentsService(mock_db)
        mock_github_service = AsyncMock()
        mock_github_service.get_directory_contents.return_value = [_repo_entry("reviewer")]

        with (
            patch("src.services.agents.service.github_projects_service", mock_github_service),
            patch(
                "src.services.agents.service.commit_files_workflow",
                AsyncMock(return_value=_workflow_result(pr_number=88, issue_number=66)),
            ),
        ):
            result = await service.update_agent(
                project_id=PROJECT_ID,
                owner=OWNER,
                repo=REPO,
                agent_id="repo:reviewer",
                body=SimpleNamespace(
                    name="Reviewer",
                    description=None,
                    icon_name=None,
                    system_prompt="Review pull requests carefully.",
                    tools=["read", "comment", "write"],
                    default_model_id=None,
                    default_model_name=None,
                ),
                access_token=ACCESS_TOKEN,
                github_user_id=GITHUB_USER_ID,
            )

        assert result.pr_number == 88
        assert result.agent.status == AgentStatus.PENDING_PR
        assert result.agent.source == AgentSource.LOCAL
        assert result.agent.tools == ["read", "comment", "write"]

        cursor = await mock_db.execute(
            "SELECT slug, tools, lifecycle_status, github_pr_number FROM agent_configs WHERE slug = ?",
            ("reviewer",),
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row["slug"] == "reviewer"
        assert row["tools"] == '["read", "comment", "write"]'
        assert row["lifecycle_status"] == AgentStatus.PENDING_PR.value
        assert row["github_pr_number"] == 88

    async def test_update_agent_embeds_selected_mcp_servers_into_agent_frontmatter(self, mock_db):
        await _insert_mcp_tool(mock_db, tool_id="tool-123")

        service = AgentsService(mock_db)
        mock_github_service = AsyncMock()
        mock_github_service.get_directory_contents.return_value = [_repo_entry("reviewer")]
        workflow = AsyncMock(return_value=_workflow_result(pr_number=89, issue_number=67))

        with (
            patch("src.services.agents.service.github_projects_service", mock_github_service),
            patch("src.services.agents.service.commit_files_workflow", workflow),
        ):
            result = await service.update_agent(
                project_id=PROJECT_ID,
                owner=OWNER,
                repo=REPO,
                agent_id="repo:reviewer",
                body=SimpleNamespace(
                    name="Reviewer",
                    description=None,
                    icon_name=None,
                    system_prompt="Review pull requests carefully.",
                    tools=["tool-123"],
                    default_model_id=None,
                    default_model_name=None,
                ),
                access_token=ACCESS_TOKEN,
                github_user_id=GITHUB_USER_ID,
            )

        assert result.pr_number == 89
        assert result.agent.tools == ["tool-123"]

        files = workflow.await_args.kwargs["files"]
        agent_file = next(file for file in files if file["path"].endswith(".agent.md"))
        content = agent_file["content"]

        assert "mcp-servers:" in content
        assert "context7:" in content
        assert "url: https://example.com/mcp" in content
        assert "solune-tool-ids: tool-123" in content
        assert "tool-123" not in content.split("mcp-servers:", 1)[0]
