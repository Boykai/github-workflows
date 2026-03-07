"""PipelineService — CRUD operations for Agent Pipeline configurations."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime

import aiosqlite

from src.models.pipeline import (
    AIModel,
    PipelineConfig,
    PipelineConfigCreate,
    PipelineConfigListResponse,
    PipelineConfigSummary,
    PipelineConfigUpdate,
    PipelineStage,
)

logger = logging.getLogger(__name__)

# Column allowlist for dynamic SET clauses
_PIPELINE_COLUMNS = frozenset({"name", "description", "stages", "updated_at"})

# Static list of available AI models
_AVAILABLE_MODELS: list[AIModel] = [
    AIModel(
        id="gpt-4o",
        name="GPT-4o",
        provider="OpenAI",
        context_window_size=128_000,
        cost_tier="premium",
        capability_category="general",
    ),
    AIModel(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider="OpenAI",
        context_window_size=128_000,
        cost_tier="economy",
        capability_category="general",
    ),
    AIModel(
        id="claude-sonnet-4",
        name="Claude Sonnet 4",
        provider="Anthropic",
        context_window_size=200_000,
        cost_tier="premium",
        capability_category="coding",
    ),
    AIModel(
        id="claude-haiku-3.5",
        name="Claude 3.5 Haiku",
        provider="Anthropic",
        context_window_size=200_000,
        cost_tier="economy",
        capability_category="general",
    ),
    AIModel(
        id="gemini-2.5-pro",
        name="Gemini 2.5 Pro",
        provider="Google",
        context_window_size=1_000_000,
        cost_tier="premium",
        capability_category="general",
    ),
    AIModel(
        id="gemini-2.5-flash",
        name="Gemini 2.5 Flash",
        provider="Google",
        context_window_size=1_000_000,
        cost_tier="standard",
        capability_category="general",
    ),
]


class PipelineService:
    """Manages pipeline configuration records in the SQLite database."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    # ── List ──────────────────────────────────────────────────────────

    async def list_pipelines(
        self,
        project_id: str,
        sort: str = "updated_at",
        order: str = "desc",
    ) -> PipelineConfigListResponse:
        """List all pipeline configurations for a project."""
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
            summaries.append(
                PipelineConfigSummary(
                    id=row_dict["id"],
                    name=row_dict["name"],
                    description=row_dict.get("description", ""),
                    stage_count=len(parsed_stages),
                    agent_count=agent_count,
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
        stages_json = json.dumps([s.model_dump() for s in body.stages])

        try:
            await self._db.execute(
                """
                INSERT INTO pipeline_configs (id, project_id, name, description, stages, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (pipeline_id, project_id, body.name, body.description, stages_json, now, now),
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
        """
        existing = await self.get_pipeline(project_id, pipeline_id)
        if existing is None:
            return None

        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return existing

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        updates["updated_at"] = now

        if "stages" in updates and updates["stages"] is not None:
            updates["stages"] = json.dumps(
                [s.model_dump() if hasattr(s, "model_dump") else s for s in updates["stages"]]
            )

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

    # ── Models ────────────────────────────────────────────────────────

    @staticmethod
    def list_models() -> list[AIModel]:
        """Return the static list of available AI models."""
        return list(_AVAILABLE_MODELS)

    # ── Helpers ───────────────────────────────────────────────────────

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
            created_at=row_dict["created_at"],
            updated_at=row_dict["updated_at"],
        )
