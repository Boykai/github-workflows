"""Agent Creator Service — orchestrates the #agent chat command.

Implements a guided multi-step conversation for creating custom GitHub
agents.  State is held in a module-level ``BoundedDict`` keyed by session
ID (web chat) or GitHub user ID (Signal).

Entry points:
- ``handle_agent_command()`` — called from ``api/chat.py`` and ``signal_chat.py``
  when a message starts with ``#agent`` or an active creation session exists.
"""

from __future__ import annotations

import json
import re
import uuid

import aiosqlite
import yaml

from src.logging_utils import get_logger
from src.models.agent_creator import (
    AgentCreationState,
    AgentPreview,
    CreationStep,
    PipelineStepResult,
)
from src.services.ai_agent import get_ai_agent_service
from src.services.github_projects import github_projects_service
from src.utils import BoundedDict, utcnow

logger = get_logger(__name__)


async def is_admin_user(db: aiosqlite.Connection, github_user_id: str) -> bool:
    """Check whether *github_user_id* matches the admin in global_settings.

    If no admin has been set yet (``admin_github_user_id`` is NULL) and the
    application is running in debug mode, the first caller is auto-promoted.
    In production mode, a missing admin always denies access.
    """
    try:
        cursor = await db.execute("SELECT admin_github_user_id FROM global_settings WHERE id = 1")
        row = await cursor.fetchone()
        if row is None:
            return False
        admin_id = row["admin_github_user_id"] if isinstance(row, dict) else row[0]

        if admin_id is None:
            # Check if an explicit admin is configured via env var.
            from src.config import get_settings

            settings = get_settings()
            if settings.admin_github_user_id:
                # Production (or debug) with explicit admin — allow only that user
                # and persist to DB so future checks hit the fast path.
                if str(github_user_id) != str(settings.admin_github_user_id):
                    return False
                cursor = await db.execute(
                    "UPDATE global_settings SET admin_github_user_id = ? "
                    "WHERE id = 1 AND admin_github_user_id IS NULL",
                    (github_user_id,),
                )
                await db.commit()
                if cursor.rowcount > 0:
                    logger.info(
                        "Seeded admin user %s from ADMIN_GITHUB_USER_ID via #agent command",
                        github_user_id,
                    )
                return True
            # No explicit admin configured
            if not settings.debug:
                logger.error(
                    "ADMIN_GITHUB_USER_ID not set in production — denying admin access for user %s",
                    github_user_id,
                )
                return False
            # Debug mode only: auto-promote the first authenticated user (atomic CAS).
            cursor = await db.execute(
                "UPDATE global_settings SET admin_github_user_id = ? "
                "WHERE id = 1 AND admin_github_user_id IS NULL",
                (github_user_id,),
            )
            await db.commit()
            if cursor.rowcount > 0:
                logger.info(
                    "Auto-promoted user %s as admin via #agent command (debug mode)", github_user_id
                )
                return True
            # Another user won the race — re-read.
            cursor = await db.execute(
                "SELECT admin_github_user_id FROM global_settings WHERE id = 1"
            )
            row = await cursor.fetchone()
            if row is None:
                return False
            admin_id = row["admin_github_user_id"] if isinstance(row, dict) else row[0]

        return admin_id is not None and str(admin_id) == str(github_user_id)
    except Exception as e:
        logger.warning("Admin check failed — denying access: %s", e, exc_info=True)
        return False


# ── Module-level state ─────────────────────────────────────────────────
# Keyed by session_id (web) or github_user_id (Signal).
_agent_sessions: BoundedDict[str, AgentCreationState] = BoundedDict(maxlen=100)

# Confirmation keywords
_CONFIRM_WORDS = frozenset(
    {
        "create",
        "confirm",
        "yes",
        "looks good",
        "lgtm",
        "go",
        "do it",
        "ok",
        "approve",
    }
)


# ── Public API ─────────────────────────────────────────────────────────


def get_active_session(session_key: str) -> AgentCreationState | None:
    """Return an active agent creation session, if any."""
    return _agent_sessions.get(session_key)


def clear_session(session_key: str) -> None:
    """Remove a creation session (cleanup)."""
    _agent_sessions.pop(session_key, None)


async def handle_agent_command(
    *,
    message: str,
    session_key: str,
    project_id: str | None,
    owner: str | None,
    repo: str | None,
    github_user_id: str,
    access_token: str,
    db: aiosqlite.Connection,
    project_columns: list[str] | None = None,
) -> str:
    """Main entry point — process an #agent message or continue an active session.

    Returns a markdown-formatted response string.
    """
    state = _agent_sessions.get(session_key)

    # Enforce admin-only access (FR-002)
    if not await is_admin_user(db, github_user_id):
        return "⛔ The `#agent` command is restricted to admin users."

    if state is None:
        # New command — parse and initialise state
        return await _handle_new_command(
            message=message,
            session_key=session_key,
            project_id=project_id,
            owner=owner,
            repo=repo,
            github_user_id=github_user_id,
            access_token=access_token,
            db=db,
            project_columns=project_columns,
        )

    # Existing session — route by current step
    return await _handle_existing_session(
        state=state,
        message=message,
        session_key=session_key,
        access_token=access_token,
        db=db,
        project_columns=project_columns,
    )


# ── Command parsing ────────────────────────────────────────────────────


def parse_command(command_text: str) -> tuple[str, str | None]:
    """Parse ``/agent <description> [#<status>]`` (also accepts legacy ``#agent``).

    Returns ``(description, raw_status_or_none)``.
    Raises ``ValueError`` if description is empty.
    """
    text = command_text.strip()
    # Strip the /agent or #agent prefix (case-insensitive)
    text = re.sub(r"^[/#]agent\s*", "", text, flags=re.IGNORECASE).strip()

    if not text:
        raise ValueError("empty description")

    # Look for trailing #<status> — last token starting with #
    parts = text.rsplit("#", maxsplit=1)
    if len(parts) == 2 and parts[1].strip():
        description = parts[0].strip()
        raw_status = parts[1].strip()
        if not description:
            raise ValueError("empty description")
        return description, raw_status

    return text, None


def _normalize_status(name: str) -> str:
    """Normalize a status name for fuzzy matching."""
    return name.lower().replace("-", "").replace("_", "").replace(" ", "")


def fuzzy_match_status(
    raw_status: str,
    columns: list[str],
) -> tuple[str | None, bool, list[str]]:
    """Resolve *raw_status* against existing project *columns*.

    Matching strategy (in order):
    1. Exact normalized match (``in-review`` == ``In Review``)
    2. Contains match (``review`` matches ``In Review`` and ``Code Review``)

    Returns ``(resolved_name | None, is_ambiguous, matching_columns)``.
    """
    normalized_input = _normalize_status(raw_status)

    # Pass 1: exact normalized match
    exact_matches: list[str] = [
        col for col in columns if _normalize_status(col) == normalized_input
    ]

    if len(exact_matches) == 1:
        return exact_matches[0], False, exact_matches
    if len(exact_matches) > 1:
        return None, True, exact_matches

    # Pass 2: contains match (input is a substring of the normalized column)
    contains_matches: list[str] = [
        col for col in columns if normalized_input in _normalize_status(col)
    ]

    if len(contains_matches) == 1:
        return contains_matches[0], False, contains_matches
    if len(contains_matches) > 1:
        return None, True, contains_matches

    return None, False, []


# ── Internal handlers ──────────────────────────────────────────────────


async def _handle_new_command(
    *,
    message: str,
    session_key: str,
    project_id: str | None,
    owner: str | None,
    repo: str | None,
    github_user_id: str,
    access_token: str,
    db: aiosqlite.Connection,
    project_columns: list[str] | None = None,
) -> str:
    """Parse a fresh ``#agent`` command and set up the creation session."""
    try:
        description, raw_status = parse_command(message)
    except ValueError:
        return (
            "**Error:** Could not parse the `#agent` command. "
            "Usage: `#agent <description> [#<status-name>]`\n\n"
            "Example: `#agent Reviews PRs for security vulnerabilities #in-review`"
        )

    state = AgentCreationState(
        session_id=session_key,
        github_user_id=github_user_id,
        project_id=project_id,
        owner=owner,
        repo=repo,
        raw_description=description,
        raw_status=raw_status,
    )

    # If project is unknown, we need to ask (Signal flow)
    if not project_id:
        state.step = CreationStep.RESOLVE_PROJECT
        _agent_sessions[session_key] = state
        return await _prompt_project_selection(state, access_token)

    # We have a project — proceed to status resolution
    return await _resolve_status_step(
        state=state,
        session_key=session_key,
        access_token=access_token,
        db=db,
        project_columns=project_columns,
    )


async def _handle_existing_session(
    *,
    state: AgentCreationState,
    message: str,
    session_key: str,
    access_token: str,
    db: aiosqlite.Connection,
    project_columns: list[str] | None = None,
) -> str:
    """Route to the correct handler based on the current step."""
    step = state.step

    if step == CreationStep.RESOLVE_PROJECT:
        return await _handle_project_selection(
            state=state,
            message=message,
            session_key=session_key,
            access_token=access_token,
            db=db,
        )

    if step == CreationStep.RESOLVE_STATUS:
        return await _handle_status_selection(
            state=state,
            message=message,
            session_key=session_key,
            access_token=access_token,
            db=db,
            project_columns=project_columns,
        )

    if step in (CreationStep.PREVIEW, CreationStep.EDIT_LOOP):
        return await _handle_preview_response(
            state=state,
            message=message,
            session_key=session_key,
            access_token=access_token,
            db=db,
        )

    if step == CreationStep.DONE:
        # Session is over — clean up and start fresh if it looks like a new command
        clear_session(session_key)
        if message.strip().lower().startswith("/agent") or message.strip().lower().startswith(
            "#agent"
        ):
            return await handle_agent_command(
                message=message,
                session_key=session_key,
                project_id=state.project_id,
                owner=state.owner,
                repo=state.repo,
                github_user_id=state.github_user_id,
                access_token=access_token,
                db=db,
                project_columns=project_columns,
            )
        return "The previous agent creation is complete. Type `#agent <description>` to start a new one."

    return "Unexpected state. Type `#agent <description>` to start over."


# ── Status resolution ──────────────────────────────────────────────────


async def _resolve_status_step(
    *,
    state: AgentCreationState,
    session_key: str,
    access_token: str,
    db: aiosqlite.Connection,
    project_columns: list[str] | None = None,
) -> str:
    """Resolve the status column and move to preview or ask for clarification."""
    columns = project_columns or []

    if state.raw_status:
        resolved, is_ambiguous, matches = fuzzy_match_status(state.raw_status, columns)

        if resolved:
            state.resolved_status = resolved
            state.is_new_column = False
            state.step = CreationStep.PREVIEW
            _agent_sessions[session_key] = state
            return await _generate_and_present_preview(state, session_key, access_token)

        if is_ambiguous:
            # Present matches for user selection
            state.step = CreationStep.RESOLVE_STATUS
            state.ambiguous_columns = matches
            _agent_sessions[session_key] = state
            opts = "\n".join(f"{i + 1}. {col}" for i, col in enumerate(matches))
            return (
                f"**Multiple columns match '{state.raw_status}':**\n{opts}\n\n"
                "Please reply with the number of your choice."
            )

        # No match — offer to create a new column
        # Title-case the raw status for the new column name
        proposed_name = state.raw_status.replace("-", " ").replace("_", " ").title()
        state.resolved_status = proposed_name
        state.is_new_column = True
        state.step = CreationStep.PREVIEW
        _agent_sessions[session_key] = state
        return await _generate_and_present_preview(state, session_key, access_token)

    # No status provided — ask the user to choose
    state.step = CreationStep.RESOLVE_STATUS
    _agent_sessions[session_key] = state
    if columns:
        opts = "\n".join(f"{i + 1}. {col}" for i, col in enumerate(columns))
        return (
            "**Which status column should this agent be assigned to?**\n"
            f"{opts}\n\n"
            "Reply with a number, or type a new column name."
        )
    return "**Which status column should this agent be assigned to?** (type a column name)"


async def _handle_status_selection(
    *,
    state: AgentCreationState,
    message: str,
    session_key: str,
    access_token: str,
    db: aiosqlite.Connection,
    project_columns: list[str] | None = None,
) -> str:
    """Handle user's status column selection."""
    text = message.strip()
    columns = state.ambiguous_columns or project_columns or []

    # Check if user typed a number
    if text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(columns):
            state.resolved_status = columns[idx]
            state.is_new_column = False
            state.step = CreationStep.PREVIEW
            _agent_sessions[session_key] = state
            return await _generate_and_present_preview(state, session_key, access_token)
        return f"Please choose a number between 1 and {len(columns)}."

    # Treat as a new column name
    proposed = text.replace("-", " ").replace("_", " ").title()
    state.resolved_status = proposed
    state.is_new_column = True
    state.step = CreationStep.PREVIEW
    _agent_sessions[session_key] = state
    return await _generate_and_present_preview(state, session_key, access_token)


# ── Preview generation ─────────────────────────────────────────────────


async def _generate_and_present_preview(
    state: AgentCreationState,
    session_key: str,
    access_token: str,
) -> str:
    """Call the AI service to generate a preview and format it for display."""
    ai_service = get_ai_agent_service()

    try:
        config = await ai_service.generate_agent_config(
            description=state.raw_description,
            status_column=state.resolved_status or "",
            github_token=access_token,
        )
    except Exception as exc:
        logger.error("Failed to generate agent config: %s", exc)
        clear_session(session_key)
        return (
            f"**Error:** Failed to generate agent configuration. Please try again.\n\nDetail: {exc}"
        )

    slug = AgentPreview.name_to_slug(config["name"])

    # Use tools from AI-generated config if provided; otherwise empty list.
    # These should be Copilot tool/capability identifiers, not agent slugs.
    raw_tools = config.get("tools") or []
    if isinstance(raw_tools, list):
        tools: list[str] = [str(t) for t in raw_tools]
    else:
        logger.warning("Agent config 'tools' field is not a list; defaulting to empty")
        tools = []

    preview = AgentPreview(
        name=config["name"],
        slug=slug,
        description=config["description"],
        system_prompt=config["system_prompt"],
        status_column=state.resolved_status or "",
        tools=tools,
    )
    state.preview = preview
    state.step = CreationStep.PREVIEW
    _agent_sessions[session_key] = state

    return _format_preview(preview, state.is_new_column)


def _format_preview(preview: AgentPreview, is_new_column: bool) -> str:
    """Format an AgentPreview as markdown for chat display."""
    new_col_note = " *(new column)*" if is_new_column else ""
    prompt_excerpt = preview.system_prompt[:500]
    if len(preview.system_prompt) > 500:
        prompt_excerpt += "..."

    tools_display = ", ".join(f"`{t}`" for t in preview.tools) if preview.tools else "none"

    return (
        f"## Agent Preview: {preview.name}\n\n"
        f"**Slug:** `{preview.slug}`\n"
        f"**Description:** {preview.description}\n"
        f"**Status Column:** {preview.status_column}{new_col_note}\n"
        f"**Tools:** {tools_display}\n\n"
        f"**Files to create:**\n"
        f"- `.github/agents/{preview.slug}.agent.md`\n"
        f"- `.github/prompts/{preview.slug}.prompt.md`\n\n"
        f"**System Prompt:**\n> {prompt_excerpt}\n\n"
        "---\n"
        "Type **create** to confirm, or describe changes (e.g., *change the name to SecBot*)."
    )


async def _handle_preview_response(
    *,
    state: AgentCreationState,
    message: str,
    session_key: str,
    access_token: str,
    db: aiosqlite.Connection,
) -> str:
    """Handle user's response to a preview — confirm or edit."""
    text = message.strip().lower()

    # Check for confirmation
    if text in _CONFIRM_WORDS:
        return await _execute_creation_pipeline(
            state=state,
            session_key=session_key,
            access_token=access_token,
            db=db,
        )

    # Treat as an edit request
    return await _apply_edit(
        state=state,
        edit_instruction=message.strip(),
        session_key=session_key,
        access_token=access_token,
    )


async def _apply_edit(
    *,
    state: AgentCreationState,
    edit_instruction: str,
    session_key: str,
    access_token: str,
) -> str:
    """Apply a user's edit request to the current preview."""
    if not state.preview:
        return "No preview to edit. Type `#agent <description>` to start over."

    ai_service = get_ai_agent_service()
    current_config = {
        "name": state.preview.name,
        "description": state.preview.description,
        "system_prompt": state.preview.system_prompt,
    }

    try:
        updated = await ai_service.edit_agent_config(
            current_config=current_config,
            edit_instruction=edit_instruction,
            github_token=access_token,
        )
    except Exception as exc:
        logger.error("Failed to apply edit: %s", exc)
        return (
            f"**Error:** Could not apply edit. Please try again.\n\nDetail: {exc}\n\n"
            "Type **create** to confirm the current preview, or describe another change."
        )

    slug = AgentPreview.name_to_slug(updated["name"])
    state.preview = AgentPreview(
        name=updated["name"],
        slug=slug,
        description=updated["description"],
        system_prompt=updated["system_prompt"],
        status_column=state.preview.status_column,
        tools=state.preview.tools,
    )
    state.step = CreationStep.EDIT_LOOP
    _agent_sessions[session_key] = state

    return _format_preview(state.preview, state.is_new_column)


# ── Pipeline execution ─────────────────────────────────────────────────


async def _execute_creation_pipeline(
    *,
    state: AgentCreationState,
    session_key: str,
    access_token: str,
    db: aiosqlite.Connection,
) -> str:
    """Execute the 7-step creation pipeline with best-effort semantics."""
    if not state.preview or not state.project_id or not state.owner or not state.repo:
        clear_session(session_key)
        return "**Error:** Missing required context. Please start over with `#agent <description>`."

    state.step = CreationStep.EXECUTING
    _agent_sessions[session_key] = state

    preview = state.preview
    results: list[PipelineStepResult] = []

    # Track artifacts for downstream steps
    agent_config_id: str | None = None
    issue_number: int | None = None
    issue_node_id: str | None = None
    issue_database_id: int | None = None
    item_id: str | None = None
    branch_name = f"agent/{preview.slug}"
    repo_info: dict | None = None
    commit_oid: str | None = None
    pr_info: dict | None = None

    # ── Step 1: Check for duplicate name ──
    try:
        cursor = await db.execute(
            "SELECT id FROM agent_configs WHERE name = ? AND project_id = ?",
            (preview.name, state.project_id),
        )
        existing = await cursor.fetchone()
        if existing:
            clear_session(session_key)
            return (
                f"**Error:** An agent named **{preview.name}** already exists in this project. "
                "Please choose a different name."
            )
    except Exception as exc:
        logger.warning("Duplicate check failed (proceeding): %s", exc)

    # ── Step 2: Save agent config to database ──
    agent_config_id = str(uuid.uuid4())
    try:
        tools_json = json.dumps(preview.tools)
        await db.execute(
            """INSERT INTO agent_configs
               (id, name, slug, description, system_prompt, status_column,
                tools, project_id, owner, repo, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                agent_config_id,
                preview.name,
                preview.slug,
                preview.description,
                preview.system_prompt,
                preview.status_column,
                tools_json,
                state.project_id,
                state.owner,
                state.repo,
                state.github_user_id,
                utcnow().isoformat(),
            ),
        )
        await db.commit()
        results.append(
            PipelineStepResult(
                step_name="Save agent configuration",
                success=True,
                detail=f"ID: {agent_config_id}",
            )
        )
    except Exception as exc:
        logger.error("Step 2 (save config) failed: %s", exc)
        results.append(
            PipelineStepResult(
                step_name="Save agent configuration",
                success=False,
                error=str(exc),
            )
        )

    # ── Step 3: Create/verify project column ──
    if state.is_new_column:
        try:
            # The column will be created when we move the issue to this status.
            # For now, just note it.
            results.append(
                PipelineStepResult(
                    step_name="Create project column",
                    success=True,
                    detail=f"Column '{preview.status_column}' will be created on assignment",
                )
            )
        except Exception as exc:
            logger.error("Step 3 (create column) failed: %s", exc)
            results.append(
                PipelineStepResult(
                    step_name="Create project column",
                    success=False,
                    error=str(exc),
                )
            )
    else:
        results.append(
            PipelineStepResult(
                step_name="Verify project column",
                success=True,
                detail=f"Column '{preview.status_column}' exists",
            )
        )

    # ── Step 4: Create GitHub Issue ──
    issue_body = generate_issue_body(preview)
    try:
        issue = await github_projects_service.create_issue(
            access_token=access_token,
            owner=state.owner,
            repo=state.repo,
            title=f"Agent Config: {preview.name}",
            body=issue_body,
            labels=["agent-config"],
        )
        issue_number = issue["number"]
        issue_node_id = issue.get("node_id")
        issue_database_id = issue.get("id")
        results.append(
            PipelineStepResult(
                step_name="Create GitHub Issue",
                success=True,
                detail=f"#{issue_number} — {issue.get('html_url', '')}",
            )
        )

        # Update DB record
        if agent_config_id:
            try:
                await db.execute(
                    "UPDATE agent_configs SET github_issue_number = ? WHERE id = ?",
                    (issue_number, agent_config_id),
                )
                await db.commit()
            except Exception as e:
                logger.debug("Suppressed error: %s", e)
    except Exception as exc:
        logger.error("Step 4 (create issue) failed: %s", exc)
        results.append(
            PipelineStepResult(
                step_name="Create GitHub Issue",
                success=False,
                error=str(exc),
            )
        )

    # ── Step 5: Create branch from default branch ──
    try:
        repo_info = await github_projects_service.get_repository_info(
            access_token,
            state.owner,
            state.repo,
        )
        ref_id = await github_projects_service.create_branch(
            access_token=access_token,
            repository_id=repo_info["repository_id"],
            branch_name=branch_name,
            from_oid=repo_info["head_oid"],
        )
        if ref_id:
            results.append(
                PipelineStepResult(
                    step_name="Create branch",
                    success=True,
                    detail=f"`{branch_name}`",
                )
            )
            # Update DB
            if agent_config_id:
                try:
                    await db.execute(
                        "UPDATE agent_configs SET branch_name = ? WHERE id = ?",
                        (branch_name, agent_config_id),
                    )
                    await db.commit()
                except Exception as e:
                    logger.debug("Suppressed error: %s", e)
        else:
            results.append(
                PipelineStepResult(
                    step_name="Create branch",
                    success=False,
                    error="create_branch returned None",
                )
            )
    except Exception as exc:
        logger.error("Step 5 (create branch) failed: %s", exc)
        results.append(
            PipelineStepResult(
                step_name="Create branch",
                success=False,
                error=str(exc),
            )
        )

    # ── Step 6: Commit configuration files ──
    branch_created = any(r.step_name == "Create branch" and r.success for r in results)
    if branch_created and repo_info:
        files = generate_config_files(preview)
        try:
            # For a newly created branch, the HEAD is the same as the source OID
            commit_oid = await github_projects_service.commit_files(
                access_token=access_token,
                owner=state.owner,
                repo=state.repo,
                branch_name=branch_name,
                head_oid=repo_info["head_oid"],
                files=files,
                message=f"Add agent config: {preview.name}",
            )
            if commit_oid:
                results.append(
                    PipelineStepResult(
                        step_name="Commit configuration files",
                        success=True,
                        detail=f"{len(files)} files committed",
                    )
                )
            else:
                results.append(
                    PipelineStepResult(
                        step_name="Commit configuration files",
                        success=False,
                        error="commit_files returned None",
                    )
                )
        except Exception as exc:
            logger.error("Step 6 (commit files) failed: %s", exc)
            results.append(
                PipelineStepResult(
                    step_name="Commit configuration files",
                    success=False,
                    error=str(exc),
                )
            )
    else:
        results.append(
            PipelineStepResult(
                step_name="Commit configuration files",
                success=False,
                error="Skipped — branch creation failed",
            )
        )

    # ── Step 7: Open Pull Request ──
    commit_succeeded = any(
        r.step_name == "Commit configuration files" and r.success for r in results
    )
    if commit_succeeded and repo_info:
        issue_ref = f"Closes #{issue_number}" if issue_number else ""
        pr_body = (
            f"## Agent: {preview.name}\n\n"
            f"{preview.description}\n\n"
            f"**Status Column:** {preview.status_column}\n"
            f"**Files:**\n"
            f"- `.github/agents/{preview.slug}.agent.md`\n"
            f"- `.github/prompts/{preview.slug}.prompt.md`\n\n"
            f"{issue_ref}"
        )
        try:
            pr_info = await github_projects_service.create_pull_request(
                access_token=access_token,
                repository_id=repo_info["repository_id"],
                title=f"Add agent: {preview.name}",
                body=pr_body,
                head_branch=branch_name,
                base_branch=repo_info["default_branch"],
            )
            if pr_info:
                pr_number = pr_info.get("number", 0)
                results.append(
                    PipelineStepResult(
                        step_name="Open Pull Request",
                        success=True,
                        detail=f"PR #{pr_number} — {pr_info.get('url', '')}",
                    )
                )
                if agent_config_id and pr_number:
                    try:
                        await db.execute(
                            "UPDATE agent_configs SET github_pr_number = ? WHERE id = ?",
                            (pr_number, agent_config_id),
                        )
                        await db.commit()
                    except Exception as e:
                        logger.debug("Suppressed error: %s", e)
            else:
                results.append(
                    PipelineStepResult(
                        step_name="Open Pull Request",
                        success=False,
                        error="create_pull_request returned None",
                    )
                )
        except Exception as exc:
            logger.error("Step 7 (create PR) failed: %s", exc)
            results.append(
                PipelineStepResult(
                    step_name="Open Pull Request",
                    success=False,
                    error=str(exc),
                )
            )
    else:
        results.append(
            PipelineStepResult(
                step_name="Open Pull Request",
                success=False,
                error="Skipped — file commit failed",
            )
        )

    # ── Step 8: Move issue to "In Review" on project board ──
    if issue_node_id and state.project_id:
        try:
            # Add issue to project using public API method
            item_id = await github_projects_service.add_issue_to_project(
                access_token=access_token,
                project_id=state.project_id,
                issue_node_id=issue_node_id,
                issue_database_id=issue_database_id,
            )
            if not item_id:
                # Treat missing item ID as failure instead of silently succeeding
                results.append(
                    PipelineStepResult(
                        step_name="Move issue to In Review",
                        success=False,
                        error="Failed to add issue to project — missing project item id",
                    )
                )
            else:
                await github_projects_service.update_item_status_by_name(
                    access_token=access_token,
                    project_id=state.project_id,
                    item_id=item_id,
                    status_name="In Review",
                )
                results.append(
                    PipelineStepResult(
                        step_name="Move issue to In Review",
                        success=True,
                        detail=f"Issue #{issue_number} moved to In Review",
                    )
                )
        except Exception as exc:
            logger.error("Step 8 (move issue) failed: %s", exc)
            results.append(
                PipelineStepResult(
                    step_name="Move issue to In Review",
                    success=False,
                    error=str(exc),
                )
            )
    else:
        results.append(
            PipelineStepResult(
                step_name="Move issue to In Review",
                success=False,
                error="Skipped — issue creation failed",
            )
        )

    # ── Update pipeline mapping ──
    try:
        await _update_pipeline_mappings(
            db=db,
            project_id=state.project_id,
            status_column=preview.status_column,
            agent_slug=preview.slug,
        )
    except Exception as exc:
        logger.warning("Failed to update pipeline mappings: %s", exc)

    # ── Done ──
    state.pipeline_results = results
    state.step = CreationStep.DONE
    _agent_sessions[session_key] = state

    return _format_pipeline_report(preview, results)


# ── File generation helpers ────────────────────────────────────────────


def generate_issue_body(preview: AgentPreview) -> str:
    """Generate the GitHub Issue body markdown for an agent config."""
    tools_list = ", ".join(f"`{t}`" for t in preview.tools[:10])
    if len(preview.tools) > 10:
        tools_list += f" (+{len(preview.tools) - 10} more)"

    return (
        f"# Agent Configuration: {preview.name}\n\n"
        f"**Description:** {preview.description}\n"
        f"**Status Column:** {preview.status_column}\n"
        f"**Slug:** `{preview.slug}`\n"
        f"**Tools:** {tools_list}\n\n"
        f"## System Prompt\n\n{preview.system_prompt}\n\n"
        "---\n"
        "*This issue was automatically generated by the `#agent` command.*"
    )


def generate_config_files(preview: AgentPreview) -> list[dict]:
    """Generate the 2 config files for commit: agent .md and prompt .md.

    Files follow the GitHub Custom Agent format:
      - ``.github/agents/{slug}.agent.md`` — plain Markdown with YAML
        frontmatter (description, optional tools) followed by the full
        system prompt as the Markdown body.  The file starts with ``---``
        so that ``_FRONTMATTER_RE`` in agent discovery can parse it.
      - ``.github/prompts/{slug}.prompt.md`` — prompt-fenced routing file
        that references the agent by slug.
    """
    # 1. Agent definition: .github/agents/{slug}.agent.md
    # Build YAML frontmatter using yaml.dump for safe serialization —
    # avoids breakage when description/tool IDs contain YAML-special
    # characters like ':', '#', quotes, or newlines.
    frontmatter_data: dict[str, object] = {"name": preview.name, "description": preview.description}
    if preview.icon_name:
        frontmatter_data["icon"] = preview.icon_name
    if preview.mcp_servers:
        frontmatter_data["mcp-servers"] = preview.mcp_servers
    if preview.tool_ids:
        frontmatter_data["metadata"] = {"solune-tool-ids": ",".join(preview.tool_ids)}
    frontmatter = yaml.dump(frontmatter_data, default_flow_style=False, sort_keys=False).rstrip(
        "\n"
    )

    # Plain Markdown starting with YAML frontmatter (no outer code fence)
    # so the backend's _FRONTMATTER_RE (^---…---) can discover this agent.
    agent_content = f"---\n{frontmatter}\n---\n\n{preview.system_prompt}\n"

    # 2. Prompt routing file: .github/prompts/{slug}.prompt.md
    prompt_content = f"```prompt\n---\nagent: {preview.slug}\n---\n```\n"

    return [
        {"path": f".github/agents/{preview.slug}.agent.md", "content": agent_content},
        {"path": f".github/prompts/{preview.slug}.prompt.md", "content": prompt_content},
    ]


def _format_pipeline_report(preview: AgentPreview, results: list[PipelineStepResult]) -> str:
    """Format the per-step status report with checkmarks/crosses."""
    lines = [f"## Agent Created: {preview.name}\n"]

    for r in results:
        icon = "✅" if r.success else "❌"
        line = f"{icon} **{r.step_name}**"
        if r.detail:
            line += f" — {r.detail}"
        if r.error and not r.success:
            line += f"\n   Error: {r.error}"
        lines.append(line)

    succeeded = sum(1 for r in results if r.success)
    total = len(results)
    lines.append(f"\n**Result:** {succeeded}/{total} steps completed successfully.")

    return "\n".join(lines)


# ── Project resolution (Signal) ────────────────────────────────────────


async def _prompt_project_selection(
    state: AgentCreationState,
    access_token: str,
) -> str:
    """Prompt the user to select a project (for Signal when no context)."""
    return (
        "**Which project should this agent be created for?**\n\n"
        "Please provide the project name or ID."
    )


async def _handle_project_selection(
    *,
    state: AgentCreationState,
    message: str,
    session_key: str,
    access_token: str,
    db: aiosqlite.Connection,
) -> str:
    """Handle user's project selection in Signal flow."""
    text = message.strip()

    # If user typed a number and we have available_projects
    if text.isdigit() and state.available_projects:
        idx = int(text) - 1
        if 0 <= idx < len(state.available_projects):
            project = state.available_projects[idx]
            state.project_id = project["id"]
            # Try to resolve owner/repo
            try:
                owner, repo = await _resolve_owner_repo(access_token, project["id"])
                state.owner = owner
                state.repo = repo
            except Exception as e:
                logger.debug("Suppressed error: %s", e)

            return await _resolve_status_step(
                state=state,
                session_key=session_key,
                access_token=access_token,
                db=db,
            )
        return f"Please choose a number between 1 and {len(state.available_projects)}."

    # Fallback: cannot resolve project from free text in V1
    return (
        "Could not resolve project. Please provide the project number, "
        "or type `#agent <description>` in the web chat where a project is selected."
    )


async def _resolve_owner_repo(access_token: str, project_id: str) -> tuple[str, str]:
    """Resolve owner/repo from a project ID using the existing utility."""
    from src.utils import resolve_repository

    return await resolve_repository(access_token, project_id)


# ── Pipeline mapping update ────────────────────────────────────────────


async def _update_pipeline_mappings(
    *,
    db: aiosqlite.Connection,
    project_id: str,
    status_column: str,
    agent_slug: str,
) -> None:
    """Add the new agent to the project's agent_pipeline_mappings."""
    try:
        cursor = await db.execute(
            "SELECT agent_pipeline_mappings FROM project_settings WHERE project_id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
        if row:
            raw = row[0] if not isinstance(row, dict) else row.get("agent_pipeline_mappings", "{}")
            mappings = json.loads(raw) if raw else {}
        else:
            mappings = {}

        # Ensure the status column has a list and add the slug
        if status_column not in mappings:
            mappings[status_column] = []
        if agent_slug not in mappings[status_column]:
            mappings[status_column].append(agent_slug)

        await db.execute(
            "UPDATE project_settings SET agent_pipeline_mappings = ? WHERE project_id = ?",
            (json.dumps(mappings), project_id),
        )
        await db.commit()
        logger.info(
            "Updated pipeline mappings: added %s to %s in project %s",
            agent_slug,
            status_column,
            project_id,
        )
    except Exception as exc:
        logger.warning("Could not update pipeline mappings: %s", exc)
