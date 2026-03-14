from __future__ import annotations

# pyright: reportAttributeAccessIssue=false
from src.logging_utils import get_logger
from src.services.github_projects.graphql import (
    CREATE_BRANCH_MUTATION,
    GET_BRANCH_HEAD_QUERY,
)

logger = get_logger(__name__)


class BranchesMixin:
    """Branch creation, deletion, and HEAD lookup."""

    async def delete_branch(
        self,
        access_token: str,
        owner: str,
        repo: str,
        branch_name: str,
    ) -> bool:
        """
        Delete a branch from a repository.

        Used to clean up child PR branches after they are merged into the
        parent/main branch for an issue.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            branch_name: Name of the branch to delete (without refs/heads/ prefix)

        Returns:
            True if branch was deleted successfully
        """
        try:
            # Use REST API to delete the branch reference
            response = await self._rest_response(
                access_token,
                "DELETE",
                f"/repos/{owner}/{repo}/git/refs/heads/{branch_name}",
            )

            if response.status_code == 204:
                logger.info(
                    "Successfully deleted branch '%s' from %s/%s",
                    branch_name,
                    owner,
                    repo,
                )
                return True
            elif response.status_code == 422:
                # Branch doesn't exist or already deleted
                logger.debug(
                    "Branch '%s' does not exist or was already deleted",
                    branch_name,
                )
                return True
            else:
                logger.warning(
                    "Failed to delete branch '%s': %d %s",
                    branch_name,
                    response.status_code,
                    response.text,
                )
                return False

        except Exception as e:
            logger.error("Failed to delete branch '%s': %s", branch_name, e)
            return False

    async def create_branch(
        self,
        access_token: str,
        repository_id: str,
        branch_name: str,
        from_oid: str,
    ) -> str | None:
        """Create a Git branch from a given commit SHA.

        Args:
            access_token: GitHub OAuth token.
            repository_id: Repository node ID.
            branch_name: Bare branch name (e.g., ``agent/my-bot``).
            from_oid: Commit SHA to branch from.

        Returns:
            Ref ID on success, ``None`` on failure.
        """
        qualified_name = f"refs/heads/{branch_name}"
        try:
            data = await self._graphql(
                access_token,
                CREATE_BRANCH_MUTATION,
                {
                    "repositoryId": repository_id,
                    "name": qualified_name,
                    "oid": from_oid,
                },
            )
            ref_data = (data.get("createRef") or {}).get("ref") or {}
            ref_id = ref_data.get("id")
            logger.info("Created branch %s (ref=%s)", branch_name, ref_id)
            return ref_id
        except ValueError as exc:
            error_msg = str(exc).lower()
            # Branch already exists — treat as success for idempotent pipeline
            if "already exists" in error_msg or "reference already exists" in error_msg:
                logger.info("Branch %s already exists — treating as success", branch_name)
                return "existing"
            logger.error("Failed to create branch %s: %s", branch_name, exc)
            return None

    async def get_branch_head_oid(
        self,
        access_token: str,
        owner: str,
        repo: str,
        branch_name: str,
    ) -> str | None:
        """Fetch the HEAD OID for a specific branch.

        Args:
            access_token: GitHub OAuth token.
            owner: Repository owner.
            repo: Repository name.
            branch_name: Bare branch name (e.g., ``chore/add-template-foo``).

        Returns:
            Commit SHA on success, ``None`` if branch not found.
        """
        qualified = f"refs/heads/{branch_name}"
        try:
            data = await self._graphql(
                access_token,
                GET_BRANCH_HEAD_QUERY,
                {"owner": owner, "name": repo, "qualifiedName": qualified},
            )
            ref = (data.get("repository") or {}).get("ref")
            if not ref:
                return None
            return (ref.get("target") or {}).get("oid")
        except ValueError:
            return None
