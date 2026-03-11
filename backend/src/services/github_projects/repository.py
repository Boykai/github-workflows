from __future__ import annotations

# pyright: reportAttributeAccessIssue=false
import base64
from typing import cast

from src.logging_utils import get_logger
from src.services.github_projects.graphql import (
    CREATE_COMMIT_ON_BRANCH_MUTATION,
    GET_REPOSITORY_INFO_QUERY,
)

logger = get_logger(__name__)


class RepositoryMixin:
    """Repository info, file/directory contents, and commit operations."""

    async def get_repository_owner(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> str:
        """
        Get the repository owner username (T043).

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner (may be org)
            repo: Repository name

        Returns:
            Owner username
        """
        repo_data = cast(dict, await self._rest(access_token, "GET", f"/repos/{owner}/{repo}"))

        # Return the owner login
        return repo_data.get("owner", {}).get("login", owner)

    async def get_directory_contents(
        self,
        access_token: str,
        owner: str,
        repo: str,
        path: str,
    ) -> list[dict]:
        """List files in a directory from the default branch via REST API.

        Returns a list of dicts with ``name``, ``path``, ``type`` keys.
        For files, ``content`` is NOT included (use ``get_file_content`` separately).
        """
        try:
            response = await self._rest_response(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/contents/{path}",
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
                return []
            return []
        except Exception as exc:
            logger.debug("get_directory_contents(%s/%s/%s) failed: %s", owner, repo, path, exc)
            return []

    async def get_file_content(
        self,
        access_token: str,
        owner: str,
        repo: str,
        path: str,
    ) -> dict | None:
        """Get a single file's decoded content from the default branch.

        Returns a dict with ``content`` (decoded text) and ``name``, or None.
        """
        try:
            response = await self._rest_response(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/contents/{path}",
                headers={"Accept": "application/vnd.github.raw+json"},
            )
            if response.status_code == 200:
                return {"content": response.text, "name": path.split("/")[-1]}
            return None
        except Exception as exc:
            logger.debug("get_file_content(%s/%s/%s) failed: %s", owner, repo, path, exc)
            return None

    async def get_file_content_from_ref(
        self,
        access_token: str,
        owner: str,
        repo: str,
        path: str,
        ref: str,
    ) -> str | None:
        """
        Get the content of a file from a specific branch/ref.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            path: File path within the repository
            ref: Git ref (branch name, commit SHA, etc.)

        Returns:
            File content as a string, or None if not found
        """
        try:
            response = await self._rest_response(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/contents/{path}",
                headers={"Accept": "application/vnd.github.raw+json"},
                params={"ref": ref},
            )

            if response.status_code == 200:
                return response.text
            else:
                logger.warning(
                    "Failed to get file %s@%s: %s",
                    path,
                    ref,
                    response.status_code,
                )
                return None

        except Exception as e:
            logger.error("Error getting file %s@%s: %s", path, ref, e)
            return None

    # ──────────────────────────────────────────────────────────────────
    # Agent Creator: Repository info, branch, commit, and PR methods
    # ──────────────────────────────────────────────────────────────────

    async def get_repository_info(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> dict:
        """Fetch repository node ID, default branch name, and HEAD SHA.

        Returns:
            ``{"repository_id": str, "default_branch": str, "head_oid": str}``
        """
        data = await self._graphql(
            access_token,
            GET_REPOSITORY_INFO_QUERY,
            {"owner": owner, "name": repo},
        )
        repo_data = data.get("repository")
        if not repo_data:
            raise ValueError(f"Repository {owner}/{repo} not found")

        default_ref = repo_data.get("defaultBranchRef") or {}
        return {
            "repository_id": repo_data["id"],
            "default_branch": default_ref.get("name", "main"),
            "head_oid": (default_ref.get("target") or {}).get("oid", ""),
        }

    async def commit_files(
        self,
        access_token: str,
        owner: str,
        repo: str,
        branch_name: str,
        head_oid: str,
        files: list[dict],
        message: str,
        deletions: list[str] | None = None,
    ) -> str | None:
        """Commit files to a branch without cloning.

        Args:
            access_token: GitHub OAuth token.
            owner: Repository owner.
            repo: Repository name.
            branch_name: Bare branch name.
            head_oid: Expected HEAD OID for optimistic concurrency.
            files: ``[{"path": "relative/path", "content": "text content"}]``
            message: Commit message headline.
            deletions: Optional list of file paths to delete in this commit.

        Returns:
            Commit OID on success, ``None`` on failure.
        """
        additions = [
            {
                "path": f["path"],
                "contents": base64.b64encode(f["content"].encode()).decode(),
            }
            for f in files
        ]

        file_changes: dict = {"additions": additions}
        if deletions:
            file_changes["deletions"] = [{"path": p} for p in deletions]

        max_attempts = 3
        current_oid = head_oid
        for attempt in range(1, max_attempts + 1):
            try:
                data = await self._graphql(
                    access_token,
                    CREATE_COMMIT_ON_BRANCH_MUTATION,
                    {
                        "repoWithOwner": f"{owner}/{repo}",
                        "branchName": branch_name,
                        "expectedHeadOid": current_oid,
                        "message": {"headline": message},
                        "fileChanges": file_changes,
                    },
                )
                commit = (data.get("createCommitOnBranch") or {}).get("commit") or {}
                oid = commit.get("oid")
                logger.info("Committed files to %s (oid=%s)", branch_name, oid)
                return oid
            except ValueError as exc:
                error_msg = str(exc).lower()
                # GitHub may phrase OID mismatch as "expected head oid" or
                # "expected branch to point to" — match both variants.
                is_oid_mismatch = (
                    "expected head oid" in error_msg or "expected branch to point to" in error_msg
                )
                if is_oid_mismatch and attempt < max_attempts:
                    # OID mismatch — fetch fresh HEAD for this specific branch
                    logger.warning(
                        "OID mismatch on commit attempt %d/%d for %s, refreshing branch HEAD",
                        attempt,
                        max_attempts,
                        branch_name,
                    )
                    try:
                        fresh_oid = await self.get_branch_head_oid(
                            access_token, owner, repo, branch_name
                        )
                        if fresh_oid:
                            current_oid = fresh_oid
                    except Exception as e:
                        logger.debug("Suppressed error: %s", e)
                    continue
                logger.error("Failed to commit files to %s: %s", branch_name, exc)
                return None
        return None
