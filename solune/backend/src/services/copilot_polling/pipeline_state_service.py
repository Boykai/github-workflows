"""Pipeline state persistence service (FR-001, FR-002, FR-003).

Provides durable SQLite-backed storage for pipeline runs and stage
states.  Replaces in-memory-only tracking with write-through persistence
so pipeline state survives application restarts.
"""

from __future__ import annotations

import asyncio
import json

import aiosqlite

from src.logging_utils import get_logger
from src.models.pipeline_events import PipelineRunStateChanged, PipelineStageStateChanged
from src.models.pipeline_run import (
    PipelineRun,
    PipelineRunListResponse,
    PipelineRunStageState,
    PipelineRunStageSummary,
    PipelineRunSummary,
)
from src.models.stage_group import StageGroup, StageGroupListResponse
from src.utils import utcnow

logger = get_logger(__name__)

_VALID_RUN_STATUSES = frozenset({"pending", "running", "completed", "failed", "cancelled"})
_VALID_STAGE_STATUSES = frozenset({"pending", "running", "completed", "failed", "skipped"})


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return utcnow().isoformat()


class PipelineRunService:
    """Service for persisting pipeline runs to SQLite via aiosqlite."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db
        self._lock = asyncio.Lock()

    # ── Pipeline Run CRUD ───────────────────────────────────────

    async def create_run(
        self,
        pipeline_config_id: str,
        project_id: str,
        trigger: str = "manual",
        stages: list[dict] | None = None,
    ) -> PipelineRun:
        """Create a new pipeline run with initial stage states.

        Uses a transaction to ensure atomicity of the run + stages insert.
        """
        now = _now_iso()
        async with self._lock:
            try:
                cursor = await self._db.execute(
                    """
                    INSERT INTO pipeline_runs
                        (pipeline_config_id, project_id, status, started_at, trigger)
                    VALUES (?, ?, 'pending', ?, ?)
                    """,
                    (pipeline_config_id, project_id, now, trigger),
                )
                run_id = cursor.lastrowid
                if run_id is None:
                    raise RuntimeError("Failed to persist pipeline run ID")

                # Create stage states if stages are provided
                stage_states: list[PipelineRunStageState] = []
                if stages:
                    for stage in stages:
                        stage_cursor = await self._db.execute(
                            """
                            INSERT INTO pipeline_stage_states
                                (pipeline_run_id, stage_id, group_id, status)
                            VALUES (?, ?, ?, 'pending')
                            """,
                            (run_id, stage["stage_id"], stage.get("group_id")),
                        )
                        stage_state_id = stage_cursor.lastrowid
                        if stage_state_id is None:
                            raise RuntimeError("Failed to persist pipeline stage state ID")
                        stage_states.append(
                            PipelineRunStageState(
                                id=stage_state_id,
                                stage_id=stage["stage_id"],
                                group_id=stage.get("group_id"),
                                status="pending",
                            )
                        )

                await self._db.commit()

                return PipelineRun(
                    id=run_id,
                    pipeline_config_id=pipeline_config_id,
                    project_id=project_id,
                    status="pending",
                    started_at=now,
                    completed_at=None,
                    trigger=trigger,
                    stages=stage_states,
                    created_at=now,
                    updated_at=now,
                )
            except Exception:
                await self._db.rollback()
                raise

    async def get_run(self, run_id: int) -> PipelineRun | None:
        """Get a pipeline run by ID with all stage states."""
        cursor = await self._db.execute(
            "SELECT * FROM pipeline_runs WHERE id = ?",
            (run_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None

        stages = await self._get_run_stages(run_id)
        return self._row_to_run(row, stages)

    async def list_runs(
        self,
        pipeline_config_id: str,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PipelineRunListResponse:
        """List pipeline runs with pagination and optional status filter.

        No artificial cap on results (FR-003).
        """
        conditions = ["pipeline_config_id = ?"]
        params: list[str | int] = [pipeline_config_id]

        if status:
            conditions.append("status = ?")
            params.append(status)

        where = " AND ".join(conditions)

        # Get total count
        count_cursor = await self._db.execute(
            f"SELECT COUNT(*) FROM pipeline_runs WHERE {where}",
            params,
        )
        count_row = await count_cursor.fetchone()
        total = count_row[0] if count_row else 0

        # Get paginated results
        query_params: list[str | int] = [*params, limit, offset]
        cursor = await self._db.execute(
            f"""
            SELECT * FROM pipeline_runs
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            query_params,
        )
        rows = await cursor.fetchall()

        runs: list[PipelineRunSummary] = []
        for row in rows:
            run_id_val: int = row["id"]
            summary = await self._get_stage_summary(run_id_val)
            runs.append(
                PipelineRunSummary(
                    id=run_id_val,
                    pipeline_config_id=row["pipeline_config_id"],
                    status=row["status"],
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                    trigger=row["trigger"],
                    stage_summary=summary,
                )
            )

        return PipelineRunListResponse(
            runs=runs,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update_run_status(
        self,
        run_id: int,
        new_status: str,
        *,
        error_message: str | None = None,
    ) -> PipelineRunStateChanged | None:
        """Update a pipeline run's status and return the state change event.

        Uses transactional writes for concurrent safety (edge case #2).
        """
        if new_status not in _VALID_RUN_STATUSES:
            msg = f"Invalid run status '{new_status}'. Must be one of: {', '.join(sorted(_VALID_RUN_STATUSES))}"
            raise ValueError(msg)

        async with self._lock:
            cursor = await self._db.execute(
                "SELECT status, pipeline_config_id, project_id FROM pipeline_runs WHERE id = ?",
                (run_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None

            previous_status = row["status"]
            if previous_status == new_status:
                return None

            now = _now_iso()
            terminal_statuses = {"completed", "failed", "cancelled"}
            completed_at = now if new_status in terminal_statuses else None

            try:
                await self._db.execute(
                    """
                    UPDATE pipeline_runs
                    SET status = ?, completed_at = ?, error_message = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (new_status, completed_at, error_message, now, run_id),
                )
                await self._db.commit()
            except Exception:
                await self._db.rollback()
                raise

            return PipelineRunStateChanged(
                run_id=run_id,
                pipeline_config_id=row["pipeline_config_id"],
                project_id=row["project_id"],
                previous_status=previous_status,
                new_status=new_status,
                timestamp=now,
                error_message=error_message,
            )

    async def cancel_run(self, run_id: int) -> PipelineRunStateChanged | None:
        """Cancel a running or pending pipeline run."""
        return await self.update_run_status(run_id, "cancelled")

    # ── Stage State Operations ──────────────────────────────────

    async def update_stage_status(
        self,
        stage_state_id: int,
        new_status: str,
        *,
        agent_id: str | None = None,
        error_message: str | None = None,
        label_name: str | None = None,
    ) -> PipelineStageStateChanged | None:
        """Update a stage's status and return the state change event."""
        if new_status not in _VALID_STAGE_STATUSES:
            msg = f"Invalid stage status '{new_status}'. Must be one of: {', '.join(sorted(_VALID_STAGE_STATUSES))}"
            raise ValueError(msg)

        async with self._lock:
            cursor = await self._db.execute(
                """
                SELECT id, pipeline_run_id, stage_id, group_id, status
                FROM pipeline_stage_states
                WHERE id = ?
                """,
                (stage_state_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None

            previous_status = row["status"]
            if previous_status == new_status:
                return None

            now = _now_iso()
            started_at = now if new_status == "running" and previous_status == "pending" else None
            completed_at = now if new_status in {"completed", "failed", "skipped"} else None

            # Clear timestamps when resetting to pending (e.g. during recovery)
            clear_started = new_status == "pending"
            clear_completed = new_status in {"pending", "running"}

            try:
                await self._db.execute(
                    """
                    UPDATE pipeline_stage_states
                    SET status = ?,
                        started_at = CASE WHEN ? THEN NULL ELSE COALESCE(?, started_at) END,
                        completed_at = CASE WHEN ? THEN NULL ELSE COALESCE(?, completed_at) END,
                        agent_id = COALESCE(?, agent_id),
                        error_message = ?,
                        label_name = COALESCE(?, label_name),
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        new_status,
                        clear_started,
                        started_at,
                        clear_completed,
                        completed_at,
                        agent_id,
                        error_message,
                        label_name,
                        now,
                        stage_state_id,
                    ),
                )
                await self._db.commit()
            except Exception:
                await self._db.rollback()
                raise

            # Use stored agent_id if the argument is None so the event
            # accurately reflects the persisted value.
            effective_agent_id = (
                agent_id
                if agent_id is not None
                else row["agent_id"]
                if "agent_id" in row.keys()
                else None
            )

            return PipelineStageStateChanged(
                stage_state_id=stage_state_id,
                pipeline_run_id=row["pipeline_run_id"],
                stage_id=row["stage_id"],
                group_id=row["group_id"],
                previous_status=previous_status,
                new_status=new_status,
                agent_id=effective_agent_id,
                timestamp=now,
            )

    # ── Stage Groups ────────────────────────────────────────────

    async def list_groups(self, pipeline_config_id: str) -> StageGroupListResponse:
        """List all stage groups for a pipeline configuration."""
        cursor = await self._db.execute(
            """
            SELECT * FROM stage_groups
            WHERE pipeline_config_id = ?
            ORDER BY order_index
            """,
            (pipeline_config_id,),
        )
        rows = await cursor.fetchall()
        groups = [self._row_to_group(row) for row in rows]
        return StageGroupListResponse(groups=groups, total=len(groups))

    async def upsert_groups(
        self,
        pipeline_config_id: str,
        groups: list[dict],
    ) -> StageGroupListResponse:
        """Create or update stage groups atomically.

        Replaces all existing groups for the pipeline config.
        """
        async with self._lock:
            try:
                await self._db.execute(
                    "DELETE FROM stage_groups WHERE pipeline_config_id = ?",
                    (pipeline_config_id,),
                )
                created_groups: list[StageGroup] = []
                for group in groups:
                    cursor = await self._db.execute(
                        """
                        INSERT INTO stage_groups
                            (pipeline_config_id, name, execution_mode, order_index)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            pipeline_config_id,
                            group["name"],
                            group.get("execution_mode", "sequential"),
                            group["order_index"],
                        ),
                    )
                    group_id = cursor.lastrowid
                    if group_id is None:
                        raise RuntimeError("Failed to persist pipeline stage group ID")
                    now = _now_iso()
                    created_groups.append(
                        StageGroup(
                            id=group_id,
                            pipeline_config_id=pipeline_config_id,
                            name=group["name"],
                            execution_mode=group.get("execution_mode", "sequential"),
                            order_index=group["order_index"],
                            created_at=now,
                            updated_at=now,
                        )
                    )
                await self._db.commit()
                return StageGroupListResponse(groups=created_groups, total=len(created_groups))
            except Exception:
                await self._db.rollback()
                raise

    # ── Startup Recovery ────────────────────────────────────────

    async def rebuild_active_runs(self) -> list[PipelineRun]:
        """Query incomplete runs from DB and return them for in-memory reconstruction.

        Called during startup to restore the working set (FR-002).
        """
        cursor = await self._db.execute(
            """
            SELECT * FROM pipeline_runs
            WHERE status IN ('pending', 'running')
            ORDER BY created_at ASC
            """,
        )
        rows = await cursor.fetchall()
        runs: list[PipelineRun] = []
        for row in rows:
            stages = await self._get_run_stages(row["id"])
            runs.append(self._row_to_run(row, stages))
        logger.info("Rebuilt %d active pipeline runs from database", len(runs))
        return runs

    async def check_integrity(self) -> bool:
        """Run SQLite PRAGMA integrity_check on startup (edge case #1).

        Returns True if the database passes integrity checks.
        Falls back gracefully with a warning if integrity check fails.
        """
        try:
            cursor = await self._db.execute("PRAGMA integrity_check")
            result = await cursor.fetchone()
            if result and result[0] == "ok":
                logger.info("Database integrity check passed")
                return True
            logger.warning("Database integrity check returned: %s", result)
            return False
        except Exception:
            logger.exception("Database integrity check failed")
            return False

    # ── Private Helpers ─────────────────────────────────────────

    async def _get_run_stages(self, run_id: int) -> list[PipelineRunStageState]:
        """Get all stage states for a pipeline run."""
        cursor = await self._db.execute(
            "SELECT * FROM pipeline_stage_states WHERE pipeline_run_id = ? ORDER BY id",
            (run_id,),
        )
        rows = await cursor.fetchall()
        return [
            PipelineRunStageState(
                id=row["id"],
                stage_id=row["stage_id"],
                group_id=row["group_id"],
                status=row["status"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                agent_id=row["agent_id"],
                label_name=row["label_name"],
                error_message=row["error_message"],
            )
            for row in rows
        ]

    async def _get_stage_summary(self, run_id: int) -> PipelineRunStageSummary:
        """Get aggregated stage counts for a pipeline run."""
        cursor = await self._db.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped
            FROM pipeline_stage_states
            WHERE pipeline_run_id = ?
            """,
            (run_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return PipelineRunStageSummary()
        return PipelineRunStageSummary(
            total=row["total"] or 0,
            completed=row["completed"] or 0,
            failed=row["failed"] or 0,
            running=row["running"] or 0,
            pending=row["pending"] or 0,
            skipped=row["skipped"] or 0,
        )

    @staticmethod
    def _row_to_run(
        row: aiosqlite.Row,
        stages: list[PipelineRunStageState],
    ) -> PipelineRun:
        """Convert a database row + stages to a PipelineRun model."""
        metadata_raw = row["metadata"]
        metadata = json.loads(metadata_raw) if metadata_raw else None
        return PipelineRun(
            id=row["id"],
            pipeline_config_id=row["pipeline_config_id"],
            project_id=row["project_id"],
            status=row["status"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            trigger=row["trigger"],
            error_message=row["error_message"],
            metadata=metadata,
            stages=stages,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_group(row: aiosqlite.Row) -> StageGroup:
        """Convert a database row to a StageGroup model."""
        return StageGroup(
            id=row["id"],
            pipeline_config_id=row["pipeline_config_id"],
            name=row["name"],
            execution_mode=row["execution_mode"],
            order_index=row["order_index"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
