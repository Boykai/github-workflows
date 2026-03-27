# Quickstart: Self-Evolving Roadmap Engine

**Feature Branch**: `001-roadmap-engine` | **Date**: 2026-03-27
**Phase**: 1 — Design & Contracts

## Overview

This guide provides a step-by-step implementation order for the Self-Evolving Roadmap Engine feature. Each section maps to the user stories in `spec.md` and references the concrete artifacts in `data-model.md` and `contracts/roadmap-api.yaml`.

## Implementation Order

### Step 1: Data Layer — Models & Migration (Foundation)

**Files to create/modify**:
- `src/models/roadmap.py` — NEW: Pydantic models
- `src/models/settings.py` — MODIFY: Extend `ProjectBoardConfig`
- `src/migrations/039_roadmap_cycles.sql` — NEW: Audit table

**What to do**:
1. Add roadmap fields to `ProjectBoardConfig` in `src/models/settings.py`:
   - `roadmap_enabled: bool = False`
   - `roadmap_seed: str = ""`
   - `roadmap_batch_size: int = Field(default=3, ge=1, le=10)`
   - `roadmap_pipeline_id: str | None = None`
   - `roadmap_auto_launch: bool = False`
   - `roadmap_grace_minutes: int = Field(default=0, ge=0, le=1440)`

2. Create `src/models/roadmap.py` with `RoadmapItem`, `RoadmapBatch`, `RoadmapCycleLog`, `RoadmapCycleStatus` as defined in `data-model.md`.

3. Create migration `039_roadmap_cycles.sql` with the schema from `data-model.md`.

**Validates**: FR-001, FR-002, FR-003

---

### Step 2: Settings Store Helpers

**Files to modify**:
- `src/services/settings_store.py` — MODIFY: Add roadmap config helpers

**What to do**:
1. Add `get_roadmap_config(db, project_id) -> ProjectBoardConfig` helper that reads the board config JSON and returns the Pydantic model (reuse existing `load_board_config` if available, or follow the same pattern as `is_queue_mode_enabled()`).
2. Add `save_roadmap_config(db, project_id, config_update)` helper that merges roadmap fields into the existing board config JSON and saves.

**Validates**: FR-001

---

### Step 3: REST Endpoints — Config & History (P1, P6)

**Files to create/modify**:
- `src/api/roadmap.py` — NEW: FastAPI router
- `src/main.py` — MODIFY: Register router

**What to do**:
1. Create `src/api/roadmap.py` with a `router = APIRouter(prefix="/roadmap", tags=["Roadmap"])`.
2. Implement `GET /roadmap/config` — reads ProjectBoardConfig, returns roadmap fields.
3. Implement `PUT /roadmap/config` — validates and merges roadmap fields.
4. Implement `GET /roadmap/history` — queries `roadmap_cycles` table with pagination.
5. Register the router in `src/main.py`.

**Dependencies**: Use `get_session_dep` and `verify_project_access` from existing auth infrastructure.

**Validates**: FR-008 (partial), FR-001

---

### Step 4: AI Prompt Template

**Files to create**:
- `src/prompts/roadmap_generation.py` — NEW: Prompt template

**What to do**:
1. Create system prompt with persona: "You are a product engineering lead analyzing a codebase to propose the next batch of high-impact features."
2. Define JSON output schema: array of `{title, body, rationale, priority, size}`.
3. Include instructions for:
   - Aligning with the seed vision
   - Avoiding titles in the dedup list
   - Providing concrete, actionable issue bodies
   - Assigning realistic priority and size
4. Create factory function `create_roadmap_generation_prompt(seed, batch_size, codebase_context, recent_titles)` that returns `list[dict[str, str]]` (system + user messages).

**Pattern**: Follow `src/prompts/issue_generation.py` structure.

**Validates**: FR-004 (partial)

---

### Step 5: Generator Service (P2)

**Files to create**:
- `src/services/roadmap/__init__.py` — NEW: Package init
- `src/services/roadmap/generator.py` — NEW: Generation logic

**What to do**:
1. Implement `generate_roadmap_batch(project_id, user_id, access_token) -> RoadmapBatch`:
   - Load roadmap config from settings
   - Validate: seed non-empty (FR-014), pipeline exists (FR-011)
   - Query recent cycle titles from `roadmap_cycles` (last 30 cycles) for dedup (FR-013)
   - Gather CodeGraphContext signals (FR-004)
   - Build prompt via `create_roadmap_generation_prompt()`
   - Call `CompletionProvider.complete()` with the prompt
   - Parse JSON response into `RoadmapBatch` (FR-004)
   - Handle parse failures: log error, record cycle as "failed" (FR-012)
   - On success: insert cycle record into `roadmap_cycles` with status "completed"
   - Return the batch

**Validates**: FR-004, FR-011, FR-012, FR-013, FR-014

---

### Step 6: Launcher Service (P2)

**Files to create**:
- `src/services/roadmap/launcher.py` — NEW: Launch logic

**What to do**:
1. Implement `launch_roadmap_batch(batch, project_id, session) -> list[int]`:
   - Iterate `batch.items`
   - For each item, call `execute_pipeline_launch()` with:
     - `project_id=project_id`
     - `issue_description=item.body` (title derived by the existing logic)
     - `pipeline_id=config.roadmap_pipeline_id`
     - `session=session`
   - Collect and return created issue numbers
   - Zero new issue-creation code — fully delegated

**Validates**: FR-005

---

### Step 7: Generate & Skip Endpoints (P2, P3)

**Files to modify**:
- `src/api/roadmap.py` — ADD: Generate and skip endpoints

**What to do**:
1. Implement `POST /roadmap/generate`:
   - Call `generate_roadmap_batch()`
   - Call `launch_roadmap_batch()` (or return batch for manual review if grace_minutes > 0)
   - Return `GenerateResponse` with cycle_id and batch
2. Implement `POST /roadmap/items/{issue_number}/skip`:
   - Delegate to existing pipeline state removal/skip mechanism
   - Return `SkipResponse`

**Validates**: FR-008

---

### Step 8: Queue-Empty Hook — Auto-Launch (P4)

**Files to modify**:
- `src/services/copilot_polling/pipeline.py` — MODIFY: Hook in `_dequeue_next_pipeline()`

**What to do**:
1. In `_dequeue_next_pipeline()`, after the `if not queued: return` branch (line ~65), add the roadmap auto-launch check:
   ```python
   # Queue is empty — check if roadmap auto-launch should trigger
   if not queued:
       await _maybe_trigger_roadmap(access_token, project_id)
       return
   ```
2. Implement `_maybe_trigger_roadmap(access_token, project_id)`:
   - Load roadmap config
   - Check `roadmap_enabled` and `roadmap_auto_launch`
   - Check debounce: `_roadmap_last_trigger[project_id]` ≥ 5 minutes ago
   - Check daily cap: `_roadmap_daily_count[project_id]` < 10 for today's UTC date
   - If all checks pass: call `generate_roadmap_batch()` + `launch_roadmap_batch()`
   - Update debounce timestamp and daily counter
   - Fire-and-forget via `asyncio.create_task()` to avoid blocking the dequeue path

**Validates**: FR-006, FR-007

---

### Step 9: Signal Notifications (P5)

**Files to modify**:
- `src/services/signal_delivery.py` — MODIFY: Add roadmap notification

**What to do**:
1. Add `format_roadmap_notification(batch: RoadmapBatch, project_name: str) -> str`:
   ```
   🗺️ Roadmap: {N} items queued — {Title A, Title B, …}.
   Reply SKIP {number} to veto.
   ```
2. Add `deliver_roadmap_notification(batch, project_id, user_id)`:
   - Format the message
   - Call existing `deliver_signal_notification()` flow
   - Fire-and-forget (non-blocking)

**Validates**: FR-009, FR-010

---

### Step 10: Frontend — Settings Panel (P1)

**Files to create/modify**:
- `src/components/settings/RoadmapSettings.tsx` — NEW: Settings section
- `src/components/settings/ProjectSettings.tsx` — MODIFY: Include RoadmapSettings
- `src/types/index.ts` — MODIFY: Add roadmap fields to TypeScript types

**What to do**:
1. Add roadmap fields to `ProjectBoardConfig` TypeScript type in `src/types/index.ts`.
2. Create `RoadmapSettings` component with:
   - Enable/disable toggle
   - Seed vision textarea
   - Batch size number input (1–10)
   - Pipeline dropdown selector (use existing pipeline list)
   - Auto-launch toggle
   - Grace minutes input (optional, advanced)
3. Integrate into `ProjectSettings.tsx` as a new section.
4. Follow existing patterns: controlled form state → API call on save.

**Validates**: FR-001, FR-015 (partial)

---

### Step 11: Frontend — Board Badge (P1)

**Files to create/modify**:
- `src/components/board/RoadmapBadge.tsx` — NEW: Compact state badge
- `src/pages/ProjectsPage.tsx` — MODIFY: Include badge

**What to do**:
1. Create `RoadmapBadge` component that displays roadmap state: "Active", "Idle", "Generating…"
2. Place near the queue mode toggle on the board page.
3. Derive state from: roadmap_enabled (from settings), active pipeline count, and generation status.

**Validates**: FR-015

## Key Dependencies Between Steps

```text
Step 1 (Models) ─────────┐
                          ├──→ Step 3 (Config API)
Step 2 (Settings Store) ──┘         │
                                    ├──→ Step 10 (Frontend Settings)
Step 4 (Prompt Template) ───┐       │
                            ├──→ Step 5 (Generator)
Step 1 (Models) ────────────┘       │
                                    ├──→ Step 7 (Generate API)
Step 5 (Generator) ─────────────────┘       │
                                            ├──→ Step 8 (Auto-launch Hook)
Step 6 (Launcher) ──────────────────────────┘
                                            │
Step 9 (Signal) ← depends on Step 5        │
Step 11 (Badge) ← depends on Step 10       │
```

## Verification Checklist

- [ ] ProjectBoardConfig persists roadmap fields via existing JSON column
- [ ] roadmap_cycles table created by migration 039
- [ ] GET/PUT /roadmap/config round-trips all 6 config fields
- [ ] POST /roadmap/generate returns valid batch matching batch_size
- [ ] Generated titles do not duplicate recent cycle titles
- [ ] POST /roadmap/items/{issue_number}/skip removes item from queue
- [ ] GET /roadmap/history returns cycles in reverse chronological order
- [ ] Auto-launch triggers after 5-minute idle debounce
- [ ] Auto-launch respects 10-cycle/day cap
- [ ] Signal notification sent with correct format on cycle completion
- [ ] Settings page Roadmap section saves and reloads correctly
- [ ] Board badge reflects live roadmap state
