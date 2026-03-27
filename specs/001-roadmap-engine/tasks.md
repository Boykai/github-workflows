# Tasks: Self-Evolving Roadmap Engine

**Feature Branch**: `001-roadmap-engine` | **Date**: 2026-03-27
**Phase**: Implementation

## Phase 1: Data Layer — Models & Migration

- [X] T-001: Add roadmap fields to `ProjectBoardConfig` in `src/models/settings.py` (FR-001)
- [X] T-002: Create `src/models/roadmap.py` with RoadmapItem, RoadmapBatch, RoadmapCycleLog, RoadmapCycleStatus (FR-002, FR-003)
- [X] T-003: Create migration `039_roadmap_cycles.sql` for audit/dedup table (FR-003)

## Phase 2: Settings Store

- [X] T-004: Roadmap config persistence via existing `board_display_config` JSON — no extra store helpers needed (FR-001)

## Phase 3: AI Prompt Template

- [X] T-005: Create `src/prompts/roadmap_generation.py` with system prompt and `create_roadmap_generation_prompt()` (FR-004)

## Phase 4: Generator Service

- [X] T-006: Create `src/services/roadmap/__init__.py` package (FR-004)
- [X] T-007: Implement `generate_roadmap_batch()` in `src/services/roadmap/generator.py` with config loading, seed validation, dedup, context gathering, AI call, response parsing, cycle persistence (FR-004, FR-011, FR-012, FR-013, FR-014)

## Phase 5: Launcher Service

- [X] T-008: Implement `launch_roadmap_batch()` in `src/services/roadmap/launcher.py` delegating to `execute_pipeline_launch()` (FR-005)

## Phase 6: REST API Endpoints

- [X] T-009: Create `src/api/roadmap.py` with 5 endpoints: GET/PUT config, POST generate, GET history, POST skip (FR-008)
- [X] T-010: Register roadmap router in `src/api/__init__.py` (FR-008)

## Phase 7: Queue-Empty Hook — Auto-Launch

- [X] T-011: Add `_maybe_trigger_roadmap()` with 5-min debounce and 10-cycle/day cap (FR-006, FR-007)
- [X] T-012: Hook into `_dequeue_next_pipeline()` queue-empty branch (FR-006)

## Phase 8: Signal Notifications

- [X] T-013: Add `format_roadmap_notification()` to `signal_delivery.py` (FR-009)
- [X] T-014: Add `deliver_roadmap_notification()` with fire-and-forget delivery (FR-009)

## Phase 9: Frontend

- [X] T-015: Add roadmap fields to `ProjectBoardConfig` TypeScript interface in `types/index.ts` (FR-001)
- [X] T-016: Create `RoadmapSettings.tsx` component with toggle, textarea, inputs, selectors (FR-001, FR-015)
- [X] T-017: Create `RoadmapBadge.tsx` component (Active/Idle/Generating) (FR-015)
- [X] T-018: Integrate RoadmapSettings into `ProjectSettings.tsx` (FR-001)
- [X] T-019: Integrate RoadmapBadge into `ProjectsPage.tsx` near queue mode toggle (FR-015)

## Phase 10: Unit Tests

- [X] T-020: Create `test_roadmap_models.py` — 25 tests for model validation, serialization, defaults
- [X] T-021: Create `test_roadmap_generator.py` — 13 tests for AI response parsing and prompt building
- [X] T-022: Create `test_roadmap_debounce.py` — 7 tests for debounce guards, daily cap, condition checks

## Phase 11: Validation

- [X] T-023: All 45 new backend tests pass
- [X] T-024: All existing backend tests pass (no regressions)
- [X] T-025: Frontend type-check, lint, and 1345 tests pass
- [X] T-026: Code review feedback addressed
- [X] T-027: CodeQL security scan — 0 alerts
