# Quickstart: Project Page UX Overhaul

**Feature Branch**: `028-project-page-ux`
**Date**: 2026-03-07

## Prerequisites

- Docker Compose running (`docker compose up -d`)
- GitHub project with at least 3 columns and 5+ issues (some with sub-issues)
- At least one saved pipeline configuration in the project
- Browser with DevTools (Chrome recommended)

## Verification Commands

### Backend

```bash
# Run all backend tests
cd backend && pip install -e ".[dev]" && pytest tests/ -x -v

# Run specific sub-issue filter tests (once created)
cd backend && pytest tests/unit/test_board_filter.py -x -v

# Lint backend
cd backend && ruff check src/ && pyright src/
```

### Frontend

```bash
# Install dependencies (including new react-markdown, remark-gfm)
cd frontend && npm install

# Run all frontend tests
cd frontend && npx vitest run

# Run specific formatAgentName tests (once created)
cd frontend && npx vitest run src/tests/utils/formatAgentName.test.ts

# Lint frontend
cd frontend && npx eslint src/ && npx tsc --noEmit

# Build frontend
cd frontend && npm run build
```

### Full Stack

```bash
# Build and run everything
docker compose up --build -d

# Verify the app is running
curl http://localhost:3000/api/health
```

## Manual Verification Checklist

### 1. Drag/Drop Fix (FR-011, FR-012)

- [ ] Open project page with agent pipeline
- [ ] Click and hold an agent tile — verify tile stays under cursor (NO teleport/jump)
- [ ] Drag agent tile to different column — verify smooth movement
- [ ] Drop agent tile — verify it lands in correct column
- [ ] Repeat 10 times — verify zero teleport occurrences
- [ ] Drag an issue card between kanban columns — verify smooth drag/drop
- [ ] Test on touch device (or Chrome touch simulation) — verify drag works with delay

### 2. Pipeline Restyling (FR-001)

- [ ] Compare Agent Pipeline section with Pipeline Stages on `/pipeline` page
- [ ] Verify: lighter borders (`border-border/60`), reduced visual weight
- [ ] Verify: consistent spacing (`gap-3`), rounded corners (`rounded-[1.2rem]`)
- [ ] Verify: `celestial-panel` class applied to container

### 3. Agent Metadata & Names (FR-002, FR-003, FR-004)

- [ ] Verify agent tile shows formatted name (e.g., "Spec Kit - Tasks" not "speckit.tasks")
- [ ] Verify agent tile shows model name (e.g., "GPT-4o") if configured
- [ ] Verify agent tile shows tool count (e.g., "3 tools") if tools assigned
- [ ] Verify agent with no model/tools shows name only (no empty metadata)
- [ ] Verify `display_name` takes precedence over slug formatting

### 4. Pipeline Config Selector (FR-005, FR-006)

- [ ] Open Agent Pipeline preset selector
- [ ] Verify saved pipeline configurations appear alongside built-in presets
- [ ] Select a saved configuration — verify pipeline updates
- [ ] Navigate away and return — verify selection persists
- [ ] Create a new issue — verify it inherits selected pipeline config

### 5. Markdown Rendering (FR-008)

- [ ] Select a GitHub Issue with Markdown body
- [ ] Verify headings render with proper sizes
- [ ] Verify code blocks render with monospace font and background
- [ ] Verify lists (bullet and numbered) render correctly
- [ ] Verify bold, italic, links render correctly
- [ ] Verify long descriptions scroll within container (not break layout)
- [ ] Verify issue with empty body shows no description section

### 6. Done Column Filter (FR-007)

- [ ] View the "Done" kanban column
- [ ] Verify only parent issues appear (no sub-issues)
- [ ] Verify issue count is accurate (excludes sub-issues)
- [ ] Verify sub-issues still appear in their parent's detail view

### 7. Remove Add Column (FR-009)

- [ ] View the project board
- [ ] Verify NO "+ Add column" button exists

### 8. Unified Layout (FR-010)

- [ ] Verify Agent Pipeline columns align with kanban columns vertically
- [ ] Resize browser window — verify alignment maintained at all widths > 1024px
- [ ] Verify both sections span full page width
- [ ] Verify column count matches between pipeline and kanban

### 9. Drop Target Indicators (FR-013)

- [ ] During drag, hover over valid drop target
- [ ] Verify visual indicator (border highlight or background change)
- [ ] Verify indicator disappears when drag leaves the target

## Expected Test Coverage

| Area | Test Type | File |
|------|-----------|------|
| `formatAgentName` | Unit test | `frontend/src/tests/utils/formatAgentName.test.ts` |
| Sub-issue filter | Unit test | `backend/tests/unit/test_board_filter.py` |
| Agent tile rendering | Visual verification | Manual |
| Drag/drop interaction | Manual testing | Manual |
| Markdown rendering | Visual verification | Manual |
| Layout alignment | Visual verification | Manual |
