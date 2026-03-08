# Quickstart: Project Board — Parent Issue Hierarchy, Sub-Issue Display, Agent Pipeline Fixes & Functional Filters

**Feature**: 029-board-hierarchy-filters  
**Date**: 2026-03-07

## Prerequisites

- Python 3.12+ with pip
- Node.js 20+ with npm
- GitHub personal access token with `repo` and `project` scopes
- Access to a GitHub Project with parent issues that have sub-issues

## Backend Verification

```bash
cd backend

# Install dependencies
python -m pip install -e ".[dev]"

# Type check
pyright

# Lint
python -m ruff check src/

# Run tests
python -m pytest tests/ -v

# Start backend server
python -m uvicorn src.main:app --reload --port 8000
```

## Frontend Verification

```bash
cd frontend

# Install dependencies
npm install

# Type check
npx tsc --noEmit

# Lint
npx eslint src/

# Run tests
npx vitest run

# Start dev server
npm run dev
```

## Full Stack Verification

```bash
# From repository root
docker compose up --build
```

## Manual Verification Checklist

### 1. Parent-Only Board View (FR-001)

- [ ] Load a project board with parent issues that have sub-issues
- [ ] Confirm ONLY parent issues appear as top-level cards in all columns
- [ ] Confirm no sub-issues appear as standalone cards in any column
- [ ] Verify issue count in column headers reflects parent-only count
- [ ] Load a project board where all issues are sub-issues (no parents) → verify empty state message

### 2. Collapsible Sub-Issues (FR-002, FR-003)

- [ ] Find a parent issue card with sub-issues
- [ ] Confirm sub-issue section is collapsed by default
- [ ] Confirm toggle shows chevron (▶) and count badge (e.g., "3 sub-issues")
- [ ] Click toggle → sub-issue list expands; chevron changes to ▼
- [ ] Each sub-issue tile shows: state icon (○ open, ✓ closed), title, agent name, model name
- [ ] Click toggle again → sub-issue list collapses
- [ ] Find a parent issue with zero sub-issues → confirm no toggle is visible
- [ ] Find a sub-issue with no assigned agent → confirm "Unassigned" is displayed
- [ ] Test rapid toggle clicks → no visual flickering

### 3. Label Chips on Parent Cards (FR-004)

- [ ] Find a parent issue with labels assigned on GitHub
- [ ] Confirm all labels appear as colored chips on the card
- [ ] Confirm chip colors match GitHub label colors
- [ ] Confirm chip text shows label name
- [ ] Find a parent issue with no labels → confirm no label section is rendered
- [ ] Find a parent issue with 5+ labels → confirm labels wrap to next line
- [ ] Hover over a label with a long name → confirm full name shown in tooltip

### 4. Scrollable Columns (FR-005)

- [ ] Load a project board with a column containing 15+ parent issue cards
- [ ] Scroll within that column → confirm only that column scrolls
- [ ] Confirm other columns' scroll positions are unaffected
- [ ] Confirm page-level scroll does not trigger
- [ ] Load a board where all columns have few items → confirm no scrollbars visible

### 5. Agent Pipeline Model & Tool Count (FR-006, FR-007)

- [ ] Load a project with an Agent Pipeline configured
- [ ] Verify every agent tile shows its model name (e.g., "Claude 3.5 Sonnet")
- [ ] Verify every agent tile shows its tool count (e.g., "5 tools")
- [ ] Verify no agent tiles have missing model name or tool count when the agent has them configured
- [ ] Find an agent with 0 tools → confirm "0 tools" or graceful omission
- [ ] Find an agent with no model configured → confirm model field omitted gracefully

### 6. Custom Pipeline Label (FR-008)

- [ ] With no saved pipeline selected, confirm the saved-pipeline selector shows its generic label
- [ ] Select a saved pipeline configuration → confirm the selector surfaces the configuration name
- [ ] Make a manual change to the pipeline (add/remove agent) → confirm the selector reverts to its generic label
- [ ] Select a saved pipeline, refresh the page → confirm the selector still surfaces the configuration name
- [ ] If the saved pipeline is deleted while active → confirm the selector reverts to its generic label

### 7. Filter Controls (FR-009)

- [ ] Click "Filter" button → confirm filter panel opens
- [ ] Apply filter by label → confirm only matching parent issues are displayed
- [ ] Apply filter by assignee → confirm only matching parent issues are displayed
- [ ] Apply multiple filters (label AND assignee) → confirm AND logic (both must match)
- [ ] Clear all filters → confirm full board restored
- [ ] Confirm Filter button shows active indicator when filters are applied
- [ ] Confirm active indicator removed when filters cleared
- [ ] Apply filter that matches no issues → confirm "No issues match" empty state

### 8. Sort Controls (FR-010)

- [ ] Click "Sort" button → confirm sort panel opens
- [ ] Sort by "Title A-Z" → confirm cards in each column are alphabetically ordered
- [ ] Sort by "Title Z-A" → confirm reverse alphabetical order
- [ ] Sort by "Priority — Highest First" → confirm P1 before P2 before P3
- [ ] Sort by "Created — Newest First" → confirm newest issues first
- [ ] Clear sort → confirm default order restored
- [ ] Confirm Sort button shows active indicator when sort is applied

### 9. Group By Controls (FR-011)

- [ ] Click "Group By" button → confirm group panel opens
- [ ] Group by "Assignee" → confirm cards within each column are organized under assignee headers
- [ ] Confirm unassigned items appear under "Unassigned" group
- [ ] Group by "Milestone" → confirm cards organized under milestone headers
- [ ] Group by "Label" → confirm cards organized under label headers
- [ ] Remove grouping → confirm default layout restored
- [ ] Confirm Group By button shows active indicator when grouping is active

### 10. Persistence (FR-012)

- [ ] Apply a filter, sort, and group-by configuration
- [ ] Refresh the page
- [ ] Confirm the filter, sort, and group-by selections are restored
- [ ] Switch to a different project → confirm controls reset (per-project persistence)
- [ ] Switch back to original project → confirm original selections restored

### 11. Active State Indicators (FR-013)

- [ ] With no controls active → all toolbar buttons show default (no highlight) state
- [ ] Apply a filter → Filter button shows accent highlight/badge
- [ ] Apply a sort → Sort button shows accent highlight/badge
- [ ] Apply a group → Group By button shows accent highlight/badge
- [ ] Clear all controls → all indicators removed

## Expected Test Coverage

| Test Type | Location | Coverage |
|-----------|----------|----------|
| Backend model tests | `backend/tests/` | Label model, BoardItem with labels, milestone, timestamps |
| Backend service tests | `backend/tests/` | Sub-issue filtering from all columns, label parsing |
| Frontend component tests | `frontend/src/components/board/__tests__/` | IssueCard collapse toggle, label chip rendering |
| Frontend hook tests | `frontend/src/hooks/` | useBoardControls filter/sort/group transforms and persistence guards |
| E2E tests | Optional | Full board interaction with filter/sort/group |
