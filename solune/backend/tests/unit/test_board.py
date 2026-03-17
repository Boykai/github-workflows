"""Unit tests for board API endpoints, models, and BoardMixin service methods."""

from unittest.mock import AsyncMock, patch

import pytest

from src.models.board import (
    Assignee,
    BoardColumn,
    BoardDataResponse,
    BoardItem,
    BoardProject,
    BoardProjectListResponse,
    ContentType,
    CustomFieldValue,
    Label,
    LinkedPR,
    PRState,
    Repository,
    StatusColor,
    StatusField,
    StatusOption,
)
from src.services.github_projects import GitHubProjectsService
from src.services.github_projects.board import BoardMixin

TOKEN = "ghp_test_token"
USERNAME = "octocat"
PROJECT_ID = "PVT_kwDOTest"


# ── Helpers ──────────────────────────────────────────────────────────


def _make_graphql_project_node(
    *,
    node_id="PVT_1",
    title="Board",
    url="https://github.com/users/octocat/projects/1",
    closed=False,
    short_description="desc",
    field=None,
):
    """Build a minimal projectsV2 node for list_board_projects."""
    if field is None:
        field = {
            "id": "PVTSSF_status",
            "options": [
                {"id": "opt_todo", "name": "Todo", "color": "GRAY"},
                {"id": "opt_done", "name": "Done", "color": "GREEN", "description": "Finished"},
            ],
        }
    return {
        "id": node_id,
        "title": title,
        "url": url,
        "closed": closed,
        "shortDescription": short_description,
        "field": field,
    }


def _board_models_dict():
    """Return the board_models dict expected by _parse_board_item."""
    return {
        "Assignee": Assignee,
        "BoardItem": BoardItem,
        "ContentType": ContentType,
        "CustomFieldValue": CustomFieldValue,
        "Label": Label,
        "LinkedPR": LinkedPR,
        "PRState": PRState,
        "Repository": Repository,
    }


def _make_item_node(
    *,
    item_id="PVTI_1",
    content_id="I_1",
    title="Fix bug",
    number=42,
    state=None,
    status_name="Todo",
    status_option_id="opt_todo",
    assignees=None,
    labels=None,
    repo_owner="octocat",
    repo_name="my-repo",
    linked_prs=None,
    priority=None,
    size=None,
    estimate=None,
    issue_type=None,
    milestone=None,
    created_at="2024-01-01T00:00:00Z",
    updated_at="2024-01-02T00:00:00Z",
):
    """Build a GraphQL item node for _parse_board_item."""
    content = {
        "id": content_id,
        "title": title,
        "number": number,
        "url": f"https://github.com/{repo_owner}/{repo_name}/issues/{number}",
        "body": "Some body",
        "createdAt": created_at,
        "updatedAt": updated_at,
        "assignees": {"nodes": assignees or []},
        "labels": {"nodes": labels or []},
        "repository": {"owner": {"login": repo_owner}, "name": repo_name},
        "timelineItems": {"nodes": linked_prs or []},
    }
    if state is not None:
        content["state"] = state
    if issue_type is not None:
        content["issueType"] = {"name": issue_type}
    if milestone is not None:
        content["milestone"] = {"title": milestone}

    field_values_nodes = []
    field_values_nodes.append(
        {
            "field": {"name": "Status"},
            "name": status_name,
            "optionId": status_option_id,
        }
    )
    if priority:
        field_values_nodes.append(
            {
                "field": {"name": "Priority"},
                "name": priority,
                "color": "ORANGE",
            }
        )
    if size:
        field_values_nodes.append(
            {
                "field": {"name": "Size"},
                "name": size,
                "color": "BLUE",
            }
        )
    if estimate is not None:
        field_values_nodes.append(
            {
                "field": {"name": "Estimate"},
                "number": estimate,
            }
        )

    return {
        "id": item_id,
        "content": content,
        "fieldValues": {"nodes": field_values_nodes},
    }


def _make_get_board_data_response(items, *, has_next_page=False, end_cursor=None):
    """Build a get_board_data GraphQL response."""
    return {
        "node": {
            "title": "Sprint Board",
            "shortDescription": "The board",
            "url": "https://github.com/users/octocat/projects/1",
            "owner": {"login": "octocat"},
            "field": {
                "id": "PVTSSF_status",
                "options": [
                    {"id": "opt_todo", "name": "Todo", "color": "GRAY"},
                    {"id": "opt_done", "name": "Done", "color": "GREEN"},
                ],
            },
            "items": {
                "nodes": items,
                "pageInfo": {
                    "hasNextPage": has_next_page,
                    "endCursor": end_cursor,
                },
            },
        }
    }


# ============ Model Tests ============


class TestBoardModels:
    """Tests for board Pydantic models."""

    def test_status_color_enum_values(self):
        """StatusColor enum should contain all GitHub predefined colors."""
        expected = {"GRAY", "BLUE", "GREEN", "YELLOW", "ORANGE", "RED", "PINK", "PURPLE"}
        actual = {c.value for c in StatusColor}
        assert actual == expected

    def test_content_type_enum_values(self):
        """ContentType enum should have issue, draft_issue, pull_request."""
        expected = {"issue", "draft_issue", "pull_request"}
        actual = {c.value for c in ContentType}
        assert actual == expected

    def test_pr_state_enum_values(self):
        """PRState enum should have open, closed, merged."""
        expected = {"open", "closed", "merged"}
        actual = {c.value for c in PRState}
        assert actual == expected

    def test_status_option_creation(self):
        """Should create a StatusOption with all fields."""
        opt = StatusOption(
            option_id="f75ad846",
            name="In Progress",
            color=StatusColor.YELLOW,
            description="Work in progress",
        )
        assert opt.option_id == "f75ad846"
        assert opt.name == "In Progress"
        assert opt.color == StatusColor.YELLOW
        assert opt.description == "Work in progress"

    def test_status_option_optional_description(self):
        """StatusOption description should be optional."""
        opt = StatusOption(
            option_id="abc123",
            name="Todo",
            color=StatusColor.GRAY,
        )
        assert opt.description is None

    def test_board_project_creation(self):
        """Should create a BoardProject with status field."""
        project = BoardProject(
            project_id="PVT_kwDOBWNFuc4AAgab",
            name="Development Board",
            description="Sprint board",
            url="https://github.com/users/octocat/projects/1",
            owner_login="octocat",
            status_field=StatusField(
                field_id="PVTSSF_lADOBWNFuc4AAqzs",
                options=[
                    StatusOption(option_id="opt1", name="Todo", color=StatusColor.GRAY),
                    StatusOption(option_id="opt2", name="Done", color=StatusColor.GREEN),
                ],
            ),
        )
        assert project.project_id == "PVT_kwDOBWNFuc4AAgab"
        assert project.name == "Development Board"
        assert len(project.status_field.options) == 2

    def test_board_item_with_all_fields(self):
        """Should create a BoardItem with all metadata fields."""
        item = BoardItem(
            item_id="PVTI_abc123",
            content_id="I_xyz789",
            content_type=ContentType.ISSUE,
            title="Add project board feature",
            number=164,
            repository=Repository(owner="octocat", name="github-workflows"),
            url="https://github.com/octocat/github-workflows/issues/164",
            body="Implement the board feature",
            status="In Progress",
            status_option_id="opt2",
            assignees=[
                Assignee(
                    login="octocat",
                    avatar_url="https://avatars.githubusercontent.com/u/583231",
                ),
            ],
            priority=CustomFieldValue(name="P1", color=StatusColor.RED),
            size=CustomFieldValue(name="M"),
            estimate=5.0,
            linked_prs=[
                LinkedPR(
                    pr_id="PR_abc",
                    number=165,
                    title="Implement board UI",
                    state=PRState.OPEN,
                    url="https://github.com/octocat/repo/pull/165",
                ),
            ],
        )
        assert item.item_id == "PVTI_abc123"
        assert item.content_type == ContentType.ISSUE
        assert item.number == 164
        assert len(item.assignees) == 1
        assert item.priority.name == "P1"
        assert item.estimate == 5.0
        assert len(item.linked_prs) == 1

    def test_board_item_draft_issue(self):
        """Draft issues should have nullable fields."""
        item = BoardItem(
            item_id="PVTI_draft",
            content_type=ContentType.DRAFT_ISSUE,
            title="Draft task",
            status="Todo",
            status_option_id="opt1",
        )
        assert item.content_id is None
        assert item.number is None
        assert item.repository is None
        assert item.url is None
        assert item.body is None
        assert item.priority is None
        assert item.size is None
        assert item.estimate is None
        assert item.assignees == []
        assert item.linked_prs == []

    def test_board_column_defaults(self):
        """BoardColumn should have sensible defaults."""
        col = BoardColumn(
            status=StatusOption(option_id="opt1", name="Todo", color=StatusColor.GRAY),
        )
        assert col.items == []
        assert col.item_count == 0
        assert col.estimate_total == 0.0

    def test_board_column_with_items(self):
        """BoardColumn should calculate item_count and estimate_total."""
        items = [
            BoardItem(
                item_id="1",
                content_type=ContentType.ISSUE,
                title="Task 1",
                status="Todo",
                status_option_id="opt1",
                estimate=3.0,
            ),
            BoardItem(
                item_id="2",
                content_type=ContentType.ISSUE,
                title="Task 2",
                status="Todo",
                status_option_id="opt1",
                estimate=5.0,
            ),
        ]
        col = BoardColumn(
            status=StatusOption(option_id="opt1", name="Todo", color=StatusColor.GRAY),
            items=items,
            item_count=2,
            estimate_total=8.0,
        )
        assert col.item_count == 2
        assert col.estimate_total == 8.0

    def test_board_data_response(self):
        """Should create a complete BoardDataResponse."""
        project = BoardProject(
            project_id="PVT_test",
            name="Test Project",
            url="https://github.com/test/project",
            owner_login="test",
            status_field=StatusField(
                field_id="SF_test",
                options=[
                    StatusOption(option_id="opt1", name="Todo", color=StatusColor.GRAY),
                ],
            ),
        )
        columns = [
            BoardColumn(
                status=StatusOption(option_id="opt1", name="Todo", color=StatusColor.GRAY),
                items=[],
                item_count=0,
                estimate_total=0.0,
            ),
        ]
        response = BoardDataResponse(project=project, columns=columns)
        assert response.project.name == "Test Project"
        assert len(response.columns) == 1

    def test_board_project_list_response(self):
        """Should create a BoardProjectListResponse."""
        project = BoardProject(
            project_id="PVT_test",
            name="Test",
            url="https://github.com/test",
            owner_login="test",
            status_field=StatusField(field_id="SF_1", options=[]),
        )
        response = BoardProjectListResponse(projects=[project])
        assert len(response.projects) == 1

    def test_custom_field_value_optional_color(self):
        """CustomFieldValue color should be optional."""
        val = CustomFieldValue(name="P2")
        assert val.color is None

    def test_linked_pr_creation(self):
        """Should create LinkedPR with all required fields."""
        pr = LinkedPR(
            pr_id="PR_test",
            number=42,
            title="Fix bug",
            state=PRState.MERGED,
            url="https://github.com/test/repo/pull/42",
        )
        assert pr.number == 42
        assert pr.state == PRState.MERGED


class TestBuildBoardColumnsSubIssueFiltering:
    """_build_board_columns filters sub-issues using both ID matching and label detection."""

    @staticmethod
    def _make_board_item(
        item_id: str,
        content_id: str,
        status_option_id: str,
        labels: list | None = None,
        sub_issues: list | None = None,
        **kwargs,
    ) -> BoardItem:
        from src.models.board import Label, SubIssue

        return BoardItem(
            item_id=item_id,
            content_id=content_id,
            content_type=ContentType.ISSUE,
            title=kwargs.get("title", f"Issue {item_id}"),
            status=kwargs.get("status", "In Progress"),
            status_option_id=status_option_id,
            labels=[Label(id=f"L_{lbl}", name=lbl, color="ededed") for lbl in (labels or [])],
            sub_issues=[
                SubIssue(id=si, number=i + 1, title=f"Sub {si}", url="", state="open")
                for i, si in enumerate(sub_issues or [])
            ],
        )

    def test_filters_sub_issue_by_label(self):
        """Items with the 'sub-issue' label are excluded even if not in any parent's sub_issues."""
        from src.services.github_projects.board import BoardMixin

        opt = StatusOption(option_id="opt1", name="In Progress", color="YELLOW")
        parent = self._make_board_item("P1", "C_P1", "opt1", sub_issues=[])
        sub = self._make_board_item("S1", "C_S1", "opt1", labels=["sub-issue"])

        columns = BoardMixin._build_board_columns(
            [parent, sub],
            [opt],
            {
                "BoardColumn": BoardColumn,
                "StatusOption": StatusOption,
                "StatusColor": StatusColor,
            },
        )

        assert len(columns) == 1
        assert len(columns[0].items) == 1
        assert columns[0].items[0].item_id == "P1"

    def test_filters_sub_issue_by_parent_reference(self):
        """Items referenced in a parent's sub_issues list are excluded (legacy behaviour)."""
        from src.services.github_projects.board import BoardMixin

        opt = StatusOption(option_id="opt1", name="In Progress", color="YELLOW")
        parent = self._make_board_item("P1", "C_P1", "opt1", sub_issues=["C_S1"])
        sub = self._make_board_item("S1", "C_S1", "opt1")

        columns = BoardMixin._build_board_columns(
            [parent, sub],
            [opt],
            {
                "BoardColumn": BoardColumn,
                "StatusOption": StatusOption,
                "StatusColor": StatusColor,
            },
        )

        assert len(columns[0].items) == 1
        assert columns[0].items[0].item_id == "P1"

    def test_keeps_parent_issues_without_sub_issue_label(self):
        """Parent issues without the sub-issue label remain on the board."""
        from src.services.github_projects.board import BoardMixin

        opt = StatusOption(option_id="opt1", name="Todo", color="GRAY")
        parent = self._make_board_item("P1", "C_P1", "opt1", labels=["feature", "active"])

        columns = BoardMixin._build_board_columns(
            [parent],
            [opt],
            {
                "BoardColumn": BoardColumn,
                "StatusOption": StatusOption,
                "StatusColor": StatusColor,
            },
        )

        assert len(columns[0].items) == 1


# =====================================================================
# list_board_projects
# =====================================================================


class TestListBoardProjects:
    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_success_with_projects(self, service):
        """Should return BoardProject list from GraphQL response."""
        graphql_data = {
            "user": {
                "projectsV2": {
                    "nodes": [
                        _make_graphql_project_node(node_id="PVT_1", title="Sprint Board"),
                        _make_graphql_project_node(node_id="PVT_2", title="Backlog"),
                    ]
                }
            }
        }
        with patch.object(service, "_graphql", new_callable=AsyncMock, return_value=graphql_data):
            result = await service.list_board_projects(TOKEN, USERNAME)

        assert len(result) == 2
        assert isinstance(result[0], BoardProject)
        assert result[0].project_id == "PVT_1"
        assert result[0].name == "Sprint Board"
        assert result[0].owner_login == USERNAME
        assert len(result[0].status_field.options) == 2
        assert result[0].status_field.options[0].name == "Todo"
        assert result[0].status_field.options[1].description == "Finished"

    @pytest.mark.asyncio
    async def test_empty_when_user_is_none(self, service):
        """Should return empty list when GraphQL returns no user data."""
        graphql_data = {"user": None}
        with patch.object(service, "_graphql", new_callable=AsyncMock, return_value=graphql_data):
            result = await service.list_board_projects(TOKEN, USERNAME)

        assert result == []

    @pytest.mark.asyncio
    async def test_empty_when_no_user_key(self, service):
        """Should return empty list when response has no 'user' key."""
        graphql_data = {}
        with patch.object(service, "_graphql", new_callable=AsyncMock, return_value=graphql_data):
            result = await service.list_board_projects(TOKEN, USERNAME)

        assert result == []

    @pytest.mark.asyncio
    async def test_excludes_closed_projects(self, service):
        """Closed projects should be filtered out."""
        graphql_data = {
            "user": {
                "projectsV2": {
                    "nodes": [
                        _make_graphql_project_node(node_id="PVT_open", closed=False),
                        _make_graphql_project_node(node_id="PVT_closed", closed=True),
                    ]
                }
            }
        }
        with patch.object(service, "_graphql", new_callable=AsyncMock, return_value=graphql_data):
            result = await service.list_board_projects(TOKEN, USERNAME)

        assert len(result) == 1
        assert result[0].project_id == "PVT_open"

    @pytest.mark.asyncio
    async def test_excludes_projects_without_status_field(self, service):
        """Projects that lack a Status field should be skipped."""
        graphql_data = {
            "user": {
                "projectsV2": {
                    "nodes": [
                        _make_graphql_project_node(node_id="PVT_with"),
                        _make_graphql_project_node(node_id="PVT_without"),
                    ]
                }
            }
        }
        graphql_data["user"]["projectsV2"]["nodes"][1]["field"] = None

        with patch.object(service, "_graphql", new_callable=AsyncMock, return_value=graphql_data):
            result = await service.list_board_projects(TOKEN, USERNAME)

        assert len(result) == 1
        assert result[0].project_id == "PVT_with"

    @pytest.mark.asyncio
    async def test_skips_none_nodes(self, service):
        """None entries in the nodes list should be skipped."""
        graphql_data = {
            "user": {
                "projectsV2": {
                    "nodes": [
                        None,
                        _make_graphql_project_node(node_id="PVT_real"),
                    ]
                }
            }
        }
        with patch.object(service, "_graphql", new_callable=AsyncMock, return_value=graphql_data):
            result = await service.list_board_projects(TOKEN, USERNAME)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_status_option_default_color(self, service):
        """Options without a color should default to GRAY."""
        node = _make_graphql_project_node()
        node["field"]["options"][0].pop("color")
        graphql_data = {"user": {"projectsV2": {"nodes": [node]}}}

        with patch.object(service, "_graphql", new_callable=AsyncMock, return_value=graphql_data):
            result = await service.list_board_projects(TOKEN, USERNAME)

        assert result[0].status_field.options[0].color == StatusColor.GRAY


# =====================================================================
# _parse_board_item
# =====================================================================


class TestParseBoardItem:
    """Tests for BoardMixin._parse_board_item static method."""

    def test_valid_issue_item(self):
        """Should parse a standard issue item with all fields."""
        node = _make_item_node(
            assignees=[{"login": "alice", "avatarUrl": "https://avatar/alice"}],
            labels=[{"id": "L1", "name": "bug", "color": "d73a4a"}],
            priority="P1",
            estimate=3.0,
            issue_type="Bug",
            milestone="v1.0",
        )
        result = BoardMixin._parse_board_item(node, _board_models_dict())

        assert isinstance(result, BoardItem)
        assert result.item_id == "PVTI_1"
        assert result.content_id == "I_1"
        assert result.title == "Fix bug"
        assert result.number == 42
        assert result.content_type == ContentType.ISSUE
        assert result.status == "Todo"
        assert result.status_option_id == "opt_todo"
        assert len(result.assignees) == 1
        assert result.assignees[0].login == "alice"
        assert len(result.labels) == 1
        assert result.labels[0].name == "bug"
        assert result.priority is not None
        assert result.priority.name == "P1"
        assert result.estimate == 3.0
        assert result.issue_type == "Bug"
        assert result.milestone == "v1.0"
        assert result.repository is not None
        assert result.repository.owner == "octocat"

    def test_pull_request_item(self):
        """Items with number + state should be detected as PULL_REQUEST."""
        node = _make_item_node(state="OPEN")
        result = BoardMixin._parse_board_item(node, _board_models_dict())

        assert result is not None
        assert result.content_type == ContentType.PULL_REQUEST

    def test_draft_issue_item(self):
        """Items without a number should be detected as DRAFT_ISSUE."""
        node = _make_item_node()
        node["content"]["number"] = None
        result = BoardMixin._parse_board_item(node, _board_models_dict())

        assert result is not None
        assert result.content_type == ContentType.DRAFT_ISSUE

    def test_none_item_returns_none(self):
        """Passing None should return None."""
        result = BoardMixin._parse_board_item(None, _board_models_dict())
        assert result is None

    def test_empty_dict_returns_none(self):
        """Passing an empty dict (no content) should return None."""
        result = BoardMixin._parse_board_item({}, _board_models_dict())
        assert result is None

    def test_empty_content_returns_none(self):
        """Item with content=None or content={} should return None."""
        result = BoardMixin._parse_board_item({"content": None}, _board_models_dict())
        assert result is None

        result = BoardMixin._parse_board_item({"content": {}}, _board_models_dict())
        assert result is None

    def test_missing_assignees(self):
        """Items with no assignees should have an empty list."""
        node = _make_item_node()
        result = BoardMixin._parse_board_item(node, _board_models_dict())

        assert result is not None
        assert result.assignees == []

    def test_missing_labels(self):
        """Items with no labels should have an empty list."""
        node = _make_item_node()
        result = BoardMixin._parse_board_item(node, _board_models_dict())

        assert result is not None
        assert result.labels == []

    def test_no_status_defaults_to_no_status(self):
        """If no Status field value exists, status defaults to 'No Status'."""
        node = _make_item_node()
        node["fieldValues"]["nodes"] = []
        result = BoardMixin._parse_board_item(node, _board_models_dict())

        assert result is not None
        assert result.status == "No Status"

    def test_linked_prs_parsed(self):
        """Linked PRs from timeline items should be parsed."""
        pr_event = {
            "subject": {
                "id": "PR_1",
                "number": 100,
                "title": "Fix it",
                "state": "MERGED",
                "url": "https://github.com/octocat/repo/pull/100",
            }
        }
        node = _make_item_node(linked_prs=[pr_event])
        result = BoardMixin._parse_board_item(node, _board_models_dict())

        assert result is not None
        assert len(result.linked_prs) == 1
        assert result.linked_prs[0].pr_id == "PR_1"
        assert result.linked_prs[0].state == PRState.MERGED

    def test_linked_prs_deduplication(self):
        """Duplicate PR IDs from timeline events should be deduplicated."""
        pr_event = {
            "subject": {
                "id": "PR_1",
                "number": 100,
                "title": "Fix it",
                "state": "OPEN",
                "url": "https://github.com/octocat/repo/pull/100",
            }
        }
        node = _make_item_node(linked_prs=[pr_event, pr_event])
        result = BoardMixin._parse_board_item(node, _board_models_dict())

        assert result is not None
        assert len(result.linked_prs) == 1

    def test_linked_pr_source_key(self):
        """PR data from 'source' key (not 'subject') should also be parsed."""
        pr_event = {
            "source": {
                "id": "PR_2",
                "number": 200,
                "title": "PR from source",
                "state": "CLOSED",
                "url": "https://github.com/octocat/repo/pull/200",
            }
        }
        node = _make_item_node(linked_prs=[pr_event])
        result = BoardMixin._parse_board_item(node, _board_models_dict())

        assert result is not None
        assert len(result.linked_prs) == 1
        assert result.linked_prs[0].state == PRState.CLOSED

    def test_no_repository(self):
        """Items without repository data should have repository=None."""
        node = _make_item_node()
        node["content"]["repository"] = None
        result = BoardMixin._parse_board_item(node, _board_models_dict())

        assert result is not None
        assert result.repository is None

    def test_size_custom_field(self):
        """Size custom field should be parsed."""
        node = _make_item_node(size="Large")
        result = BoardMixin._parse_board_item(node, _board_models_dict())

        assert result is not None
        assert result.size is not None
        assert result.size.name == "Large"

    def test_none_field_values_skipped(self):
        """None entries in fieldValues nodes should be skipped gracefully."""
        node = _make_item_node()
        node["fieldValues"]["nodes"].insert(0, None)
        result = BoardMixin._parse_board_item(node, _board_models_dict())

        assert result is not None
        assert result.status == "Todo"

    def test_no_milestone(self):
        """Items without a milestone should have milestone=None."""
        node = _make_item_node()
        result = BoardMixin._parse_board_item(node, _board_models_dict())

        assert result is not None
        assert result.milestone is None

    def test_no_issue_type(self):
        """Items without an issueType should have issue_type=None."""
        node = _make_item_node()
        result = BoardMixin._parse_board_item(node, _board_models_dict())

        assert result is not None
        assert result.issue_type is None


# =====================================================================
# get_board_data
# =====================================================================


class TestGetBoardData:
    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_success_single_page(self, service):
        """Should return BoardDataResponse with parsed items."""
        item_node = _make_item_node(status_option_id="opt_todo")
        graphql_resp = _make_get_board_data_response([item_node])

        with (
            patch.object(service, "_graphql", new_callable=AsyncMock, return_value=graphql_resp),
            patch.object(service, "get_sub_issues", new_callable=AsyncMock, return_value=[]),
            patch.object(
                service, "_reconcile_board_items", new_callable=AsyncMock, return_value=[]
            ),
            patch("src.services.github_projects.board.save_done_items", new_callable=AsyncMock),
        ):
            result = await service.get_board_data(TOKEN, PROJECT_ID)

        assert isinstance(result, BoardDataResponse)
        assert result.project.name == "Sprint Board"
        assert result.project.project_id == PROJECT_ID
        todo_col = next((c for c in result.columns if c.status.name == "Todo"), None)
        assert todo_col is not None
        assert todo_col.item_count == 1

    @pytest.mark.asyncio
    async def test_pagination(self, service):
        """Should follow pagination cursors to collect all items."""
        item1 = _make_item_node(item_id="PVTI_1", status_option_id="opt_todo")
        item2 = _make_item_node(item_id="PVTI_2", status_option_id="opt_done")
        page1 = _make_get_board_data_response([item1], has_next_page=True, end_cursor="cursor1")
        page2 = _make_get_board_data_response([item2], has_next_page=False)

        mock_graphql = AsyncMock(side_effect=[page1, page2])

        with (
            patch.object(service, "_graphql", mock_graphql),
            patch.object(service, "get_sub_issues", new_callable=AsyncMock, return_value=[]),
            patch.object(
                service, "_reconcile_board_items", new_callable=AsyncMock, return_value=[]
            ),
            patch("src.services.github_projects.board.save_done_items", new_callable=AsyncMock),
        ):
            result = await service.get_board_data(TOKEN, PROJECT_ID)

        assert mock_graphql.await_count == 2
        total_items = sum(c.item_count for c in result.columns)
        assert total_items == 2

    @pytest.mark.asyncio
    async def test_raises_when_project_not_found(self, service):
        """Should raise ValueError if node is missing."""
        graphql_resp = {"node": None}

        with (
            patch.object(service, "_graphql", new_callable=AsyncMock, return_value=graphql_resp),
            pytest.raises(ValueError, match="Project not found"),
        ):
            await service.get_board_data(TOKEN, PROJECT_ID)

    @pytest.mark.asyncio
    async def test_raises_when_no_status_field(self, service):
        """Should raise ValueError if the project has no Status field."""
        graphql_resp = {
            "node": {
                "title": "No Status Project",
                "field": None,
                "items": {"nodes": [], "pageInfo": {"hasNextPage": False}},
            }
        }

        with (
            patch.object(service, "_graphql", new_callable=AsyncMock, return_value=graphql_resp),
            pytest.raises(ValueError, match="no Status field"),
        ):
            await service.get_board_data(TOKEN, PROJECT_ID)

    @pytest.mark.asyncio
    async def test_sub_issues_fetched_for_items(self, service):
        """Should fetch sub-issues for each issue item and detect agent slug."""
        item_node = _make_item_node(status_option_id="opt_todo")
        graphql_resp = _make_get_board_data_response([item_node])

        sub_issues = [
            {
                "node_id": "SI_1",
                "number": 99,
                "title": "[speckit.implement] Sub task",
                "html_url": "https://github.com/octocat/my-repo/issues/99",
                "state": "open",
                "assignees": [{"login": "bob", "avatar_url": "https://avatar/bob"}],
            }
        ]

        with (
            patch.object(service, "_graphql", new_callable=AsyncMock, return_value=graphql_resp),
            patch.object(
                service, "get_sub_issues", new_callable=AsyncMock, return_value=sub_issues
            ),
            patch.object(
                service, "_reconcile_board_items", new_callable=AsyncMock, return_value=[]
            ),
            patch("src.services.github_projects.board.save_done_items", new_callable=AsyncMock),
        ):
            result = await service.get_board_data(TOKEN, PROJECT_ID)

        all_items = [item for col in result.columns for item in col.items]
        assert len(all_items) == 1
        assert len(all_items[0].sub_issues) == 1
        assert all_items[0].sub_issues[0].assigned_agent == "speckit.implement"

    @pytest.mark.asyncio
    async def test_done_items_persisted(self, service):
        """Should call save_done_items for items with Done status."""
        item_node = _make_item_node(status_name="Done", status_option_id="opt_done")
        graphql_resp = _make_get_board_data_response([item_node])

        mock_save = AsyncMock()

        with (
            patch.object(service, "_graphql", new_callable=AsyncMock, return_value=graphql_resp),
            patch.object(service, "get_sub_issues", new_callable=AsyncMock, return_value=[]),
            patch.object(
                service, "_reconcile_board_items", new_callable=AsyncMock, return_value=[]
            ),
            patch("src.services.github_projects.board.save_done_items", mock_save),
        ):
            await service.get_board_data(TOKEN, PROJECT_ID)

        mock_save.assert_awaited_once()
        assert mock_save.call_args[0][0] == PROJECT_ID
