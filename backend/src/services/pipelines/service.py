"""PipelineService — CRUD operations for Agent Pipeline configurations."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import aiosqlite

from src.logging_utils import get_logger
from src.models.pipeline import (
    PipelineConfig,
    PipelineConfigCreate,
    PipelineConfigListResponse,
    PipelineConfigSummary,
    PipelineConfigUpdate,
    PipelineStage,
    ProjectPipelineAssignment,
)

logger = get_logger(__name__)

_CANONICAL_PROJECT_SETTINGS_USER = "__workflow__"

# Column allowlist for dynamic SET clauses
_PIPELINE_COLUMNS = frozenset({"name", "description", "stages", "updated_at", "blocking"})


# ---------------------------------------------------------------------------
# Helper to build a standard agent dict with model_id/model_name set to Auto
# ---------------------------------------------------------------------------
def _agent(aid: str, slug: str, display: str) -> dict:
    return {
        "id": aid,
        "agent_slug": slug,
        "agent_display_name": display,
        "model_id": "",
        "model_name": "",
        "tool_ids": [],
        "tool_count": 0,
        "config": {},
    }


# Preset pipeline definitions
_PRESET_DEFINITIONS = [
    # ── Spec Kit ──────────────────────────────────────────────────────
    {
        "preset_id": "spec-kit",
        "name": "Spec Kit",
        "description": "Full specification workflow: specify → plan → tasks → implement → analyze",
        "stages": [
            {
                "id": "preset-sk-stage-1",
                "name": "Specify",
                "order": 0,
                "agents": [_agent("preset-sk-agent-1", "speckit.specify", "Spec Writer")],
            },
            {
                "id": "preset-sk-stage-2",
                "name": "Plan",
                "order": 1,
                "agents": [_agent("preset-sk-agent-2", "speckit.plan", "Planner")],
            },
            {
                "id": "preset-sk-stage-3",
                "name": "Tasks",
                "order": 2,
                "agents": [_agent("preset-sk-agent-3", "speckit.tasks", "Task Generator")],
            },
            {
                "id": "preset-sk-stage-4",
                "name": "Implement",
                "order": 3,
                "agents": [_agent("preset-sk-agent-4", "speckit.implement", "Implementer")],
            },
            {
                "id": "preset-sk-stage-5",
                "name": "Analyze",
                "order": 4,
                "agents": [_agent("preset-sk-agent-5", "speckit.analyze", "Analyzer")],
            },
        ],
    },
    # ── GitHub Copilot ────────────────────────────────────────────────
    {
        "preset_id": "github-copilot",
        "name": "GitHub Copilot",
        "description": "Single-stage pipeline powered by GitHub Copilot",
        "stages": [
            {
                "id": "preset-gc-stage-1",
                "name": "Execute",
                "order": 0,
                "agents": [_agent("preset-gc-agent-1", "copilot", "GitHub Copilot")],
            },
        ],
    },
    # ── Easy ──────────────────────────────────────────────────────────
    {
        "preset_id": "easy",
        "name": "Easy",
        "description": "Lightweight pipeline: Copilot implements, review agents check quality",
        "stages": [
            {"id": "preset-easy-stage-0", "name": "Backlog", "order": 0, "agents": []},
            {"id": "preset-easy-stage-1", "name": "Ready", "order": 1, "agents": []},
            {
                "id": "preset-easy-stage-2",
                "name": "In progress",
                "order": 2,
                "agents": [
                    _agent("preset-easy-agent-1", "copilot", "GitHub Copilot"),
                    _agent("preset-easy-agent-2", "copilot-review", "Copilot Review"),
                    _agent("preset-easy-agent-3", "judge", "judge"),
                    _agent("preset-easy-agent-4", "linter", "linter"),
                ],
            },
            {
                "id": "preset-easy-stage-3",
                "name": "In review",
                "order": 3,
                "agents": [
                    _agent("preset-easy-agent-5", "human", "Human"),
                ],
            },
            {"id": "preset-easy-stage-4", "name": "Done", "order": 4, "agents": []},
        ],
    },
    # ── Medium ────────────────────────────────────────────────────────
    {
        "preset_id": "medium",
        "name": "Medium",
        "description": "Balanced pipeline: Spec Kit plans, Copilot implements, review agents verify",
        "stages": [
            {
                "id": "preset-med-stage-0",
                "name": "Backlog",
                "order": 0,
                "agents": [
                    _agent("preset-med-agent-1", "speckit.specify", "Spec Kit - Specify"),
                ],
            },
            {
                "id": "preset-med-stage-1",
                "name": "Ready",
                "order": 1,
                "agents": [
                    _agent("preset-med-agent-2", "speckit.plan", "Spec Kit - Plan"),
                    _agent("preset-med-agent-3", "speckit.tasks", "Spec Kit - Tasks"),
                ],
            },
            {
                "id": "preset-med-stage-2",
                "name": "In progress",
                "order": 2,
                "agents": [
                    _agent("preset-med-agent-4", "speckit.implement", "Spec Kit - Implement"),
                    _agent("preset-med-agent-5", "copilot-review", "Copilot Review"),
                    _agent("preset-med-agent-6", "judge", "judge"),
                    _agent("preset-med-agent-7", "linter", "linter"),
                ],
            },
            {
                "id": "preset-med-stage-3",
                "name": "In review",
                "order": 3,
                "agents": [
                    _agent("preset-med-agent-8", "human", "Human"),
                ],
            },
            {"id": "preset-med-stage-4", "name": "Done", "order": 4, "agents": []},
        ],
    },
    # ── Hard ──────────────────────────────────────────────────────────
    {
        "preset_id": "hard",
        "name": "Hard",
        "description": "Thorough pipeline: Spec Kit specifies & plans, full implementation and review",
        "stages": [
            {
                "id": "preset-hard-stage-0",
                "name": "Backlog",
                "order": 0,
                "agents": [
                    _agent("preset-hard-agent-1", "speckit.specify", "Spec Kit - Specify"),
                ],
            },
            {
                "id": "preset-hard-stage-1",
                "name": "Ready",
                "order": 1,
                "agents": [
                    _agent("preset-hard-agent-2", "speckit.plan", "Spec Kit - Plan"),
                    _agent("preset-hard-agent-3", "speckit.tasks", "Spec Kit - Tasks"),
                ],
            },
            {
                "id": "preset-hard-stage-2",
                "name": "In progress",
                "order": 2,
                "agents": [
                    _agent("preset-hard-agent-4", "speckit.implement", "Spec Kit - Implement"),
                    _agent("preset-hard-agent-5", "copilot-review", "Copilot Review"),
                    _agent("preset-hard-agent-6", "judge", "judge"),
                    _agent("preset-hard-agent-7", "linter", "linter"),
                ],
            },
            {
                "id": "preset-hard-stage-3",
                "name": "In review",
                "order": 3,
                "agents": [
                    _agent("preset-hard-agent-8", "human", "Human"),
                ],
            },
            {"id": "preset-hard-stage-4", "name": "Done", "order": 4, "agents": []},
        ],
    },
    # ── Expert ────────────────────────────────────────────────────────
    {
        "preset_id": "expert",
        "name": "Expert",
        "description": "Comprehensive pipeline: full Spec Kit, Designer, QA, Tester, Archivist, dual review",
        "stages": [
            {
                "id": "preset-exp-stage-0",
                "name": "Backlog",
                "order": 0,
                "agents": [
                    _agent("preset-exp-agent-1", "speckit.specify", "Spec Kit - Specify"),
                    _agent("preset-exp-agent-2", "designer", "designer"),
                ],
            },
            {
                "id": "preset-exp-stage-1",
                "name": "Ready",
                "order": 1,
                "agents": [
                    _agent("preset-exp-agent-3", "speckit.plan", "Spec Kit - Plan"),
                    _agent("preset-exp-agent-4", "speckit.tasks", "Spec Kit - Tasks"),
                ],
            },
            {
                "id": "preset-exp-stage-2",
                "name": "In progress",
                "order": 2,
                "agents": [
                    _agent("preset-exp-agent-5", "speckit.implement", "Spec Kit - Implement"),
                    _agent("preset-exp-agent-6", "copilot-review", "Copilot Review"),
                    _agent("preset-exp-agent-7", "judge", "judge"),
                    _agent("preset-exp-agent-8", "quality-assurance", "quality-assurance"),
                    _agent("preset-exp-agent-9", "tester", "tester"),
                    _agent("preset-exp-agent-10", "copilot-review", "Copilot Review"),
                    _agent("preset-exp-agent-11", "judge", "judge"),
                    _agent("preset-exp-agent-12", "archivist", "archivist"),
                    _agent("preset-exp-agent-13", "linter", "linter"),
                ],
            },
            {
                "id": "preset-exp-stage-3",
                "name": "In review",
                "order": 3,
                "agents": [
                    _agent("preset-exp-agent-14", "human", "Human"),
                ],
            },
            {"id": "preset-exp-stage-4", "name": "Done", "order": 4, "agents": []},
        ],
    },
]


class PipelineService:
    """Manages pipeline configuration records in the SQLite database."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _normalize_tool_counts(stages: list[PipelineStage]) -> list[PipelineStage]:
        """Ensure tool_count matches len(tool_ids) for every agent node."""
        for stage in stages:
            for agent in stage.agents:
                agent.tool_count = len(agent.tool_ids)
        return stages

    @staticmethod
    def _row_to_config(row_dict: dict) -> PipelineConfig:
        """Convert a database row dict to a PipelineConfig model."""
        stages_raw = json.loads(row_dict.get("stages", "[]"))
        stages = [PipelineStage(**s) for s in stages_raw]
        return PipelineConfig(
            id=row_dict["id"],
            project_id=row_dict["project_id"],
            name=row_dict["name"],
            description=row_dict.get("description", ""),
            stages=stages,
            is_preset=bool(row_dict.get("is_preset", 0)),
            preset_id=row_dict.get("preset_id", ""),
            blocking=bool(row_dict.get("blocking", 0)),
            created_at=row_dict["created_at"],
            updated_at=row_dict["updated_at"],
        )

    # ── List ──────────────────────────────────────────────────────────

    async def list_pipelines(
        self,
        project_id: str,
        sort: str = "updated_at",
        order: str = "desc",
    ) -> PipelineConfigListResponse:
        """List all pipeline configurations for a project with enriched summaries."""
        allowed_sort = {"updated_at", "name", "created_at"}
        allowed_order = {"asc", "desc"}
        sort_col = sort if sort in allowed_sort else "updated_at"
        sort_dir = order if order in allowed_order else "desc"

        cursor = await self._db.execute(
            f"SELECT * FROM pipeline_configs WHERE project_id = ? ORDER BY {sort_col} {sort_dir.upper()}",
            (project_id,),
        )
        rows = await cursor.fetchall()

        summaries: list[PipelineConfigSummary] = []
        for row in rows:
            row_dict = dict(row)
            stages = json.loads(row_dict.get("stages", "[]"))
            parsed_stages = [PipelineStage(**s) for s in stages]
            agent_count = sum(len(s.agents) for s in parsed_stages)
            total_tool_count = sum(a.tool_count for s in parsed_stages for a in s.agents)
            summaries.append(
                PipelineConfigSummary(
                    id=row_dict["id"],
                    name=row_dict["name"],
                    description=row_dict.get("description", ""),
                    stage_count=len(parsed_stages),
                    agent_count=agent_count,
                    total_tool_count=total_tool_count,
                    is_preset=bool(row_dict.get("is_preset", 0)),
                    preset_id=row_dict.get("preset_id", ""),
                    stages=parsed_stages,
                    blocking=bool(row_dict.get("blocking", 0)),
                    updated_at=row_dict["updated_at"],
                )
            )

        return PipelineConfigListResponse(pipelines=summaries, total=len(summaries))

    # ── Get ───────────────────────────────────────────────────────────

    async def get_pipeline(
        self,
        project_id: str,
        pipeline_id: str,
    ) -> PipelineConfig | None:
        """Get a single pipeline configuration by ID."""
        cursor = await self._db.execute(
            "SELECT * FROM pipeline_configs WHERE id = ? AND project_id = ?",
            (pipeline_id, project_id),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_config(dict(row))

    # ── Create ────────────────────────────────────────────────────────

    async def create_pipeline(
        self,
        project_id: str,
        body: PipelineConfigCreate,
    ) -> PipelineConfig:
        """Create a new pipeline configuration.

        Raises:
            ValueError: If a pipeline with the same name already exists.
        """
        pipeline_id = str(uuid.uuid4())
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        normalized_stages = self._normalize_tool_counts(list(body.stages))
        stages_json = json.dumps([s.model_dump() for s in normalized_stages])

        try:
            await self._db.execute(
                """
                INSERT INTO pipeline_configs (id, project_id, name, description, stages, blocking, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pipeline_id,
                    project_id,
                    body.name,
                    body.description,
                    stages_json,
                    int(body.blocking),
                    now,
                    now,
                ),
            )
            await self._db.commit()
        except aiosqlite.IntegrityError as exc:
            raise ValueError(
                f"A pipeline named '{body.name}' already exists in this project."
            ) from exc

        pipeline = await self.get_pipeline(project_id, pipeline_id)
        assert pipeline is not None
        return pipeline

    # ── Update ────────────────────────────────────────────────────────

    async def update_pipeline(
        self,
        project_id: str,
        pipeline_id: str,
        body: PipelineConfigUpdate,
    ) -> PipelineConfig | None:
        """Update an existing pipeline configuration.

        Returns None if the pipeline does not exist.
        Raises ValueError on duplicate name.
        Raises PermissionError if the pipeline is a preset.
        """
        existing = await self.get_pipeline(project_id, pipeline_id)
        if existing is None:
            return None

        if existing.is_preset:
            raise PermissionError(
                "Cannot modify preset pipelines. Use 'Save as Copy' to create an editable version."
            )

        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return existing

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        updates["updated_at"] = now

        if "stages" in updates and updates["stages"] is not None:
            # Normalize tool counts before saving
            raw_stages = updates["stages"]
            parsed = [
                PipelineStage(**(s.model_dump() if hasattr(s, "model_dump") else s))
                for s in raw_stages
            ]
            self._normalize_tool_counts(parsed)
            updates["stages"] = json.dumps([s.model_dump() for s in parsed])

        if "blocking" in updates and updates["blocking"] is not None:
            updates["blocking"] = int(bool(updates["blocking"]))

        # Validate columns against allowlist
        safe_updates = {k: v for k, v in updates.items() if k in _PIPELINE_COLUMNS}
        if not safe_updates:
            return existing

        set_clause = ", ".join(f"{col} = ?" for col in safe_updates)
        values = [*list(safe_updates.values()), pipeline_id, project_id]

        try:
            await self._db.execute(
                f"UPDATE pipeline_configs SET {set_clause} WHERE id = ? AND project_id = ?",
                values,
            )
            await self._db.commit()
        except aiosqlite.IntegrityError as exc:
            raise ValueError(
                f"A pipeline named '{updates.get('name', '')}' already exists in this project."
            ) from exc

        return await self.get_pipeline(project_id, pipeline_id)

    # ── Delete ────────────────────────────────────────────────────────

    async def delete_pipeline(
        self,
        project_id: str,
        pipeline_id: str,
    ) -> bool:
        """Delete a pipeline configuration. Returns True if deleted."""
        cursor = await self._db.execute(
            "DELETE FROM pipeline_configs WHERE id = ? AND project_id = ?",
            (pipeline_id, project_id),
        )
        await self._db.commit()
        return cursor.rowcount > 0

    # ── Presets ───────────────────────────────────────────────────────

    async def seed_presets(
        self,
        project_id: str,
    ) -> dict:
        """Idempotently seed preset pipeline configurations for a project."""
        seeded: list[str] = []
        skipped: list[str] = []

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        for preset in _PRESET_DEFINITIONS:
            preset_id = preset["preset_id"]
            blocking = int(bool(preset.get("blocking", False)))
            # Check if already seeded
            cursor = await self._db.execute(
                "SELECT id FROM pipeline_configs WHERE preset_id = ? AND project_id = ?",
                (preset_id, project_id),
            )
            existing = await cursor.fetchone()
            if existing:
                skipped.append(preset_id)
                continue

            pipeline_id = str(uuid.uuid4())
            stages_json = json.dumps(preset["stages"])
            try:
                await self._db.execute(
                    """
                    INSERT INTO pipeline_configs
                        (id, project_id, name, description, stages, is_preset, preset_id, blocking, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                    """,
                    (
                        pipeline_id,
                        project_id,
                        preset["name"],
                        preset["description"],
                        stages_json,
                        preset_id,
                        blocking,
                        now,
                        now,
                    ),
                )
                seeded.append(preset_id)
            except aiosqlite.IntegrityError:
                skipped.append(preset_id)

        if seeded:
            await self._db.commit()

        return {"seeded": seeded, "skipped": skipped, "total": len(seeded) + len(skipped)}

    # ── Assignment ───────────────────────────────────────────────────

    async def get_assignment(
        self,
        project_id: str,
    ) -> ProjectPipelineAssignment:
        """Get the current pipeline assignment for a project."""
        cursor = await self._db.execute(
            """
            SELECT assigned_pipeline_id, pipeline_blocking_override
            FROM project_settings
            WHERE github_user_id = ? AND project_id = ?
            LIMIT 1
            """,
            (_CANONICAL_PROJECT_SETTINGS_USER, project_id),
        )
        row = await cursor.fetchone()
        if row:
            row_dict = dict(row)
            pipeline_id = row_dict.get("assigned_pipeline_id", "") or ""
            raw_override = row_dict.get("pipeline_blocking_override")
            blocking_override: bool | None = (
                bool(raw_override) if raw_override is not None else None
            )
        else:
            pipeline_id = ""
            blocking_override = None
        return ProjectPipelineAssignment(
            project_id=project_id,
            pipeline_id=pipeline_id,
            blocking_override=blocking_override,
        )

    async def set_assignment(
        self,
        project_id: str,
        pipeline_id: str,
    ) -> ProjectPipelineAssignment:
        """Set the pipeline assignment for a project.

        Raises ValueError if pipeline_id is non-empty and doesn't exist.
        Preserves any existing project-level blocking_override.
        """
        if pipeline_id:
            existing = await self.get_pipeline(project_id, pipeline_id)
            if existing is None:
                raise ValueError(f"Pipeline '{pipeline_id}' not found in this project.")

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        await self._db.execute(
            """
            INSERT INTO project_settings (github_user_id, project_id, updated_at, assigned_pipeline_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(github_user_id, project_id) DO UPDATE SET
                assigned_pipeline_id = excluded.assigned_pipeline_id,
                updated_at = excluded.updated_at
            """,
            (_CANONICAL_PROJECT_SETTINGS_USER, project_id, now, pipeline_id),
        )
        await self._db.commit()

        return await self.get_assignment(project_id)

    async def set_blocking_override(
        self,
        project_id: str,
        blocking_override: bool | None,
    ) -> ProjectPipelineAssignment:
        """Set the project-level blocking override for the assigned pipeline.

        None   = inherit blocking behaviour from the assigned pipeline (no override).
        True   = force blocking ON for all issues in this project.
        False  = force blocking OFF for all issues in this project.
        """
        raw: int | None = int(blocking_override) if blocking_override is not None else None
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        await self._db.execute(
            """
            INSERT INTO project_settings (github_user_id, project_id, updated_at, pipeline_blocking_override)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(github_user_id, project_id) DO UPDATE SET
                pipeline_blocking_override = excluded.pipeline_blocking_override,
                updated_at = excluded.updated_at
            """,
            (_CANONICAL_PROJECT_SETTINGS_USER, project_id, now, raw),
        )
        await self._db.commit()

        return await self.get_assignment(project_id)
