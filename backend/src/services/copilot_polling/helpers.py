"""Issue body tracking helpers — shared across multiple polling sub-modules."""

import logging

import src.services.copilot_polling as _cp

from .state import (
    _pending_agent_assignments,
)

logger = logging.getLogger(__name__)


def _get_sub_issue_number(
    pipeline: "object | None",
    agent_name: str,
    parent_issue_number: int,
) -> int:
    """Return the sub-issue number for an agent, falling back to the parent.

    Markdown file comments and other non-Done outputs are posted on the
    sub-issue.  The ``<agent>: Done!`` marker is posted on the **parent**
    issue only (handled separately by the caller).
    """
    if pipeline and getattr(pipeline, "agent_sub_issues", None):
        sub_info = pipeline.agent_sub_issues.get(agent_name)
        if sub_info and sub_info.get("number"):
            return sub_info["number"]
    return parent_issue_number


async def _check_agent_done_on_sub_or_parent(
    access_token: str,
    owner: str,
    repo: str,
    parent_issue_number: int,
    agent_name: str,
    pipeline: "object | None" = None,
) -> bool:
    """Check if an agent's Done! marker exists on the parent issue (preferred) or sub-issue.

    Done! markers are now posted on the **parent** issue only.  Falls back to
    the sub-issue for backward compatibility with issues created before this
    policy change.
    """
    # Check parent issue first (new canonical location for Done! markers)
    done = await _cp.github_projects_service.check_agent_completion_comment(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=parent_issue_number,
        agent_name=agent_name,
    )
    if done:
        return True

    # Fall back to sub-issue for backward compat (old issues had Done! on sub-issue)
    sub_number = _get_sub_issue_number(pipeline, agent_name, parent_issue_number)
    if sub_number != parent_issue_number:
        return await _cp.github_projects_service.check_agent_completion_comment(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=sub_number,
            agent_name=agent_name,
        )

    return False


async def _check_agent_done_on_parent(
    access_token: str,
    owner: str,
    repo: str,
    parent_issue_number: int,
    agent_name: str,
) -> bool:
    """Check if an agent's Done! marker exists on the parent issue only."""
    return await _cp.github_projects_service.check_agent_completion_comment(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=parent_issue_number,
        agent_name=agent_name,
    )


async def _update_issue_tracking(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    agent_name: str,
    new_state: str,
) -> bool:
    """
    Update the agent tracking table in a GitHub Issue's body.

    Fetches the current body, updates the agent's state, and pushes it back.

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name
        issue_number: Issue number
        agent_name: Agent name to update
        new_state: "active" or "done"

    Returns:
        True if update succeeded
    """
    try:
        issue_data = await _cp.github_projects_service.get_issue_with_comments(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )
        body = issue_data.get("body", "")
        if not body:
            return False

        if new_state == "active":
            updated_body = _cp.mark_agent_active(body, agent_name)
        elif new_state == "done":
            updated_body = _cp.mark_agent_done(body, agent_name)
        else:
            return False

        if updated_body == body:
            return True  # No change needed

        success = await _cp.github_projects_service.update_issue_body(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            body=updated_body,
        )
        if success:
            logger.info(
                "Tracking update: '%s' → %s on issue #%d",
                agent_name,
                new_state,
                issue_number,
            )
        return success
    except Exception as e:
        logger.warning("Failed to update tracking for issue #%d: %s", issue_number, e)
        return False


async def _get_tracking_state_from_issue(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
) -> tuple[str, list[dict]]:
    """
    Fetch the issue body and comments for tracking-based decisions.

    Returns:
        Tuple of (body, comments)
    """
    issue_data = await _cp.github_projects_service.get_issue_with_comments(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
    )
    return issue_data.get("body", ""), issue_data.get("comments", [])


def _get_sub_issue_numbers_for_issue(
    parent_issue_number: int,
    pipeline: "object | None" = None,
) -> list[int]:
    """Collect all known sub-issue numbers for a parent issue.

    Merges sub-issue numbers from the pipeline state (if present) AND the
    global sub-issue store, deduplicating.

    Returns:
        List of unique sub-issue numbers (excludes the parent itself).
    """
    numbers: set[int] = set()

    # From pipeline state
    if pipeline and getattr(pipeline, "agent_sub_issues", None):
        for info in pipeline.agent_sub_issues.values():
            num = info.get("number")
            if num and num != parent_issue_number:
                numbers.add(int(num))

    # From global store (survives pipeline resets / restarts)
    global_subs = _cp.get_issue_sub_issues(parent_issue_number)
    for info in global_subs.values():
        num = info.get("number")
        if num and num != parent_issue_number:
            numbers.add(int(num))

    return sorted(numbers)


async def _get_linked_prs_including_sub_issues(
    access_token: str,
    owner: str,
    repo: str,
    parent_issue_number: int,
    pipeline: "object | None" = None,
    current_agent: str = "",
) -> list[dict]:
    """Get all linked PRs for a parent issue AND its sub-issues.

    First checks the parent issue's timeline (cheapest / most common path).
    If no PRs found, checks the current agent's sub-issue, then broadens to
    all sub-issues.  Any PR discovered via a sub-issue is explicitly linked
    to the parent issue so future detection cycles find it directly.

    Args:
        access_token: GitHub access token.
        owner: Repository owner.
        repo: Repository name.
        parent_issue_number: Parent issue number.
        pipeline: Optional pipeline state for sub-issue lookup.
        current_agent: Current agent name (checked first for efficiency).

    Returns:
        Deduplicated list of PR dicts (same shape as ``get_linked_pull_requests``).
    """
    # Step 1: Check the parent issue's timeline
    parent_prs = await _cp.github_projects_service.get_linked_pull_requests(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=parent_issue_number,
    )

    # Collect all PRs from parent AND sub-issues, deduplicating by PR number.
    # We must NOT return early when parent_prs is non-empty because the parent
    # may only have the main PR linked.  Child PRs created via sub-issue
    # assignments are linked to the sub-issue, NOT the parent, until
    # _link_prs_to_parent explicitly connects them.  The early return caused
    # child PRs to be invisible to _find_completed_child_pr and
    # _merge_child_pr_if_applicable, allowing the next agent to start before
    # the previous agent's child PR was merged (issue #740).
    seen_pr_numbers: set[int] = set()
    all_prs: list[dict] = []

    for pr in parent_prs or []:
        pr_num = pr.get("number")
        if pr_num and pr_num not in seen_pr_numbers:
            seen_pr_numbers.add(pr_num)
            all_prs.append(pr)

    # Step 2: Check sub-issues for additional PRs not on the parent
    # Prioritise the current agent's sub-issue (single API call)
    priority_sub = None
    if current_agent:
        priority_sub = _get_sub_issue_number(pipeline, current_agent, parent_issue_number)
        if priority_sub and priority_sub != parent_issue_number:
            sub_prs = await _cp.github_projects_service.get_linked_pull_requests(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=priority_sub,
            )
            for pr in sub_prs:
                pr_num = pr.get("number")
                if pr_num and pr_num not in seen_pr_numbers:
                    seen_pr_numbers.add(pr_num)
                    all_prs.append(pr)

    # Step 3: Broaden to all sub-issues
    sub_numbers = _get_sub_issue_numbers_for_issue(parent_issue_number, pipeline)
    for sub_num in sub_numbers:
        if sub_num == priority_sub:
            continue  # Already checked above
        sub_prs = await _cp.github_projects_service.get_linked_pull_requests(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=sub_num,
        )
        for pr in sub_prs:
            pr_num = pr.get("number")
            if pr_num and pr_num not in seen_pr_numbers:
                seen_pr_numbers.add(pr_num)
                all_prs.append(pr)

    # Link any newly-discovered sub-issue PRs to the parent so future
    # detection cycles find them directly via the parent's timeline.
    new_prs = [p for p in all_prs if p.get("number") not in {
        pr.get("number") for pr in (parent_prs or [])
    }]
    if new_prs:
        await _link_prs_to_parent(
            access_token, owner, repo, parent_issue_number, new_prs,
        )

    return all_prs


async def _link_prs_to_parent(
    access_token: str,
    owner: str,
    repo: str,
    parent_issue_number: int,
    prs: list[dict],
) -> None:
    """Link discovered PRs to the parent issue for future detection.

    Silently swallows errors — linking is best-effort.
    """
    for pr in prs:
        pr_num = pr.get("number")
        if not pr_num:
            continue
        try:
            await _cp.github_projects_service.link_pull_request_to_issue(
                access_token=access_token,
                owner=owner,
                repo=repo,
                pr_number=pr_num,
                issue_number=parent_issue_number,
            )
            logger.info(
                "Linked sub-issue PR #%d to parent issue #%d",
                pr_num,
                parent_issue_number,
            )
        except Exception as e:
            logger.debug(
                "Could not link PR #%d to parent issue #%d: %s",
                pr_num,
                parent_issue_number,
                e,
            )


async def _reconstruct_sub_issue_mappings(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
) -> dict[str, dict]:
    """Fetch sub-issues from GitHub and build ``agent_name → sub-issue`` mapping.

    Sub-issue titles follow the pattern ``[agent-name] Title``.  This parses
    the agent name from the bracketed prefix.
    """
    try:
        raw_subs = await _cp.github_projects_service.get_sub_issues(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )
        mappings: dict[str, dict] = {}
        for si in raw_subs:
            si_title = si.get("title", "")
            if si_title.startswith("[") and "]" in si_title:
                si_agent = si_title[1 : si_title.index("]")]
                mappings[si_agent] = {
                    "number": si.get("number"),
                    "node_id": si.get("node_id", ""),
                    "url": si.get("html_url", ""),
                }
        if mappings:
            logger.info(
                "Reconstructed %d sub-issue mappings for issue #%d",
                len(mappings),
                issue_number,
            )
            # Also persist to the global store so mappings survive pipeline resets
            _cp.set_issue_sub_issues(issue_number, mappings)
        return mappings
    except Exception as e:
        logger.debug(
            "Could not reconstruct sub-issue mappings for issue #%d: %s",
            issue_number,
            e,
        )
        return {}
