"""Unit tests for BranchesMixin (delete, create, HEAD lookup)."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.services.github_projects import GitHubProjectsService

# ---------------------------------------------------------------------------
# delete_branch
# ---------------------------------------------------------------------------


class TestDeleteBranch:
    """Tests for delete_branch."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_returns_true_on_204(self, service):
        """Successful deletion returns True."""
        mock_resp = Mock(status_code=204)
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.delete_branch("tok", "owner", "repo", "feature/x")
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_true_on_422_already_deleted(self, service):
        """Branch already deleted (422) is treated as success."""
        mock_resp = Mock(status_code=422)
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.delete_branch("tok", "owner", "repo", "feature/x")
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_on_404(self, service):
        """A 404 (or any non-204/422 status) returns False."""
        mock_resp = Mock(status_code=404, text="Not Found")
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.delete_branch("tok", "owner", "repo", "feature/x")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_500(self, service):
        """Server error returns False."""
        mock_resp = Mock(status_code=500, text="Internal Server Error")
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.delete_branch("tok", "owner", "repo", "feature/x")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_exception(self, service):
        """Network-level exception returns False."""
        service._rest_response = AsyncMock(side_effect=Exception("timeout"))
        result = await service.delete_branch("tok", "owner", "repo", "feature/x")
        assert result is False

    @pytest.mark.asyncio
    async def test_calls_rest_with_correct_path(self, service):
        """Should call REST DELETE with the correct refs/heads/ path."""
        mock_resp = Mock(status_code=204)
        service._rest_response = AsyncMock(return_value=mock_resp)
        await service.delete_branch("tok", "owner", "repo", "my-branch")
        service._rest_response.assert_awaited_once_with(
            "tok",
            "DELETE",
            "/repos/owner/repo/git/refs/heads/my-branch",
        )


# ---------------------------------------------------------------------------
# create_branch
# ---------------------------------------------------------------------------


class TestCreateBranch:
    """Tests for create_branch."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_returns_ref_id_on_success(self, service):
        """Should return the ref ID from the GraphQL response."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={"createRef": {"ref": {"id": "REF_abc123"}}},
        ):
            result = await service.create_branch("tok", "REPO_ID", "feature/x", "deadbeef")
        assert result == "REF_abc123"

    @pytest.mark.asyncio
    async def test_returns_existing_when_branch_already_exists(self, service):
        """Idempotent: returns 'existing' when branch already exists."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            side_effect=ValueError("Reference already exists"),
        ):
            result = await service.create_branch("tok", "REPO_ID", "feature/x", "deadbeef")
        assert result == "existing"

    @pytest.mark.asyncio
    async def test_returns_existing_on_already_exists_variant(self, service):
        """Idempotent: handles the 'already exists' wording variant."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            side_effect=ValueError("Branch already exists for this repo"),
        ):
            result = await service.create_branch("tok", "REPO_ID", "feature/x", "deadbeef")
        assert result == "existing"

    @pytest.mark.asyncio
    async def test_returns_none_on_other_value_error(self, service):
        """Non-duplicate ValueError returns None."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            side_effect=ValueError("Something completely different"),
        ):
            result = await service.create_branch("tok", "REPO_ID", "feature/x", "deadbeef")
        assert result is None

    @pytest.mark.asyncio
    async def test_passes_qualified_ref_name(self, service):
        """Should prefix branch_name with refs/heads/."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={"createRef": {"ref": {"id": "REF_1"}}},
        ) as mock_gql:
            await service.create_branch("tok", "REPO_ID", "my-branch", "abc123")
        variables = mock_gql.call_args[0][2]
        assert variables["name"] == "refs/heads/my-branch"

    @pytest.mark.asyncio
    async def test_handles_missing_ref_in_response(self, service):
        """Should return None when createRef.ref is missing."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={"createRef": {"ref": None}},
        ):
            result = await service.create_branch("tok", "REPO_ID", "feature/x", "deadbeef")
        assert result is None

    @pytest.mark.asyncio
    async def test_handles_empty_create_ref(self, service):
        """Should return None when createRef is None."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={"createRef": None},
        ):
            result = await service.create_branch("tok", "REPO_ID", "feature/x", "deadbeef")
        assert result is None


# ---------------------------------------------------------------------------
# get_branch_head_oid
# ---------------------------------------------------------------------------


class TestGetBranchHeadOid:
    """Tests for get_branch_head_oid."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_returns_oid_on_success(self, service):
        """Should return the commit OID for an existing branch."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={"repository": {"ref": {"target": {"oid": "abc123"}}}},
        ):
            result = await service.get_branch_head_oid("tok", "owner", "repo", "feature/x")
        assert result == "abc123"

    @pytest.mark.asyncio
    async def test_returns_none_when_branch_missing(self, service):
        """Should return None when the branch does not exist."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={"repository": {"ref": None}},
        ):
            result = await service.get_branch_head_oid("tok", "owner", "repo", "gone")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_graphql_value_error(self, service):
        """Should return None when _graphql raises ValueError."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            side_effect=ValueError("Not found"),
        ):
            result = await service.get_branch_head_oid("tok", "owner", "repo", "bad")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_repository_is_none(self, service):
        """Should return None when the repository key is None."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={"repository": None},
        ):
            result = await service.get_branch_head_oid("tok", "owner", "repo", "x")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_target_is_none(self, service):
        """Should return None when target is None."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={"repository": {"ref": {"target": None}}},
        ):
            result = await service.get_branch_head_oid("tok", "owner", "repo", "x")
        assert result is None

    @pytest.mark.asyncio
    async def test_passes_qualified_ref_name(self, service):
        """Should prefix the branch name with refs/heads/."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={"repository": {"ref": {"target": {"oid": "def456"}}}},
        ) as mock_gql:
            await service.get_branch_head_oid("tok", "owner", "repo", "my-branch")
        variables = mock_gql.call_args[0][2]
        assert variables["qualifiedName"] == "refs/heads/my-branch"
