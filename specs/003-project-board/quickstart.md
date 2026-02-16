# Quickstart Guide: Standalone Project Board Page

**Feature**: 003-project-board | **Date**: 2026-02-16  
**Estimated Time**: 3-4 hours  
**Prerequisites**: Git access, Node.js 18+, Python 3.11+, text editor, GitHub token with `read:project` and `repo` scopes

## Overview

This guide walks through implementing the standalone project board page feature. The implementation spans both backend (FastAPI endpoints + GraphQL queries) and frontend (React components + TypeScript types). The feature adds a Kanban-style board view of GitHub Projects V2 data with auto-refresh and detail modals.

**Complexity**: ⭐⭐⭐ Moderate-High (3/5)  
**Risk Level**: Moderate  
**Rollback**: Remove new files + revert modifications to 3 existing files

---

## Step 1: Verify Current State

**Purpose**: Confirm you're working with expected baseline

### 1.1 Check Current Branch

```bash
cd /home/runner/work/github-workflows/github-workflows
git status
```

**Expected**: On branch `copilot/add-project-board-page-again` or similar feature branch

### 1.2 Verify Repository Structure

```bash
ls backend/src/api/
ls frontend/src/components/
```

**Expected**: Backend has `projects.py`, `tasks.py`, etc. Frontend has `sidebar/`, `chat/`, etc.

### 1.3 Install Dependencies

```bash
# Backend
cd backend && pip install -e ".[dev]"

# Frontend
cd ../frontend && npm install
```

---

## Step 2: Create Backend Pydantic Models

**Purpose**: Define data models for board API responses (FR-015)

### 2.1 Create `backend/src/models/project_board.py`

Create new file with Pydantic models for:
- `BoardAssignee` — login, avatar_url
- `LinkedPullRequest` — pr_number, title, state, url
- `BoardIssueCard` — all issue card fields
- `BoardStatusColumn` — column metadata + items
- `BoardProject` — project metadata + status column summaries
- Request/response models for all 3 endpoints

### 2.2 Verify Models

```bash
cd backend
python -c "from src.models.project_board import BoardDataResponse; print('OK')"
```

**Expected**: `OK` with no import errors

---

## Step 3: Extend GitHub Projects Service

**Purpose**: Add GraphQL queries for board data and linked PRs (FR-014)

### 3.1 Add New GraphQL Queries to `backend/src/services/github_projects.py`

Add two new query constants:
1. `GET_BOARD_DATA_QUERY` — fetches project items with field values, assignees, and repo info
2. `GET_LINKED_PRS_QUERY` — fetches linked PRs for batched issue IDs using timeline items

### 3.2 Add New Service Methods

Add methods to `GitHubProjectsService`:
1. `get_board_data(access_token, project_id)` — executes board data query, parses response into `BoardStatusColumn` list
2. `get_linked_prs(access_token, content_ids)` — executes linked PRs query, returns dict mapping content IDs to PR lists

### 3.3 Verify Service Methods

```bash
cd backend
python -c "from src.services.github_projects import github_projects_service; print('OK')"
```

---

## Step 4: Create Backend API Endpoints

**Purpose**: Add FastAPI routes for project board data (FR-014)

### 4.1 Create `backend/src/api/project_board.py`

Create new router with 3 endpoints:
1. `GET /projects` — list available projects (reuses existing service)
2. `GET /{project_id}/board` — fetch and return grouped board data
3. `POST /linked-prs` — fetch linked PRs for content IDs

### 4.2 Register Router in `backend/src/api/__init__.py`

Add:
```python
from src.api.project_board import router as project_board_router
router.include_router(project_board_router, prefix="/project-board", tags=["project-board"])
```

### 4.3 Verify Endpoints

```bash
cd backend
python -c "from src.api.project_board import router; print(f'Routes: {len(router.routes)}')"
```

**Expected**: `Routes: 3`

---

## Step 5: Extend Frontend TypeScript Types

**Purpose**: Add type definitions for board data (FR-015)

### 5.1 Add Types to `frontend/src/types/index.ts`

Add new interfaces at the end of the file:
- `BoardAssignee`
- `LinkedPullRequest`
- `BoardIssueCard`
- `BoardStatusColumn`
- `BoardProject`
- `BoardProjectListResponse`
- `BoardDataResponse`
- `LinkedPRsRequest`
- `LinkedPRsResponse`

### 5.2 Verify Types

```bash
cd frontend
npx tsc --noEmit
```

**Expected**: No type errors

---

## Step 6: Extend Frontend API Client

**Purpose**: Add API methods for project board endpoints

### 6.1 Add `projectBoardApi` to `frontend/src/services/api.ts`

Add new API object with 3 methods:
- `listProjects()` — GET /project-board/projects
- `getBoardData(projectId)` — GET /project-board/{projectId}/board
- `getLinkedPRs(contentIds)` — POST /project-board/linked-prs

### 6.2 Add Required Imports

Add new types to the import statement at the top of `api.ts`.

---

## Step 7: Create `useProjectBoard` Hook

**Purpose**: Centralize data fetching and auto-refresh logic (FR-010, FR-011)

### 7.1 Create `frontend/src/hooks/useProjectBoard.ts`

Implement hook with:
- `useQuery` for project list with key `['board-projects']`
- `useQuery` for board data with key `['board-data', projectId]` and `refetchInterval: isModalOpen ? false : 15000`
- State for `selectedProjectId`, `isModalOpen`, `selectedCard`
- Functions for `selectProject`, `openModal`, `closeModal`

### 7.2 Verify Hook

```bash
cd frontend
npx tsc --noEmit
```

---

## Step 8: Create Frontend Components

**Purpose**: Build the Kanban board UI (FR-001 through FR-009)

### 8.1 Create Component Directory

```bash
mkdir -p frontend/src/components/project-board
```

### 8.2 Create `ProjectBoardPage.tsx`

Main page component that:
- Uses `useProjectBoard` hook
- Renders project dropdown (select element)
- Renders board columns in horizontal layout
- Shows loading/error states
- Manages modal state

### 8.3 Create `BoardColumn.tsx`

Column component that:
- Renders colored status dot
- Renders column name, item count, aggregate estimate
- Renders scrollable list of `BoardIssueCard` components
- Accepts `onCardClick` callback

### 8.4 Create `BoardIssueCard.tsx`

Card component that:
- Renders repo name and issue number
- Renders issue title (truncated)
- Renders up to 3 assignee avatars (+N overflow)
- Renders linked PR badge (if any)
- Renders priority/size/estimate badges with color coding
- Clickable (triggers `onClick` prop)

### 8.5 Create `IssueDetailModal.tsx`

Modal component that:
- Renders overlay with centered modal content
- Shows full issue details (title, body, status, assignees, linked PRs, badges)
- "Open on GitHub" link opens in new tab
- Closes on: click outside, Escape key, close button
- Renders nothing when `isOpen` is false

---

## Step 9: Add Navigation and Routing

**Purpose**: Wire up page navigation (FR-001)

### 9.1 Modify `frontend/src/App.tsx`

- Import `ProjectBoardPage`
- Add `currentPage` state: `'chat' | 'project-board'`
- Conditionally render `ProjectBoardPage` or existing chat view
- Pass `onNavigate` callback to sidebar

### 9.2 Modify `frontend/src/components/sidebar/ProjectSidebar.tsx`

- Add `onNavigateToBoard` prop
- Add navigation button/link to project board page

---

## Step 10: Add Board Styles

**Purpose**: Style the board to match the app's design system (FR-016)

### 10.1 Add Styles to `frontend/src/App.css`

Add CSS classes for:
- `.project-board-page` — page layout
- `.board-project-selector` — dropdown styling
- `.board-container` — horizontal scrollable board
- `.board-column` — column layout with header
- `.board-column-header` — status dot, name, counts
- `.board-issue-card` — card styling with hover effects
- `.board-card-badges` — priority/size/estimate badges with colors
- `.board-assignee-avatars` — avatar image layout
- `.board-pr-badge` — linked PR indicator
- `.issue-detail-modal` — modal overlay and content
- Status dot color classes for each GitHub color name

---

## Step 11: Manual Verification

**Purpose**: Confirm changes work in running application

### 11.1 Start Development Servers

```bash
# Terminal 1: Backend
cd backend && uvicorn src.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

### 11.2 Verify Board Page

1. Navigate to the app in browser
2. Click "Project Board" in sidebar
3. Select a project from dropdown
4. Verify columns render with correct status names and colors
5. Verify issue cards show repo name, title, badges
6. Click an issue card — verify modal opens with details
7. Click "Open on GitHub" — verify link opens in new tab
8. Close modal — verify board returns to normal
9. Wait 15 seconds — verify auto-refresh indicator appears

### 11.3 Build Check

```bash
cd frontend && npm run build
cd ../backend && python -m py_compile src/api/project_board.py
```

**Expected**: Both build and compile succeed

---

## Troubleshooting

### Issue: GitHub API returns 401

**Symptom**: Board fails to load with authentication error  
**Solution**: Verify GitHub token has `read:project` and `repo` scopes. Re-authenticate if needed.

### Issue: Board shows no columns

**Symptom**: Project selected but no columns render  
**Solution**: Verify the GitHub Project has a "Status" field configured. Projects without a Status field will show an empty board.

### Issue: Linked PRs not showing

**Symptom**: Issue cards show no PR badges despite having linked PRs  
**Solution**: Check the linked PRs endpoint is registered correctly. Verify issues have PRs that reference them (via "Fixes #N" or manual linking).

### Issue: Auto-refresh not working

**Symptom**: Board doesn't update after 15 seconds  
**Solution**: Verify `refetchInterval` is set to `15000` in the `useQuery` config. Check browser console for network errors.

### Issue: TypeScript errors

**Symptom**: `npm run build` fails with type errors  
**Solution**: Run `npx tsc --noEmit` to see specific errors. Ensure all new types are exported from `types/index.ts`.

---

## Rollback Procedure

If issues arise, revert changes via:

### Files to Remove (New)
```bash
rm backend/src/models/project_board.py
rm backend/src/api/project_board.py
rm frontend/src/hooks/useProjectBoard.ts
rm -rf frontend/src/components/project-board/
```

### Files to Revert (Modified)
```bash
git checkout HEAD -- backend/src/api/__init__.py
git checkout HEAD -- frontend/src/types/index.ts
git checkout HEAD -- frontend/src/services/api.ts
git checkout HEAD -- frontend/src/App.tsx
git checkout HEAD -- frontend/src/App.css
git checkout HEAD -- frontend/src/components/sidebar/ProjectSidebar.tsx
```

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: /project-board route accessible via sidebar navigation
- [ ] **FR-002**: Dropdown lists all available GitHub Projects
- [ ] **FR-003**: Kanban board renders with status columns
- [ ] **FR-004**: Columns show colored dots, names, counts, estimates
- [ ] **FR-005**: Cards show repo name, issue number, title, assignee avatars
- [ ] **FR-006**: Cards show linked PR badge when applicable
- [ ] **FR-007**: Cards show priority/size/estimate badges with colors
- [ ] **FR-008**: Clicking card opens detail modal
- [ ] **FR-009**: Modal has "Open on GitHub" link
- [ ] **FR-010**: Auto-refresh every 15 seconds
- [ ] **FR-011**: Auto-refresh pauses when modal is open
- [ ] **FR-012**: Loading indicators shown during data fetch
- [ ] **FR-013**: Error messages with retry on failure
- [ ] **FR-014**: Backend endpoints proxy GitHub API correctly
- [ ] **FR-015**: TypeScript types extended with all new fields
- [ ] **FR-016**: Styling matches app design system

---

## Success Criteria

✅ **Feature Complete** when:
1. User can navigate to project board from sidebar
2. User can select a project and see Kanban board
3. Issue cards display all required data fields
4. Detail modal opens with full information and GitHub link
5. Board auto-refreshes every 15 seconds
6. Loading and error states work correctly
7. Styling matches existing app design system

**Total Time**: ~3-4 hours for experienced developer

---

## Next Steps

After completing this guide:

1. **Review**: Self-review changes in git diff
2. **Test**: Run `npm run build` and `ruff check .` to verify no issues
3. **Verify**: Manual testing of all user scenarios
4. **Commit**: Push changes to feature branch
5. **Handoff**: Ready for speckit.tasks agent to generate task list

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (11 steps)
- [x] Prerequisites documented
- [x] Time estimate included (3-4 hours)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Rollback procedure defined
- [x] Validation checklist aligned with spec FRs
- [x] Success criteria clearly stated

**Status**: ✅ **QUICKSTART COMPLETE** - Ready for implementation by speckit.tasks
