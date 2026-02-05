"""Unit tests for GitHub Projects service - Copilot custom agent assignment."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.models.project import ProjectType
from src.models.task import Task
from src.services.github_projects import GitHubProjectsService

# =============================================================================
# Core GraphQL and HTTP Tests
# =============================================================================


class TestGraphQLMethod:
    """Tests for the _graphql method."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_graphql_success(self, service):
        """Should return data on successful GraphQL response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"data": {"user": {"id": "123", "name": "Test"}}}

        with patch.object(service, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            result = await service._graphql(
                access_token="test-token",
                query="query { user { id name } }",
                variables={"login": "testuser"},
            )

            assert result == {"user": {"id": "123", "name": "Test"}}
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_graphql_with_extra_headers(self, service):
        """Should include extra headers when provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"data": {"result": "ok"}}

        with patch.object(service, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            await service._graphql(
                access_token="test-token",
                query="mutation { test }",
                variables={},
                extra_headers={"GraphQL-Features": "copilot_support"},
            )

            call_args = mock_client.post.call_args
            headers = call_args.kwargs["headers"]
            assert headers["GraphQL-Features"] == "copilot_support"

    @pytest.mark.asyncio
    async def test_graphql_raises_on_errors(self, service):
        """Should raise ValueError when GraphQL returns errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"errors": [{"message": "Field not found"}]}

        with patch.object(service, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            with pytest.raises(ValueError) as exc_info:
                await service._graphql(
                    access_token="test-token",
                    query="query { invalid }",
                    variables={},
                )

            assert "GraphQL error" in str(exc_info.value)
            assert "Field not found" in str(exc_info.value)


# =============================================================================
# Project Listing Tests
# =============================================================================


class TestListUserProjects:
    """Tests for listing user projects."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_list_user_projects_success(self, service):
        """Should return list of user projects."""
        mock_response = {
            "user": {
                "projectsV2": {
                    "nodes": [
                        {
                            "id": "PVT_123",
                            "title": "My Project",
                            "url": "https://github.com/users/testuser/projects/1",
                            "shortDescription": "Test project",
                            "closed": False,
                            "field": {
                                "id": "FIELD_1",
                                "options": [
                                    {"id": "OPT_1", "name": "Todo", "color": "gray"},
                                    {"id": "OPT_2", "name": "Done", "color": "green"},
                                ],
                            },
                            "items": {"totalCount": 10},
                        }
                    ]
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            projects = await service.list_user_projects(
                access_token="test-token",
                username="testuser",
            )

            assert len(projects) == 1
            assert projects[0].project_id == "PVT_123"
            assert projects[0].name == "My Project"
            assert projects[0].type == ProjectType.USER
            assert len(projects[0].status_columns) == 2

    @pytest.mark.asyncio
    async def test_list_user_projects_empty(self, service):
        """Should return empty list when no projects found."""
        mock_response = {"user": None}

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            projects = await service.list_user_projects(
                access_token="test-token",
                username="testuser",
            )

            assert projects == []

    @pytest.mark.asyncio
    async def test_list_user_projects_excludes_closed(self, service):
        """Should exclude closed projects."""
        mock_response = {
            "user": {
                "projectsV2": {
                    "nodes": [
                        {
                            "id": "PVT_1",
                            "title": "Open Project",
                            "url": "https://github.com/users/u/projects/1",
                            "closed": False,
                            "field": None,
                            "items": {"totalCount": 5},
                        },
                        {
                            "id": "PVT_2",
                            "title": "Closed Project",
                            "url": "https://github.com/users/u/projects/2",
                            "closed": True,
                            "field": None,
                            "items": {"totalCount": 3},
                        },
                    ]
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            projects = await service.list_user_projects(
                access_token="test-token",
                username="u",
            )

            assert len(projects) == 1
            assert projects[0].name == "Open Project"


class TestListOrgProjects:
    """Tests for listing organization projects."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_list_org_projects_success(self, service):
        """Should return list of organization projects."""
        mock_response = {
            "organization": {
                "projectsV2": {
                    "nodes": [
                        {
                            "id": "PVT_ORG_1",
                            "title": "Org Project",
                            "url": "https://github.com/orgs/testorg/projects/1",
                            "shortDescription": "Org description",
                            "closed": False,
                            "field": {
                                "id": "FIELD_1",
                                "options": [
                                    {"id": "OPT_1", "name": "Backlog"},
                                ],
                            },
                            "items": {"totalCount": 20},
                        }
                    ]
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            projects = await service.list_org_projects(
                access_token="test-token",
                org="testorg",
            )

            assert len(projects) == 1
            assert projects[0].project_id == "PVT_ORG_1"
            assert projects[0].type == ProjectType.ORGANIZATION
            assert projects[0].owner_login == "testorg"


class TestParseProjects:
    """Tests for _parse_projects helper method."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    def test_parse_projects_with_default_status_columns(self, service):
        """Should use default status columns when none found."""
        nodes = [
            {
                "id": "PVT_1",
                "title": "No Status Field",
                "url": "https://github.com/users/u/projects/1",
                "closed": False,
                "field": None,  # No status field
                "items": {"totalCount": 0},
            }
        ]

        projects = service._parse_projects(
            nodes=nodes,
            owner_login="u",
            project_type=ProjectType.USER,
        )

        assert len(projects) == 1
        assert len(projects[0].status_columns) == 3
        assert projects[0].status_columns[0].name == "Todo"
        assert projects[0].status_columns[1].name == "In Progress"
        assert projects[0].status_columns[2].name == "Done"

    def test_parse_projects_skips_null_nodes(self, service):
        """Should skip null nodes in response."""
        nodes = [
            None,
            {
                "id": "PVT_1",
                "title": "Valid",
                "url": "url",
                "closed": False,
                "field": None,
                "items": {"totalCount": 0},
            },
        ]

        projects = service._parse_projects(
            nodes=nodes,
            owner_login="u",
            project_type=ProjectType.USER,
        )

        assert len(projects) == 1


# =============================================================================
# Project Items Tests
# =============================================================================


class TestGetProjectItems:
    """Tests for fetching project items."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_get_project_items_success(self, service):
        """Should return list of tasks from project."""
        mock_response = {
            "node": {
                "items": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "id": "ITEM_1",
                            "fieldValueByName": {"name": "Todo", "optionId": "OPT_1"},
                            "content": {
                                "id": "ISSUE_1",
                                "number": 42,
                                "title": "Test Issue",
                                "body": "Description here",
                                "repository": {"owner": {"login": "owner"}, "name": "repo"},
                            },
                        }
                    ],
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            tasks = await service.get_project_items(
                access_token="test-token",
                project_id="PVT_123",
            )

            assert len(tasks) == 1
            assert tasks[0].github_item_id == "ITEM_1"
            assert tasks[0].title == "Test Issue"
            assert tasks[0].status == "Todo"
            assert tasks[0].issue_number == 42
            assert tasks[0].repository_owner == "owner"
            assert tasks[0].repository_name == "repo"

    @pytest.mark.asyncio
    async def test_get_project_items_pagination(self, service):
        """Should handle pagination correctly."""
        # First page
        page1_response = {
            "node": {
                "items": {
                    "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                    "nodes": [
                        {
                            "id": "ITEM_1",
                            "fieldValueByName": {"name": "Todo", "optionId": "OPT_1"},
                            "content": {"title": "Task 1", "body": ""},
                        }
                    ],
                }
            }
        }
        # Second page
        page2_response = {
            "node": {
                "items": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "id": "ITEM_2",
                            "fieldValueByName": {"name": "Done", "optionId": "OPT_2"},
                            "content": {"title": "Task 2", "body": ""},
                        }
                    ],
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.side_effect = [page1_response, page2_response]

            tasks = await service.get_project_items(
                access_token="test-token",
                project_id="PVT_123",
            )

            assert len(tasks) == 2
            assert tasks[0].title == "Task 1"
            assert tasks[1].title == "Task 2"
            assert mock_graphql.call_count == 2


# =============================================================================
# Item Creation and Update Tests
# =============================================================================


class TestCreateDraftItem:
    """Tests for creating draft items."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_create_draft_item_success(self, service):
        """Should create draft item and return ID."""
        mock_response = {"addProjectV2DraftIssue": {"projectItem": {"id": "ITEM_NEW"}}}

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            item_id = await service.create_draft_item(
                access_token="test-token",
                project_id="PVT_123",
                title="New Task",
                description="Task description",
            )

            assert item_id == "ITEM_NEW"
            call_args = mock_graphql.call_args
            assert call_args.args[2]["title"] == "New Task"
            assert call_args.args[2]["body"] == "Task description"


class TestUpdateItemStatus:
    """Tests for updating item status."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_update_item_status_success(self, service):
        """Should update item status and return True."""
        mock_response = {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "ITEM_1"}}}

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            with patch("asyncio.sleep", new_callable=AsyncMock):  # Skip delay
                result = await service.update_item_status(
                    access_token="test-token",
                    project_id="PVT_123",
                    item_id="ITEM_1",
                    field_id="FIELD_1",
                    option_id="OPT_1",
                )

            assert result is True

    @pytest.mark.asyncio
    async def test_update_item_status_failure(self, service):
        """Should return False on failure."""
        mock_response = {"updateProjectV2ItemFieldValue": {"projectV2Item": None}}

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await service.update_item_status(
                    access_token="test-token",
                    project_id="PVT_123",
                    item_id="ITEM_1",
                    field_id="FIELD_1",
                    option_id="OPT_1",
                )

            assert result is False


class TestUpdateItemStatusByName:
    """Tests for updating item status by name."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_update_status_by_name_success(self, service):
        """Should find status option and update."""
        mock_field_response = {
            "node": {
                "field": {
                    "id": "FIELD_1",
                    "options": [
                        {"id": "OPT_1", "name": "Todo"},
                        {"id": "OPT_2", "name": "Done"},
                    ],
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_field_response

            with patch.object(service, "update_item_status", new_callable=AsyncMock) as mock_update:
                mock_update.return_value = True

                result = await service.update_item_status_by_name(
                    access_token="test-token",
                    project_id="PVT_123",
                    item_id="ITEM_1",
                    status_name="Done",
                )

                assert result is True
                mock_update.assert_called_once_with(
                    access_token="test-token",
                    project_id="PVT_123",
                    item_id="ITEM_1",
                    field_id="FIELD_1",
                    option_id="OPT_2",
                )

    @pytest.mark.asyncio
    async def test_update_status_by_name_not_found(self, service):
        """Should return False when status not found."""
        mock_field_response = {
            "node": {"field": {"id": "FIELD_1", "options": [{"id": "OPT_1", "name": "Todo"}]}}
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_field_response

            result = await service.update_item_status_by_name(
                access_token="test-token",
                project_id="PVT_123",
                item_id="ITEM_1",
                status_name="NonExistent",
            )

            assert result is False


# =============================================================================
# Issue Creation and Management Tests
# =============================================================================


class TestCreateIssue:
    """Tests for creating GitHub issues."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_create_issue_success(self, service):
        """Should create issue via REST API."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "id": 123,
            "node_id": "I_123",
            "number": 42,
            "html_url": "https://github.com/owner/repo/issues/42",
            "title": "Test Issue",
        }

        with patch.object(service, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            result = await service.create_issue(
                access_token="test-token",
                owner="owner",
                repo="repo",
                title="Test Issue",
                body="Issue body",
                labels=["bug", "enhancement"],
            )

            assert result["number"] == 42
            assert result["node_id"] == "I_123"

            call_args = mock_client.post.call_args
            assert call_args.kwargs["json"]["title"] == "Test Issue"
            assert call_args.kwargs["json"]["labels"] == ["bug", "enhancement"]


class TestAddIssueToProject:
    """Tests for adding issues to projects."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_add_issue_to_project_success(self, service):
        """Should add issue to project and return item ID."""
        mock_response = {"addProjectV2ItemById": {"item": {"id": "ITEM_NEW"}}}

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            item_id = await service.add_issue_to_project(
                access_token="test-token",
                project_id="PVT_123",
                issue_node_id="I_456",
            )

            assert item_id == "ITEM_NEW"


class TestAssignIssue:
    """Tests for assigning users to issues."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_assign_issue_success(self, service):
        """Should assign users to issue."""
        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(service, "_client") as mock_client:
            mock_client.patch = AsyncMock(return_value=mock_response)

            result = await service.assign_issue(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=42,
                assignees=["user1", "user2"],
            )

            assert result is True
            call_args = mock_client.patch.call_args
            assert call_args.kwargs["json"]["assignees"] == ["user1", "user2"]

    @pytest.mark.asyncio
    async def test_assign_issue_failure(self, service):
        """Should return False on failure."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.text = "Validation failed"

        with patch.object(service, "_client") as mock_client:
            mock_client.patch = AsyncMock(return_value=mock_response)

            result = await service.assign_issue(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=42,
                assignees=["invalid-user"],
            )

            assert result is False


class TestValidateAssignee:
    """Tests for validating assignees."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_validate_assignee_success(self, service):
        """Should return True for valid assignee."""
        mock_response = Mock()
        mock_response.status_code = 204

        with patch.object(service, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await service.validate_assignee(
                access_token="test-token",
                owner="owner",
                repo="repo",
                username="validuser",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_validate_assignee_invalid(self, service):
        """Should return False for invalid assignee."""
        mock_response = Mock()
        mock_response.status_code = 404

        with patch.object(service, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await service.validate_assignee(
                access_token="test-token",
                owner="owner",
                repo="repo",
                username="invaliduser",
            )

            assert result is False


# =============================================================================
# Repository Info Tests
# =============================================================================


class TestGetRepositoryOwner:
    """Tests for getting repository owner."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_get_repository_owner_success(self, service):
        """Should return repository owner login."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"owner": {"login": "repo-owner"}}

        with patch.object(service, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            owner = await service.get_repository_owner(
                access_token="test-token",
                owner="owner",
                repo="repo",
            )

            assert owner == "repo-owner"


class TestGetProjectRepository:
    """Tests for getting project repository."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_get_project_repository_success(self, service):
        """Should return repository from project items."""
        mock_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "content": {
                                "repository": {
                                    "owner": {"login": "found-owner"},
                                    "name": "found-repo",
                                }
                            }
                        }
                    ]
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            result = await service.get_project_repository(
                access_token="test-token",
                project_id="PVT_123",
            )

            assert result == ("found-owner", "found-repo")

    @pytest.mark.asyncio
    async def test_get_project_repository_not_found(self, service):
        """Should return None when no repository found."""
        mock_response = {"node": {"items": {"nodes": []}}}

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            result = await service.get_project_repository(
                access_token="test-token",
                project_id="PVT_123",
            )

            assert result is None


# =============================================================================
# Project Fields Tests
# =============================================================================


class TestGetProjectFields:
    """Tests for getting project fields."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_get_project_fields_success(self, service):
        """Should return dict of project fields."""
        mock_response = {
            "node": {
                "fields": {
                    "nodes": [
                        {
                            "id": "FIELD_1",
                            "name": "Status",
                            "dataType": "SINGLE_SELECT",
                            "options": [{"id": "OPT_1", "name": "Todo"}],
                        },
                        {
                            "id": "FIELD_2",
                            "name": "Priority",
                            "dataType": "SINGLE_SELECT",
                            "options": [{"id": "OPT_P1", "name": "High"}],
                        },
                        {"id": "FIELD_3", "name": "Estimate", "dataType": "NUMBER"},
                    ]
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            fields = await service.get_project_fields(
                access_token="test-token",
                project_id="PVT_123",
            )

            assert len(fields) == 3
            assert "Status" in fields
            assert "Priority" in fields
            assert "Estimate" in fields
            assert fields["Status"]["dataType"] == "SINGLE_SELECT"
            assert fields["Estimate"]["dataType"] == "NUMBER"

    @pytest.mark.asyncio
    async def test_get_project_fields_error(self, service):
        """Should return empty dict on error."""
        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.side_effect = Exception("GraphQL error")

            fields = await service.get_project_fields(
                access_token="test-token",
                project_id="PVT_123",
            )

            assert fields == {}


class TestUpdateProjectItemField:
    """Tests for updating project item fields."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_update_single_select_field(self, service):
        """Should update single select field."""
        with patch.object(service, "get_project_fields", new_callable=AsyncMock) as mock_get_fields:
            mock_get_fields.return_value = {
                "Priority": {
                    "id": "FIELD_1",
                    "dataType": "SINGLE_SELECT",
                    "options": [
                        {"id": "OPT_1", "name": "P1"},
                        {"id": "OPT_2", "name": "P2"},
                    ],
                }
            }

            with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
                mock_graphql.return_value = {}

                result = await service.update_project_item_field(
                    access_token="test-token",
                    project_id="PVT_123",
                    item_id="ITEM_1",
                    field_name="Priority",
                    value="P1",
                )

                assert result is True
                call_args = mock_graphql.call_args
                assert call_args.args[2]["optionId"] == "OPT_1"

    @pytest.mark.asyncio
    async def test_update_number_field(self, service):
        """Should update number field."""
        with patch.object(service, "get_project_fields", new_callable=AsyncMock) as mock_get_fields:
            mock_get_fields.return_value = {
                "Estimate": {"id": "FIELD_1", "dataType": "NUMBER", "options": []}
            }

            with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
                mock_graphql.return_value = {}

                result = await service.update_project_item_field(
                    access_token="test-token",
                    project_id="PVT_123",
                    item_id="ITEM_1",
                    field_name="Estimate",
                    value=8.5,
                )

                assert result is True
                call_args = mock_graphql.call_args
                assert call_args.args[2]["number"] == 8.5

    @pytest.mark.asyncio
    async def test_update_field_not_found(self, service):
        """Should return False when field not found."""
        with patch.object(service, "get_project_fields", new_callable=AsyncMock) as mock_get_fields:
            mock_get_fields.return_value = {}

            result = await service.update_project_item_field(
                access_token="test-token",
                project_id="PVT_123",
                item_id="ITEM_1",
                field_name="NonExistent",
                value="test",
            )

            assert result is False


# =============================================================================
# Pull Request Tests
# =============================================================================


class TestGetPullRequest:
    """Tests for getting pull request details."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_get_pull_request_success(self, service):
        """Should return PR details."""
        mock_response = {
            "repository": {
                "pullRequest": {
                    "id": "PR_123",
                    "number": 42,
                    "title": "Fix bug",
                    "body": "PR description",
                    "state": "OPEN",
                    "isDraft": False,
                    "url": "https://github.com/owner/repo/pull/42",
                    "author": {"login": "contributor"},
                    "createdAt": "2026-01-01T10:00:00Z",
                    "updatedAt": "2026-01-02T10:00:00Z",
                    "commits": {
                        "nodes": [
                            {
                                "commit": {
                                    "oid": "abc123",
                                    "committedDate": "2026-01-02T09:00:00Z",
                                    "statusCheckRollup": {"state": "SUCCESS"},
                                }
                            }
                        ]
                    },
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            pr = await service.get_pull_request(
                access_token="test-token",
                owner="owner",
                repo="repo",
                pr_number=42,
            )

            assert pr["number"] == 42
            assert pr["title"] == "Fix bug"
            assert pr["is_draft"] is False
            assert pr["check_status"] == "SUCCESS"
            assert pr["last_commit"]["sha"] == "abc123"

    @pytest.mark.asyncio
    async def test_get_pull_request_not_found(self, service):
        """Should return None when PR not found."""
        mock_response = {"repository": {"pullRequest": None}}

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            pr = await service.get_pull_request(
                access_token="test-token",
                owner="owner",
                repo="repo",
                pr_number=999,
            )

            assert pr is None


class TestRequestCopilotReview:
    """Tests for requesting Copilot review."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_request_copilot_review_success(self, service):
        """Should successfully request Copilot review."""
        mock_response = {
            "requestReviewsByLogin": {
                "pullRequest": {
                    "id": "PR_123",
                    "number": 42,
                    "url": "https://github.com/owner/repo/pull/42",
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            result = await service.request_copilot_review(
                access_token="test-token",
                pr_node_id="PR_123",
                pr_number=42,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_request_copilot_review_failure(self, service):
        """Should return False on failure."""
        mock_response = {"requestReviewsByLogin": {"pullRequest": None}}

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            result = await service.request_copilot_review(
                access_token="test-token",
                pr_node_id="PR_123",
            )

            assert result is False


class TestHasCopilotReviewedPr:
    """Tests for checking if Copilot reviewed PR."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_has_copilot_reviewed_true(self, service):
        """Should return True when Copilot has reviewed."""
        mock_response = {
            "repository": {
                "pullRequest": {
                    "reviews": {
                        "nodes": [
                            {"author": {"login": "human"}, "state": "APPROVED"},
                            {"author": {"login": "copilot"}, "state": "COMMENTED"},
                        ]
                    }
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            result = await service.has_copilot_reviewed_pr(
                access_token="test-token",
                owner="owner",
                repo="repo",
                pr_number=42,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_has_copilot_reviewed_false(self, service):
        """Should return False when Copilot has not reviewed."""
        mock_response = {
            "repository": {
                "pullRequest": {
                    "reviews": {
                        "nodes": [
                            {"author": {"login": "human"}, "state": "APPROVED"},
                        ]
                    }
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            result = await service.has_copilot_reviewed_pr(
                access_token="test-token",
                owner="owner",
                repo="repo",
                pr_number=42,
            )

            assert result is False


# =============================================================================
# Polling and Change Detection Tests
# =============================================================================


class TestDetectChanges:
    """Tests for _detect_changes helper method."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    def test_detect_new_tasks(self, service):
        """Should detect newly added tasks."""
        old_tasks = []
        new_tasks = [
            Task(
                project_id="PVT_1",
                github_item_id="ITEM_1",
                title="New Task",
                status="Todo",
                status_option_id="OPT_1",
            )
        ]

        changes = service._detect_changes(old_tasks, new_tasks)

        assert len(changes) == 1
        assert changes[0]["type"] == "task_created"
        assert changes[0]["title"] == "New Task"

    def test_detect_deleted_tasks(self, service):
        """Should detect deleted tasks."""
        old_tasks = [
            Task(
                project_id="PVT_1",
                github_item_id="ITEM_1",
                title="Old Task",
                status="Todo",
                status_option_id="OPT_1",
            )
        ]
        new_tasks = []

        changes = service._detect_changes(old_tasks, new_tasks)

        assert len(changes) == 1
        assert changes[0]["type"] == "task_deleted"
        assert changes[0]["title"] == "Old Task"

    def test_detect_status_changes(self, service):
        """Should detect status changes."""
        old_tasks = [
            Task(
                project_id="PVT_1",
                github_item_id="ITEM_1",
                title="Task",
                status="Todo",
                status_option_id="OPT_1",
            )
        ]
        new_tasks = [
            Task(
                project_id="PVT_1",
                github_item_id="ITEM_1",
                title="Task",
                status="Done",
                status_option_id="OPT_2",
            )
        ]

        changes = service._detect_changes(old_tasks, new_tasks)

        assert len(changes) == 1
        assert changes[0]["type"] == "status_changed"
        assert changes[0]["old_status"] == "Todo"
        assert changes[0]["new_status"] == "Done"

    def test_detect_title_changes(self, service):
        """Should detect title changes."""
        old_tasks = [
            Task(
                project_id="PVT_1",
                github_item_id="ITEM_1",
                title="Old Title",
                status="Todo",
                status_option_id="OPT_1",
            )
        ]
        new_tasks = [
            Task(
                project_id="PVT_1",
                github_item_id="ITEM_1",
                title="New Title",
                status="Todo",
                status_option_id="OPT_1",
            )
        ]

        changes = service._detect_changes(old_tasks, new_tasks)

        assert len(changes) == 1
        assert changes[0]["type"] == "title_changed"
        assert changes[0]["old_title"] == "Old Title"
        assert changes[0]["new_title"] == "New Title"


class TestPollProjectChanges:
    """Tests for polling project changes."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_poll_project_changes_detects_ready_trigger(self, service):
        """Should detect Ready status trigger."""
        old_tasks = [
            Task(
                project_id="PVT_1",
                github_item_id="ITEM_1",
                title="Task",
                status="Backlog",
                status_option_id="OPT_1",
            )
        ]
        current_tasks = [
            Task(
                project_id="PVT_1",
                github_item_id="ITEM_1",
                title="Task",
                status="Ready",
                status_option_id="OPT_2",
            )
        ]

        with patch.object(service, "get_project_items", new_callable=AsyncMock) as mock_get_items:
            mock_get_items.return_value = current_tasks

            result = await service.poll_project_changes(
                access_token="test-token",
                project_id="PVT_1",
                cached_tasks=old_tasks,
                ready_status="Ready",
            )

            assert len(result["changes"]) == 1
            assert result["changes"][0]["type"] == "status_changed"

            ready_triggers = [
                t for t in result["workflow_triggers"] if t["trigger"] == "ready_detected"
            ]
            assert len(ready_triggers) == 1


# =============================================================================
# Original Copilot Agent Tests (preserved from original file)
# =============================================================================


class TestGetIssueWithComments:
    """Tests for fetching issue details with comments."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_get_issue_with_comments_success(self, service):
        """Should fetch issue title, body, and comments."""
        mock_response = {
            "repository": {
                "issue": {
                    "id": "I_123",
                    "title": "Test Issue",
                    "body": "Issue description here",
                    "comments": {
                        "nodes": [
                            {
                                "id": "C_1",
                                "author": {"login": "user1"},
                                "body": "First comment",
                                "createdAt": "2026-01-01T10:00:00Z",
                            },
                            {
                                "id": "C_2",
                                "author": {"login": "user2"},
                                "body": "Second comment",
                                "createdAt": "2026-01-02T10:00:00Z",
                            },
                        ]
                    },
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            result = await service.get_issue_with_comments(
                access_token="test-token",
                owner="test-owner",
                repo="test-repo",
                issue_number=42,
            )

            assert result["title"] == "Test Issue"
            assert result["body"] == "Issue description here"
            assert len(result["comments"]) == 2
            assert result["comments"][0]["author"] == "user1"
            assert result["comments"][0]["body"] == "First comment"
            assert result["comments"][1]["author"] == "user2"

    @pytest.mark.asyncio
    async def test_get_issue_with_comments_no_comments(self, service):
        """Should handle issues with no comments."""
        mock_response = {
            "repository": {
                "issue": {
                    "id": "I_123",
                    "title": "No Comments Issue",
                    "body": "Just a description",
                    "comments": {"nodes": []},
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            result = await service.get_issue_with_comments(
                access_token="test-token",
                owner="test-owner",
                repo="test-repo",
                issue_number=1,
            )

            assert result["title"] == "No Comments Issue"
            assert result["comments"] == []

    @pytest.mark.asyncio
    async def test_get_issue_with_comments_error_returns_empty(self, service):
        """Should return empty dict on error."""
        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.side_effect = Exception("GraphQL error")

            result = await service.get_issue_with_comments(
                access_token="test-token",
                owner="test-owner",
                repo="test-repo",
                issue_number=42,
            )

            assert result == {"title": "", "body": "", "comments": []}


class TestFormatIssueContextAsPrompt:
    """Tests for formatting issue context as agent prompt."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    def test_format_with_all_fields(self, service):
        """Should format title, body, and comments into prompt."""
        issue_data = {
            "title": "Add feature X",
            "body": "We need to implement feature X for users.",
            "comments": [
                {
                    "author": "alice",
                    "body": "I think we should use approach A",
                    "created_at": "2026-01-01T10:00:00Z",
                },
                {
                    "author": "bob",
                    "body": "Agreed, let's also consider edge cases",
                    "created_at": "2026-01-02T10:00:00Z",
                },
            ],
        }

        result = service.format_issue_context_as_prompt(issue_data)

        assert "## Issue Title" in result
        assert "Add feature X" in result
        assert "## Issue Description" in result
        assert "We need to implement feature X" in result
        assert "## Comments and Discussion" in result
        assert "Comment 1 by @alice" in result
        assert "approach A" in result
        assert "Comment 2 by @bob" in result
        assert "edge cases" in result

    def test_format_with_empty_body(self, service):
        """Should handle empty body gracefully."""
        issue_data = {
            "title": "Quick fix",
            "body": "",
            "comments": [],
        }

        result = service.format_issue_context_as_prompt(issue_data)

        assert "## Issue Title" in result
        assert "Quick fix" in result
        assert "## Issue Description" not in result

    def test_format_with_no_comments(self, service):
        """Should not include comments section when empty."""
        issue_data = {
            "title": "New feature",
            "body": "Description here",
            "comments": [],
        }

        result = service.format_issue_context_as_prompt(issue_data)

        assert "## Issue Title" in result
        assert "## Issue Description" in result
        assert "## Comments and Discussion" not in result


class TestAssignCopilotToIssue:
    """Tests for assigning Copilot with custom agents."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_assign_copilot_rest_api_success(self, service):
        """Should successfully assign Copilot via REST API."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"assignees": [{"login": "copilot-swe-agent[bot]"}]}

        with patch.object(service, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            result = await service.assign_copilot_to_issue(
                access_token="test-token",
                owner="test-owner",
                repo="test-repo",
                issue_node_id="I_123",
                issue_number=42,
                custom_agent="speckit.specify",
                custom_instructions="Test instructions",
            )

            assert result is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "assignees" in call_args.kwargs["json"]
            assert call_args.kwargs["json"]["assignees"] == ["copilot-swe-agent[bot]"]
            assert call_args.kwargs["json"]["agent_assignment"]["custom_agent"] == "speckit.specify"

    @pytest.mark.asyncio
    async def test_assign_copilot_rest_api_with_custom_instructions(self, service):
        """Should include custom instructions in payload."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"assignees": [{"login": "copilot-swe-agent[bot]"}]}

        with patch.object(service, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            await service.assign_copilot_to_issue(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_node_id="I_123",
                issue_number=1,
                custom_agent="speckit.specify",
                custom_instructions="## Issue Title\nTest\n\n## Description\nContent",
            )

            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]
            assert (
                payload["agent_assignment"]["custom_instructions"]
                == "## Issue Title\nTest\n\n## Description\nContent"
            )
            assert payload["agent_assignment"]["custom_agent"] == "speckit.specify"

    @pytest.mark.asyncio
    async def test_assign_copilot_falls_back_to_graphql_on_rest_failure(self, service):
        """Should fall back to GraphQL when REST API fails."""
        mock_rest_response = Mock()
        mock_rest_response.status_code = 422
        mock_rest_response.text = "Validation failed"
        mock_rest_response.headers = {"X-Request-Id": "123"}

        with patch.object(service, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_rest_response)

            with patch.object(
                service, "_assign_copilot_graphql", new_callable=AsyncMock
            ) as mock_graphql:
                mock_graphql.return_value = True

                result = await service.assign_copilot_to_issue(
                    access_token="test-token",
                    owner="owner",
                    repo="repo",
                    issue_node_id="I_123",
                    issue_number=42,
                    custom_agent="speckit.specify",
                )

                assert result is True
                mock_graphql.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_copilot_without_issue_number_uses_graphql(self, service):
        """Should use GraphQL directly when issue_number is not provided."""
        with patch.object(
            service, "_assign_copilot_graphql", new_callable=AsyncMock
        ) as mock_graphql:
            mock_graphql.return_value = True

            result = await service.assign_copilot_to_issue(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_node_id="I_123",
                issue_number=None,  # No issue number
                custom_agent="speckit.specify",
            )

            assert result is True
            mock_graphql.assert_called_once()


class TestAssignCopilotGraphQL:
    """Tests for GraphQL-based Copilot assignment."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_graphql_assign_success(self, service):
        """Should successfully assign via GraphQL."""
        with patch.object(service, "get_copilot_bot_id", new_callable=AsyncMock) as mock_get_bot:
            mock_get_bot.return_value = ("BOT_ID_123", "REPO_ID_456")

            with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
                mock_graphql.return_value = {
                    "addAssigneesToAssignable": {
                        "assignable": {"assignees": {"nodes": [{"login": "copilot-swe-agent"}]}}
                    }
                }

                result = await service._assign_copilot_graphql(
                    access_token="test-token",
                    owner="owner",
                    repo="repo",
                    issue_node_id="I_123",
                    custom_agent="speckit.specify",
                    custom_instructions="Test prompt",
                )

                assert result is True

    @pytest.mark.asyncio
    async def test_graphql_assign_no_bot_available(self, service):
        """Should return False when Copilot bot is not available."""
        with patch.object(service, "get_copilot_bot_id", new_callable=AsyncMock) as mock_get_bot:
            mock_get_bot.return_value = (None, "REPO_ID_456")

            result = await service._assign_copilot_graphql(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_node_id="I_123",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_graphql_assign_no_repo_id(self, service):
        """Should return False when repository ID is not found."""
        with patch.object(service, "get_copilot_bot_id", new_callable=AsyncMock) as mock_get_bot:
            mock_get_bot.return_value = ("BOT_ID_123", None)

            result = await service._assign_copilot_graphql(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_node_id="I_123",
            )

            assert result is False


class TestGetCopilotBotId:
    """Tests for getting Copilot bot ID."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_get_copilot_bot_id_found(self, service):
        """Should return bot ID when Copilot is available."""
        mock_response = {
            "repository": {
                "id": "REPO_123",
                "suggestedActors": {
                    "nodes": [
                        {"login": "copilot-swe-agent", "__typename": "Bot", "id": "BOT_456"},
                        {"login": "other-user", "__typename": "User", "id": "USER_789"},
                    ]
                },
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            bot_id, repo_id = await service.get_copilot_bot_id(
                access_token="test-token",
                owner="owner",
                repo="repo",
            )

            assert bot_id == "BOT_456"
            assert repo_id == "REPO_123"

    @pytest.mark.asyncio
    async def test_get_copilot_bot_id_not_available(self, service):
        """Should return None when Copilot is not in suggested actors."""
        mock_response = {
            "repository": {
                "id": "REPO_123",
                "suggestedActors": {
                    "nodes": [
                        {"login": "some-user", "__typename": "User", "id": "USER_123"},
                    ]
                },
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            bot_id, repo_id = await service.get_copilot_bot_id(
                access_token="test-token",
                owner="owner",
                repo="repo",
            )

            assert bot_id is None
            assert repo_id == "REPO_123"

    @pytest.mark.asyncio
    async def test_get_copilot_bot_id_error(self, service):
        """Should return None on error."""
        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.side_effect = Exception("GraphQL error")

            bot_id, repo_id = await service.get_copilot_bot_id(
                access_token="test-token",
                owner="owner",
                repo="repo",
            )

            assert bot_id is None
            assert repo_id is None


class TestLinkedPullRequests:
    """Tests for getting linked pull requests."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_get_linked_prs_success(self, service):
        """Should return linked PRs for an issue."""
        mock_response = {
            "repository": {
                "issue": {
                    "id": "I_123",
                    "title": "Test Issue",
                    "state": "OPEN",
                    "timelineItems": {
                        "nodes": [
                            {
                                "subject": {
                                    "id": "PR_1",
                                    "number": 42,
                                    "title": "Fix issue",
                                    "state": "OPEN",
                                    "isDraft": False,
                                    "url": "https://github.com/owner/repo/pull/42",
                                    "author": {"login": "copilot-swe-agent[bot]"},
                                    "createdAt": "2026-01-01T10:00:00Z",
                                    "updatedAt": "2026-01-02T10:00:00Z",
                                }
                            }
                        ]
                    },
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            prs = await service.get_linked_pull_requests(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert len(prs) == 1
            assert prs[0]["number"] == 42
            assert prs[0]["is_draft"] is False
            assert prs[0]["author"] == "copilot-swe-agent[bot]"

    @pytest.mark.asyncio
    async def test_get_linked_prs_no_prs(self, service):
        """Should return empty list when no PRs linked."""
        mock_response = {
            "repository": {
                "issue": {
                    "id": "I_123",
                    "timelineItems": {"nodes": []},
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            prs = await service.get_linked_pull_requests(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert prs == []

    @pytest.mark.asyncio
    async def test_get_linked_prs_error(self, service):
        """Should return empty list on error."""
        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.side_effect = Exception("GraphQL error")

            prs = await service.get_linked_pull_requests(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert prs == []


class TestMarkPrReadyForReview:
    """Tests for marking PR ready for review."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_mark_pr_ready_success(self, service):
        """Should successfully mark PR as ready."""
        mock_response = {
            "markPullRequestReadyForReview": {
                "pullRequest": {
                    "id": "PR_123",
                    "number": 42,
                    "isDraft": False,
                    "state": "OPEN",
                    "url": "https://github.com/owner/repo/pull/42",
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            result = await service.mark_pr_ready_for_review(
                access_token="test-token",
                pr_node_id="PR_123",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_mark_pr_ready_failure(self, service):
        """Should return False on failure."""
        mock_response = {
            "markPullRequestReadyForReview": {
                "pullRequest": {
                    "id": "PR_123",
                    "number": 42,
                    "isDraft": True,  # Still draft
                    "state": "OPEN",
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            result = await service.mark_pr_ready_for_review(
                access_token="test-token",
                pr_node_id="PR_123",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_mark_pr_ready_error(self, service):
        """Should return False on error."""
        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.side_effect = Exception("GraphQL error")

            result = await service.mark_pr_ready_for_review(
                access_token="test-token",
                pr_node_id="PR_123",
            )

            assert result is False


class TestCheckCopilotFinishedEvents:
    """Tests for _check_copilot_finished_events helper method."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    def test_returns_true_for_copilot_work_finished_event(self, service):
        """Should return True when copilot_work_finished event exists."""
        events = [
            {"event": "copilot_work_started"},
            {"event": "committed"},
            {"event": "copilot_work_finished"},
        ]
        assert service._check_copilot_finished_events(events) is True

    def test_returns_true_for_review_requested_from_copilot(self, service):
        """Should return True when review_requested event from Copilot exists."""
        events = [
            {"event": "copilot_work_started"},
            {
                "event": "review_requested",
                "review_requester": {"login": "Copilot"},
                "requested_reviewer": {"login": "some-user"},
            },
        ]
        assert service._check_copilot_finished_events(events) is True

    def test_returns_false_for_no_finish_events(self, service):
        """Should return False when no finish events exist."""
        events = [
            {"event": "copilot_work_started"},
            {"event": "committed"},
            {"event": "assigned"},
        ]
        assert service._check_copilot_finished_events(events) is False

    def test_returns_false_for_review_requested_not_from_copilot(self, service):
        """Should return False when review_requested is from a user, not Copilot."""
        events = [
            {
                "event": "review_requested",
                "review_requester": {"login": "some-user"},  # Not Copilot
                "requested_reviewer": {"login": "another-user"},
            },
        ]
        assert service._check_copilot_finished_events(events) is False

    def test_returns_false_for_empty_events(self, service):
        """Should return False for empty events list."""
        assert service._check_copilot_finished_events([]) is False

    def test_handles_missing_login_gracefully(self, service):
        """Should handle missing login field gracefully."""
        events = [
            {
                "event": "review_requested",
                "review_requester": {},  # Missing login
            },
        ]
        assert service._check_copilot_finished_events(events) is False


class TestCheckCopilotPrCompletion:
    """Tests for checking Copilot PR completion.

    Copilot is detected as "finished work" when timeline has:
    - 'copilot_work_finished' event, OR
    - 'review_requested' event where review_requester is Copilot
    """

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_copilot_draft_pr_with_commits_is_finished(self, service):
        """Should detect finished Copilot PR (draft + has finish events)."""
        linked_prs = [
            {
                "id": "PR_123",
                "number": 42,
                "title": "Fix issue",
                "state": "OPEN",
                "is_draft": True,  # Still draft (Copilot doesn't mark ready)
                "url": "https://github.com/owner/repo/pull/42",
                "author": "copilot-swe-agent[bot]",
            }
        ]

        pr_details = {
            "id": "PR_123",
            "number": 42,
            "last_commit": {"sha": "abc1234567890"},
        }

        # Timeline events indicating Copilot finished work
        timeline_events = [{"event": "copilot_work_finished"}]

        with (
            patch.object(
                service, "get_linked_pull_requests", new_callable=AsyncMock
            ) as mock_get_prs,
            patch.object(service, "get_pull_request", new_callable=AsyncMock) as mock_get_pr,
            patch.object(
                service, "get_pr_timeline_events", new_callable=AsyncMock
            ) as mock_get_timeline,
        ):
            mock_get_prs.return_value = linked_prs
            mock_get_pr.return_value = pr_details
            mock_get_timeline.return_value = timeline_events

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is not None
            assert result["number"] == 42
            assert result["is_draft"] is True
            assert result["copilot_finished"] is True

    @pytest.mark.asyncio
    async def test_copilot_finished_via_review_requested_event(self, service):
        """Should detect Copilot finished when review_requested event from Copilot exists."""
        linked_prs = [
            {
                "id": "PR_123",
                "number": 42,
                "title": "Fix issue",
                "state": "OPEN",
                "is_draft": True,
                "url": "https://github.com/owner/repo/pull/42",
                "author": "copilot-swe-agent[bot]",
            }
        ]

        pr_details = {
            "id": "PR_123",
            "number": 42,
            "last_commit": {"sha": "abc1234567890"},
        }

        # Timeline events with review_requested from Copilot
        timeline_events = [
            {"event": "copilot_work_started"},
            {
                "event": "review_requested",
                "review_requester": {"login": "Copilot"},
                "requested_reviewer": {"login": "some-user"},
            },
        ]

        with (
            patch.object(
                service, "get_linked_pull_requests", new_callable=AsyncMock
            ) as mock_get_prs,
            patch.object(service, "get_pull_request", new_callable=AsyncMock) as mock_get_pr,
            patch.object(
                service, "get_pr_timeline_events", new_callable=AsyncMock
            ) as mock_get_timeline,
        ):
            mock_get_prs.return_value = linked_prs
            mock_get_pr.return_value = pr_details
            mock_get_timeline.return_value = timeline_events

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is not None
            assert result["number"] == 42
            assert result["copilot_finished"] is True

    @pytest.mark.asyncio
    async def test_copilot_pr_already_ready_is_finished(self, service):
        """Should detect already-ready Copilot PR (edge case)."""
        linked_prs = [
            {
                "id": "PR_123",
                "number": 42,
                "title": "Fix issue",
                "state": "OPEN",
                "is_draft": False,  # Already marked ready (manual or edge case)
                "url": "https://github.com/owner/repo/pull/42",
                "author": "copilot-swe-agent[bot]",
            }
        ]

        pr_details = {
            "id": "PR_123",
            "number": 42,
        }

        with (
            patch.object(
                service, "get_linked_pull_requests", new_callable=AsyncMock
            ) as mock_get_prs,
            patch.object(service, "get_pull_request", new_callable=AsyncMock) as mock_get_pr,
        ):
            mock_get_prs.return_value = linked_prs
            mock_get_pr.return_value = pr_details

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is not None
            assert result["number"] == 42
            assert result["is_draft"] is False

    @pytest.mark.asyncio
    async def test_no_copilot_pr(self, service):
        """Should return None when no Copilot PR exists."""
        linked_prs = [
            {
                "id": "PR_123",
                "number": 42,
                "state": "OPEN",
                "is_draft": False,
                "author": "human-user",  # Not Copilot
            }
        ]

        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs:
            mock_get_prs.return_value = linked_prs

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_copilot_pr_closed(self, service):
        """Should return None when Copilot PR is closed/merged."""
        linked_prs = [
            {
                "id": "PR_123",
                "number": 42,
                "state": "MERGED",  # Already merged
                "is_draft": False,
                "author": "copilot-swe-agent[bot]",
            }
        ]

        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs:
            mock_get_prs.return_value = linked_prs

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_copilot_draft_pr_no_commits_not_finished(self, service):
        """Should return None when Copilot PR has no finish events yet."""
        linked_prs = [
            {
                "id": "PR_123",
                "number": 42,
                "title": "WIP: Fix issue",
                "state": "OPEN",
                "is_draft": True,
                "url": "https://github.com/owner/repo/pull/42",
                "author": "copilot-swe-agent[bot]",
            }
        ]

        pr_details = {
            "id": "PR_123",
            "number": 42,
            "check_status": None,
            "last_commit": None,
        }

        # No finish events yet - Copilot still working
        timeline_events = [
            {"event": "copilot_work_started"},
            {"event": "committed"},
        ]

        with (
            patch.object(
                service, "get_linked_pull_requests", new_callable=AsyncMock
            ) as mock_get_prs,
            patch.object(service, "get_pull_request", new_callable=AsyncMock) as mock_get_pr,
            patch.object(
                service, "get_pr_timeline_events", new_callable=AsyncMock
            ) as mock_get_timeline,
        ):
            mock_get_prs.return_value = linked_prs
            mock_get_pr.return_value = pr_details
            mock_get_timeline.return_value = timeline_events

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_copilot_with_alternative_bot_name(self, service):
        """Should detect Copilot PR with 'copilot' in author name."""
        linked_prs = [
            {
                "id": "PR_123",
                "number": 42,
                "title": "Fix issue",
                "state": "OPEN",
                "is_draft": False,
                "url": "https://github.com/owner/repo/pull/42",
                "author": "copilot[bot]",  # Alternative Copilot bot name
            }
        ]

        pr_details = {
            "id": "PR_123",
            "number": 42,
        }

        with (
            patch.object(
                service, "get_linked_pull_requests", new_callable=AsyncMock
            ) as mock_get_prs,
            patch.object(service, "get_pull_request", new_callable=AsyncMock) as mock_get_pr,
        ):
            mock_get_prs.return_value = linked_prs
            mock_get_pr.return_value = pr_details

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is not None
            assert result["number"] == 42

    @pytest.mark.asyncio
    async def test_multiple_prs_finds_first_copilot_finished(self, service):
        """Should find first finished Copilot PR when multiple PRs exist."""
        linked_prs = [
            {
                "id": "PR_1",
                "number": 10,
                "state": "OPEN",
                "is_draft": True,
                "author": "human-user",  # Not Copilot
            },
            {
                "id": "PR_2",
                "number": 20,
                "state": "MERGED",
                "is_draft": False,
                "author": "copilot-swe-agent[bot]",  # Merged, not processable
            },
            {
                "id": "PR_3",
                "number": 30,
                "state": "OPEN",
                "is_draft": True,
                "author": "copilot-swe-agent[bot]",  # This is the one
            },
        ]

        pr_details = {
            "id": "PR_3",
            "number": 30,
            "check_status": "SUCCESS",
            "last_commit": {"sha": "abc123"},
        }

        # Timeline events indicating Copilot finished work
        timeline_events = [{"event": "copilot_work_finished"}]

        with (
            patch.object(
                service, "get_linked_pull_requests", new_callable=AsyncMock
            ) as mock_get_prs,
            patch.object(service, "get_pull_request", new_callable=AsyncMock) as mock_get_pr,
            patch.object(
                service, "get_pr_timeline_events", new_callable=AsyncMock
            ) as mock_get_timeline,
        ):
            mock_get_prs.return_value = linked_prs
            mock_get_pr.return_value = pr_details
            mock_get_timeline.return_value = timeline_events

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is not None
            assert result["number"] == 30
            assert result["copilot_finished"] is True

    @pytest.mark.asyncio
    async def test_returns_none_when_no_linked_prs(self, service):
        """Should return None when issue has no linked PRs."""
        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs:
            mock_get_prs.return_value = []

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_handles_exception_gracefully(self, service):
        """Should return None when an exception occurs."""
        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs:
            mock_get_prs.side_effect = Exception("API Error")

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_handles_get_pull_request_returning_none(self, service):
        """Should continue to next PR when get_pull_request returns None."""
        linked_prs = [
            {
                "id": "PR_1",
                "number": 10,
                "state": "OPEN",
                "is_draft": True,
                "author": "copilot-swe-agent[bot]",
            },
            {
                "id": "PR_2",
                "number": 20,
                "state": "OPEN",
                "is_draft": False,  # Already ready
                "author": "copilot-swe-agent[bot]",
            },
        ]

        pr_details_2 = {
            "id": "PR_2",
            "number": 20,
        }

        with (
            patch.object(
                service, "get_linked_pull_requests", new_callable=AsyncMock
            ) as mock_get_prs,
            patch.object(service, "get_pull_request", new_callable=AsyncMock) as mock_get_pr,
        ):
            mock_get_prs.return_value = linked_prs
            # First call returns None, second returns details
            mock_get_pr.side_effect = [None, pr_details_2]

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            # Should still find the second PR which is already ready
            assert result is not None
            assert result["number"] == 20
