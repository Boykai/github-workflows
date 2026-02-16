# API & Implementation Contracts: Standalone Project Board Page

**Feature**: 003-project-board | **Date**: 2026-02-16  
**Purpose**: Define exact API contracts, file modifications, and new files required for implementation

---

## Contract 1: Backend API Endpoints

### 1.1 GET /api/v1/project-board/projects

**Purpose**: List all available GitHub Projects V2 for the authenticated user  
**Authentication**: Session cookie (existing `get_session_dep`)  
**Response Model**: `BoardProjectListResponse`

**Request**:
```
GET /api/v1/project-board/projects
Cookie: session=<session_token>
```

**Response (200 OK)**:
```json
{
  "projects": [
    {
      "project_id": "PVT_kwHOABC123",
      "title": "Sprint Board",
      "description": "Current sprint tracking",
      "url": "https://github.com/users/user/projects/1",
      "item_count": 24,
      "status_columns": [
        {
          "name": "Todo",
          "color": "GRAY",
          "option_id": "f75ad846"
        },
        {
          "name": "In Progress",
          "color": "YELLOW",
          "option_id": "47fc9ee4"
        },
        {
          "name": "Done",
          "color": "GREEN",
          "option_id": "98236657"
        }
      ]
    }
  ]
}
```

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session
- `500 Internal Server Error` — GitHub API failure

---

### 1.2 GET /api/v1/project-board/{project_id}/board

**Purpose**: Fetch full board data for a specific project, grouped by status columns  
**Authentication**: Session cookie  
**Response Model**: `BoardDataResponse`

**Request**:
```
GET /api/v1/project-board/PVT_kwHOABC123/board
Cookie: session=<session_token>
```

**Response (200 OK)**:
```json
{
  "project_id": "PVT_kwHOABC123",
  "title": "Sprint Board",
  "columns": [
    {
      "name": "Todo",
      "color": "GRAY",
      "option_id": "f75ad846",
      "description": null,
      "item_count": 3,
      "total_estimate": 13,
      "items": [
        {
          "item_id": "PVTI_item1",
          "content_id": "I_issue1",
          "issue_number": 42,
          "title": "Add user authentication",
          "body": "Implement OAuth2 flow...",
          "state": "OPEN",
          "url": "https://github.com/owner/repo/issues/42",
          "repo_name": "repo",
          "repo_full_name": "owner/repo",
          "status": "Todo",
          "priority": "P1",
          "size": "L",
          "estimate": 8,
          "assignees": [
            {
              "login": "developer1",
              "avatar_url": "https://avatars.githubusercontent.com/u/12345"
            }
          ],
          "linked_prs": [
            {
              "pr_number": 55,
              "title": "feat: Add OAuth2 login flow",
              "state": "OPEN",
              "url": "https://github.com/owner/repo/pull/55"
            }
          ]
        }
      ]
    }
  ]
}
```

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session
- `404 Not Found` — Project not found or user doesn't have access
- `500 Internal Server Error` — GitHub API failure

---

### 1.3 POST /api/v1/project-board/linked-prs

**Purpose**: Fetch linked pull requests for a batch of issue content IDs  
**Authentication**: Session cookie  
**Request Model**: `LinkedPRsRequest`  
**Response Model**: `LinkedPRsResponse`

**Request**:
```
POST /api/v1/project-board/linked-prs
Cookie: session=<session_token>
Content-Type: application/json

{
  "content_ids": ["I_issue1", "I_issue2", "I_issue3"]
}
```

**Response (200 OK)**:
```json
{
  "linked_prs": {
    "I_issue1": [
      {
        "pr_number": 55,
        "title": "feat: Add OAuth2 login flow",
        "state": "OPEN",
        "url": "https://github.com/owner/repo/pull/55"
      }
    ],
    "I_issue2": [],
    "I_issue3": [
      {
        "pr_number": 60,
        "title": "fix: Database connection pool",
        "state": "MERGED",
        "url": "https://github.com/owner/repo/pull/60"
      }
    ]
  }
}
```

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session
- `422 Unprocessable Entity` — Invalid content_ids format
- `500 Internal Server Error` — GitHub API failure

---

## Contract 2: Backend Pydantic Models

### New File: `backend/src/models/project_board.py`

```python
from pydantic import BaseModel


class BoardAssignee(BaseModel):
    login: str
    avatar_url: str


class LinkedPullRequest(BaseModel):
    pr_number: int
    title: str
    state: str  # "OPEN", "CLOSED", "MERGED"
    url: str


class BoardIssueCard(BaseModel):
    item_id: str
    content_id: str | None = None
    issue_number: int | None = None
    title: str
    body: str | None = None
    state: str | None = None
    url: str | None = None
    repo_name: str | None = None
    repo_full_name: str | None = None
    status: str | None = None
    priority: str | None = None
    size: str | None = None
    estimate: float | None = None
    assignees: list[BoardAssignee] = []
    linked_prs: list[LinkedPullRequest] = []


class BoardStatusColumn(BaseModel):
    name: str
    color: str
    option_id: str
    description: str | None = None
    item_count: int = 0
    total_estimate: float | None = None
    items: list[BoardIssueCard] = []


class BoardProject(BaseModel):
    project_id: str
    title: str
    description: str | None = None
    url: str
    item_count: int = 0
    status_columns: list[BoardStatusColumnSummary] = []


class BoardStatusColumnSummary(BaseModel):
    name: str
    color: str
    option_id: str


class BoardProjectListResponse(BaseModel):
    projects: list[BoardProject] = []


class BoardDataResponse(BaseModel):
    project_id: str
    title: str
    columns: list[BoardStatusColumn] = []


class LinkedPRsRequest(BaseModel):
    content_ids: list[str]


class LinkedPRsResponse(BaseModel):
    linked_prs: dict[str, list[LinkedPullRequest]] = {}
```

---

## Contract 3: Frontend TypeScript Types

### Modified File: `frontend/src/types/index.ts`

**New types to add**:

```typescript
// ============ Project Board Types ============

export interface BoardAssignee {
  login: string;
  avatar_url: string;
}

export interface LinkedPullRequest {
  pr_number: number;
  title: string;
  state: 'OPEN' | 'CLOSED' | 'MERGED';
  url: string;
}

export interface BoardIssueCard {
  item_id: string;
  content_id: string | null;
  issue_number: number | null;
  title: string;
  body: string | null;
  state: string | null;
  url: string | null;
  repo_name: string | null;
  repo_full_name: string | null;
  status: string | null;
  priority: string | null;
  size: string | null;
  estimate: number | null;
  assignees: BoardAssignee[];
  linked_prs: LinkedPullRequest[];
}

export interface BoardStatusColumn {
  name: string;
  color: string;
  option_id: string;
  description: string | null;
  item_count: number;
  total_estimate: number | null;
  items: BoardIssueCard[];
}

export interface BoardProject {
  project_id: string;
  title: string;
  description: string | null;
  url: string;
  item_count: number;
  status_columns: { name: string; color: string; option_id: string }[];
}

export interface BoardProjectListResponse {
  projects: BoardProject[];
}

export interface BoardDataResponse {
  project_id: string;
  title: string;
  columns: BoardStatusColumn[];
}

export interface LinkedPRsRequest {
  content_ids: string[];
}

export interface LinkedPRsResponse {
  linked_prs: Record<string, LinkedPullRequest[]>;
}
```

---

## Contract 4: Frontend API Client Extensions

### Modified File: `frontend/src/services/api.ts`

**New API methods to add**:

```typescript
// ============ Project Board API ============

export const projectBoardApi = {
  listProjects(): Promise<BoardProjectListResponse> {
    return request<BoardProjectListResponse>('/project-board/projects');
  },

  getBoardData(projectId: string): Promise<BoardDataResponse> {
    return request<BoardDataResponse>(`/project-board/${projectId}/board`);
  },

  getLinkedPRs(contentIds: string[]): Promise<LinkedPRsResponse> {
    return request<LinkedPRsResponse>('/project-board/linked-prs', {
      method: 'POST',
      body: JSON.stringify({ content_ids: contentIds }),
    });
  },
};
```

---

## Contract 5: New Frontend Components

### 5.1 New File: `frontend/src/components/project-board/ProjectBoardPage.tsx`

**Props**: None (page-level component)  
**State**: `selectedProjectId`, `isModalOpen`, `selectedCard`  
**Data**: Uses `useProjectBoard` hook for data fetching and auto-refresh  
**Behavior**:
- Renders project dropdown (from `BoardProject[]`)
- Renders `BoardColumn` for each status column
- Manages modal open/close state
- Provides "Back to Chat" navigation

### 5.2 New File: `frontend/src/components/project-board/BoardColumn.tsx`

**Props**: `column: BoardStatusColumn`, `onCardClick: (card: BoardIssueCard) => void`  
**Behavior**:
- Renders column header: colored status dot, name, item count, total estimate
- Renders scrollable list of `BoardIssueCard` components

### 5.3 New File: `frontend/src/components/project-board/BoardIssueCard.tsx`

**Props**: `card: BoardIssueCard`, `onClick: () => void`  
**Behavior**:
- Renders repo name + issue number
- Renders issue title
- Renders assignee avatar images (max 3, +N overflow)
- Renders linked PR badge (count, colored by state)
- Renders priority/size/estimate badges with color coding

### 5.4 New File: `frontend/src/components/project-board/IssueDetailModal.tsx`

**Props**: `card: BoardIssueCard`, `isOpen: boolean`, `onClose: () => void`  
**Behavior**:
- Modal overlay with click-outside and Escape key to close
- Displays full issue details: title, body, status, priority, size, estimate
- Lists assignees with avatars and usernames
- Lists linked PRs with state badges
- "Open on GitHub" link (opens in new tab)
- Close button

---

## Contract 6: Cross-Cutting Concerns

### 6.1 Backend Router Registration

**Modified File**: `backend/src/api/__init__.py`

Add import and include for project board router:
```python
from src.api.project_board import router as project_board_router
router.include_router(project_board_router, prefix="/project-board", tags=["project-board"])
```

### 6.2 Frontend Navigation

**Modified File**: `frontend/src/App.tsx`

Add state-based routing to switch between chat view and project board view:
- Add `currentPage` state: `'chat' | 'project-board'`
- Conditionally render `ProjectBoardPage` when `currentPage === 'project-board'`
- Pass `onNavigate` callback to sidebar/header for switching pages

### 6.3 Sidebar Navigation Link

**Modified File**: `frontend/src/components/sidebar/ProjectSidebar.tsx`

Add navigation link/button to switch to project board page:
- New button in sidebar header or footer area
- Calls `onNavigate('project-board')` callback

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change:

### Backend Files (No Changes)
- `backend/src/services/github_auth.py` — Auth service unchanged
- `backend/src/api/auth.py` — Auth endpoints unchanged
- `backend/src/api/tasks.py` — Tasks endpoints unchanged
- `backend/src/api/chat.py` — Chat endpoints unchanged
- `backend/src/config.py` — No new config settings needed (uses existing `CACHE_TTL_SECONDS`)
- `backend/tests/` — Tests optional per constitution

### Frontend Files (No Changes)
- `frontend/src/hooks/useAuth.ts` — Auth hook unchanged
- `frontend/src/hooks/useProjects.ts` — Existing projects hook unchanged
- `frontend/src/hooks/useChat.ts` — Chat hook unchanged
- `frontend/src/components/chat/` — Chat components unchanged
- `frontend/src/components/auth/` — Auth components unchanged

---

## Verification Contract

After implementing changes, verify the following:

### Project Board Route (FR-001)
- [ ] Navigate to project board page via sidebar navigation
- [ ] Board page renders with project dropdown

### Project List (FR-002)
- [ ] Dropdown lists all available GitHub Projects
- [ ] Selecting a project loads the board

### Board Columns (FR-003, FR-004)
- [ ] Columns appear for each status field
- [ ] Each column shows colored status dot, name, count, aggregate estimate

### Issue Cards (FR-005, FR-006, FR-007)
- [ ] Cards show repo name/issue number, title, assignee avatars
- [ ] Cards show linked PR badge when applicable
- [ ] Cards show priority/size/estimate badges with colors

### Detail Modal (FR-008, FR-009)
- [ ] Clicking a card opens the detail modal
- [ ] Modal shows expanded issue information
- [ ] "Open on GitHub" link works in new tab
- [ ] Modal closes on click-outside, Escape, or close button

### Auto-Refresh (FR-010, FR-011)
- [ ] Board refreshes every 15 seconds
- [ ] Refresh pauses when modal is open

### Loading/Error States (FR-012, FR-013)
- [ ] Loading indicator shown while fetching data
- [ ] Error message with retry button shown on failure

### Styling (FR-016)
- [ ] Board styling matches app's design system
- [ ] Dark mode supported

---

## Contract Compliance Checklist

- [x] All API endpoints documented with request/response examples
- [x] All new files and their purposes listed
- [x] All modified files and their changes documented
- [x] Pydantic models defined for all backend entities
- [x] TypeScript types defined for all frontend entities
- [x] Component props and behavior specified
- [x] Cross-cutting concerns identified (router registration, navigation)
- [x] Out-of-scope files explicitly listed
- [x] Verification criteria defined for all functional requirements

**Status**: ✅ **CONTRACTS COMPLETE** - Ready for quickstart generation
