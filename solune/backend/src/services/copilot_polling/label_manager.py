"""GitHub label manager for pipeline state tracking (FR-015).

Manages pipeline state labels on GitHub repositories. Labels follow the
format ``solune:pipeline:{run_id}:stage:{stage_id}:{status}`` and are used
for state recovery on startup, reducing GitHub API calls by ~60%.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import quote

from src.logging_utils import get_logger

logger = get_logger(__name__)

# Label format: solune:pipeline:{run_id}:stage:{stage_id}:{status}
LABEL_PREFIX = "solune:pipeline:"
LABEL_PATTERN = re.compile(r"^solune:pipeline:(\d+):stage:([^:]+):([a-z]+)$")


@dataclass
class ParsedLabel:
    """A parsed pipeline state label."""

    run_id: int
    stage_id: str
    status: str
    full_name: str


def build_label_name(run_id: int, stage_id: str, status: str) -> str:
    """Build a pipeline state label name."""
    return f"solune:pipeline:{run_id}:stage:{stage_id}:{status}"


def parse_label(label_name: str) -> ParsedLabel | None:
    """Parse a pipeline state label name into components.

    Returns None if the label doesn't match the expected format.
    """
    match = LABEL_PATTERN.match(label_name)
    if not match:
        return None
    return ParsedLabel(
        run_id=int(match.group(1)),
        stage_id=match.group(2),
        status=match.group(3),
        full_name=label_name,
    )


async def create_pipeline_label(
    access_token: str,
    owner: str,
    repo: str,
    run_id: int,
    stage_id: str,
    status: str,
) -> str | None:
    """Create a pipeline state label on the GitHub repository.

    Returns the label name on success, None on failure.
    """
    label_name = build_label_name(run_id, stage_id, status)
    try:
        from src.services.github_projects import github_projects_service

        response = await github_projects_service.rest_request(
            access_token,
            "POST",
            f"/repos/{owner}/{repo}/labels",
            json={
                "name": label_name,
                "color": _status_color(status),
                "description": f"Pipeline run {run_id} stage {stage_id}",
            },
        )
        if response and hasattr(response, "status_code") and response.status_code < 300:
            logger.debug("Created pipeline label: %s", label_name)
            return label_name
        # GitHub returns 422 with "already_exists" for duplicate label names
        if response and hasattr(response, "status_code") and response.status_code == 422:
            logger.debug("Pipeline label already exists (422): %s", label_name)
            return label_name
        logger.warning("Failed to create pipeline label %s: %s", label_name, response)
        return None
    except Exception:
        logger.exception("Error creating pipeline label: %s", label_name)
        return None


async def update_pipeline_label(
    access_token: str,
    owner: str,
    repo: str,
    run_id: int,
    stage_id: str,
    old_status: str,
    new_status: str,
) -> str | None:
    """Update a pipeline state label by deleting the old and creating a new one.

    GitHub labels are immutable names — updates require delete + create.
    Creates the new label first so that if creation fails, the old label
    is preserved (no state loss).
    Returns the new label name on success, None on failure.
    """
    new_label = await create_pipeline_label(access_token, owner, repo, run_id, stage_id, new_status)
    if new_label is None:
        return None
    old_name = build_label_name(run_id, stage_id, old_status)
    await delete_pipeline_label(access_token, owner, repo, old_name)
    return new_label


async def delete_pipeline_label(
    access_token: str,
    owner: str,
    repo: str,
    label_name: str,
) -> bool:
    """Delete a pipeline state label from the repository."""
    try:
        from src.services.github_projects import github_projects_service

        await github_projects_service.rest_request(
            access_token,
            "DELETE",
            f"/repos/{owner}/{repo}/labels/{quote(label_name, safe='')}",
        )
        logger.debug("Deleted pipeline label: %s", label_name)
        return True
    except Exception:
        logger.debug("Could not delete pipeline label %s (may not exist)", label_name)
        return False


async def query_pipeline_labels(
    access_token: str,
    owner: str,
    repo: str,
) -> list[ParsedLabel]:
    """Query all pipeline state labels from the repository.

    Used during startup recovery to reconcile DB state with label state.
    Returns parsed labels, filtering out any non-pipeline labels.
    """
    labels: list[ParsedLabel] = []
    try:
        from src.services.github_projects import github_projects_service

        page = 1
        while True:
            response = await github_projects_service.rest_request(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/labels",
                params={"per_page": 100, "page": page},
            )
            if not response or not hasattr(response, "parsed_data"):
                break
            data = response.parsed_data
            if not data:
                break

            for label_data in data:
                name = (
                    label_data.get("name", "")
                    if isinstance(label_data, dict)
                    else getattr(label_data, "name", "")
                )
                parsed = parse_label(name)
                if parsed:
                    labels.append(parsed)

            # Check if there are more pages
            if len(data) < 100:
                break
            page += 1

    except Exception:
        logger.exception("Error querying pipeline labels from %s/%s", owner, repo)

    logger.info("Found %d pipeline state labels in %s/%s", len(labels), owner, repo)
    return labels


def _status_color(status: str) -> str:
    """Map pipeline stage status to a label color."""
    colors = {
        "pending": "d4c5f9",  # light purple
        "running": "0e8a16",  # green
        "completed": "1d76db",  # blue
        "failed": "e11d48",  # red
        "skipped": "6b7280",  # gray
        "cancelled": "fbbf24",  # amber
    }
    return colors.get(status, "d4c5f9")
