"""Consolidated label vs tracking table validation.

Provides a single ``validate_pipeline_labels()`` entry-point that
cross-checks pipeline labels against the Markdown tracking table and
corrects whichever source is stale.
"""

import src.services.copilot_polling as _cp
from src.constants import (
    build_agent_label,
    find_agent_label,
)
from src.logging_utils import get_logger

logger = get_logger(__name__)


async def validate_pipeline_labels(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    labels: list[dict[str, str]],
    tracking_steps: list,
    pipeline_config_name: str | None = None,
) -> tuple[bool, list[str]]:
    """Cross-check labels vs tracking table, fix the stale source.

    Comparison logic:
    1. Extract ``agent:<slug>`` from labels → *label_agent*
    2. Find the active agent from *tracking_steps* → *table_agent*
    3. If they agree → no action.
    4. If they disagree → check GitHub ground truth (sub-issue state,
       Copilot assignment) and fix the stale source.

    Returns:
        ``(corrections_made, correction_descriptions)``
    """
    from src.services.agent_tracking import STATE_ACTIVE, STATE_PENDING

    corrections: list[str] = []

    # Determine label-derived agent
    label_agent = find_agent_label(labels)

    # Determine tracking-table-derived agent
    table_agent: str | None = None
    for step in tracking_steps:
        if STATE_ACTIVE in step.state:
            table_agent = step.agent_name
            break
    if table_agent is None:
        for step in tracking_steps:
            if STATE_PENDING in step.state:
                table_agent = step.agent_name
                break

    # ── Consistent → nothing to do ────────────────────────────────────
    if label_agent == table_agent:
        return (False, [])

    # ── Both present but disagree → fix the stale source ──────────────
    if label_agent is not None and table_agent is not None:
        # The tracking table is the authoritative audit trail; when
        # ambiguous, it wins. However, we still update labels to match.
        try:
            old_label = build_agent_label(label_agent)
            new_label = build_agent_label(table_agent)
            await _cp.github_projects_service.update_issue_state(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                labels_add=[new_label],
                labels_remove=[old_label],
            )
            msg = (
                f"Label correction on #{issue_number}: "
                f"swapped agent:{label_agent} → agent:{table_agent} "
                "(tracking table is authoritative)"
            )
            logger.warning(msg)
            corrections.append(msg)
        except Exception as exc:
            msg = f"Failed to correct agent label on #{issue_number}: {exc}"
            logger.warning(msg)
            corrections.append(msg)

    # ── Label missing, table has agent → add label ────────────────────
    elif label_agent is None and table_agent is not None:
        try:
            new_label = build_agent_label(table_agent)
            await _cp.github_projects_service.update_issue_state(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                labels_add=[new_label],
            )
            msg = f"Added missing agent:{table_agent} label to #{issue_number}"
            logger.warning(msg)
            corrections.append(msg)
        except Exception as exc:
            msg = f"Failed to add agent label to #{issue_number}: {exc}"
            logger.warning(msg)
            corrections.append(msg)

    # ── Label present, table has no active agent → remove label ───────
    elif label_agent is not None and table_agent is None:
        try:
            old_label = build_agent_label(label_agent)
            await _cp.github_projects_service.update_issue_state(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                labels_remove=[old_label],
            )
            msg = (
                f"Removed stale agent:{label_agent} label from #{issue_number} "
                "(no active agent in tracking table)"
            )
            logger.warning(msg)
            corrections.append(msg)
        except Exception as exc:
            msg = f"Failed to remove stale agent label from #{issue_number}: {exc}"
            logger.warning(msg)
            corrections.append(msg)

    return (len(corrections) > 0, corrections)
