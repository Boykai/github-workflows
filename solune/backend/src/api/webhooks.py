"""GitHub Webhook endpoints for handling events."""

import hashlib
import hmac
import re
from typing import Any, cast

from fastapi import APIRouter, Header, Request
from pydantic import ValidationError as PydanticValidationError

from src.api.webhook_models import (
    CheckRunEvent,
    CheckSuiteEvent,
    IssuesEvent,
    PingEvent,
    PullRequestData,
    PullRequestEvent,
)
from src.config import get_settings
from src.exceptions import AppException, AuthenticationError
from src.logging_utils import get_logger
from src.services.activity_logger import log_event
from src.services.cache import cache, get_repo_agents_cache_key
from src.services.database import get_db
from src.services.github_projects import github_projects_service
from src.utils import BoundedSet

logger = get_logger(__name__)
router = APIRouter()

# In-memory storage for tracking processed events (deduplication).
# Uses BoundedSet to maintain insertion order and automatically evict
# the oldest entries when capacity is reached.
_processed_delivery_ids: BoundedSet[str] = BoundedSet(maxlen=1000)


def verify_webhook_signature(payload: bytes, signature: str | None, secret: str) -> bool:
    """
    Verify GitHub webhook signature.

    Args:
        payload: Raw request body
        signature: X-Hub-Signature-256 header value
        secret: Webhook secret configured in GitHub

    Returns:
        True if signature is valid
    """
    if not signature:
        return False

    if not signature.startswith("sha256="):
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected}", signature)


def extract_issue_number_from_pr(pr_data: PullRequestData | dict[str, Any]) -> int | None:
    """
    Extract linked issue number from PR body or branch name.

    Looks for patterns like:
    - "Fixes #123" or "Closes #123" in body
    - Branch names like "issue-123-..." or "123-feature"

    Args:
        pr_data: Pull request data from webhook

    Returns:
        Issue number if found, None otherwise
    """
    # Check PR body for issue references
    if isinstance(pr_data, PullRequestData):
        body = pr_data.body or ""
        branch_name = pr_data.head.ref
    else:
        body = pr_data.get("body") or ""
        branch_name = pr_data.get("head", {}).get("ref", "")

    # Common patterns: Fixes #123, Closes #123, Resolves #123, Related to #123
    patterns = [
        r"(?:fixes|closes|resolves|fix|close|resolve)\s*#(\d+)",
        r"(?:related\s+to|relates\s+to|ref|references?)\s*#(\d+)",
        r"#(\d+)",  # Fallback: any issue reference
    ]

    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return int(match.group(1))

    # Check branch name for issue number
    # Patterns like: issue-123, 123-feature, feature/123-description
    branch_patterns = [
        r"issue[/-](\d+)",
        r"^(\d+)[/-]",
        r"/(\d+)[/-]",
    ]

    for pattern in branch_patterns:
        match = re.search(pattern, branch_name, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


async def handle_copilot_pr_ready(
    pr_data: dict,
    repo_owner: str,
    repo_name: str,
    access_token: str,
) -> dict[str, Any]:
    """
    Handle when a Copilot PR is marked ready for review.

    1. Find the linked issue
    2. Update the issue status to "In Review"

    Args:
        pr_data: Pull request data from webhook
        repo_owner: Repository owner
        repo_name: Repository name
        access_token: GitHub access token (from app installation or stored token)

    Returns:
        Result dict with status and details
    """
    pr_number = pr_data.get("number")
    pr_author = pr_data.get("user", {}).get("login", "")

    logger.info(
        "Handling Copilot PR #%d ready for review (author: %s)",
        pr_number,
        pr_author,
    )

    # Extract linked issue number
    issue_number = extract_issue_number_from_pr(pr_data)

    if not issue_number:
        logger.warning(
            "Could not find linked issue for PR #%d",
            pr_number,
        )
        return {
            "status": "skipped",
            "reason": "no_linked_issue",
            "pr_number": pr_number,
        }

    logger.info(
        "Found linked issue #%d for PR #%d",
        issue_number,
        pr_number,
    )

    # Get project item ID for the issue to update its status
    # This requires finding the issue in the project
    try:
        # First, we need to get the project ID from stored data
        # For now, we'll use the update_item_status_by_name method
        # which handles looking up the status field

        # Get linked PRs to find the project item
        linked_prs = await github_projects_service.get_linked_pull_requests(
            access_token=access_token,
            owner=repo_owner,
            repo=repo_name,
            issue_number=issue_number,
        )

        logger.info(
            "Issue #%d has %d linked PRs",
            issue_number,
            len(linked_prs),
        )

        # The status update will be handled by finding the issue's project item
        # and updating its status field
        return {
            "status": "processed",
            "pr_number": pr_number,
            "issue_number": issue_number,
            "action": "status_update_pending",
            "message": f"Issue #{issue_number} should be updated to 'In Review'",
        }

    except Exception as e:
        logger.error(
            "Failed to process PR #%d completion: %s",
            pr_number,
            e,
            exc_info=True,
        )
        return {
            "status": "error",
            "pr_number": pr_number,
            "error": "Failed to process PR completion",
        }


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: str | None = Header(None, alias="X-GitHub-Event"),
    x_github_delivery: str | None = Header(None, alias="X-GitHub-Delivery"),
    x_hub_signature_256: str | None = Header(None, alias="X-Hub-Signature-256"),
) -> dict[str, Any]:
    """
    Handle incoming GitHub webhook events.

    Supported events:
    - pull_request: Detect when Copilot PRs are ready for review

    Headers:
    - X-GitHub-Event: Event type (e.g., "pull_request")
    - X-GitHub-Delivery: Unique delivery ID for deduplication
    - X-Hub-Signature-256: HMAC signature for verification
    """
    settings = get_settings()

    # Read raw body for signature verification
    body = await request.body()

    # Verify signature — always required regardless of debug mode.
    # Developers must configure a local test secret (GITHUB_WEBHOOK_SECRET).
    if settings.github_webhook_secret:
        if not verify_webhook_signature(body, x_hub_signature_256, settings.github_webhook_secret):
            logger.warning("Invalid webhook signature")
            raise AuthenticationError("Invalid or missing webhook signature")
    else:
        logger.warning("Webhook rejected: GITHUB_WEBHOOK_SECRET is not configured")
        raise AuthenticationError("Invalid or missing webhook signature")

    # Deduplicate by delivery ID
    if x_github_delivery:
        if x_github_delivery in _processed_delivery_ids:
            logger.info("Duplicate delivery %s, skipping", x_github_delivery)
            return {"status": "duplicate", "delivery_id": x_github_delivery}

        _processed_delivery_ids.add(x_github_delivery)

    # Parse JSON payload
    try:
        raw_payload = await request.json()
    except Exception as e:
        logger.error("Failed to parse webhook payload: %s", e)
        raise AppException("Invalid JSON payload", status_code=400) from e

    payload: (
        PullRequestEvent
        | IssuesEvent
        | PingEvent
        | CheckRunEvent
        | CheckSuiteEvent
        | dict[str, Any]
    )
    try:
        if x_github_event == "pull_request":
            payload = PullRequestEvent.model_validate(raw_payload)
        elif x_github_event == "issues":
            payload = IssuesEvent.model_validate(raw_payload)
        elif x_github_event == "ping":
            payload = PingEvent.model_validate(raw_payload)
        elif x_github_event == "check_run":
            payload = CheckRunEvent.model_validate(raw_payload)
        elif x_github_event == "check_suite":
            payload = CheckSuiteEvent.model_validate(raw_payload)
        else:
            payload = raw_payload
    except PydanticValidationError as e:
        logger.warning("Invalid webhook payload for event %s: %s", x_github_event, e)
        raise AppException(
            "Invalid webhook payload",
            status_code=422,
            details={"errors": e.errors()},
        ) from e

    logger.info(
        "Received GitHub webhook: event=%s, delivery=%s",
        x_github_event,
        x_github_delivery,
    )

    # Handle pull_request events
    if x_github_event == "pull_request":
        result = await handle_pull_request_event(cast(PullRequestEvent | dict[str, Any], payload))
        pr_info = raw_payload.get("pull_request", {}) if isinstance(raw_payload, dict) else {}
        repo_info = raw_payload.get("repository", {}) if isinstance(raw_payload, dict) else {}
        webhook_action = raw_payload.get("action", "") if isinstance(raw_payload, dict) else ""
        repo_full = repo_info.get("full_name", "") if isinstance(repo_info, dict) else ""
        sender = (
            pr_info.get("user", {}).get("login", "system")
            if isinstance(pr_info, dict)
            else "system"
        )
        await log_event(
            get_db(),
            event_type="webhook",
            entity_type="issue",
            entity_id=str(pr_info.get("number", "")) if isinstance(pr_info, dict) else "",
            project_id=(
                result.get("project_id", "")
                if isinstance(result, dict) and isinstance(result.get("project_id"), str)
                else ""
            ),
            actor=sender,
            action=webhook_action or "received",
            summary=f"Webhook: pull_request {webhook_action} on {repo_full}",
            detail={
                "webhook_type": "pull_request",
                "action": webhook_action,
                "sender": sender,
                "repository": repo_full,
            },
        )
        return result

    # Handle check_run events for CI failure detection (auto-merge)
    if x_github_event == "check_run" and isinstance(payload, CheckRunEvent):
        result = await handle_check_run_event(payload)
        return result

    # Handle check_suite events for CI failure detection (auto-merge)
    if x_github_event == "check_suite" and isinstance(payload, CheckSuiteEvent):
        result = await handle_check_suite_event(payload)
        return result

    # Acknowledge other events — do not echo user-controlled header values
    return {
        "status": "ignored",
        "message": "Event type not handled",
    }


async def handle_pull_request_event(payload: PullRequestEvent | dict[str, Any]) -> dict[str, Any]:
    """
    Handle pull_request webhook events.

    Detects when GitHub Copilot marks a draft PR as ready for review,
    then updates the linked issue status to "In Review".
    """
    if isinstance(payload, PullRequestEvent):
        action = payload.action
        pr_data = payload.pull_request.model_dump()
        pr_number = payload.pull_request.number
        pr_author = payload.pull_request.user.login
        is_draft = payload.pull_request.draft
        repo_owner = payload.repository.owner.login
        repo_name = payload.repository.name
        merged = payload.pull_request.merged
    else:
        action = payload.get("action")
        pr_data = payload.get("pull_request", {})
        repo_data = payload.get("repository", {})
        pr_number = pr_data.get("number")
        pr_author = pr_data.get("user", {}).get("login", "")
        is_draft = pr_data.get("draft", False)
        repo_owner = repo_data.get("owner", {}).get("login", "")
        repo_name = repo_data.get("name", "")
        merged = pr_data.get("merged")

    logger.info(
        "Pull request event: action=%s, pr=#%d, author=%s, is_draft=%s",
        action,
        pr_number,
        pr_author,
        is_draft,
    )

    if action == "closed" and merged:
        cache.delete(get_repo_agents_cache_key(repo_owner, repo_name))
        logger.info(
            "Invalidated repo agent cache for %s/%s after merged PR #%d",
            repo_owner,
            repo_name,
            pr_number,
        )
        return {
            "status": "processed",
            "event": "pull_request",
            "action": action,
            "pr_number": pr_number,
            "repository": f"{repo_owner}/{repo_name}",
            "cache_invalidated": True,
        }

    # Check if this is a Copilot PR being marked ready for review
    is_copilot_pr = "copilot" in pr_author.lower() or pr_author == "copilot-swe-agent[bot]"

    # Detect when a draft PR becomes ready for review
    # action="ready_for_review" is sent when a draft is converted to ready
    if action == "ready_for_review" and is_copilot_pr:
        logger.info(
            "Copilot PR #%d marked ready for review in %s/%s",
            pr_number,
            repo_owner,
            repo_name,
        )

        return await update_issue_status_for_copilot_pr(
            pr_data=pr_data,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pr_number=pr_number,
            pr_author=pr_author,
        )

    # Also handle when PR is opened and not a draft (Copilot might open PRs directly)
    if action == "opened" and is_copilot_pr and not is_draft:
        logger.info(
            "Copilot opened non-draft PR #%d in %s/%s",
            pr_number,
            repo_owner,
            repo_name,
        )

        return await update_issue_status_for_copilot_pr(
            pr_data=pr_data,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pr_number=pr_number,
            pr_author=pr_author,
        )

    return {
        "status": "ignored",
        "event": "pull_request",
        "action": action,
        "pr_number": pr_number,
        "reason": "not_copilot_ready_event",
    }


async def update_issue_status_for_copilot_pr(
    pr_data: dict,
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    pr_author: str,
) -> dict[str, Any]:
    """
    Update linked issue status to 'In Review' when Copilot PR is ready.

    Args:
        pr_data: Pull request data from webhook
        repo_owner: Repository owner
        repo_name: Repository name
        pr_number: Pull request number
        pr_author: PR author username

    Returns:
        Result dict with status and details
    """
    settings = get_settings()

    # Extract linked issue number from PR
    issue_number = extract_issue_number_from_pr(pr_data)

    if not issue_number:
        logger.warning(
            "Could not find linked issue for PR #%d",
            pr_number,
        )
        return {
            "status": "detected",
            "event": "copilot_pr_ready",
            "pr_number": pr_number,
            "pr_author": pr_author,
            "repository": f"{repo_owner}/{repo_name}",
            "action": "no_linked_issue_found",
            "message": f"Copilot PR #{pr_number} is ready but no linked issue found.",
        }

    logger.info(
        "Found linked issue #%d for Copilot PR #%d",
        issue_number,
        pr_number,
    )

    # Check if we have a webhook token to perform the update
    if not settings.github_webhook_token:
        logger.warning(
            "No GITHUB_WEBHOOK_TOKEN configured - cannot update issue status automatically"
        )
        return {
            "status": "detected",
            "event": "copilot_pr_ready",
            "pr_number": pr_number,
            "pr_author": pr_author,
            "repository": f"{repo_owner}/{repo_name}",
            "issue_number": issue_number,
            "action_needed": "update_issue_status_to_in_review",
            "message": f"Copilot PR #{pr_number} is ready. Issue #{issue_number} should be updated to 'In Review'. Configure GITHUB_WEBHOOK_TOKEN for automatic updates.",
        }

    # Get the project ID for this repository
    # We need to find which project contains this issue
    try:
        # Try to find the project for this repository
        # First, list user's projects to find the matching one
        projects_response = await github_projects_service.rest_request(
            settings.github_webhook_token,
            "GET",
            "/user",
        )

        if projects_response.status_code != 200:
            logger.error("Failed to authenticate with webhook token")
            return {
                "status": "error",
                "event": "copilot_pr_ready",
                "pr_number": pr_number,
                "error": "Failed to authenticate with webhook token",
            }

        # Get projects for the repository owner
        webhook_user = projects_response.json()
        webhook_username: str = webhook_user.get("login", repo_owner)
        projects = await github_projects_service.list_user_projects(
            settings.github_webhook_token, webhook_username
        )

        # Find the project that contains this repository
        target_project = None
        target_item_id = None

        for project in projects:
            # Get project items to find our issue
            try:
                items = await github_projects_service.get_project_items(
                    settings.github_webhook_token,
                    project.project_id,
                )

                for item in items:
                    # Check if this item matches our issue by issue number
                    if item.issue_number is not None and item.issue_number == issue_number:
                        target_project = project
                        target_item_id = item.github_item_id
                        break
                    # Also check by title match as fallback
                    if item.title and f"#{issue_number}" in item.title:
                        target_project = project
                        target_item_id = item.github_item_id
                        break

                if target_project:
                    break

            except Exception as e:
                logger.warning("Failed to get items for project %s: %s", project.project_id, e)
                continue

        if not target_project or not target_item_id:
            logger.warning(
                "Could not find issue #%d in any project",
                issue_number,
            )
            return {
                "status": "detected",
                "event": "copilot_pr_ready",
                "pr_number": pr_number,
                "pr_author": pr_author,
                "repository": f"{repo_owner}/{repo_name}",
                "issue_number": issue_number,
                "action": "issue_not_in_project",
                "message": f"Copilot PR #{pr_number} is ready. Issue #{issue_number} not found in any project.",
            }

        # ── Pipeline-position guard: only move to "In Review" when appropriate ──
        # For pipeline-tracked issues, the status transition should only happen
        # when the pipeline has reached the copilot-review step.  If an earlier
        # agent (e.g. speckit.implement) finishes and its PR triggers a
        # ready_for_review event, we must NOT move the issue to "In Review"
        # prematurely — the pipeline's own _transition_after_pipeline_complete()
        # handles status transitions at the correct time.
        from src.services.copilot_polling import get_pipeline_state

        pipeline = get_pipeline_state(issue_number)
        if pipeline is not None:
            current_agent = getattr(pipeline, "current_agent", None)
            if current_agent and current_agent != "copilot-review":
                logger.warning(
                    "Webhook guard: skipping 'In Review' move for issue #%d — "
                    "pipeline current agent is '%s', not 'copilot-review'",
                    issue_number,
                    current_agent,
                )
                return {
                    "status": "skipped",
                    "event": "copilot_pr_ready",
                    "pr_number": pr_number,
                    "pr_author": pr_author,
                    "repository": f"{repo_owner}/{repo_name}",
                    "issue_number": issue_number,
                    "reason": "pipeline_agent_not_copilot_review",
                    "current_agent": current_agent,
                    "message": (
                        f"Skipped moving issue #{issue_number} to 'In Review': "
                        f"pipeline current agent is '{current_agent}', not 'copilot-review'"
                    ),
                }

        # Update the issue status to "In Review"
        logger.info(
            "Updating issue #%d status to 'In Review' in project %s",
            issue_number,
            target_project.project_id,
        )

        success = await github_projects_service.update_item_status_by_name(
            access_token=settings.github_webhook_token,
            project_id=target_project.project_id,
            item_id=target_item_id,
            status_name="In Review",
        )

        if success:
            logger.info(
                "Successfully updated issue #%d to 'In Review' status",
                issue_number,
            )
            return {
                "status": "success",
                "event": "copilot_pr_ready",
                "pr_number": pr_number,
                "pr_author": pr_author,
                "repository": f"{repo_owner}/{repo_name}",
                "issue_number": issue_number,
                "project_id": target_project.project_id,
                "action": "status_updated",
                "new_status": "In Review",
                "message": f"Issue #{issue_number} status updated to 'In Review' after Copilot PR #{pr_number} ready.",
            }
        else:
            logger.error(
                "Failed to update issue #%d status",
                issue_number,
            )
            return {
                "status": "error",
                "event": "copilot_pr_ready",
                "pr_number": pr_number,
                "issue_number": issue_number,
                "error": "Failed to update issue status",
            }

    except Exception as e:
        logger.error(
            "Error updating issue status for Copilot PR #%d: %s",
            pr_number,
            e,
            exc_info=True,
        )
        return {
            "status": "error",
            "event": "copilot_pr_ready",
            "pr_number": pr_number,
            "issue_number": issue_number,
            "error": "Failed to update issue status",
        }


async def handle_check_run_event(payload: CheckRunEvent) -> dict[str, Any]:
    """Handle check_run webhook events for CI failure detection.

    Routes check_run completed events with failure/timed_out conclusions
    to the DevOps agent dispatcher for auto-merge-enabled pipelines.
    """
    if payload.action != "completed":
        return {"status": "ignored", "reason": "action_not_completed"}

    conclusion = payload.check_run.conclusion
    if conclusion not in ("failure", "timed_out"):
        return {"status": "ignored", "reason": "conclusion_not_failure"}

    # Find associated PRs
    pr_numbers = [pr.number for pr in payload.check_run.pull_requests]
    if not pr_numbers:
        return {"status": "ignored", "reason": "no_associated_prs"}

    logger.info(
        "Check run '%s' failed (conclusion=%s) for PRs %s",
        payload.check_run.name,
        conclusion,
        pr_numbers,
    )

    return {
        "status": "processed",
        "event": "check_run_failure",
        "check_name": payload.check_run.name,
        "conclusion": conclusion,
        "pr_numbers": pr_numbers,
    }


async def handle_check_suite_event(payload: CheckSuiteEvent) -> dict[str, Any]:
    """Handle check_suite webhook events for CI failure detection.

    Routes check_suite completed events with failure conclusions
    to the DevOps agent dispatcher for auto-merge-enabled pipelines.
    """
    if payload.action != "completed":
        return {"status": "ignored", "reason": "action_not_completed"}

    conclusion = payload.check_suite.conclusion
    if conclusion != "failure":
        return {"status": "ignored", "reason": "conclusion_not_failure"}

    # Find associated PRs
    pr_numbers = [pr.number for pr in payload.check_suite.pull_requests]
    if not pr_numbers:
        return {"status": "ignored", "reason": "no_associated_prs"}

    logger.info(
        "Check suite failed (conclusion=%s) for PRs %s",
        conclusion,
        pr_numbers,
    )

    return {
        "status": "processed",
        "event": "check_suite_failure",
        "conclusion": conclusion,
        "pr_numbers": pr_numbers,
    }
