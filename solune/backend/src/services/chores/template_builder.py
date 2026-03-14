"""Template builder — generates and commits GitHub Issue Templates for chores."""

from __future__ import annotations

import re
import time

from src.logging_utils import get_logger

logger = get_logger(__name__)


def build_template(name: str, content: str) -> str:
    """Build a complete .md GitHub Issue Template with YAML front matter.

    If the user's content already starts with YAML front matter (``---``),
    it is used as-is.  Otherwise, default front matter is prepended.

    Args:
        name: Chore display name.
        content: Body content (may already include front matter).

    Returns:
        Full template string (YAML front matter + markdown body).
    """
    if content.lstrip().startswith("---"):
        # Content already has front matter — use as-is
        return content.strip() + "\n"

    # Generate default front matter
    front_matter = (
        "---\n"
        f"name: {name}\n"
        f"about: Recurring chore — {name}\n"
        f"title: '[CHORE] {name}'\n"
        f"labels: chore\n"
        f"assignees: ''\n"
        "---\n\n"
    )
    return front_matter + content.strip() + "\n"


def derive_template_path(name: str) -> str:
    """Derive the .github/ISSUE_TEMPLATE/ file path from a chore name.

    Args:
        name: Chore display name.

    Returns:
        Path like ``.github/ISSUE_TEMPLATE/chore-bug-bash.md``.
    """
    slug = _slugify(name)
    return f".github/ISSUE_TEMPLATE/chore-{slug}.md"


def is_sparse_input(text: str) -> bool:
    """Determine if user input is sparse (needs AI chat refinement).

    Heuristic per research.md R6:
    - Rich indicators: markdown headings (##), list markers (- *), ≥3 newlines
    - If any rich indicator → RICH
    - If word count ≤ 15 → SPARSE
    - If word count ≤ 40 AND single line → SPARSE
    - Else → RICH

    Args:
        text: Raw user input.

    Returns:
        True if sparse, False if rich.
    """
    stripped = text.strip()
    if not stripped:
        return True

    # Rich indicators
    lines = stripped.split("\n")
    has_headings = bool(re.search(r"^#{1,6}\s", stripped, re.MULTILINE))
    has_lists = bool(re.search(r"^[\-\*]\s", stripped, re.MULTILINE))
    has_multi_newlines = stripped.count("\n") >= 3

    if has_headings or has_lists or has_multi_newlines:
        return False

    word_count = len(stripped.split())

    if word_count <= 15:
        return True

    if word_count <= 40 and len(lines) <= 1:
        return True

    return False


async def commit_template_to_repo(
    github_service,
    access_token: str,
    owner: str,
    repo: str,
    project_id: str,
    name: str,
    template_content: str,
) -> dict:
    """Commit a GitHub Issue Template via branch + PR + tracking issue.

    Full workflow:
    1. Get repo info (ID, default branch, HEAD OID)
    2. Create a feature branch
    3. Commit the template file
    4. Open a Pull Request
    5. Create a tracking issue in "In review" status
    6. Add the tracking issue to the project

    Args:
        github_service: GitHubProjectsService instance.
        access_token: User's OAuth token.
        owner: Repository owner.
        repo: Repository name.
        project_id: Project node ID.
        name: Chore display name.
        template_content: Full template content (with front matter).

    Returns:
        Dict with keys: template_path, pr_number, pr_url, tracking_issue_number
    """
    template_path = derive_template_path(name)
    slug = _slugify(name)
    branch_name = f"chore/add-template-{slug}"

    # 1. Get repo info
    repo_info = await github_service.get_repository_info(access_token, owner, repo)
    repository_id = repo_info["repository_id"]
    default_branch = repo_info["default_branch"]
    head_oid = repo_info["head_oid"]

    # 2. Create branch (may already exist from a previous attempt)
    ref_id = await github_service.create_branch(access_token, repository_id, branch_name, head_oid)
    if ref_id is None:
        raise RuntimeError(f"Failed to create branch {branch_name}")

    # If the branch already exists, its HEAD may differ from the default
    # branch HEAD.  Fetch the actual branch HEAD for the commit.
    commit_base_oid = head_oid
    if ref_id == "existing":
        branch_head = await github_service.get_branch_head_oid(
            access_token, owner, repo, branch_name
        )
        if branch_head:
            commit_base_oid = branch_head

    # 3. Commit template file
    commit_oid = await github_service.commit_files(
        access_token,
        owner,
        repo,
        branch_name,
        commit_base_oid,
        [{"path": template_path, "content": template_content}],
        f"chore: add issue template for {name}",
    )
    if commit_oid is None:
        raise RuntimeError(f"Failed to commit template to {branch_name}")

    # 4. Create Pull Request
    pr = await github_service.create_pull_request(
        access_token,
        repository_id,
        title=f"chore: add issue template — {name}",
        body=(
            f"Adds GitHub Issue Template for the **{name}** chore.\n\n"
            f"Template path: `{template_path}`\n\n"
            "_Auto-generated by Chores feature._"
        ),
        head_branch=branch_name,
        base_branch=default_branch,
    )
    pr_number = pr["number"] if pr else None
    pr_url = pr["url"] if pr else None

    # 5. Create tracking issue
    tracking_issue = await github_service.create_issue(
        access_token,
        owner,
        repo,
        title=f"[Chore Template Review] {name}",
        body=(
            f"Review and merge the issue template for **{name}**.\n\n"
            f"PR: {'#' + str(pr_number) if pr_number else 'N/A'}\n\n"
            "_Auto-generated by Chores feature._"
        ),
        labels=["chore"],
    )
    tracking_issue_number = tracking_issue["number"]
    tracking_issue_node_id = tracking_issue["node_id"]

    # 6. Add tracking issue to project
    try:
        await github_service.add_issue_to_project(access_token, project_id, tracking_issue_node_id)
    except Exception:
        logger.warning(
            "Failed to add tracking issue #%d to project %s",
            tracking_issue_number,
            project_id,
        )

    return {
        "template_path": template_path,
        "pr_number": pr_number,
        "pr_url": pr_url,
        "tracking_issue_number": tracking_issue_number,
    }


def _slugify(name: str) -> str:
    """Convert a chore name to a URL/file-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "chore"


async def update_template_in_repo(
    github_service,
    access_token: str,
    owner: str,
    repo: str,
    chore_name: str,
    template_path: str,
    template_content: str,
    old_template_path: str | None = None,
) -> dict:
    """Update an existing chore template in the repo via branch + PR.

    When the chore is renamed, *old_template_path* points to the previous
    file.  The commit will create the file at *template_path* and delete
    *old_template_path* in a single atomic commit so the rename is clean.

    Args:
        github_service: GitHubProjectsService instance.
        access_token: User's OAuth token.
        owner: Repository owner.
        repo: Repository name.
        chore_name: Chore display name.
        template_path: Target template file path (new path when renamed).
        template_content: Updated template content (with front matter).
        old_template_path: Previous file path to delete when renamed.

    Returns:
        Dict with keys: pr_number, pr_url
    """
    slug = _slugify(chore_name)
    timestamp = int(time.time())
    branch_name = f"chore/update-{slug}-{timestamp}"

    repo_info = await github_service.get_repository_info(access_token, owner, repo)
    repository_id = repo_info["repository_id"]
    default_branch = repo_info["default_branch"]
    head_oid = repo_info["head_oid"]

    ref_id = await github_service.create_branch(access_token, repository_id, branch_name, head_oid)
    if ref_id is None:
        raise RuntimeError(f"Failed to create branch {branch_name}")

    commit_base_oid = head_oid
    if ref_id == "existing":
        branch_head = await github_service.get_branch_head_oid(
            access_token, owner, repo, branch_name
        )
        if branch_head:
            commit_base_oid = branch_head

    # When renamed, delete the old file in the same commit.
    deletions = None
    if old_template_path and old_template_path != template_path:
        deletions = [old_template_path]

    commit_oid = await github_service.commit_files(
        access_token,
        owner,
        repo,
        branch_name,
        commit_base_oid,
        [{"path": template_path, "content": template_content}],
        f"chore: update {chore_name}",
        deletions=deletions,
    )
    if commit_oid is None:
        raise RuntimeError(f"Failed to commit template update to {branch_name}")

    pr = await github_service.create_pull_request(
        access_token,
        repository_id,
        title=f"chore: update {chore_name}",
        body=(
            f"Updates the GitHub Issue Template for **{chore_name}**.\n\n"
            f"Template path: `{template_path}`\n\n"
            "_Auto-generated by inline Chore editing._"
        ),
        head_branch=branch_name,
        base_branch=default_branch,
    )
    return {
        "pr_number": pr["number"] if pr else None,
        "pr_url": pr["url"] if pr else None,
    }


async def merge_chore_pr(
    github_service,
    access_token: str,
    owner: str,
    repo: str,
    pr_number: int,
    merge_method: str = "SQUASH",
) -> tuple[bool, str | None]:
    """Merge a chore PR into the base branch.

    Args:
        github_service: GitHubProjectsService instance.
        access_token: User's OAuth token.
        owner: Repository owner.
        repo: Repository name.
        pr_number: Pull request number.
        merge_method: Merge strategy (MERGE, SQUASH, REBASE).

    Returns:
        Tuple of (success: bool, error_message: str | None).
    """
    try:
        # Get the PR node ID
        pr_info = await github_service.get_pull_request(access_token, owner, repo, pr_number)
        if not pr_info:
            return False, f"PR #{pr_number} not found"

        pr_node_id = pr_info.get("id")
        if not pr_node_id:
            return False, f"PR #{pr_number} missing node_id"

        result = await github_service.merge_pull_request(
            access_token,
            pr_node_id,
            pr_number=pr_number,
            merge_method=merge_method,
        )
        if result and result.get("merged"):
            return True, None
        return False, "Merge was not completed"
    except Exception as exc:
        logger.warning("Failed to merge PR #%s: %s", pr_number, exc)
        return False, str(exc)
