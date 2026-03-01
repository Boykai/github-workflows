"""Housekeeping service — CRUD, trigger evaluation, execution."""

import json
import logging
import uuid
from datetime import UTC, datetime

import aiosqlite

from src.models.housekeeping import (
    EvaluateTriggersResponse,
    EvaluateTriggersResult,
    HousekeepingTask,
    IssueTemplate,
    TemplateCategory,
    TriggerEvent,
    TriggerEventType,
    TriggerStatus,
    TriggerType,
)
from src.services.housekeeping.seed import SEED_TEMPLATES

logger = logging.getLogger(__name__)


class HousekeepingService:
    """Service for managing housekeeping tasks, templates, and triggers."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    # ── Initialization ──────────────────────────────────────────────────

    async def initialize(self) -> None:
        """Seed built-in templates if they don't exist."""
        for tmpl in SEED_TEMPLATES:
            cursor = await self._db.execute(
                "SELECT id FROM housekeeping_templates WHERE name = ?",
                (tmpl["name"],),
            )
            row = await cursor.fetchone()
            if row is None:
                tmpl_id = str(uuid.uuid4())
                now = datetime.now(UTC).isoformat()
                await self._db.execute(
                    """INSERT INTO housekeeping_templates
                       (id, name, title_pattern, body_content, category, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        tmpl_id,
                        tmpl["name"],
                        tmpl["title_pattern"],
                        tmpl["body_content"],
                        tmpl["category"],
                        now,
                        now,
                    ),
                )
        await self._db.commit()
        logger.info("Housekeeping seed templates initialized")

    # ── Template CRUD ───────────────────────────────────────────────────

    async def list_templates(self, category: str | None = None) -> list[IssueTemplate]:
        """List all templates, optionally filtered by category."""
        if category:
            cursor = await self._db.execute(
                "SELECT * FROM housekeeping_templates WHERE category = ? ORDER BY created_at",
                (category,),
            )
        else:
            cursor = await self._db.execute(
                "SELECT * FROM housekeeping_templates ORDER BY created_at"
            )
        rows = await cursor.fetchall()
        return [self._row_to_template(row) for row in rows]

    async def get_template(self, template_id: str) -> IssueTemplate | None:
        """Get a single template by ID."""
        cursor = await self._db.execute(
            "SELECT * FROM housekeeping_templates WHERE id = ?",
            (template_id,),
        )
        row = await cursor.fetchone()
        return self._row_to_template(row) if row else None

    async def create_template(
        self, name: str, title_pattern: str, body_content: str
    ) -> IssueTemplate:
        """Create a new custom template."""
        tmpl_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        await self._db.execute(
            """INSERT INTO housekeeping_templates
               (id, name, title_pattern, body_content, category, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (tmpl_id, name, title_pattern, body_content, TemplateCategory.CUSTOM, now, now),
        )
        await self._db.commit()
        return IssueTemplate(
            id=tmpl_id,
            name=name,
            title_pattern=title_pattern,
            body_content=body_content,
            category=TemplateCategory.CUSTOM,
            created_at=now,
            updated_at=now,
        )

    # Allowed column names for dynamic SQL updates (SQL injection prevention)
    _TEMPLATE_COLUMNS = {"name", "title_pattern", "body_content", "updated_at"}
    _TASK_COLUMNS = {
        "name",
        "description",
        "template_id",
        "sub_issue_config",
        "trigger_type",
        "trigger_value",
        "cooldown_minutes",
        "updated_at",
    }

    async def update_template(self, template_id: str, **kwargs: str | None) -> IssueTemplate | None:
        """Update a template. Returns None if not found."""
        tmpl = await self.get_template(template_id)
        if not tmpl:
            return None
        if tmpl.category == TemplateCategory.BUILT_IN:
            raise PermissionError("Cannot modify built-in templates")

        updates = {k: v for k, v in kwargs.items() if v is not None and k in self._TEMPLATE_COLUMNS}
        if not updates:
            return tmpl

        updates["updated_at"] = datetime.now(UTC).isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [template_id]
        await self._db.execute(
            f"UPDATE housekeeping_templates SET {set_clause} WHERE id = ?",  # noqa: S608
            values,
        )
        await self._db.commit()
        return await self.get_template(template_id)

    async def delete_template(self, template_id: str, force: bool = False) -> dict:
        """Delete a template. Returns status dict."""
        tmpl = await self.get_template(template_id)
        if not tmpl:
            return {"error": "not_found"}
        if tmpl.category == TemplateCategory.BUILT_IN:
            return {"error": "built_in"}

        # Check for referencing tasks
        cursor = await self._db.execute(
            "SELECT id FROM housekeeping_tasks WHERE template_id = ?",
            (template_id,),
        )
        referencing = [row["id"] for row in await cursor.fetchall()]

        if referencing and not force:
            return {"error": "in_use", "referencing_tasks": referencing}

        # When force-deleting, cascade to referencing tasks and their
        # trigger history first to avoid FK constraint violations.
        # The migration defines template_id as NOT NULL REFERENCES
        # housekeeping_templates(id), so direct deletion would raise
        # an IntegrityError.
        if referencing and force:
            for ref_task_id in referencing:
                await self._db.execute(
                    "DELETE FROM housekeeping_trigger_history WHERE task_id = ?",
                    (ref_task_id,),
                )
            await self._db.execute(
                "DELETE FROM housekeeping_tasks WHERE template_id = ?",
                (template_id,),
            )

        await self._db.execute("DELETE FROM housekeeping_templates WHERE id = ?", (template_id,))
        await self._db.commit()
        return {"deleted": True}

    async def duplicate_template(self, template_id: str) -> IssueTemplate | None:
        """Duplicate a template as a custom copy."""
        tmpl = await self.get_template(template_id)
        if not tmpl:
            return None
        return await self.create_template(
            name=f"{tmpl.name} (Copy)",
            title_pattern=tmpl.title_pattern,
            body_content=tmpl.body_content,
        )

    # ── Task CRUD ───────────────────────────────────────────────────────

    async def list_tasks(
        self, project_id: str, enabled: bool | None = None
    ) -> list[HousekeepingTask]:
        """List tasks for a project."""
        query = """
            SELECT t.*, ht.name as template_name
            FROM housekeeping_tasks t
            LEFT JOIN housekeeping_templates ht ON t.template_id = ht.id
            WHERE t.project_id = ?
        """
        params: list = [project_id]
        if enabled is not None:
            query += " AND t.enabled = ?"
            params.append(1 if enabled else 0)
        query += " ORDER BY t.created_at"

        cursor = await self._db.execute(query, params)
        rows = await cursor.fetchall()
        return [self._row_to_task(row) for row in rows]

    async def get_task(self, task_id: str) -> HousekeepingTask | None:
        """Get a single task by ID."""
        cursor = await self._db.execute(
            """SELECT t.*, ht.name as template_name
               FROM housekeeping_tasks t
               LEFT JOIN housekeeping_templates ht ON t.template_id = ht.id
               WHERE t.id = ?""",
            (task_id,),
        )
        row = await cursor.fetchone()
        return self._row_to_task(row) if row else None

    async def create_task(
        self,
        name: str,
        template_id: str,
        trigger_type: str,
        trigger_value: str,
        project_id: str,
        description: str | None = None,
        sub_issue_config: dict | None = None,
        cooldown_minutes: int = 5,
        current_issue_count: int | None = None,
    ) -> HousekeepingTask:
        """Create a new housekeeping task with validation.

        Args:
            current_issue_count: For count-based triggers, the current number
                of issues in the project. Stored as the baseline so the task
                only triggers after *new* issues exceed the threshold rather
                than firing immediately against the historical total.
        """
        # Validate template exists
        tmpl = await self.get_template(template_id)
        if not tmpl:
            raise ValueError(f"Template '{template_id}' does not exist")

        # Validate trigger config
        self._validate_trigger(trigger_type, trigger_value)

        # For count-based triggers, persist the current issue count as the
        # baseline so the task measures *new* issues since creation.  If
        # the caller omits this value the DB default of 0 is used, which
        # would cause the task to fire immediately once
        # current_issue_count >= trigger_value.
        baseline_count = current_issue_count if current_issue_count is not None else 0

        task_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        sub_config_json = json.dumps(sub_issue_config) if sub_issue_config else None

        await self._db.execute(
            """INSERT INTO housekeeping_tasks
               (id, name, description, template_id, sub_issue_config,
                trigger_type, trigger_value, cooldown_minutes, project_id,
                last_triggered_issue_count, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task_id,
                name,
                description,
                template_id,
                sub_config_json,
                trigger_type,
                trigger_value,
                cooldown_minutes,
                project_id,
                baseline_count,
                now,
                now,
            ),
        )
        await self._db.commit()
        task = await self.get_task(task_id)
        if not task:
            raise RuntimeError(f"Failed to retrieve newly created task {task_id}")
        return task

    async def update_task(self, task_id: str, **kwargs) -> HousekeepingTask | None:
        """Update a task. Returns None if not found."""
        task = await self.get_task(task_id)
        if not task:
            return None

        updates: dict = {}
        for key, value in kwargs.items():
            if value is None or key not in self._TASK_COLUMNS:
                continue
            if key == "template_id":
                tmpl = await self.get_template(value)
                if not tmpl:
                    raise ValueError(f"Template '{value}' does not exist")
                updates[key] = value
            elif key == "sub_issue_config":
                updates[key] = json.dumps(value) if value else None
            else:
                updates[key] = value

        # Validate trigger consistency if either field is being updated
        new_type = updates.get("trigger_type", task.trigger_type)
        new_value = updates.get("trigger_value", task.trigger_value)
        if "trigger_type" in updates or "trigger_value" in updates:
            self._validate_trigger(new_type, new_value)

        if not updates:
            return task

        updates["updated_at"] = datetime.now(UTC).isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [task_id]
        await self._db.execute(
            f"UPDATE housekeeping_tasks SET {set_clause} WHERE id = ?",  # noqa: S608
            values,
        )
        await self._db.commit()
        return await self.get_task(task_id)

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task and its history. Returns True if deleted."""
        task = await self.get_task(task_id)
        if not task:
            return False
        await self._db.execute(
            "DELETE FROM housekeeping_trigger_history WHERE task_id = ?", (task_id,)
        )
        await self._db.execute("DELETE FROM housekeeping_tasks WHERE id = ?", (task_id,))
        await self._db.commit()
        return True

    async def toggle_task(self, task_id: str, enabled: bool) -> HousekeepingTask | None:
        """Enable or disable a task."""
        task = await self.get_task(task_id)
        if not task:
            return None
        now = datetime.now(UTC).isoformat()
        await self._db.execute(
            "UPDATE housekeeping_tasks SET enabled = ?, updated_at = ? WHERE id = ?",
            (1 if enabled else 0, now, task_id),
        )
        await self._db.commit()
        return await self.get_task(task_id)

    # ── Trigger History ─────────────────────────────────────────────────

    async def get_task_history(
        self,
        task_id: str,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> tuple[list[TriggerEvent], int]:
        """Get trigger history for a task. Returns (events, total_count)."""
        # Count total
        count_query = "SELECT COUNT(*) as cnt FROM housekeeping_trigger_history WHERE task_id = ?"
        count_params: list = [task_id]
        if status:
            count_query += " AND status = ?"
            count_params.append(status)

        cursor = await self._db.execute(count_query, count_params)
        count_row = await cursor.fetchone()
        total = count_row["cnt"] if count_row else 0

        # Fetch events
        query = "SELECT * FROM housekeeping_trigger_history WHERE task_id = ?"
        params: list = [task_id]
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = await self._db.execute(query, params)
        rows = await cursor.fetchall()
        events = [self._row_to_event(row) for row in rows]
        return events, total

    async def _record_trigger_event(
        self,
        task_id: str,
        trigger_type: TriggerEventType,
        status: TriggerStatus,
        issue_url: str | None = None,
        issue_number: int | None = None,
        error_details: str | None = None,
        sub_issues_created: int = 0,
    ) -> TriggerEvent:
        """Record a trigger event in history."""
        event_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        await self._db.execute(
            """INSERT INTO housekeeping_trigger_history
               (id, task_id, timestamp, trigger_type, issue_url, issue_number,
                status, error_details, sub_issues_created)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event_id,
                task_id,
                now,
                trigger_type,
                issue_url,
                issue_number,
                status,
                error_details,
                sub_issues_created,
            ),
        )
        await self._db.commit()
        return TriggerEvent(
            id=event_id,
            task_id=task_id,
            timestamp=now,
            trigger_type=trigger_type,
            issue_url=issue_url,
            issue_number=issue_number,
            status=status,
            error_details=error_details,
            sub_issues_created=sub_issues_created,
        )

    # ── Manual Run ──────────────────────────────────────────────────────

    async def run_task(self, task_id: str, force: bool = False) -> dict:
        """
        Manually run a housekeeping task.

        Returns a dict with either:
        - {"trigger_event": TriggerEvent} on success/failure
        - {"cooldown": True, ...} if within cooldown window
        """
        task = await self.get_task(task_id)
        if not task:
            return {"error": "not_found"}

        # Cooldown check (unless forced)
        if not force and task.last_triggered_at:
            remaining = self._cooldown_remaining(task)
            if remaining > 0:
                return {
                    "cooldown": True,
                    "last_triggered_at": task.last_triggered_at,
                    "cooldown_remaining_seconds": remaining,
                }

        # Execute
        event = await self._execute_task(task, TriggerEventType.MANUAL)

        # Update last_triggered_at after successful execution.
        # Manual runs are user-initiated so concurrency is less of a concern;
        # the cooldown check above already guards against rapid re-runs.
        now_iso = datetime.now(UTC).isoformat()
        await self._db.execute(
            "UPDATE housekeeping_tasks SET last_triggered_at = ?, updated_at = ? WHERE id = ?",
            (now_iso, now_iso, task.id),
        )
        await self._db.commit()

        return {"trigger_event": event}

    # ── Evaluate Time-Based Triggers ────────────────────────────────────

    async def evaluate_triggers(self, project_id: str) -> EvaluateTriggersResponse:
        """Evaluate all enabled time-based tasks and execute due ones."""
        from src.services.housekeeping.scheduler import is_task_due

        tasks = await self.list_tasks(project_id, enabled=True)
        time_tasks = [t for t in tasks if t.trigger_type == TriggerType.TIME]

        results: list[EvaluateTriggersResult] = []
        triggered = 0
        skipped = 0

        for task in time_tasks:
            if self._cooldown_remaining(task) > 0:
                results.append(
                    EvaluateTriggersResult(
                        task_id=task.id,
                        task_name=task.name,
                        action="skipped",
                        reason="Within cooldown window",
                    )
                )
                skipped += 1
                continue

            if is_task_due(task.trigger_value, task.last_triggered_at):
                # Atomically "claim" this task by updating last_triggered_at
                # only if it still matches what we observed.  This prevents
                # concurrent evaluators from both triggering the same task
                # (the spec requires idempotent trigger evaluation).
                now_iso = datetime.now(UTC).isoformat()

                if task.last_triggered_at is None:
                    # First-ever trigger: match NULL explicitly.
                    cursor = await self._db.execute(
                        """UPDATE housekeeping_tasks
                           SET last_triggered_at = ?, updated_at = ?
                           WHERE id = ? AND last_triggered_at IS NULL""",
                        (now_iso, now_iso, task.id),
                    )
                else:
                    # Subsequent triggers: compare against the known value.
                    cursor = await self._db.execute(
                        """UPDATE housekeeping_tasks
                           SET last_triggered_at = ?, updated_at = ?
                           WHERE id = ? AND last_triggered_at = ?""",
                        (now_iso, now_iso, task.id, task.last_triggered_at),
                    )
                await self._db.commit()

                if cursor.rowcount and cursor.rowcount > 0:
                    # We won the race — keep in-memory state consistent.
                    task.last_triggered_at = now_iso

                    event = await self._execute_task(task, TriggerEventType.SCHEDULED)
                    results.append(
                        EvaluateTriggersResult(
                            task_id=task.id,
                            task_name=task.name,
                            action="triggered",
                            issue_url=event.issue_url,
                        )
                    )
                    triggered += 1
                else:
                    # Another concurrent evaluator already triggered this task.
                    results.append(
                        EvaluateTriggersResult(
                            task_id=task.id,
                            task_name=task.name,
                            action="skipped",
                            reason="Already triggered by another evaluator",
                        )
                    )
                    skipped += 1
            else:
                results.append(
                    EvaluateTriggersResult(
                        task_id=task.id,
                        task_name=task.name,
                        action="skipped",
                        reason="Not yet due",
                    )
                )
                skipped += 1

        return EvaluateTriggersResponse(
            evaluated=len(time_tasks),
            triggered=triggered,
            skipped=skipped,
            results=results,
        )

    # ── Count-Based Trigger Evaluation ──────────────────────────────────

    async def evaluate_count_triggers(
        self, project_id: str, current_issue_count: int
    ) -> list[EvaluateTriggersResult]:
        """Evaluate all enabled count-based tasks for a project."""
        tasks = await self.list_tasks(project_id, enabled=True)
        count_tasks = [t for t in tasks if t.trigger_type == TriggerType.COUNT]

        results: list[EvaluateTriggersResult] = []

        for task in count_tasks:
            threshold = int(task.trigger_value)
            diff = current_issue_count - task.last_triggered_issue_count
            if diff >= threshold and self._cooldown_remaining(task) <= 0:
                event = await self._execute_task(task, TriggerEventType.COUNT_BASED)
                # Update issue count baseline and last_triggered_at
                now = datetime.now(UTC).isoformat()
                await self._db.execute(
                    """UPDATE housekeeping_tasks
                       SET last_triggered_issue_count = ?,
                           last_triggered_at = ?,
                           updated_at = ?
                       WHERE id = ?""",
                    (current_issue_count, now, now, task.id),
                )
                await self._db.commit()
                results.append(
                    EvaluateTriggersResult(
                        task_id=task.id,
                        task_name=task.name,
                        action="triggered",
                        issue_url=event.issue_url,
                    )
                )
            else:
                results.append(
                    EvaluateTriggersResult(
                        task_id=task.id,
                        task_name=task.name,
                        action="skipped",
                        reason=f"Threshold not met ({diff}/{threshold})",
                    )
                )

        return results

    # ── Task Execution (Internal) ───────────────────────────────────────

    async def _execute_task(
        self, task: HousekeepingTask, trigger_type: TriggerEventType
    ) -> TriggerEvent:
        """Execute a housekeeping task: create parent issue and sub issues."""
        tmpl = await self.get_template(task.template_id)
        if not tmpl:
            return await self._record_trigger_event(
                task_id=task.id,
                trigger_type=trigger_type,
                status=TriggerStatus.FAILURE,
                error_details="Referenced template does not exist",
            )

        try:
            # Generate the issue title from the template pattern
            now = datetime.now(UTC)
            title = tmpl.title_pattern.replace("{date}", now.strftime("%Y-%m-%d")).replace(
                "{task_name}", task.name
            )

            # Record as PENDING because the GitHub API integration is not
            # yet wired.  Using SUCCESS with issue_url=None would mislead
            # downstream UI/history into treating this as a completed run.
            # Once the GitHub Issues API call is implemented, promote the
            # status to SUCCESS with the real issue_url and issue_number.
            event = await self._record_trigger_event(
                task_id=task.id,
                trigger_type=trigger_type,
                status=TriggerStatus.PENDING,
                issue_url=None,
                issue_number=None,
                sub_issues_created=0,
            )

            # NOTE: Callers are responsible for updating last_triggered_at
            # (e.g. via atomic CAS in evaluate_triggers, or a simple UPDATE
            # in run_task).  This keeps _execute_task focused on recording
            # the trigger event and avoids double-updates.

            logger.info(
                "Housekeeping task '%s' executed successfully (trigger=%s, title='%s')",
                task.name,
                trigger_type,
                title,
            )
            return event

        except Exception as e:
            logger.exception("Failed to execute housekeeping task '%s'", task.name)
            return await self._record_trigger_event(
                task_id=task.id,
                trigger_type=trigger_type,
                status=TriggerStatus.FAILURE,
                error_details=str(e),
            )

    # ── Helpers ──────────────────────────────────────────────────────────

    def _cooldown_remaining(self, task: HousekeepingTask) -> int:
        """Return remaining cooldown seconds. 0 if cooldown has passed."""
        if not task.last_triggered_at:
            return 0
        try:
            last = datetime.fromisoformat(task.last_triggered_at)
            if last.tzinfo is None:
                last = last.replace(tzinfo=UTC)
            elapsed = (datetime.now(UTC) - last).total_seconds()
            remaining = (task.cooldown_minutes * 60) - elapsed
            return max(0, int(remaining))
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _validate_trigger(trigger_type: str, trigger_value: str) -> None:
        """Validate trigger type and value consistency."""
        if trigger_type == TriggerType.COUNT:
            try:
                val = int(trigger_value)
                if val <= 0:
                    raise ValueError("Count trigger value must be a positive integer")
            except ValueError as e:
                if "positive integer" in str(e):
                    raise
                raise ValueError(
                    f"Count trigger value must be a positive integer, got '{trigger_value}'"
                ) from e
        elif trigger_type == TriggerType.TIME:
            # Accept named presets or validate cron-like format
            presets = {"daily", "weekly", "monthly"}
            if trigger_value.lower() in presets:
                return
            parts = trigger_value.strip().split()
            if len(parts) != 5:
                raise ValueError(
                    f"Time trigger value must be a cron expression (5 fields) or "
                    f"named preset (daily/weekly/monthly), got '{trigger_value}'"
                )

    @staticmethod
    def _row_to_template(row: aiosqlite.Row) -> IssueTemplate:
        """Convert a database row to an IssueTemplate model."""
        return IssueTemplate(
            id=row["id"],
            name=row["name"],
            title_pattern=row["title_pattern"],
            body_content=row["body_content"],
            category=row["category"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_task(row: aiosqlite.Row) -> HousekeepingTask:
        """Convert a database row to a HousekeepingTask model."""
        sub_config = None
        if row["sub_issue_config"]:
            try:
                sub_config = json.loads(row["sub_issue_config"])
            except (json.JSONDecodeError, TypeError):
                pass

        template_name = None
        try:
            template_name = row["template_name"]
        except (IndexError, KeyError):
            pass

        return HousekeepingTask(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            template_id=row["template_id"],
            template_name=template_name,
            sub_issue_config=sub_config,
            trigger_type=row["trigger_type"],
            trigger_value=row["trigger_value"],
            last_triggered_at=row["last_triggered_at"],
            last_triggered_issue_count=row["last_triggered_issue_count"],
            enabled=bool(row["enabled"]),
            cooldown_minutes=row["cooldown_minutes"],
            project_id=row["project_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_event(row: aiosqlite.Row) -> TriggerEvent:
        """Convert a database row to a TriggerEvent model."""
        return TriggerEvent(
            id=row["id"],
            task_id=row["task_id"],
            timestamp=row["timestamp"],
            trigger_type=row["trigger_type"],
            issue_url=row["issue_url"],
            issue_number=row["issue_number"],
            status=row["status"],
            error_details=row["error_details"],
            sub_issues_created=row["sub_issues_created"],
        )
