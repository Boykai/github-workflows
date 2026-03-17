"""Unit tests for ProjectsMixin (projects.py)."""

from unittest.mock import AsyncMock, patch

import pytest

from src.models.project import GitHubProject, ProjectType
from src.models.task import Task
from src.services.github_projects.service import GitHubProjectsService


@pytest.fixture
def service():
    svc = GitHubProjectsService()
    svc._graphql = AsyncMock()
    svc._rest = AsyncMock()
    svc._rest_response = AsyncMock()
    svc._cycle_cache = {}
    svc._cycle_cache_hit_count = 0
    return svc


def _make_project_node(
    node_id="PVT_1",
    title="Sprint 1",
    url="https://github.com/orgs/acme/projects/1",
    closed=False,
    *,
    field_id="PVTSSF_1",
    options=None,
):
    """Build a GraphQL project node fixture."""
    if options is None:
        options = [
            {"id": "opt_todo", "name": "Todo", "color": "gray"},
            {"id": "opt_ip", "name": "In Progress", "color": "yellow"},
            {"id": "opt_done", "name": "Done", "color": "green"},
        ]
    return {
        "id": node_id,
        "title": title,
        "url": url,
        "closed": closed,
        "shortDescription": "A project",
        "field": {"id": field_id, "options": options},
        "items": {"totalCount": 10},
    }


# ═══════════════════════════════════════════════════════════════════════════
# list_user_projects
# ═══════════════════════════════════════════════════════════════════════════


class TestListUserProjects:
    @pytest.mark.asyncio
    async def test_success_with_projects(self, service):
        """Should return parsed GitHubProject list for a user."""
        service._graphql.return_value = {
            "user": {
                "projectsV2": {
                    "nodes": [_make_project_node()],
                }
            }
        }

        result = await service.list_user_projects("tok", "alice")

        assert len(result) == 1
        proj = result[0]
        assert isinstance(proj, GitHubProject)
        assert proj.project_id == "PVT_1"
        assert proj.name == "Sprint 1"
        assert proj.type == ProjectType.USER
        assert proj.owner_login == "alice"
        assert len(proj.status_columns) == 3
        assert proj.status_columns[0].name == "Todo"

    @pytest.mark.asyncio
    async def test_empty_when_user_none(self, service):
        """Should return [] when user data is missing."""
        service._graphql.return_value = {"user": None}

        result = await service.list_user_projects("tok", "ghost")

        assert result == []

    @pytest.mark.asyncio
    async def test_excludes_closed_projects(self, service):
        """Closed projects should be filtered out."""
        service._graphql.return_value = {
            "user": {
                "projectsV2": {
                    "nodes": [
                        _make_project_node(node_id="PVT_open", closed=False),
                        _make_project_node(node_id="PVT_closed", closed=True),
                    ]
                }
            }
        }

        result = await service.list_user_projects("tok", "alice")

        assert len(result) == 1
        assert result[0].project_id == "PVT_open"

    @pytest.mark.asyncio
    async def test_default_status_columns_when_no_field(self, service):
        """Projects without a status field should receive default columns."""
        node = _make_project_node()
        node["field"] = None
        service._graphql.return_value = {"user": {"projectsV2": {"nodes": [node]}}}

        result = await service.list_user_projects("tok", "alice")

        assert len(result) == 1
        # Default columns come from DEFAULT_STATUS_COLUMNS
        assert len(result[0].status_columns) >= 2


# ═══════════════════════════════════════════════════════════════════════════
# list_org_projects
# ═══════════════════════════════════════════════════════════════════════════


class TestListOrgProjects:
    @pytest.mark.asyncio
    async def test_success_with_projects(self, service):
        """Should return parsed GitHubProject list for an org."""
        service._graphql.return_value = {
            "organization": {
                "projectsV2": {
                    "nodes": [_make_project_node(title="Org Board")],
                }
            }
        }

        result = await service.list_org_projects("tok", "acme")

        assert len(result) == 1
        assert result[0].name == "Org Board"
        assert result[0].type == ProjectType.ORGANIZATION
        assert result[0].owner_login == "acme"

    @pytest.mark.asyncio
    async def test_empty_when_org_none(self, service):
        """Should return [] when organization data is missing."""
        service._graphql.return_value = {"organization": None}

        result = await service.list_org_projects("tok", "nope")

        assert result == []

    @pytest.mark.asyncio
    async def test_excludes_closed_projects(self, service):
        """Closed org projects should be filtered out."""
        service._graphql.return_value = {
            "organization": {
                "projectsV2": {
                    "nodes": [
                        _make_project_node(closed=False),
                        _make_project_node(node_id="PVT_2", closed=True),
                    ]
                }
            }
        }

        result = await service.list_org_projects("tok", "acme")

        assert len(result) == 1


# ═══════════════════════════════════════════════════════════════════════════
# get_project_items
# ═══════════════════════════════════════════════════════════════════════════


class TestGetProjectItems:
    @pytest.mark.asyncio
    async def test_success_single_page(self, service):
        """Should return tasks from a single page of results."""
        service._graphql.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_1",
                            "content": {
                                "id": "I_1",
                                "title": "Task one",
                                "body": "desc",
                                "number": 10,
                                "repository": {
                                    "owner": {"login": "o"},
                                    "name": "r",
                                },
                                "labels": {"nodes": [{"name": "bug", "color": "d73a4a"}]},
                            },
                            "fieldValueByName": {
                                "name": "In Progress",
                                "optionId": "opt_ip",
                            },
                        }
                    ],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }

        with patch("src.services.github_projects.projects.save_done_items", new_callable=AsyncMock):
            result = await service.get_project_items("tok", "PVT_1")

        assert len(result) == 1
        assert isinstance(result[0], Task)
        assert result[0].title == "Task one"
        assert result[0].status == "In Progress"
        assert result[0].repository_owner == "o"
        assert result[0].repository_name == "r"

    @pytest.mark.asyncio
    async def test_pagination_two_pages(self, service):
        """Should follow pagination cursors to collect all items."""
        page1 = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_1",
                            "content": {
                                "id": "I_1",
                                "title": "Task A",
                                "number": 1,
                                "repository": {"owner": {"login": "o"}, "name": "r"},
                            },
                            "fieldValueByName": {"name": "Todo", "optionId": "opt_todo"},
                        }
                    ],
                    "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                }
            }
        }
        page2 = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_2",
                            "content": {
                                "id": "I_2",
                                "title": "Task B",
                                "number": 2,
                                "repository": {"owner": {"login": "o"}, "name": "r"},
                            },
                            "fieldValueByName": {"name": "Done", "optionId": "opt_done"},
                        }
                    ],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }
        service._graphql.side_effect = [page1, page2]

        with patch("src.services.github_projects.projects.save_done_items", new_callable=AsyncMock):
            result = await service.get_project_items("tok", "PVT_1")

        assert len(result) == 2
        assert result[0].title == "Task A"
        assert result[1].title == "Task B"

    @pytest.mark.asyncio
    async def test_skips_null_items(self, service):
        """Null items and items without content should be skipped."""
        service._graphql.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        None,
                        {"id": "PVTI_1", "content": None, "fieldValueByName": {}},
                        {
                            "id": "PVTI_2",
                            "content": {
                                "id": "I_2",
                                "title": "Real task",
                                "number": 3,
                                "repository": {"owner": {"login": "o"}, "name": "r"},
                            },
                            "fieldValueByName": {"name": "Todo", "optionId": "opt_todo"},
                        },
                    ],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }

        with patch("src.services.github_projects.projects.save_done_items", new_callable=AsyncMock):
            result = await service.get_project_items("tok", "PVT_1")

        assert len(result) == 1
        assert result[0].title == "Real task"

    @pytest.mark.asyncio
    async def test_returns_cached_on_second_call(self, service):
        """Results should be cached per cycle."""
        service._graphql.return_value = {
            "node": {
                "items": {
                    "nodes": [],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }

        with patch("src.services.github_projects.projects.save_done_items", new_callable=AsyncMock):
            first = await service.get_project_items("tok", "PVT_1")
            second = await service.get_project_items("tok", "PVT_1")

        assert first is second
        assert service._graphql.call_count == 1


# ═══════════════════════════════════════════════════════════════════════════
# update_project_item_field
# ═══════════════════════════════════════════════════════════════════════════


class TestUpdateProjectItemField:
    @pytest.fixture
    def fields_data(self):
        return {
            "Priority": {
                "id": "F_priority",
                "dataType": "SINGLE_SELECT",
                "options": [
                    {"name": "High", "id": "opt_high"},
                    {"name": "Low", "id": "opt_low"},
                ],
            },
            "Estimate": {
                "id": "F_estimate",
                "dataType": "NUMBER",
                "options": [],
            },
            "Start date": {
                "id": "F_start",
                "dataType": "DATE",
                "options": [],
            },
            "Notes": {
                "id": "F_notes",
                "dataType": "TEXT",
                "options": [],
            },
        }

    @pytest.mark.asyncio
    async def test_success_single_select(self, service, fields_data):
        """Should pick the correct option and call the select mutation."""
        service.get_project_fields = AsyncMock(return_value=fields_data)
        service._graphql.return_value = {
            "updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_1"}}
        }

        result = await service.update_project_item_field(
            "tok", "PVT_1", "PVTI_1", "Priority", "High"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_success_number_field(self, service, fields_data):
        """Should call the number mutation."""
        service.get_project_fields = AsyncMock(return_value=fields_data)
        service._graphql.return_value = {}

        result = await service.update_project_item_field("tok", "PVT_1", "PVTI_1", "Estimate", 5.0)
        assert result is True

    @pytest.mark.asyncio
    async def test_success_date_field(self, service, fields_data):
        """Should call the date mutation."""
        service.get_project_fields = AsyncMock(return_value=fields_data)
        service._graphql.return_value = {}

        result = await service.update_project_item_field(
            "tok", "PVT_1", "PVTI_1", "Start date", "2025-07-01"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_success_text_field(self, service, fields_data):
        """Should call the text mutation."""
        service.get_project_fields = AsyncMock(return_value=fields_data)
        service._graphql.return_value = {}

        result = await service.update_project_item_field("tok", "PVT_1", "PVTI_1", "Notes", "hello")
        assert result is True

    @pytest.mark.asyncio
    async def test_failure_field_not_found(self, service):
        """Should return False when the field name doesn't exist."""
        service.get_project_fields = AsyncMock(return_value={})

        result = await service.update_project_item_field(
            "tok", "PVT_1", "PVTI_1", "NonExistent", "value"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_failure_option_not_found(self, service, fields_data):
        """Should return False when the option value doesn't exist for a select field."""
        service.get_project_fields = AsyncMock(return_value=fields_data)

        result = await service.update_project_item_field(
            "tok", "PVT_1", "PVTI_1", "Priority", "Critical"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_failure_exception(self, service, fields_data):
        """Should return False on exception."""
        service.get_project_fields = AsyncMock(side_effect=RuntimeError("boom"))

        result = await service.update_project_item_field(
            "tok", "PVT_1", "PVTI_1", "Priority", "High"
        )
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# _detect_changes (detect_status_changes)
# ═══════════════════════════════════════════════════════════════════════════


def _make_task(item_id: str, title: str = "T", status: str = "Todo") -> Task:
    return Task(
        project_id="PVT_1",
        github_item_id=item_id,
        title=title,
        status=status,
        status_option_id="opt",
    )


class TestDetectChanges:
    def test_task_added(self, service):
        old = []
        new = [_make_task("A")]

        changes = service._detect_changes(old, new)

        assert len(changes) == 1
        assert changes[0]["type"] == "task_created"
        assert changes[0]["task_id"] == "A"

    def test_task_removed(self, service):
        old = [_make_task("A")]
        new = []

        changes = service._detect_changes(old, new)

        assert len(changes) == 1
        assert changes[0]["type"] == "task_deleted"
        assert changes[0]["task_id"] == "A"

    def test_status_changed(self, service):
        old = [_make_task("A", status="Todo")]
        new = [_make_task("A", status="In Progress")]

        changes = service._detect_changes(old, new)

        status_changes = [c for c in changes if c["type"] == "status_changed"]
        assert len(status_changes) == 1
        assert status_changes[0]["old_status"] == "Todo"
        assert status_changes[0]["new_status"] == "In Progress"

    def test_title_changed(self, service):
        old = [_make_task("A", title="Old title")]
        new = [_make_task("A", title="New title")]

        changes = service._detect_changes(old, new)

        title_changes = [c for c in changes if c["type"] == "title_changed"]
        assert len(title_changes) == 1
        assert title_changes[0]["old_title"] == "Old title"
        assert title_changes[0]["new_title"] == "New title"

    def test_no_changes(self, service):
        tasks = [_make_task("A", title="Same", status="Todo")]
        changes = service._detect_changes(tasks, tasks)

        assert changes == []

    def test_mixed_add_remove_change(self, service):
        old = [_make_task("A", status="Todo"), _make_task("B", status="Todo")]
        new = [_make_task("A", status="Done"), _make_task("C", status="Todo")]

        changes = service._detect_changes(old, new)

        types = {c["type"] for c in changes}
        assert "status_changed" in types  # A: Todo → Done
        assert "task_deleted" in types  # B removed
        assert "task_created" in types  # C added


# ═══════════════════════════════════════════════════════════════════════════
# get_project_repository
# ═══════════════════════════════════════════════════════════════════════════


class TestGetProjectRepository:
    @pytest.mark.asyncio
    async def test_success(self, service):
        """Should extract owner/repo from the first item with a repository."""
        service._graphql.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "content": {
                                "repository": {
                                    "owner": {"login": "acme"},
                                    "name": "web-app",
                                }
                            }
                        }
                    ]
                }
            }
        }

        result = await service.get_project_repository("tok", "PVT_1")

        assert result == ("acme", "web-app")

    @pytest.mark.asyncio
    async def test_missing_repository_data(self, service):
        """Should return None when no items have repository info."""
        service._graphql.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {"content": {}},
                    ]
                }
            }
        }

        result = await service.get_project_repository("tok", "PVT_1")
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_items(self, service):
        """Should return None when there are no items."""
        service._graphql.return_value = {"node": {"items": {"nodes": []}}}

        result = await service.get_project_repository("tok", "PVT_1")
        assert result is None

    @pytest.mark.asyncio
    async def test_skips_items_with_empty_owner(self, service):
        """Items with empty owner or name should be skipped."""
        service._graphql.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "content": {
                                "repository": {
                                    "owner": {"login": ""},
                                    "name": "web-app",
                                }
                            }
                        },
                        {
                            "content": {
                                "repository": {
                                    "owner": {"login": "acme"},
                                    "name": "real-repo",
                                }
                            }
                        },
                    ]
                }
            }
        }

        result = await service.get_project_repository("tok", "PVT_1")
        assert result == ("acme", "real-repo")


# ═══════════════════════════════════════════════════════════════════════════
# create_draft_item
# ═══════════════════════════════════════════════════════════════════════════


class TestCreateDraftItem:
    @pytest.mark.asyncio
    async def test_success(self, service):
        """Should return the created item ID."""
        service._graphql.return_value = {
            "addProjectV2DraftIssue": {"projectItem": {"id": "PVTI_new"}}
        }

        result = await service.create_draft_item("tok", "PVT_1", "New task", "body")

        assert result == "PVTI_new"

    @pytest.mark.asyncio
    async def test_returns_empty_string_on_missing_data(self, service):
        """Should return '' when response is missing expected keys."""
        service._graphql.return_value = {"addProjectV2DraftIssue": {}}

        result = await service.create_draft_item("tok", "PVT_1", "New task")

        assert result == ""
