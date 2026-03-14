"""Shared GitHub commit workflow — branch → commit → PR → issue pipeline.

Extracts the common pattern used by both the ``#agent`` chat command
(``agent_creator.py``) and the Agents section REST API.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.logging_utils import get_logger
from src.services.github_projects import github_projects_service

logger = get_logger(__name__)


@dataclass
class CommitWorkflowResult:
    """Outcome of the branch → commit → PR → issue pipeline."""

    success: bool = False
    branch_name: str | None = None
    commit_oid: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    issue_number: int | None = None
    issue_node_id: str | None = None
    errors: list[str] = field(default_factory=list)


async def commit_files_workflow(
    *,
    access_token: str,
    owner: str,
    repo: str,
    branch_name: str,
    files: list[dict],
    commit_message: str,
    pr_title: str,
    pr_body: str,
    issue_title: str | None = None,
    issue_body: str | None = None,
    issue_labels: list[str] | None = None,
    project_id: str | None = None,
    target_status: str | None = None,
    delete_files: list[str] | None = None,
) -> CommitWorkflowResult:
    """Execute the shared branch → commit → PR → (optional issue) pipeline.

    Parameters
    ----------
    files
        Files to add/update: ``[{"path": "...", "content": "..."}]``.
    delete_files
        File paths to delete (for deletion workflows).
    issue_title / issue_body / issue_labels
        If provided, a tracking issue is created before the branch.
    project_id / target_status
        If provided, the issue is added to the project board and moved.
    """
    result = CommitWorkflowResult(branch_name=branch_name)

    # ── Step 1: Get repository info ──
    try:
        repo_info = await github_projects_service.get_repository_info(
            access_token,
            owner,
            repo,
        )
    except Exception as exc:
        logger.error(
            "Workflow: get_repository_info failed: %s",
            exc,
            extra={"operation": "get_repository_info"},
        )
        result.errors.append(f"Get repository info failed: {exc}")
        return result

    # ── Step 2: Create tracking issue (optional) ──
    issue_number: int | None = None
    issue_node_id: str | None = None
    issue_database_id: int | None = None

    if issue_title and issue_body:
        try:
            issue = await github_projects_service.create_issue(
                access_token=access_token,
                owner=owner,
                repo=repo,
                title=issue_title,
                body=issue_body,
                labels=issue_labels or [],
            )
            issue_number = issue["number"]
            issue_node_id = issue.get("node_id")
            issue_database_id = issue.get("id")
            result.issue_number = issue_number
            result.issue_node_id = issue_node_id
        except Exception as exc:
            logger.error(
                "Workflow: create_issue failed: %s", exc, extra={"operation": "create_issue"}
            )
            result.errors.append(f"Create issue failed: {exc}")
            # Non-fatal — continue with branch/commit/PR

    # ── Step 3: Create branch ──
    try:
        ref_id = await github_projects_service.create_branch(
            access_token=access_token,
            repository_id=repo_info["repository_id"],
            branch_name=branch_name,
            from_oid=repo_info["head_oid"],
        )
        if not ref_id:
            result.errors.append("create_branch returned None")
            return result
    except Exception as exc:
        logger.error(
            "Workflow: create_branch failed: %s", exc, extra={"operation": "create_branch"}
        )
        result.errors.append(f"Create branch failed: {exc}")
        return result

    # ── Step 4: Commit files ──
    try:
        commit_oid = await github_projects_service.commit_files(
            access_token=access_token,
            owner=owner,
            repo=repo,
            branch_name=branch_name,
            head_oid=repo_info["head_oid"],
            files=files or [],
            message=commit_message,
            deletions=delete_files,
        )
        if not commit_oid:
            result.errors.append("commit_files returned None")
            return result
        result.commit_oid = commit_oid
    except Exception as exc:
        logger.error("Workflow: commit_files failed: %s", exc, extra={"operation": "commit_files"})
        result.errors.append(f"Commit files failed: {exc}")
        return result

    # ── Step 5: Open Pull Request ──
    # Attach PR to the tracking issue if one was created
    final_pr_body = pr_body
    if issue_number:
        final_pr_body = f"{pr_body}\n\nCloses #{issue_number}"

    try:
        pr_info = await github_projects_service.create_pull_request(
            access_token=access_token,
            repository_id=repo_info["repository_id"],
            title=pr_title,
            body=final_pr_body,
            head_branch=branch_name,
            base_branch=repo_info["default_branch"],
        )
        if pr_info:
            result.pr_number = pr_info.get("number", 0)
            result.pr_url = pr_info.get("url", "")
            result.success = True
        else:
            result.errors.append("create_pull_request returned None")
            return result
    except Exception as exc:
        logger.error(
            "Workflow: create_pull_request failed: %s",
            exc,
            extra={"operation": "create_pull_request"},
        )
        result.errors.append(f"Create PR failed: {exc}")
        return result

    # ── Step 6: Add issue to project board (optional) ──
    if issue_node_id and project_id and target_status:
        try:
            item_id = await github_projects_service.add_issue_to_project(
                access_token=access_token,
                project_id=project_id,
                issue_node_id=issue_node_id,
                issue_database_id=issue_database_id,
            )
            if item_id:
                await github_projects_service.update_item_status_by_name(
                    access_token=access_token,
                    project_id=project_id,
                    item_id=item_id,
                    status_name=target_status,
                )
        except Exception as exc:
            logger.warning("Workflow: move issue to project board failed: %s", exc)
            result.errors.append(f"Move issue to board failed: {exc}")
            # Non-fatal — PR was already created

    return result
