"""Unit tests for RepositoryMixin (file/dir contents, repo info, commits)."""

import base64
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.services.github_projects import GitHubProjectsService

# ---------------------------------------------------------------------------
# get_repository_owner
# ---------------------------------------------------------------------------


class TestGetRepositoryOwner:
    """Tests for get_repository_owner."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_returns_owner_login(self, service):
        """Should return the owner login from REST response."""
        service._rest = AsyncMock(return_value={"owner": {"login": "octocat"}, "name": "my-repo"})
        result = await service.get_repository_owner("tok", "octocat", "my-repo")
        assert result == "octocat"

    @pytest.mark.asyncio
    async def test_falls_back_to_owner_param_when_missing(self, service):
        """Should return the owner param when owner.login is absent."""
        service._rest = AsyncMock(return_value={})
        result = await service.get_repository_owner("tok", "fallback-owner", "repo")
        assert result == "fallback-owner"

    @pytest.mark.asyncio
    async def test_calls_rest_with_correct_path(self, service):
        """Should call REST GET /repos/{owner}/{repo}."""
        service._rest = AsyncMock(return_value={"owner": {"login": "org1"}, "name": "repo1"})
        await service.get_repository_owner("tok", "org1", "repo1")
        service._rest.assert_awaited_once_with("tok", "GET", "/repos/org1/repo1")


# ---------------------------------------------------------------------------
# get_directory_contents
# ---------------------------------------------------------------------------


class TestGetDirectoryContents:
    """Tests for get_directory_contents."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_returns_list_on_200(self, service):
        """Should return the list of files when status is 200."""
        items = [{"name": "README.md", "path": "README.md", "type": "file"}]
        mock_resp = Mock(status_code=200)
        mock_resp.json.return_value = items
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.get_directory_contents("tok", "o", "r", "src")
        assert result == items

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_non_list_data(self, service):
        """Should return [] when response data is not a list (single file)."""
        mock_resp = Mock(status_code=200)
        mock_resp.json.return_value = {"name": "file.txt", "type": "file"}
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.get_directory_contents("tok", "o", "r", "file.txt")
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_404(self, service):
        """Should return [] on a 404 status."""
        mock_resp = Mock(status_code=404)
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.get_directory_contents("tok", "o", "r", "missing")
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_exception(self, service):
        """Network error returns []."""
        service._rest_response = AsyncMock(side_effect=Exception("timeout"))
        result = await service.get_directory_contents("tok", "o", "r", "src")
        assert result == []

    @pytest.mark.asyncio
    async def test_calls_rest_response_with_correct_path(self, service):
        """Should call _rest_response with the correct contents path."""
        mock_resp = Mock(status_code=200)
        mock_resp.json.return_value = []
        service._rest_response = AsyncMock(return_value=mock_resp)
        await service.get_directory_contents("tok", "owner", "repo", "src/lib")
        service._rest_response.assert_awaited_once_with(
            "tok", "GET", "/repos/owner/repo/contents/src/lib"
        )


# ---------------------------------------------------------------------------
# get_file_content
# ---------------------------------------------------------------------------


class TestGetFileContent:
    """Tests for get_file_content."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_returns_decoded_content_on_200(self, service):
        """Should return dict with content and name on success."""
        mock_resp = Mock(status_code=200, text="Hello world")
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.get_file_content("tok", "o", "r", "dir/readme.md")
        assert result == {"content": "Hello world", "name": "readme.md"}

    @pytest.mark.asyncio
    async def test_returns_none_on_404(self, service):
        """Should return None on 404."""
        mock_resp = Mock(status_code=404)
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.get_file_content("tok", "o", "r", "missing.txt")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self, service):
        """Network error returns None."""
        service._rest_response = AsyncMock(side_effect=Exception("boom"))
        result = await service.get_file_content("tok", "o", "r", "file.py")
        assert result is None

    @pytest.mark.asyncio
    async def test_sends_raw_accept_header(self, service):
        """Should include the raw+json Accept header."""
        mock_resp = Mock(status_code=200, text="content")
        service._rest_response = AsyncMock(return_value=mock_resp)
        await service.get_file_content("tok", "o", "r", "f.txt")
        call_kwargs = service._rest_response.call_args
        assert call_kwargs[1]["headers"]["Accept"] == "application/vnd.github.raw+json"


# ---------------------------------------------------------------------------
# get_file_content_from_ref
# ---------------------------------------------------------------------------


class TestGetFileContentFromRef:
    """Tests for get_file_content_from_ref."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_returns_content_on_200(self, service):
        """Should return the raw text content on success."""
        mock_resp = Mock(status_code=200, text="file contents here")
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.get_file_content_from_ref(
            "tok", "o", "r", "src/main.py", "feature-branch"
        )
        assert result == "file contents here"

    @pytest.mark.asyncio
    async def test_returns_none_on_non_200(self, service):
        """Should return None when the API returns a non-200 status."""
        mock_resp = Mock(status_code=404)
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.get_file_content_from_ref("tok", "o", "r", "gone.py", "main")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self, service):
        """Network error returns None."""
        service._rest_response = AsyncMock(side_effect=Exception("connection reset"))
        result = await service.get_file_content_from_ref("tok", "o", "r", "file.py", "main")
        assert result is None

    @pytest.mark.asyncio
    async def test_passes_ref_param(self, service):
        """Should include the ref query parameter."""
        mock_resp = Mock(status_code=200, text="ok")
        service._rest_response = AsyncMock(return_value=mock_resp)
        await service.get_file_content_from_ref("tok", "owner", "repo", "path/file.py", "my-branch")
        call_kwargs = service._rest_response.call_args
        assert call_kwargs[1]["params"] == {"ref": "my-branch"}


# ---------------------------------------------------------------------------
# get_repository_info
# ---------------------------------------------------------------------------


class TestGetRepositoryInfo:
    """Tests for get_repository_info."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_returns_repo_info_on_success(self, service):
        """Should return repository_id, default_branch, and head_oid."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={
                "repository": {
                    "id": "R_abc123",
                    "defaultBranchRef": {
                        "name": "main",
                        "target": {"oid": "deadbeef"},
                    },
                }
            },
        ):
            result = await service.get_repository_info("tok", "owner", "repo")
        assert result == {
            "repository_id": "R_abc123",
            "default_branch": "main",
            "head_oid": "deadbeef",
        }

    @pytest.mark.asyncio
    async def test_defaults_when_default_branch_ref_is_none(self, service):
        """Should use 'main' and empty oid when defaultBranchRef is None."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={
                "repository": {
                    "id": "R_xyz",
                    "defaultBranchRef": None,
                }
            },
        ):
            result = await service.get_repository_info("tok", "owner", "repo")
        assert result["default_branch"] == "main"
        assert result["head_oid"] == ""

    @pytest.mark.asyncio
    async def test_raises_when_repository_not_found(self, service):
        """Should raise ValueError when repository is None."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={"repository": None},
        ):
            with pytest.raises(ValueError, match="not found"):
                await service.get_repository_info("tok", "owner", "repo")

    @pytest.mark.asyncio
    async def test_passes_correct_variables(self, service):
        """Should pass owner and name as variables."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={
                "repository": {
                    "id": "R_1",
                    "defaultBranchRef": {"name": "main", "target": {"oid": "abc"}},
                }
            },
        ) as mock_gql:
            await service.get_repository_info("tok", "my-org", "my-repo")
        variables = mock_gql.call_args[0][2]
        assert variables == {"owner": "my-org", "name": "my-repo"}

    @pytest.mark.asyncio
    async def test_handles_missing_target_in_default_branch_ref(self, service):
        """Should return empty head_oid when target is missing."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={
                "repository": {
                    "id": "R_no_target",
                    "defaultBranchRef": {"name": "develop", "target": None},
                }
            },
        ):
            result = await service.get_repository_info("tok", "o", "r")
        assert result["default_branch"] == "develop"
        assert result["head_oid"] == ""


# ---------------------------------------------------------------------------
# commit_files
# ---------------------------------------------------------------------------


class TestCommitFiles:
    """Tests for commit_files."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    def _make_files(self):
        return [{"path": "hello.txt", "content": "Hello"}]

    @pytest.mark.asyncio
    async def test_returns_oid_on_success(self, service):
        """Should return the commit OID on a successful commit."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={
                "createCommitOnBranch": {"commit": {"oid": "newsha123", "url": "https://..."}}
            },
        ):
            result = await service.commit_files(
                "tok", "owner", "repo", "feature", "headoid", self._make_files(), "msg"
            )
        assert result == "newsha123"

    @pytest.mark.asyncio
    async def test_base64_encodes_file_contents(self, service):
        """Should base64 encode file contents in the mutation variables."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={"createCommitOnBranch": {"commit": {"oid": "abc"}}},
        ) as mock_gql:
            await service.commit_files(
                "tok", "owner", "repo", "br", "oid1", self._make_files(), "commit"
            )
        variables = mock_gql.call_args[0][2]
        encoded = variables["fileChanges"]["additions"][0]["contents"]
        assert base64.b64decode(encoded).decode() == "Hello"

    @pytest.mark.asyncio
    async def test_returns_none_on_non_oid_error(self, service):
        """Non-OID ValueError returns None."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            side_effect=ValueError("some random error"),
        ):
            result = await service.commit_files(
                "tok", "owner", "repo", "br", "oid", self._make_files(), "msg"
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_retries_on_oid_mismatch(self, service):
        """Should retry up to 3 times on OID mismatch errors."""
        call_count = 0

        async def graphql_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("expected head oid did not match")
            return {"createCommitOnBranch": {"commit": {"oid": "final_oid"}}}

        service._graphql = AsyncMock(side_effect=graphql_side_effect)
        service.get_branch_head_oid = AsyncMock(return_value="fresh_oid")

        result = await service.commit_files(
            "tok", "owner", "repo", "br", "stale_oid", self._make_files(), "msg"
        )
        assert result == "final_oid"
        assert service.get_branch_head_oid.await_count == 2

    @pytest.mark.asyncio
    async def test_returns_none_after_max_oid_retries(self, service):
        """Should return None after exhausting all OID retry attempts."""
        service._graphql = AsyncMock(side_effect=ValueError("expected head oid did not match"))
        service.get_branch_head_oid = AsyncMock(return_value="fresh_oid")

        result = await service.commit_files(
            "tok", "owner", "repo", "br", "stale", self._make_files(), "msg"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_retries_on_expected_branch_to_point_to(self, service):
        """Should also retry on 'expected branch to point to' OID mismatch."""
        call_count = 0

        async def graphql_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("expected branch to point to abc123")
            return {"createCommitOnBranch": {"commit": {"oid": "ok"}}}

        service._graphql = AsyncMock(side_effect=graphql_side_effect)
        service.get_branch_head_oid = AsyncMock(return_value="new_oid")

        result = await service.commit_files(
            "tok", "owner", "repo", "br", "old_oid", self._make_files(), "msg"
        )
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_returns_none_when_commit_response_empty(self, service):
        """Should return None when createCommitOnBranch is None."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={"createCommitOnBranch": None},
        ):
            result = await service.commit_files(
                "tok", "owner", "repo", "br", "oid", self._make_files(), "msg"
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_includes_deletions_when_provided(self, service):
        """Should include deletion paths in fileChanges."""
        with patch.object(
            service,
            "_graphql",
            new_callable=AsyncMock,
            return_value={"createCommitOnBranch": {"commit": {"oid": "del_oid"}}},
        ) as mock_gql:
            await service.commit_files(
                "tok",
                "owner",
                "repo",
                "br",
                "oid",
                self._make_files(),
                "msg",
                deletions=["old_file.txt"],
            )
        variables = mock_gql.call_args[0][2]
        assert variables["fileChanges"]["deletions"] == [{"path": "old_file.txt"}]

    @pytest.mark.asyncio
    async def test_continues_retry_when_get_branch_head_oid_fails(self, service):
        """Should continue retrying even if get_branch_head_oid raises."""
        call_count = 0

        async def graphql_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("expected head oid mismatch")
            return {"createCommitOnBranch": {"commit": {"oid": "ok"}}}

        service._graphql = AsyncMock(side_effect=graphql_side_effect)
        service.get_branch_head_oid = AsyncMock(side_effect=Exception("network error"))

        result = await service.commit_files(
            "tok", "owner", "repo", "br", "oid", self._make_files(), "msg"
        )
        assert result == "ok"
