"""ChoresService — CRUD operations for recurring maintenance chores."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import UTC, datetime

import aiosqlite

from src.models.chores import Chore, ChoreCreate, ChoreTriggerResult, ChoreUpdate

logger = logging.getLogger(__name__)


def _strip_front_matter(text: str) -> str:
    """Remove YAML front matter (``---\n...\n---``) from the beginning of text."""
    return re.sub(r"\A---\n.*?\n---\n?", "", text, count=1, flags=re.DOTALL).strip()


class ChoresService:
    """Manages chore records in the SQLite database."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    async def create_chore(
        self,
        project_id: str,
        body: ChoreCreate,
        *,
        template_path: str,
    ) -> Chore:
        """Create a new chore record.

        Args:
            project_id: GitHub Project node ID.
            body: Validated create payload (name + template_content).
            template_path: Path to the committed template file in the repo.

        Returns:
            The newly created Chore.

        Raises:
            ValueError: If a chore with the same name already exists in the project.
        """
        chore_id = str(uuid.uuid4())
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            await self._db.execute(
                """
                INSERT INTO chores (
                    id, project_id, name, template_path, template_content,
                    status, last_triggered_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'active', 0, ?, ?)
                """,
                (
                    chore_id,
                    project_id,
                    body.name,
                    template_path,
                    body.template_content,
                    now,
                    now,
                ),
            )
            await self._db.commit()
        except aiosqlite.IntegrityError as exc:
            raise ValueError(f"A chore named '{body.name}' already exists in this project") from exc

        chore = await self.get_chore(chore_id)
        if chore is None:
            raise ValueError(f"Failed to retrieve created chore {chore_id}")
        return chore

    async def list_chores(self, project_id: str) -> list[Chore]:
        """Return all chores for a given project, ordered by creation date."""
        cursor = await self._db.execute(
            "SELECT * FROM chores WHERE project_id = ? ORDER BY created_at ASC",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [Chore(**dict(row)) for row in rows]

    async def get_chore(self, chore_id: str) -> Chore | None:
        """Fetch a single chore by ID.  Returns None if not found."""
        cursor = await self._db.execute(
            "SELECT * FROM chores WHERE id = ?",
            (chore_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return Chore(**dict(row))

    async def update_chore(self, chore_id: str, body: ChoreUpdate) -> Chore | None:
        """Apply a partial update to a chore.

        Only fields present in `body` (non-None after exclude_unset) are written.

        Returns the updated Chore, or None if not found.
        """
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return await self.get_chore(chore_id)

        # Validate schedule consistency when both fields are part of update
        schedule_type = updates.get("schedule_type")
        schedule_value = updates.get("schedule_value")

        # If only one of the pair is set, fetch current to validate
        if ("schedule_type" in updates) != ("schedule_value" in updates):
            current = await self.get_chore(chore_id)
            if current is None:
                return None
            effective_type = updates.get("schedule_type", current.schedule_type)
            effective_value = updates.get("schedule_value", current.schedule_value)
            # Both must be set or both NULL
            if (effective_type is None) != (effective_value is None):
                raise ValueError(
                    "schedule_type and schedule_value must both be set or both be null"
                )
        elif schedule_type is not None and schedule_value is None:
            raise ValueError("schedule_type and schedule_value must both be set or both be null")
        elif schedule_type is None and schedule_value is not None:
            raise ValueError("schedule_type and schedule_value must both be set or both be null")

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        updates["updated_at"] = now

        set_clause = ", ".join(f"{col} = ?" for col in updates)
        values = list(updates.values()) + [chore_id]

        await self._db.execute(
            f"UPDATE chores SET {set_clause} WHERE id = ?",  # noqa: S608
            values,
        )
        await self._db.commit()
        return await self.get_chore(chore_id)

    async def delete_chore(self, chore_id: str) -> bool:
        """Delete a chore by ID.  Returns True if a row was deleted."""
        cursor = await self._db.execute(
            "DELETE FROM chores WHERE id = ?",
            (chore_id,),
        )
        await self._db.commit()
        return cursor.rowcount > 0

    # ── Helpers used by trigger evaluation (Phase 6) ──

    async def list_active_scheduled_chores(self) -> list[Chore]:
        """Return all active chores that have a schedule configured."""
        cursor = await self._db.execute(
            """
            SELECT * FROM chores
            WHERE status = 'active'
              AND schedule_type IS NOT NULL
              AND schedule_value IS NOT NULL
            ORDER BY created_at ASC
            """,
        )
        rows = await cursor.fetchall()
        return [Chore(**dict(row)) for row in rows]

    async def update_chore_after_trigger(
        self,
        chore_id: str,
        *,
        current_issue_number: int,
        current_issue_node_id: str,
        last_triggered_at: str,
        last_triggered_count: int,
        old_last_triggered_at: str | None,
    ) -> bool:
        """CAS-style update after triggering a chore.

        Uses WHERE last_triggered_at = old_value to prevent double-fire.
        Returns True if the update was applied.
        """
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        if old_last_triggered_at is None:
            cursor = await self._db.execute(
                """
                UPDATE chores
                SET current_issue_number = ?,
                    current_issue_node_id = ?,
                    last_triggered_at = ?,
                    last_triggered_count = ?,
                    updated_at = ?
                WHERE id = ? AND last_triggered_at IS NULL
                """,
                (
                    current_issue_number,
                    current_issue_node_id,
                    last_triggered_at,
                    last_triggered_count,
                    now,
                    chore_id,
                ),
            )
        else:
            cursor = await self._db.execute(
                """
                UPDATE chores
                SET current_issue_number = ?,
                    current_issue_node_id = ?,
                    last_triggered_at = ?,
                    last_triggered_count = ?,
                    updated_at = ?
                WHERE id = ? AND last_triggered_at = ?
                """,
                (
                    current_issue_number,
                    current_issue_node_id,
                    last_triggered_at,
                    last_triggered_count,
                    now,
                    chore_id,
                    old_last_triggered_at,
                ),
            )
        await self._db.commit()
        return cursor.rowcount > 0

    async def clear_current_issue(self, chore_id: str) -> None:
        """Clear the open-instance fields (used when issue is detected as closed)."""
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        await self._db.execute(
            """
            UPDATE chores
            SET current_issue_number = NULL,
                current_issue_node_id = NULL,
                updated_at = ?
            WHERE id = ?
            """,
            (now, chore_id),
        )
        await self._db.commit()

    async def update_chore_fields(self, chore_id: str, **kwargs) -> None:
        """Update arbitrary fields on a chore by keyword arguments.

        Used internally to set PR/tracking-issue metadata after creation.
        """
        if not kwargs:
            return
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        kwargs["updated_at"] = now

        set_clause = ", ".join(f"{col} = ?" for col in kwargs)
        values = list(kwargs.values()) + [chore_id]

        await self._db.execute(
            f"UPDATE chores SET {set_clause} WHERE id = ?",  # noqa: S608
            values,
        )
        await self._db.commit()

    # ── Trigger execution (Phase 6) ──

    async def trigger_chore(
        self,
        chore: Chore,
        *,
        github_service,
        access_token: str,
        owner: str,
        repo: str,
        project_id: str,
        parent_issue_count: int | None = None,
    ) -> ChoreTriggerResult:
        """Trigger a single chore: create issue, run agent pipeline, update record.

        Enforces the 1-open-instance constraint:
        - If current_issue_number is set, checks if the issue is still open.
        - If open, skips triggering.
        - If closed externally, clears the issue fields and proceeds.

        Returns a ChoreTriggerResult with trigger status details.
        """
        # 1-open-instance check
        if chore.current_issue_number is not None:
            is_closed = await github_service.check_issue_closed(
                access_token, owner, repo, chore.current_issue_number
            )
            if is_closed:
                await self.clear_current_issue(chore.id)
            else:
                return ChoreTriggerResult(
                    chore_id=chore.id,
                    chore_name=chore.name,
                    triggered=False,
                    skip_reason=f"Open instance exists (issue #{chore.current_issue_number})",
                )

        # Create GitHub issue from template content (strip YAML front matter)
        issue_body = _strip_front_matter(chore.template_content or "")
        issue = await github_service.create_issue(
            access_token,
            owner,
            repo,
            title=chore.name,
            body=issue_body,
            labels=["chore"],
        )

        issue_number = issue["number"]
        issue_node_id = issue["node_id"]
        issue_url = issue["html_url"]

        # Add to project
        await github_service.add_issue_to_project(access_token, project_id, issue_node_id)

        # Run agent pipeline (if workflow config exists)
        try:
            from src.services.workflow_orchestrator import (
                WorkflowContext,
                get_workflow_config,
                get_workflow_orchestrator,
            )

            config = await get_workflow_config(project_id)
            if config:
                ctx = WorkflowContext(
                    session_id=str(uuid.uuid4()),
                    project_id=project_id,
                    access_token=access_token,
                    repository_owner=owner,
                    repository_name=repo,
                    config=config,
                )
                ctx.issue_id = issue_node_id
                ctx.issue_number = issue_number

                orchestrator = get_workflow_orchestrator()
                await orchestrator.create_all_sub_issues(ctx)
        except Exception:
            logger.exception(
                "Agent pipeline failed for chore %s (issue #%s)",
                chore.name,
                issue_number,
            )

        # CAS update chore record
        # Advance last_triggered_count to current parent_issue_count for
        # count-based triggers so the baseline resets after each trigger.
        new_count = (
            parent_issue_count if parent_issue_count is not None else chore.last_triggered_count
        )
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        await self.update_chore_after_trigger(
            chore.id,
            current_issue_number=issue_number,
            current_issue_node_id=issue_node_id,
            last_triggered_at=now,
            last_triggered_count=new_count,
            old_last_triggered_at=chore.last_triggered_at,
        )

        return ChoreTriggerResult(
            chore_id=chore.id,
            chore_name=chore.name,
            triggered=True,
            issue_number=issue_number,
            issue_url=issue_url,
        )

    async def evaluate_triggers(
        self,
        *,
        github_service,
        access_token: str,
        owner: str,
        repo: str,
        project_id: str | None = None,
        parent_issue_count: int | None = None,
    ) -> dict:
        """Evaluate all active scheduled chores and trigger eligible ones.

        Args:
            github_service: GitHub service instance for API calls.
            access_token: OAuth token.
            owner: Repository owner.
            repo: Repository name.
            project_id: Optional filter to a single project.
            parent_issue_count: Current parent issue count (for count triggers).

        Returns:
            Dict with evaluated, triggered, skipped counts and results list.
        """
        from src.services.chores.counter import evaluate_count_trigger
        from src.services.chores.scheduler import evaluate_time_trigger

        chores = await self.list_active_scheduled_chores()
        if project_id:
            chores = [c for c in chores if c.project_id == project_id]

        results: list[ChoreTriggerResult] = []
        triggered = 0
        skipped = 0

        for chore in chores:
            # Proactively detect externally-closed issues (T058)
            if chore.current_issue_number is not None:
                try:
                    is_closed = await github_service.check_issue_closed(
                        access_token, owner, repo, chore.current_issue_number
                    )
                    if is_closed:
                        await self.clear_current_issue(chore.id)
                        # Refresh the chore object so trigger_chore sees it cleared
                        chore = chore.model_copy(
                            update={
                                "current_issue_number": None,
                                "current_issue_node_id": None,
                            }
                        )
                except Exception:
                    logger.exception(
                        "Failed to check issue status for chore %s (issue #%s)",
                        chore.name,
                        chore.current_issue_number,
                    )

            # Evaluate trigger condition
            should_trigger = False
            if chore.schedule_type == "time":
                should_trigger = evaluate_time_trigger(chore)
            elif chore.schedule_type == "count" and parent_issue_count is not None:
                should_trigger = evaluate_count_trigger(chore, parent_issue_count)

            if not should_trigger:
                results.append(
                    ChoreTriggerResult(
                        chore_id=chore.id,
                        chore_name=chore.name,
                        triggered=False,
                        skip_reason="Condition not met",
                    )
                )
                skipped += 1
                continue

            result = await self.trigger_chore(
                chore,
                github_service=github_service,
                access_token=access_token,
                owner=owner,
                repo=repo,
                project_id=chore.project_id,
                parent_issue_count=parent_issue_count,
            )
            results.append(result)
            if result.triggered:
                triggered += 1
            else:
                skipped += 1

        return {
            "evaluated": len(chores),
            "triggered": triggered,
            "skipped": skipped,
            "results": results,
        }
