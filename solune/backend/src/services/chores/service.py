"""ChoresService — CRUD operations for recurring maintenance chores."""

from __future__ import annotations

import re
import uuid
from base64 import b64decode
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from src.logging_utils import get_logger
from src.models.chores import Chore, ChoreCreate, ChoreStatus, ChoreTriggerResult, ChoreUpdate

logger = get_logger(__name__)

_PRESETS_DIR = Path(__file__).resolve().parent / "presets"

# Chore preset definitions — template content is loaded from files in presets/
_CHORE_PRESET_DEFINITIONS = [
    {
        "preset_id": "security-review",
        "name": "Security Review",
        "template_path": ".github/ISSUE_TEMPLATE/chore-security-review.md",
        "template_file": "security-review.md",
        "schedule_type": "count",
        "schedule_value": 10,
        "ai_enhance_enabled": True,
        "agent_pipeline_id": "",
    },
    {
        "preset_id": "performance-review",
        "name": "Performance Review",
        "template_path": ".github/ISSUE_TEMPLATE/chore-performance-review.md",
        "template_file": "performance-review.md",
        "schedule_type": "count",
        "schedule_value": 10,
        "ai_enhance_enabled": True,
        "agent_pipeline_id": "",
    },
    {
        "preset_id": "bug-basher",
        "name": "Bug Basher",
        "template_path": ".github/ISSUE_TEMPLATE/chore-bug-basher.md",
        "template_file": "bug-basher.md",
        "schedule_type": "count",
        "schedule_value": 10,
        "ai_enhance_enabled": True,
        "agent_pipeline_id": "",
    },
]

# Columns that may appear in dynamic UPDATE SET clauses.
# Any column not in this set will be rejected to prevent SQL injection.
_CHORE_UPDATABLE_COLUMNS = frozenset(
    {
        "name",
        "template_path",
        "template_content",
        "status",
        "schedule_type",
        "schedule_value",
        "last_triggered_at",
        "last_triggered_count",
        "pr_number",
        "pr_url",
        "tracking_issue_number",
        "current_issue_number",
        "current_issue_node_id",
        "execution_count",
        "ai_enhance_enabled",
        "agent_pipeline_id",
        "updated_at",
    }
)


def _strip_front_matter(text: str) -> str:
    """Remove YAML front matter (``---\n...\n---``) from the beginning of text."""
    return re.sub(r"\A---\n.*?\n---\n?", "", text, count=1, flags=re.DOTALL).strip()


class ChoreConflictError(RuntimeError):
    """Raised when an inline chore edit conflicts with newer repo content."""

    def __init__(
        self,
        message: str,
        *,
        current_sha: str | None = None,
        current_content: str | None = None,
    ) -> None:
        super().__init__(message)
        self.current_sha = current_sha
        self.current_content = current_content


class ChoresService:
    """Manages chore records in the SQLite database."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    # ── Preset Seeding ────────────────────────────────────────────────

    async def seed_presets(self, project_id: str) -> list[Chore]:
        """Seed built-in chore presets for a project (idempotent).

        Only inserts presets whose ``preset_id`` does not yet exist for the
        given project.  Returns the list of newly created presets.
        """
        created: list[Chore] = []

        for defn in _CHORE_PRESET_DEFINITIONS:
            preset_id = defn["preset_id"]

            # Check if already seeded
            cursor = await self._db.execute(
                "SELECT id FROM chores WHERE preset_id = ? AND project_id = ?",
                (preset_id, project_id),
            )
            if await cursor.fetchone():
                continue

            # Load template content from file
            template_file = _PRESETS_DIR / defn["template_file"]
            template_content = template_file.read_text(encoding="utf-8")

            chore_id = str(uuid.uuid4())
            now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

            await self._db.execute(
                """
                INSERT INTO chores (
                    id, project_id, name, template_path, template_content,
                    schedule_type, schedule_value,
                    ai_enhance_enabled, agent_pipeline_id,
                    is_preset, preset_id,
                    status, last_triggered_count, execution_count,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 'active', 0, 0, ?, ?)
                """,
                (
                    chore_id,
                    project_id,
                    defn["name"],
                    defn["template_path"],
                    template_content,
                    defn["schedule_type"],
                    defn["schedule_value"],
                    1 if defn["ai_enhance_enabled"] else 0,
                    defn["agent_pipeline_id"],
                    preset_id,
                    now,
                    now,
                ),
            )

            chore = Chore(
                id=chore_id,
                project_id=project_id,
                name=defn["name"],
                template_path=defn["template_path"],
                template_content=template_content,
                schedule_type=defn["schedule_type"],
                schedule_value=defn["schedule_value"],
                ai_enhance_enabled=defn["ai_enhance_enabled"],
                agent_pipeline_id=defn["agent_pipeline_id"],
                is_preset=True,
                preset_id=preset_id,
                status=ChoreStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )
            created.append(chore)
            logger.info("Seeded chore preset '%s' for project %s", defn["name"], project_id)

        if created:
            await self._db.commit()

        return created

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

        # Reject unexpected column names (defense-in-depth against SQL injection)
        bad = set(updates) - _CHORE_UPDATABLE_COLUMNS
        if bad:
            raise ValueError(f"Invalid update columns: {bad}")

        # Convert booleans to SQLite integers
        for key, val in list(updates.items()):
            if isinstance(val, bool):
                updates[key] = 1 if val else 0

        set_clause = ", ".join(f"{col} = ?" for col in updates)
        values = [*list(updates.values()), chore_id]

        await self._db.execute(
            f"UPDATE chores SET {set_clause} WHERE id = ?",
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
        Also atomically increments execution_count.
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
                    execution_count = execution_count + 1,
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
                    execution_count = execution_count + 1,
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
        Converts Python bools to SQLite integers (0/1) automatically.
        """
        if not kwargs:
            return
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        kwargs["updated_at"] = now

        # Reject unexpected column names (defense-in-depth against SQL injection)
        bad = set(kwargs) - _CHORE_UPDATABLE_COLUMNS
        if bad:
            raise ValueError(f"Invalid update columns: {bad}")

        # Convert booleans to SQLite integers
        for key, val in kwargs.items():
            if isinstance(val, bool):
                kwargs[key] = 1 if val else 0

        set_clause = ", ".join(f"{col} = ?" for col in kwargs)
        values = [*list(kwargs.values()), chore_id]

        await self._db.execute(
            f"UPDATE chores SET {set_clause} WHERE id = ?",
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
        github_user_id: str = "",
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

        # Append agent pipeline tracking table to the issue body so
        # subsequent pipeline updates can mark agents as active/done.
        try:
            from src.services.agent_tracking import append_tracking_to_body
            from src.services.workflow_orchestrator import (
                get_status_order,
                get_workflow_config,
            )

            config = await get_workflow_config(project_id)
            if config:
                # Resolve effective agent pipeline mappings.
                # Priority: chore's own pipeline > project-assigned / user-selected > defaults.
                # Operate on a shallow copy so we never persist overrides to the
                # shared canonical workflow config.
                effective_mappings = dict(config.agent_mappings) if config.agent_mappings else {}
                if chore.agent_pipeline_id:
                    from src.services.workflow_orchestrator.config import (
                        load_pipeline_as_agent_mappings,
                    )

                    chore_pipeline = await load_pipeline_as_agent_mappings(
                        project_id, chore.agent_pipeline_id
                    )
                    if chore_pipeline is not None:
                        effective_mappings, _, _, _ = chore_pipeline
                elif github_user_id:
                    from src.services.workflow_orchestrator.config import (
                        load_user_agent_mappings,
                    )

                    user_mappings = await load_user_agent_mappings(github_user_id, project_id)
                    if user_mappings:
                        effective_mappings = user_mappings

                if effective_mappings:
                    status_order = get_status_order(config)
                    issue_body = append_tracking_to_body(
                        issue_body, effective_mappings, status_order
                    )
        except Exception as e:
            logger.exception(
                "Failed to append agent tracking table for chore %s: %s", chore.name, e
            )

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
        issue_database_id = issue.get("id")

        # Add to project
        item_id = await github_service.add_issue_to_project(
            access_token,
            project_id,
            issue_node_id,
            issue_database_id=issue_database_id,
        )

        # Run full agent pipeline (mirrors _run_workflow_orchestration)
        try:
            from src.config import get_settings
            from src.services.copilot_polling import ensure_polling_started
            from src.services.workflow_orchestrator import (
                PipelineState,
                WorkflowContext,
                get_agent_slugs,
                get_workflow_config,
                get_workflow_orchestrator,
                set_pipeline_state,
            )
            from src.utils import utcnow

            settings = get_settings()
            config = await get_workflow_config(project_id)

            if config:
                # Ensure repo info is set on configuration
                config.repository_owner = owner
                config.repository_name = repo
                if not config.copilot_assignee:
                    config.copilot_assignee = settings.default_assignee

                # Apply effective pipeline mappings for execution.
                # Priority: chore > project-assigned > user-selected > defaults.
                try:
                    if chore.agent_pipeline_id:
                        from src.services.workflow_orchestrator.config import (
                            load_pipeline_as_agent_mappings,
                        )

                        _chore_pipeline = await load_pipeline_as_agent_mappings(
                            project_id, chore.agent_pipeline_id
                        )
                        if _chore_pipeline is not None:
                            config.agent_mappings, _, _, _ = _chore_pipeline
                    else:
                        from src.services.workflow_orchestrator.config import (
                            resolve_project_pipeline_mappings,
                        )

                        _pipeline_result = await resolve_project_pipeline_mappings(
                            project_id, github_user_id or ""
                        )
                        if _pipeline_result.agent_mappings:
                            config.agent_mappings = _pipeline_result.agent_mappings
                except Exception:
                    logger.debug(
                        "Pipeline mapping resolution failed for chore %s; using config defaults",
                        chore.name,
                    )

                # Set issue status to Backlog on the project board
                backlog_status = config.status_backlog
                try:
                    await github_service.update_item_status_by_name(
                        access_token=access_token,
                        project_id=project_id,
                        item_id=item_id,
                        status_name=backlog_status,
                    )
                    logger.info(
                        "Set chore issue #%d status to '%s' on project",
                        issue_number,
                        backlog_status,
                    )
                except Exception:
                    logger.exception(
                        "Failed to set Backlog status for chore issue #%d",
                        issue_number,
                    )

                # Build workflow context
                user_agent_model = ""
                if github_user_id:
                    try:
                        from src.services.settings_store import get_effective_user_settings

                        effective_user_settings = await get_effective_user_settings(
                            self._db, github_user_id
                        )
                        user_agent_model = effective_user_settings.ai.agent_model or ""
                    except Exception as e:
                        logger.debug(
                            "Failed to load user agent model for chore %s: %s", chore.name, e
                        )

                ctx = WorkflowContext(
                    session_id=str(uuid.uuid4()),
                    project_id=project_id,
                    access_token=access_token,
                    repository_owner=owner,
                    repository_name=repo,
                    config=config,
                    user_agent_model=user_agent_model,
                )
                ctx.issue_id = issue_node_id
                ctx.issue_number = issue_number
                ctx.project_item_id = item_id

                orchestrator = get_workflow_orchestrator()

                # Create all sub-issues upfront.
                agent_sub_issues = await orchestrator.create_all_sub_issues(ctx)
                if agent_sub_issues:
                    backlog_agents = get_agent_slugs(config, backlog_status)
                    pipeline_state = PipelineState(
                        issue_number=issue_number,
                        project_id=project_id,
                        status=backlog_status,
                        agents=backlog_agents,
                        agent_sub_issues=agent_sub_issues,
                        started_at=utcnow(),
                    )
                    set_pipeline_state(issue_number, pipeline_state)
                    logger.info(
                        "Pre-created %d sub-issues for chore issue #%d",
                        len(agent_sub_issues),
                        issue_number,
                    )

                # Assign first Backlog agent
                await orchestrator.assign_agent_for_status(ctx, backlog_status, agent_index=0)

                # Start Copilot polling so the pipeline advances
                await ensure_polling_started(
                    access_token=access_token,
                    project_id=project_id,
                    owner=owner,
                    repo=repo,
                    caller="chore_trigger",
                )
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
        cas_ok = await self.update_chore_after_trigger(
            chore.id,
            current_issue_number=issue_number,
            current_issue_node_id=issue_node_id,
            last_triggered_at=now,
            last_triggered_count=new_count,
            old_last_triggered_at=chore.last_triggered_at,
        )

        if not cas_ok:
            # A concurrent evaluator already triggered this chore.
            # Close the duplicate issue we just created to avoid orphans.
            logger.warning(
                "CAS update failed for chore %s — closing duplicate issue #%s",
                chore.name,
                issue_number,
            )
            try:
                await github_service.update_issue_state(
                    access_token,
                    owner,
                    repo,
                    issue_number,
                    state="closed",
                    state_reason="not_planned",
                )
            except Exception:
                logger.exception(
                    "Failed to close duplicate issue #%s for chore %s",
                    issue_number,
                    chore.name,
                )
            return ChoreTriggerResult(
                chore_id=chore.id,
                chore_name=chore.name,
                triggered=False,
                skip_reason="Concurrent trigger detected (CAS conflict)",
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

    # ── Inline Update (Phase 5) ──

    async def inline_update_chore(
        self,
        chore_id: str,
        body,
        *,
        github_service=None,
        access_token: str | None = None,
        owner: str | None = None,
        repo: str | None = None,
        project_id: str | None = None,
    ) -> dict:
        """Apply an inline edit to a chore and optionally create a PR.

        Returns dict with 'chore', 'pr_number', 'pr_url' keys.
        """
        from src.services.chores.template_builder import (
            build_template,
        )

        expected_sha = body.expected_sha
        updates = body.model_dump(exclude_unset=True)
        updates.pop("expected_sha", None)

        chore = await self.get_chore(chore_id)
        if chore is None:
            raise ValueError(f"Chore {chore_id} not found")

        if not updates:
            return {"chore": chore, "pr_number": None, "pr_url": None}

        needs_pr = "template_content" in updates or "name" in updates

        # When the name changes, derive the new template_path and remember
        # the old one so the repo commit can delete-and-create atomically.
        old_template_path: str | None = None
        if "name" in updates:
            from src.services.chores.template_builder import derive_template_path

            new_path = derive_template_path(updates["name"])
            if new_path != chore.template_path:
                old_template_path = chore.template_path
                updates["template_path"] = new_path

        if expected_sha and needs_pr and github_service and access_token and owner and repo:
            response = await github_service.rest_request(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/contents/{chore.template_path}",
            )
            if response.status_code == 200:
                payload = response.json()
                current_sha = payload.get("sha") if isinstance(payload, dict) else None
                if current_sha and current_sha != expected_sha:
                    current_content = None
                    encoded_content = payload.get("content") if isinstance(payload, dict) else None
                    if isinstance(encoded_content, str):
                        try:
                            current_content = b64decode(encoded_content).decode("utf-8")
                        except Exception:
                            current_content = None
                    raise ChoreConflictError(
                        "File has been modified since page load",
                        current_sha=current_sha,
                        current_content=current_content,
                    )

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        updates["updated_at"] = now

        # Reject unexpected column names (defense-in-depth against SQL injection)
        bad = set(updates) - _CHORE_UPDATABLE_COLUMNS
        if bad:
            raise ValueError(f"Invalid update columns: {bad}")

        # Convert booleans to SQLite integers
        for key, val in list(updates.items()):
            if isinstance(val, bool):
                updates[key] = 1 if val else 0

        set_clause = ", ".join(f"{col} = ?" for col in updates)
        values = [*list(updates.values()), chore_id]

        await self._db.execute(
            f"UPDATE chores SET {set_clause} WHERE id = ?",
            values,
        )
        await self._db.commit()

        chore = await self.get_chore(chore_id)
        if chore is None:
            raise ValueError(f"Chore {chore_id} not found after update")

        pr_number = None
        pr_url = None

        if needs_pr and github_service and access_token and owner and repo:
            try:
                from src.services.chores.template_builder import (
                    update_template_in_repo,
                )

                result = await update_template_in_repo(
                    github_service=github_service,
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    chore_name=chore.name,
                    template_path=chore.template_path,
                    template_content=build_template(chore.name, chore.template_content),
                    old_template_path=old_template_path,
                )
                pr_number = result.get("pr_number")
                pr_url = result.get("pr_url")

                if pr_number:
                    await self.update_chore_fields(chore_id, pr_number=pr_number, pr_url=pr_url)
                    chore = await self.get_chore(chore_id)
            except Exception as e:
                logger.exception(
                    "Failed to create PR for inline update of chore %s: %s", chore_id, e
                )

        return {"chore": chore, "pr_number": pr_number, "pr_url": pr_url}

    # ── Create with Auto-Merge (Phase 8) ──

    async def create_chore_with_auto_merge(
        self,
        project_id: str,
        body,
        *,
        github_service,
        access_token: str,
        owner: str,
        repo: str,
    ) -> dict:
        """Create a chore, commit template via PR, and auto-merge.

        Returns dict with chore, issue_number, pr_number, pr_url,
        pr_merged, merge_error.
        """
        from src.models.chores import ChoreCreate
        from src.services.chores.template_builder import (
            build_template,
            commit_template_to_repo,
        )

        template_content = build_template(body.name, body.template_content)

        # Commit template to repo via branch + PR + tracking issue
        result = await commit_template_to_repo(
            github_service=github_service,
            access_token=access_token,
            owner=owner,
            repo=repo,
            project_id=project_id,
            name=body.name,
            template_content=template_content,
        )

        # Create chore record in database
        create_body = ChoreCreate(name=body.name, template_content=body.template_content)
        chore = await self.create_chore(
            project_id,
            create_body,
            template_path=result["template_path"],
        )

        # Update chore with additional fields
        await self.update_chore_fields(
            chore.id,
            pr_number=result.get("pr_number"),
            pr_url=result.get("pr_url"),
            tracking_issue_number=result.get("tracking_issue_number"),
            template_content=template_content,
            ai_enhance_enabled=body.ai_enhance_enabled,
            agent_pipeline_id=body.agent_pipeline_id,
        )

        chore = await self.get_chore(chore.id)
        pr_number = result.get("pr_number")
        pr_url = result.get("pr_url")
        tracking_issue_number = result.get("tracking_issue_number")
        pr_merged = False
        merge_error = None

        # Auto-merge the PR if requested
        if body.auto_merge and pr_number:
            try:
                from src.services.chores.template_builder import merge_chore_pr

                merged, error = await merge_chore_pr(
                    github_service=github_service,
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    pr_number=pr_number,
                )
                pr_merged = merged
                merge_error = error
            except Exception as exc:
                logger.exception("Auto-merge failed for chore PR #%s", pr_number)
                merge_error = str(exc)

        return {
            "chore": chore,
            "issue_number": tracking_issue_number,
            "pr_number": pr_number,
            "pr_url": pr_url,
            "pr_merged": pr_merged,
            "merge_error": merge_error,
        }
