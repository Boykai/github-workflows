"""Roadmap batch generation — gathers context, calls AI, persists cycle (FR-004)."""

from __future__ import annotations

import json
import logging

from src.logging_utils import get_logger
from src.models.roadmap import RoadmapBatch, RoadmapCycleStatus, RoadmapItem
from src.prompts.roadmap_generation import create_roadmap_generation_prompt

logger = get_logger(__name__)

# Maximum number of recent cycle titles fed into the dedup prompt.
_DEDUP_HISTORY_LIMIT = 30


async def generate_roadmap_batch(
    project_id: str,
    user_id: str,
    access_token: str,
) -> RoadmapBatch:
    """Generate a roadmap batch via AI and persist the cycle audit record.

    Steps:
      1. Load roadmap config from settings.
      2. Validate: seed non-empty (FR-014), pipeline exists (FR-011).
      3. Query recent cycle titles for dedup (FR-013).
      4. Gather codebase context signals (FR-004).
      5. Build prompt and call CompletionProvider.complete().
      6. Parse JSON response into RoadmapBatch.
      7. Persist cycle record (FR-003).

    Raises:
        ValueError: If preconditions fail (empty seed, missing pipeline).
        RuntimeError: If AI response cannot be parsed.
    """
    from src.services.database import get_db

    db = get_db()

    # ── 1. Load config ──────────────────────────────────────────────
    config = await _load_roadmap_config(db, project_id)

    # ── 2. Validate preconditions ───────────────────────────────────
    if not config.roadmap_seed or not config.roadmap_seed.strip():
        raise ValueError("Seed vision is required for generation")

    if config.roadmap_pipeline_id:
        pipeline_valid = await _validate_pipeline(project_id, config.roadmap_pipeline_id)
        if not pipeline_valid:
            raise ValueError("Referenced pipeline does not exist or is not active")

    # ── 3. Recent titles for dedup ──────────────────────────────────
    recent_titles = await _get_recent_titles(db, project_id)

    # ── 4. Codebase context ─────────────────────────────────────────
    codebase_context = await _gather_codebase_context(project_id, access_token)

    # ── 5. Build prompt and call AI ─────────────────────────────────
    messages = create_roadmap_generation_prompt(
        seed=config.roadmap_seed,
        batch_size=config.roadmap_batch_size,
        codebase_context=codebase_context,
        recent_titles=recent_titles,
    )

    # Insert pending cycle row first for auditability
    cycle_id = await _insert_cycle(db, project_id, user_id, "[]", RoadmapCycleStatus.PENDING)

    try:
        ai_response = await _call_completion(messages, access_token)
        items = _parse_ai_response(ai_response)
    except Exception as exc:
        # FR-012: record as failed, no partial items
        await _update_cycle_status(db, cycle_id, RoadmapCycleStatus.FAILED)
        logger.error("Roadmap generation failed for project %s: %s", project_id, exc)
        raise RuntimeError(f"AI generation failed: {exc}") from exc

    batch = RoadmapBatch(
        items=items,
        project_id=project_id,
        user_id=user_id,
    )

    # Update cycle with batch data and mark completed
    await _update_cycle_batch(db, cycle_id, batch.model_dump_json(), RoadmapCycleStatus.COMPLETED)

    logger.info(
        "Roadmap batch generated for project %s: %d items (cycle %d)",
        project_id,
        len(items),
        cycle_id,
    )
    return batch


# ── Internal helpers ─────────────────────────────────────────────────────


async def _load_roadmap_config(db, project_id: str):
    """Load the ProjectBoardConfig for the project."""
    from src.services.settings_store import get_project_settings_row

    row = await get_project_settings_row(db, "__workflow__", project_id)
    if row is None:
        from src.models.settings import ProjectBoardConfig

        return ProjectBoardConfig()

    from src.models.settings import ProjectBoardConfig

    if row["board_display_config"]:
        raw = json.loads(row["board_display_config"])
        return ProjectBoardConfig(**raw)
    return ProjectBoardConfig()


async def _validate_pipeline(project_id: str, pipeline_id: str) -> bool:
    """Check if the pipeline exists and is accessible."""
    try:
        from src.services.copilot_polling import get_pipeline_service

        service = get_pipeline_service()
        pipeline = await service.get_pipeline(project_id, pipeline_id)
        return pipeline is not None
    except Exception:
        logger.debug("Pipeline validation failed for %s/%s", project_id, pipeline_id)
        return False


async def _get_recent_titles(db, project_id: str) -> list[str]:
    """Query recent cycle titles for dedup (FR-013)."""
    cursor = await db.execute(
        "SELECT batch_json FROM roadmap_cycles "
        "WHERE project_id = ? AND status = 'completed' "
        "ORDER BY created_at DESC LIMIT ?",
        (project_id, _DEDUP_HISTORY_LIMIT),
    )
    rows = await cursor.fetchall()
    titles: list[str] = []
    for row in rows:
        try:
            batch_data = json.loads(row[0])
            for item in batch_data.get("items", []):
                if "title" in item:
                    titles.append(item["title"])
        except (json.JSONDecodeError, KeyError):
            continue
    return titles


async def _gather_codebase_context(project_id: str, access_token: str) -> str:
    """Gather codebase signals for the AI prompt.

    Returns a summary string. Gracefully degrades if codegraphcontext
    is unavailable.
    """
    try:
        from codegraphcontext import CodeGraphContext

        cgc = CodeGraphContext()
        summary = await cgc.get_summary(project_id=project_id, token=access_token)
        return str(summary) if summary else "No codebase context available."
    except Exception:
        logger.debug("CodeGraphContext unavailable, using minimal context")
        return "No codebase context available."


async def _call_completion(messages: list[dict[str, str]], access_token: str) -> str:
    """Call the AI completion provider."""
    from src.services.completion_provider import get_completion_provider

    provider = get_completion_provider()
    return await provider.complete(messages=messages, token=access_token)


def _parse_ai_response(response: str) -> list[RoadmapItem]:
    """Parse the AI response JSON into a list of RoadmapItem models.

    Raises ValueError on parse failure (FR-012).
    """
    # Strip markdown fences if present
    text = response.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first and last lines (fences)
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"AI response is not valid JSON: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("AI response must be a JSON array")

    items = []
    for entry in data:
        items.append(RoadmapItem.model_validate(entry))

    if not items:
        raise ValueError("AI response contained no valid items")

    return items


async def _insert_cycle(
    db, project_id: str, user_id: str, batch_json: str, status: RoadmapCycleStatus
) -> int:
    """Insert a new cycle record and return the cycle ID."""
    cursor = await db.execute(
        "INSERT INTO roadmap_cycles (project_id, user_id, batch_json, status) VALUES (?, ?, ?, ?)",
        (project_id, user_id, batch_json, status.value),
    )
    await db.commit()
    return cursor.lastrowid  # type: ignore[return-value]


async def _update_cycle_status(db, cycle_id: int, status: RoadmapCycleStatus) -> None:
    """Update the status of an existing cycle record."""
    await db.execute(
        "UPDATE roadmap_cycles SET status = ? WHERE id = ?",
        (status.value, cycle_id),
    )
    await db.commit()


async def _update_cycle_batch(
    db, cycle_id: int, batch_json: str, status: RoadmapCycleStatus
) -> None:
    """Update cycle with batch data and status."""
    await db.execute(
        "UPDATE roadmap_cycles SET batch_json = ?, status = ? WHERE id = ?",
        (batch_json, status.value, cycle_id),
    )
    await db.commit()
