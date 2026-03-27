# Research: Self-Evolving Roadmap Engine

**Feature Branch**: `001-roadmap-engine` | **Date**: 2026-03-27
**Phase**: 0 — Outline & Research

## Research Tasks

### R-001: Roadmap config storage — JSON in project_settings vs. new table

**Decision**: Store roadmap config as additional JSON fields on `ProjectBoardConfig` in the existing `project_settings` table.

**Rationale**: The existing `ProjectBoardConfig` model (in `src/models/settings.py`) already stores per-project board preferences (`column_order`, `collapsed_columns`, `show_estimates`, `queue_mode`, `auto_merge`) as JSON. Roadmap config fields (`roadmap_enabled`, `roadmap_seed`, `roadmap_batch_size`, `roadmap_pipeline_id`, `roadmap_auto_launch`, `roadmap_grace_minutes`) are semantically identical — per-project feature toggles and settings. Adding them to `ProjectBoardConfig` requires only a Pydantic model change, no schema migration, because the `project_settings` table stores the config as a JSON blob in the `board_display_config` column.

**Alternatives considered**:
- **Separate `roadmap_config` table**: Rejected because it adds unnecessary schema complexity for what is essentially 6 scalar fields. The existing pattern (JSON in `project_settings`) is proven and cached by `settings_store.py`.
- **Global settings**: Rejected because roadmap configuration is per-project by design.

---

### R-002: Audit table design — roadmap_cycles

**Decision**: Create a new `roadmap_cycles` SQLite table via migration `039_roadmap_cycles.sql` with columns: `id` (INTEGER PRIMARY KEY), `project_id` (TEXT NOT NULL), `user_id` (TEXT NOT NULL), `batch_json` (TEXT NOT NULL), `status` (TEXT NOT NULL DEFAULT 'pending'), `created_at` (TEXT NOT NULL DEFAULT ISO-8601 timestamp).

**Rationale**: Cycle audit records serve two purposes: (1) deduplication — recent cycle titles are fed back to the AI prompt to prevent repeats, and (2) history — product owners can view past cycles. These records are write-heavy (one per cycle) and read on generation (dedup query) and history (paginated list). A dedicated table with indexed `project_id` and `created_at` provides efficient queries. The `batch_json` column stores the full `RoadmapBatch` serialized as JSON for auditability.

**Alternatives considered**:
- **Store in project_settings**: Rejected because cycle logs are unbounded (grow over time) while config is fixed-size. Mixing them violates separation of concerns.
- **Flat file logs**: Rejected because SQLite provides indexed queries and transactional writes that flat files cannot.

---

### R-003: Queue-empty hook — debounce and daily cap mechanism

**Decision**: Add a roadmap trigger check at the bottom of `_dequeue_next_pipeline()` in `src/services/copilot_polling/pipeline.py`, specifically in the branch where `queued` is empty (no more pipelines to dequeue). Use an in-memory per-project debounce timestamp (`_roadmap_last_trigger: dict[str, datetime]`) and daily counter (`_roadmap_daily_count: dict[str, tuple[date, int]]`) to enforce the 5-minute debounce and 10-cycle/day cap.

**Rationale**: The existing `_dequeue_next_pipeline()` is called after every pipeline completion. When `queued` is empty, the pipeline is idle — this is exactly the trigger point for auto-launch. In-memory debounce state is acceptable because: (1) the debounce is a best-effort guard, not a critical invariant, (2) server restarts naturally reset the debounce (conservative), and (3) the daily cap resets per UTC day via a simple date check.

**Alternatives considered**:
- **Separate background task / cron**: Rejected because it adds a new execution path. Hooking into the existing dequeue flow is simpler and guaranteed to fire at the right moment (pipeline just became idle).
- **Persistent debounce state in SQLite**: Rejected — unnecessary complexity. In-memory state is sufficient; a restart simply resets the 5-minute timer (safe) and daily count resets conservatively at midnight UTC.

---

### R-004: AI prompt design — structured JSON output

**Decision**: Prompt template in `src/prompts/roadmap_generation.py` with persona "You are a product engineering lead" and structured JSON output schema. Output must be a JSON array of objects: `{title, body, rationale, priority, size}`. Use the same `CompletionProvider.complete()` interface used by existing issue generation.

**Rationale**: The existing prompt pattern (see `src/prompts/issue_generation.py`) uses system prompts with structured JSON output instructions. The roadmap prompt follows the same pattern: system prompt defines the persona, format, and constraints; user message provides the seed vision, codebase signals, and dedup list. Output is raw JSON (no markdown fences) for reliable parsing.

**Alternatives considered**:
- **Multiple AI calls (one per item)**: Rejected because a single call producing a batch is more cost-efficient and produces items that are collectively coherent (aware of each other within the batch).
- **Tool/function calling**: Rejected because the existing `CompletionProvider.complete()` returns a string; adding function calling would require interface changes. String-based JSON parsing is proven in the codebase.

---

### R-005: Duplicate prevention — title-based dedup (V1)

**Decision**: Query the last 30 cycles' item titles from `roadmap_cycles` table and include them in the AI prompt as a "do not generate" list. Exact title match only in V1.

**Rationale**: The spec explicitly states "title-based dedup via recent titles in prompt (V1); embedding similarity deferred to V2." Querying recent titles is cheap (SQLite indexed query), and including them in the prompt is a natural-language instruction that LLMs follow reliably. The 30-cycle window provides sufficient history without bloating the prompt.

**Alternatives considered**:
- **Embedding similarity**: Deferred to V2 per spec. Would require a vector store and embedding model.
- **Post-generation dedup (reject duplicates after generation)**: Rejected because it wastes AI tokens and may leave incomplete batches.

---

### R-006: Veto/skip mechanism — reuse existing blocking-queue skip

**Decision**: Delegate veto entirely to the existing pipeline skip mechanism. When a product owner vetoes a roadmap item, the system calls the existing pipeline skip/remove operation for that issue number. No new skip logic is needed.

**Rationale**: The spec explicitly states "Veto/skip: delegates entirely to existing blocking-queue skip — no new skip logic." The existing `PipelineState` tracks `queued` status, and removing a queued pipeline from the state store effectively vetoes it.

**Alternatives considered**:
- **Custom veto state on RoadmapCycleLog**: Rejected — adds redundant state. The pipeline state store is the single source of truth for whether an item is active/queued/skipped.

---

### R-007: Signal notification format — roadmap cycle completion

**Decision**: Extend `signal_delivery.py` with a `format_roadmap_notification()` helper that produces: `🗺️ Roadmap: N items queued — Title A, Title B, Title C. Reply SKIP {number} to veto.` Send via the existing `deliver_signal_notification()` flow.

**Rationale**: The existing Signal delivery infrastructure (`signal_delivery.py`, `signal_bridge.py`) handles formatting, retry, and audit. Adding a new formatter function follows the existing pattern (`format_signal_message()` exists for chat messages). The message format is specified in the spec and includes actionable veto instructions.

**Alternatives considered**:
- **New Signal delivery path**: Rejected — the existing path handles retry, audit, and delivery tracking. Reusing it avoids duplication.

---

### R-008: Grace minutes — queued-but-not-launched window

**Decision**: When `roadmap_grace_minutes > 0`, generated items are inserted into the pipeline state with `queued=True` and a `grace_until` timestamp. A check in the dequeue path skips items whose grace period hasn't expired. Default is 0 (immediate launch).

**Rationale**: The spec notes this is "not fully specified — needs clarification before implementation." The simplest approach: items enter the queue with a future-timestamp guard. The existing dequeue logic already checks `queued` state; adding a timestamp check is minimal. When `grace_minutes=0`, no timestamp is set and behavior is unchanged.

**Alternatives considered**:
- **Separate staging area**: Rejected — unnecessary complexity. The existing queue mechanism with a timestamp guard achieves the same result.
- **Defer to V2**: Considered but the implementation is simple enough for V1 given the queue infrastructure already exists.

---

### R-009: CodeGraphContext signals for generation

**Decision**: Use the existing `codegraphcontext` library (already a dependency, `≥0.2.9`) to gather codebase structure signals. Call its API to get module summaries, dependency graphs, and coverage metrics. Pass these as context in the AI prompt alongside the seed vision.

**Rationale**: The `codegraphcontext` package is already installed and used in the codebase. It provides structured codebase analysis that enriches the AI prompt with real technical context, making generated features more relevant to the actual codebase state.

**Alternatives considered**:
- **Manual codebase scanning**: Rejected — reinventing what `codegraphcontext` already provides.
- **Skip codebase context**: Rejected — the spec explicitly requires "gathers CodeGraphContext signals, repo metrics."

---

### R-010: Frontend settings panel — Roadmap section

**Decision**: Add a `RoadmapSettings` component to the existing `ProjectSettings` panel. Follow the same pattern as `queue_mode` and `auto_merge` toggles: read from `ProjectBoardConfig`, update via the existing settings API. Add `RoadmapBadge` near the queue mode toggle on the board page.

**Rationale**: The existing settings panel (`src/components/settings/ProjectSettings.tsx`) already handles board config fields. Adding roadmap fields follows the exact same pattern: form state → API call → ProjectBoardConfig update. The badge follows the existing compact UI pattern.

**Alternatives considered**:
- **Separate settings page**: Rejected — the spec says "Settings page gains a Roadmap section," not a new page.
- **Roadmap activity feed as separate page**: Noted as stretch goal, out of V1 scope per spec.

## Summary of Decisions

| ID | Topic | Decision |
|----|-------|----------|
| R-001 | Config storage | JSON fields on ProjectBoardConfig (no migration) |
| R-002 | Audit table | New `roadmap_cycles` table via migration 039 |
| R-003 | Queue-empty hook | In-memory debounce + daily cap in _dequeue_next_pipeline() |
| R-004 | AI prompt | Single CompletionProvider.complete() call, JSON array output |
| R-005 | Dedup | Title-based via recent titles in prompt (V1) |
| R-006 | Veto/skip | Delegate to existing blocking-queue skip |
| R-007 | Signal notifications | New formatter in signal_delivery.py, existing delivery path |
| R-008 | Grace minutes | Timestamp guard on queued items in pipeline state |
| R-009 | Codebase context | Use existing codegraphcontext library |
| R-010 | Frontend | RoadmapSettings in existing settings panel, RoadmapBadge on board |
