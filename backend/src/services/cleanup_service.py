"""Service for repository cleanup operations.

Provides preflight analysis, sequential execution, and audit trail for
deleting stale branches and closing stale PRs while preserving items
linked to open issues on the associated GitHub Project board.
"""

import asyncio
import json
import logging
import re
import uuid
from datetime import UTC, datetime

from src.models.cleanup import (
    BranchInfo,
    CleanupAuditLogRow,
    CleanupExecuteRequest,
    CleanupExecuteResponse,
    CleanupHistoryResponse,
    CleanupItemResult,
    CleanupPreflightRequest,
    CleanupPreflightResponse,
    PullRequestInfo,
)

logger = logging.getLogger(__name__)

# Delay between sequential deletion requests to respect GitHub secondary rate limits
DELETION_DELAY_SECONDS = 0.2

# Patterns for branch naming conventions that reference issue numbers
# Matches: issue-123, 123-feature-name, copilot/fix-123, etc.
ISSUE_NUMBER_PATTERNS = [
    re.compile(r"^(?:issue-?)(\d+)", re.IGNORECASE),
    re.compile(r"^(\d+)-"),
    re.compile(r"(?:^|/)(?:fix|close|resolve|feature|bug|hotfix)[/-](\d+)", re.IGNORECASE),
]

# Patterns for issue references in PR body text
# Matches: Closes #123, Fixes #123, Resolves #123, refs #123
PR_BODY_ISSUE_PATTERNS = [
    re.compile(r"(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)", re.IGNORECASE),
    re.compile(r"#(\d+)"),
]


def _extract_issue_numbers_from_branch(branch_name: str) -> list[int]:
    """Extract referenced issue numbers from a branch name using naming conventions."""
    numbers = []
    for pattern in ISSUE_NUMBER_PATTERNS:
        match = pattern.search(branch_name)
        if match:
            numbers.append(int(match.group(1)))
    return list(set(numbers))


def _extract_issue_numbers_from_text(text: str) -> list[int]:
    """Extract referenced issue numbers from PR body text."""
    if not text:
        return []
    numbers = []
    for pattern in PR_BODY_ISSUE_PATTERNS:
        for match in pattern.finditer(text):
            numbers.append(int(match.group(1)))
    return list(set(numbers))


async def check_user_permission(
    github_service,
    access_token: str,
    owner: str,
    repo: str,
    username: str,
) -> tuple[bool, str | None]:
    """Check if the user has push access to the repository.

    Returns (has_permission, permission_error_message).
    """
    try:
        headers = github_service._build_headers(access_token)
        response = await github_service._client.get(
            f"https://api.github.com/repos/{owner}/{repo}/collaborators/{username}/permission",
            headers=headers,
        )
        if response.status_code == 200:
            data = response.json()
            permission = data.get("permission", "none")
            if permission in ("admin", "write", "maintain"):
                return True, None
            return False, (
                "You need at least push access to this repository "
                "to delete branches and close pull requests."
            )
        return False, f"Unable to verify permissions: HTTP {response.status_code}"
    except Exception as e:
        logger.error("Permission check failed: %s", e)
        return False, f"Permission check failed: {e}"


async def fetch_all_branches(
    github_service,
    access_token: str,
    owner: str,
    repo: str,
) -> list[dict]:
    """Fetch all branches from the repository via REST API with pagination."""
    branches = []
    page = 1
    per_page = 100
    headers = github_service._build_headers(access_token)

    while True:
        response = await github_service._client.get(
            f"https://api.github.com/repos/{owner}/{repo}/branches"
            f"?per_page={per_page}&page={page}",
            headers=headers,
        )
        if response.status_code != 200:
            logger.error("Failed to fetch branches page %d: %d", page, response.status_code)
            break

        page_branches = response.json()
        if not page_branches:
            break

        branches.extend(page_branches)
        if len(page_branches) < per_page:
            break
        page += 1

    return branches


async def fetch_open_prs(
    github_service,
    access_token: str,
    owner: str,
    repo: str,
) -> list[dict]:
    """Fetch all open PRs from the repository via REST API with pagination."""
    prs = []
    page = 1
    per_page = 100
    headers = github_service._build_headers(access_token)

    while True:
        response = await github_service._client.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls"
            f"?state=open&per_page={per_page}&page={page}",
            headers=headers,
        )
        if response.status_code != 200:
            logger.error("Failed to fetch PRs page %d: %d", page, response.status_code)
            break

        page_prs = response.json()
        if not page_prs:
            break

        prs.extend(page_prs)
        if len(page_prs) < per_page:
            break
        page += 1

    return prs


async def fetch_open_issues_on_board(
    github_service,
    access_token: str,
    project_id: str,
) -> list[dict]:
    """Fetch open issues from the GitHub Project board via GraphQL.

    Returns list of dicts with 'number', 'title', 'repository' info.
    """
    query = """
    query($projectId: ID!, $first: Int!, $after: String) {
      node(id: $projectId) {
        ... on ProjectV2 {
          items(first: $first, after: $after) {
            pageInfo { hasNextPage endCursor }
            nodes {
              content {
                ... on Issue {
                  number
                  title
                  state
                  repository { nameWithOwner }
                }
              }
            }
          }
        }
      }
    }
    """
    issues = []
    has_next = True
    after = None

    while has_next:
        data = await github_service._graphql(
            access_token,
            query,
            {"projectId": project_id, "first": 100, "after": after},
        )
        node = data.get("node")
        if not node:
            break

        items_data = node.get("items", {})
        page_info = items_data.get("pageInfo", {})
        has_next = page_info.get("hasNextPage", False)
        after = page_info.get("endCursor")

        for item in items_data.get("nodes", []):
            content = item.get("content") if item else None
            if not content:
                continue
            # Only include open issues (not PRs, not closed issues)
            if content.get("state") == "OPEN" and content.get("number") is not None:
                issues.append(content)

    return issues


async def preflight(
    github_service,
    access_token: str,
    username: str,
    request: CleanupPreflightRequest,
) -> CleanupPreflightResponse:
    """Perform a preflight check for the cleanup operation.

    Fetches all branches, open PRs, and open issues on the project board.
    Cross-references to determine which items to delete and which to preserve.
    """
    owner = request.owner
    repo = request.repo

    # 1. Check user permissions
    has_permission, permission_error = await check_user_permission(
        github_service, access_token, owner, repo, username
    )
    if not has_permission:
        return CleanupPreflightResponse(
            branches_to_delete=[],
            branches_to_preserve=[],
            prs_to_close=[],
            prs_to_preserve=[],
            open_issues_on_board=0,
            has_permission=False,
            permission_error=permission_error,
        )

    # 2. Fetch all data concurrently
    branches_data, prs_data, board_issues = await asyncio.gather(
        fetch_all_branches(github_service, access_token, owner, repo),
        fetch_open_prs(github_service, access_token, owner, repo),
        fetch_open_issues_on_board(github_service, access_token, request.project_id),
    )

    # 3. Build set of open issue numbers on the project board
    open_issue_numbers: set[int] = set()
    issue_titles: dict[int, str] = {}
    for issue in board_issues:
        num = issue.get("number")
        if num is not None:
            open_issue_numbers.add(num)
            issue_titles[num] = issue.get("title", "")

    # 4. Categorize branches
    branches_to_delete: list[BranchInfo] = []
    branches_to_preserve: list[BranchInfo] = []

    for branch_data in branches_data:
        name = branch_data.get("name", "")

        # Main branch is always preserved
        if name == "main":
            branches_to_preserve.append(BranchInfo(
                name=name,
                eligible_for_deletion=False,
                preservation_reason="Default protected branch",
            ))
            continue

        # Check naming convention linkage
        referenced_issues = _extract_issue_numbers_from_branch(name)
        linked_issue = None
        linking_method = None

        for issue_num in referenced_issues:
            if issue_num in open_issue_numbers:
                linked_issue = issue_num
                linking_method = "naming_convention"
                break

        if linked_issue is not None:
            branches_to_preserve.append(BranchInfo(
                name=name,
                eligible_for_deletion=False,
                linked_issue_number=linked_issue,
                linked_issue_title=issue_titles.get(linked_issue),
                linking_method=linking_method,
                preservation_reason=f"Linked to open issue #{linked_issue} on project board",
            ))
        else:
            # Check if any open PR references an open issue for this branch
            pr_linked = False
            for pr in prs_data:
                if pr.get("head", {}).get("ref") == name:
                    pr_body = pr.get("body") or ""
                    pr_issue_refs = _extract_issue_numbers_from_text(pr_body)
                    for ref_num in pr_issue_refs:
                        if ref_num in open_issue_numbers:
                            linked_issue = ref_num
                            linking_method = "pr_reference"
                            pr_linked = True
                            break
                    if pr_linked:
                        break

            if pr_linked and linked_issue is not None:
                branches_to_preserve.append(BranchInfo(
                    name=name,
                    eligible_for_deletion=False,
                    linked_issue_number=linked_issue,
                    linked_issue_title=issue_titles.get(linked_issue),
                    linking_method=linking_method,
                    preservation_reason=f"Linked to open issue #{linked_issue} via PR reference",
                ))
            else:
                branches_to_delete.append(BranchInfo(
                    name=name,
                    eligible_for_deletion=True,
                ))

    # 5. Categorize PRs
    prs_to_close: list[PullRequestInfo] = []
    prs_to_preserve: list[PullRequestInfo] = []

    preserved_branch_names = {b.name for b in branches_to_preserve}

    for pr in prs_data:
        pr_number = pr.get("number", 0)
        pr_title = pr.get("title", "")
        head_branch = pr.get("head", {}).get("ref", "")
        pr_body = pr.get("body") or ""

        # Extract issue references from PR body
        referenced = _extract_issue_numbers_from_text(pr_body)

        # Check if any referenced issue is on the board
        linked_to_board = False
        linked_issue = None
        for ref_num in referenced:
            if ref_num in open_issue_numbers:
                linked_to_board = True
                linked_issue = ref_num
                break

        # Also check if the head branch is being preserved
        branch_preserved = head_branch in preserved_branch_names

        if linked_to_board and linked_issue is not None:
            prs_to_preserve.append(PullRequestInfo(
                number=pr_number,
                title=pr_title,
                head_branch=head_branch,
                referenced_issues=referenced,
                eligible_for_deletion=False,
                preservation_reason=f"References open issue #{linked_issue} on project board",
            ))
        elif branch_preserved:
            prs_to_preserve.append(PullRequestInfo(
                number=pr_number,
                title=pr_title,
                head_branch=head_branch,
                referenced_issues=referenced,
                eligible_for_deletion=False,
                preservation_reason=f"Head branch '{head_branch}' is linked to an open issue",
            ))
        else:
            prs_to_close.append(PullRequestInfo(
                number=pr_number,
                title=pr_title,
                head_branch=head_branch,
                referenced_issues=referenced,
                eligible_for_deletion=True,
            ))

    return CleanupPreflightResponse(
        branches_to_delete=branches_to_delete,
        branches_to_preserve=branches_to_preserve,
        prs_to_close=prs_to_close,
        prs_to_preserve=prs_to_preserve,
        open_issues_on_board=len(open_issue_numbers),
        has_permission=True,
        permission_error=None,
    )


async def execute_cleanup(
    github_service,
    access_token: str,
    owner: str,
    repo: str,
    request: CleanupExecuteRequest,
    db,
    github_user_id: str,
) -> CleanupExecuteResponse:
    """Execute the cleanup operation: delete branches and close PRs sequentially.

    Creates an audit log entry, executes deletions, and updates the audit log.
    """
    operation_id = str(uuid.uuid4())
    started_at = datetime.now(UTC).isoformat()

    # Create audit log entry
    await db.execute(
        """INSERT INTO cleanup_audit_logs
        (id, github_user_id, owner, repo, project_id, started_at, status)
        VALUES (?, ?, ?, ?, ?, ?, 'in_progress')""",
        (operation_id, github_user_id, owner, repo, request.project_id, started_at),
    )
    await db.commit()

    results: list[CleanupItemResult] = []
    errors: list[CleanupItemResult] = []
    branches_deleted = 0
    prs_closed = 0

    # Delete branches sequentially
    for branch_name in request.branches_to_delete:
        # Server-side rejection of main branch
        if branch_name == "main":
            item = CleanupItemResult(
                item_type="branch",
                identifier=branch_name,
                action="failed",
                error="Cannot delete the main branch",
            )
            results.append(item)
            errors.append(item)
            continue

        try:
            success = await github_service.delete_branch(
                access_token, owner, repo, branch_name
            )
            if success:
                results.append(CleanupItemResult(
                    item_type="branch",
                    identifier=branch_name,
                    action="deleted",
                ))
                branches_deleted += 1
            else:
                item = CleanupItemResult(
                    item_type="branch",
                    identifier=branch_name,
                    action="failed",
                    error="Deletion failed — branch may be protected or already deleted",
                )
                results.append(item)
                errors.append(item)
        except Exception as e:
            item = CleanupItemResult(
                item_type="branch",
                identifier=branch_name,
                action="failed",
                error=str(e),
            )
            results.append(item)
            errors.append(item)

        # Rate limit delay
        await asyncio.sleep(DELETION_DELAY_SECONDS)

    # Close PRs sequentially
    headers = github_service._build_headers(access_token)
    for pr_number in request.prs_to_close:
        try:
            response = await github_service._client.patch(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
                json={"state": "closed"},
                headers=headers,
            )
            if response.status_code == 200:
                results.append(CleanupItemResult(
                    item_type="pr",
                    identifier=str(pr_number),
                    action="closed",
                ))
                prs_closed += 1
            else:
                item = CleanupItemResult(
                    item_type="pr",
                    identifier=str(pr_number),
                    action="failed",
                    error=f"HTTP {response.status_code}: {response.text[:200]}",
                )
                results.append(item)
                errors.append(item)
        except Exception as e:
            item = CleanupItemResult(
                item_type="pr",
                identifier=str(pr_number),
                action="failed",
                error=str(e),
            )
            results.append(item)
            errors.append(item)

        # Rate limit delay
        await asyncio.sleep(DELETION_DELAY_SECONDS)

    # Update audit log
    completed_at = datetime.now(UTC).isoformat()
    status = "completed" if not errors else "completed"
    details_json = json.dumps({"results": [r.model_dump() for r in results]})

    branches_preserved = len(request.branches_to_delete) - branches_deleted
    prs_preserved = len(request.prs_to_close) - prs_closed

    await db.execute(
        """UPDATE cleanup_audit_logs SET
        completed_at = ?, status = ?,
        branches_deleted = ?, branches_preserved = ?,
        prs_closed = ?, prs_preserved = ?,
        errors_count = ?, details = ?
        WHERE id = ?""",
        (
            completed_at, status,
            branches_deleted, branches_preserved,
            prs_closed, prs_preserved,
            len(errors), details_json,
            operation_id,
        ),
    )
    await db.commit()

    return CleanupExecuteResponse(
        operation_id=operation_id,
        branches_deleted=branches_deleted,
        branches_preserved=branches_preserved,
        prs_closed=prs_closed,
        prs_preserved=prs_preserved,
        errors=errors,
        results=results,
    )


async def get_cleanup_history(
    db,
    github_user_id: str,
    owner: str,
    repo: str,
    limit: int = 10,
) -> CleanupHistoryResponse:
    """Retrieve audit trail of past cleanup operations."""
    cursor = await db.execute(
        """SELECT id, github_user_id, owner, repo, project_id,
        started_at, completed_at, status,
        branches_deleted, branches_preserved,
        prs_closed, prs_preserved,
        errors_count, details
        FROM cleanup_audit_logs
        WHERE github_user_id = ? AND owner = ? AND repo = ?
        ORDER BY started_at DESC LIMIT ?""",
        (github_user_id, owner, repo, limit),
    )
    rows = await cursor.fetchall()

    operations = []
    for row in rows:
        operations.append(CleanupAuditLogRow(
            id=row[0],
            github_user_id=row[1],
            owner=row[2],
            repo=row[3],
            project_id=row[4],
            started_at=row[5],
            completed_at=row[6],
            status=row[7],
            branches_deleted=row[8],
            branches_preserved=row[9],
            prs_closed=row[10],
            prs_preserved=row[11],
            errors_count=row[12],
            details=row[13],
        ))

    return CleanupHistoryResponse(operations=operations, count=len(operations))
