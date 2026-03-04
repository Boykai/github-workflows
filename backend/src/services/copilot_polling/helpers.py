"""Issue body tracking helpers — shared across multiple polling sub-modules."""

import logging
import re
from typing import Any

import src.services.copilot_polling as _cp

logger = logging.getLogger(__name__)

# Matches sub-issue titles created by the orchestrator: "[agent-name] Parent Title"
_SUB_ISSUE_TITLE_RE = re.compile(r"^\[\S+\]\s")


def is_sub_issue(task: Any) -> bool:
    """Return True if the task is an agent sub-issue rather than a parent issue.

    Sub-issues are created by the orchestrator with titles matching
    ``[agent-name] Parent Title``.  GitHub can auto-move sub-issues to
    different status columns (e.g. "In Progress") when a branch is
    created; the polling loop must skip them to avoid creating spurious
    pipeline states.  A secondary label check guards against renamed titles.
    """
    title = getattr(task, "title", None) or ""
    if _SUB_ISSUE_TITLE_RE.match(title):
        return True
    # Fallback: check for the "sub-issue" label applied during creation
    labels = getattr(task, "labels", None) or []
    if isinstance(labels, list | tuple):
        for lbl in labels:
            name = lbl.get("name", "") if isinstance(lbl, dict) else str(lbl)
            if name == "sub-issue":
                return True
    return False


def _get_sub_issue_number(
    pipeline: Any,
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

    For the Human agent, also checks if the sub-issue has been closed, and
    validates that 'Done!' comments are from the assigned user only.

    For the ``copilot-review`` agent, completion is detected by checking
    whether Copilot has submitted a code review on the main PR (it never
    posts a Done! comment).
    """
    # ── Human agent: dual completion signals ──────────────────────
    if agent_name == "human":
        return await _check_human_agent_done(
            access_token=access_token,
            owner=owner,
            repo=repo,
            parent_issue_number=parent_issue_number,
            pipeline=pipeline,
        )

    # ── copilot-review: completion = Copilot submitted a PR review ──
    if agent_name == "copilot-review":
        return await _check_copilot_review_done(
            access_token=access_token,
            owner=owner,
            repo=repo,
            parent_issue_number=parent_issue_number,
        )

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


async def _check_copilot_review_done(
    access_token: str,
    owner: str,
    repo: str,
    parent_issue_number: int,
) -> bool:
    """Check if the copilot-review step is complete.

    ``copilot-review`` is NOT a coding agent — it never posts a Done!
    comment.  Instead, the pipeline requests a Copilot code review on the
    main PR.  Completion is detected by checking whether Copilot has
    actually submitted a review on that PR.

    **Self-healing**: if the PR is still a draft or the review was never
    requested (the initial assignment can fail silently), this function
    retries the un-draft and review-request operations before checking for
    completion.
    """
    # Also check for a Done! marker (posted by a previous detection cycle
    # — belt & suspenders for restarts where we lost in-memory state).
    done_marker = await _cp.github_projects_service.check_agent_completion_comment(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=parent_issue_number,
        agent_name="copilot-review",
    )
    if done_marker:
        return True

    # Locate the main PR for this issue
    main_branch_info = _cp.get_issue_main_branch(parent_issue_number)
    pr_number: int | None = None

    if main_branch_info:
        pr_number = main_branch_info["pr_number"]
    else:
        # Fallback: discover the PR via the API
        try:
            found_pr = await _cp.github_projects_service.find_existing_pr_for_issue(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=parent_issue_number,
            )
            if found_pr:
                pr_number = found_pr["number"]
        except Exception as e:
            logger.warning(
                "Could not find main PR for copilot-review completion check on issue #%d: %s",
                parent_issue_number,
                e,
            )

    if not pr_number:
        logger.debug(
            "No main PR found for copilot-review completion check on issue #%d",
            parent_issue_number,
        )
        return False

    # ── Self-healing: ensure the PR is ready-for-review and that a
    # Copilot review has been requested.  The initial assignment in
    # assign_agent_for_status may have failed to un-draft the PR or
    # request the review.  Retrying here on every poll cycle ensures the
    # pipeline recovers automatically instead of waiting forever.
    pr_details = await _cp.github_projects_service.get_pull_request(
        access_token=access_token,
        owner=owner,
        repo=repo,
        pr_number=pr_number,
    )

    if pr_details and pr_details.get("is_draft"):
        pr_node_id = pr_details.get("id")
        if pr_node_id:
            logger.warning(
                "Self-healing: main PR #%d is still a draft during copilot-review "
                "check for issue #%d — retrying draft→ready conversion",
                pr_number,
                parent_issue_number,
            )
            mark_ok = await _cp.github_projects_service.mark_pr_ready_for_review(
                access_token=access_token,
                pr_node_id=str(pr_node_id),
            )
            if mark_ok:
                from .pipeline import _system_marked_ready_prs

                _system_marked_ready_prs.add(pr_number)
                logger.info(
                    "Self-healing: converted PR #%d from draft to ready for issue #%d",
                    pr_number,
                    parent_issue_number,
                )
            else:
                logger.warning(
                    "Self-healing: failed to convert PR #%d from draft to ready — "
                    "copilot-review cannot proceed until PR is ready (issue #%d)",
                    pr_number,
                    parent_issue_number,
                )
                return False  # Cannot check review on a draft PR

    reviewed = await _cp.github_projects_service.has_copilot_reviewed_pr(
        access_token=access_token,
        owner=owner,
        repo=repo,
        pr_number=pr_number,
    )

    # ── Self-healing: if not reviewed, ensure the review was requested.
    # The initial request_copilot_review call may have failed silently.
    if not reviewed and pr_details:
        pr_node_id = pr_details.get("id")
        if pr_node_id:
            logger.info(
                "Self-healing: Copilot has not yet reviewed PR #%d for issue #%d — "
                "ensuring review is requested",
                pr_number,
                parent_issue_number,
            )
            await _cp.github_projects_service.request_copilot_review(
                access_token=access_token,
                pr_node_id=str(pr_node_id),
                pr_number=pr_number,
                owner=owner,
                repo=repo,
            )
        # Clear any stale first-detection timestamp when the review is
        # not present — protects against false positives from transient
        # API states that appear and then vanish.
        from .state import _copilot_review_first_detected

        _copilot_review_first_detected.pop(parent_issue_number, None)

    if not reviewed:
        return False

    # ── Confirmation delay: require the review to be detected on TWO
    # consecutive poll cycles before advancing.  This eliminates false
    # positives from transient GitHub API race conditions where a review
    # object briefly appears before it is fully committed.
    from src.utils import utcnow

    from .state import (
        COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS,
        _copilot_review_first_detected,
    )

    now = utcnow()
    first_seen = _copilot_review_first_detected.get(parent_issue_number)
    if first_seen is None:
        _copilot_review_first_detected[parent_issue_number] = now
        logger.info(
            "Copilot review first detected on PR #%d for issue #%d — "
            "will confirm on next poll cycle (%.0fs delay)",
            pr_number,
            parent_issue_number,
            COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS,
        )
        return False

    elapsed = (now - first_seen).total_seconds()
    if elapsed < COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS:
        logger.debug(
            "Copilot review on PR #%d awaiting confirmation (%.0f/%.0fs) for issue #%d",
            pr_number,
            elapsed,
            COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS,
            parent_issue_number,
        )
        return False

    # Review confirmed on two consecutive cycles — proceed.
    _copilot_review_first_detected.pop(parent_issue_number, None)

    logger.info(
        "Copilot code review confirmed on PR #%d for issue #%d "
        "(first seen %.0fs ago) — copilot-review step is done",
        pr_number,
        parent_issue_number,
        elapsed,
    )

    # Post a durable Done! marker so pipeline reconstruction works
    # even after a server restart (without the in-memory state).
    try:
        await _cp.github_projects_service.create_issue_comment(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=parent_issue_number,
            body="copilot-review: Done!",
        )
        logger.info(
            "Posted 'copilot-review: Done!' marker on issue #%d",
            parent_issue_number,
        )
    except Exception as e:
        logger.warning(
            "Failed to post copilot-review Done! marker on issue #%d: %s",
            parent_issue_number,
            e,
        )

    return True


async def _check_human_agent_done(
    access_token: str,
    owner: str,
    repo: str,
    parent_issue_number: int,
    pipeline: "object | None" = None,
) -> bool:
    """Check if a Human agent step is complete.

    Two completion signals:
    1. The Human sub-issue has been closed.
    2. The assigned user commented exactly 'Done!' on the parent issue.

    Returns True if either signal is detected.
    """
    sub_number = _get_sub_issue_number(pipeline, "human", parent_issue_number)

    # Signal 1: Check if the Human sub-issue has been closed
    if sub_number != parent_issue_number:
        try:
            closed = await _cp.github_projects_service.check_issue_closed(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=sub_number,
            )
            if closed:
                logger.info(
                    "Human sub-issue #%d is closed — marking Human step complete (parent #%d)",
                    sub_number,
                    parent_issue_number,
                )
                return True
        except Exception as e:
            logger.warning("Failed to check Human sub-issue #%d state: %s", sub_number, e)

    # Signal 2: Check if the assigned user commented exactly 'Done!' on the parent issue
    try:
        parent_data = await _cp.github_projects_service.get_issue_with_comments(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=parent_issue_number,
        )
        comments = parent_data.get("comments", [])

        # Determine the Human sub-issue assignee for authorization.
        # Fall back to the parent issue author if the pipeline doesn't
        # have an explicit assignee recorded.  If neither is available
        # we fail closed — no 'Done!' comment is accepted.
        assignee = _get_human_sub_issue_assignee(pipeline, parent_issue_number)
        if not assignee:
            parent_author_obj = parent_data.get("user") or {}
            assignee = (
                parent_author_obj.get("login", "") if isinstance(parent_author_obj, dict) else ""
            )

        if not assignee:
            logger.debug(
                "No authorized user determined for Human 'Done!' on parent issue #%d; "
                "ignoring any 'Done!' comments (fail closed).",
                parent_issue_number,
            )
        else:
            for comment in reversed(comments):
                # Exact match only — no .strip() per spec requirement.
                # The GitHub API returns the raw comment body; only the
                # literal string "Done!" (no surrounding whitespace) triggers
                # Human step completion.
                body = comment.get("body", "")
                if body == "Done!":
                    comment_author = comment.get("author", "")
                    if comment_author == assignee:
                        logger.info(
                            "Human step complete via 'Done!' comment from '%s' on parent issue #%d",
                            comment_author,
                            parent_issue_number,
                        )
                        return True
                    else:
                        logger.debug(
                            "Ignoring 'Done!' comment from '%s' (expected '%s') on issue #%d",
                            comment_author,
                            assignee,
                            parent_issue_number,
                        )
    except Exception as e:
        logger.warning(
            "Failed to check Human Done! comment on issue #%d: %s", parent_issue_number, e
        )

    return False


def _get_human_sub_issue_assignee(
    pipeline: "object | None",
    parent_issue_number: int,
) -> str:
    """Get the assignee of the Human sub-issue from pipeline state.

    The assignee was set during sub-issue creation to the parent issue creator.
    We store it in the sub-issue info for later validation.

    Falls back to checking the global sub-issue store.
    """
    # Check pipeline state
    agent_sub_issues: dict = getattr(pipeline, "agent_sub_issues", None) or {}
    if agent_sub_issues:
        sub_info = agent_sub_issues.get("human")
        if sub_info and sub_info.get("assignee"):
            return sub_info["assignee"]

    # Check global store
    global_subs = _cp.get_issue_sub_issues(parent_issue_number)
    sub_info = global_subs.get("human")
    if sub_info and sub_info.get("assignee"):
        return sub_info["assignee"]

    return ""


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
    pipeline: Any = None,
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
    parent_pr_numbers = {pr.get("number") for pr in (parent_prs or [])}
    new_prs = [p for p in all_prs if p.get("number") not in parent_pr_numbers]
    if new_prs:
        await _link_prs_to_parent(
            access_token,
            owner,
            repo,
            parent_issue_number,
            new_prs,
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
