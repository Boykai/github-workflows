# Data Model: Solune UI Redesign

**Feature Branch**: `025-solune-ui-redesign`  
**Date**: 2026-03-06

> This feature is frontend-only. No new backend entities are created. This document describes the **frontend data model** — component props, state shapes, and type additions needed for the redesign.

## Existing Entities (Preserved — No Changes)

These types from `frontend/src/types/index.ts` are used as-is:

| Entity | Key Fields | Used By |
|---|---|---|
| `BoardItem` | item_id, title, priority?, assignees, status, body?, sub_issues | IssueCard, ProjectBoard |
| `BoardColumn` | status (BoardStatusOption), items (BoardItem[]), item_count | BoardColumn component |
| `BoardCustomFieldValue` | name, color? | Priority/size badges |
| `BoardProject` | project_id, name, owner_login, status_field | Project selector |
| `BoardDataResponse` | columns (BoardColumn[]), items_total_count | ProjectBoard |
| `ChatMessage` | role, content, timestamp | ChatPopup, ChatInterface |
| `AITaskProposal` | id, task, status | Chat proposals |
| `WorkflowConfiguration` | agent_mappings | AgentConfigRow |
| `AvailableAgent` | name, source, enabled | AgentCard, catalog |
| `User` | login, avatar_url, selected_project_id | Auth, avatar |

## New Types (Frontend Only)

### NavRoute

Defines the 6 application routes for the sidebar and router configuration.

```typescript
interface NavRoute {
  path: string;           // e.g., '/', '/projects', '/pipeline'
  label: string;          // e.g., 'App', 'Projects', 'Agents Pipeline'
  icon: LucideIcon;       // Lucide icon component for sidebar
}
```

### SidebarState

Shape of the sidebar's persisted + runtime state.

```typescript
interface SidebarState {
  isCollapsed: boolean;   // Persisted in localStorage('sidebar-collapsed')
}
```

### RecentInteraction

A recent parent issue displayed in the sidebar.

```typescript
interface RecentInteraction {
  item_id: string;        // BoardItem.item_id
  title: string;          // BoardItem.title
  number?: number;        // BoardItem.number
  repository?: {          // BoardItem.repository
    owner: string;
    name: string;
  };
  updatedAt: string;      // Derived from board data or issue metadata
}
```

### Notification

Unified notification item combining agent and chore events.

```typescript
interface Notification {
  id: string;             // Unique identifier
  type: 'agent' | 'chore';
  title: string;          // e.g., "Agent 'triage' completed on column 'Backlog'"
  timestamp: string;      // ISO 8601
  read: boolean;
  source?: string;        // Agent name or chore name
}
```

### PriorityConfig

Maps priority values to display colors (used by IssueCard and other priority indicators).

```typescript
const PRIORITY_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  P0: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400', label: 'Critical' },
  P1: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-400', label: 'High' },
  P2: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-400', label: 'Medium' },
  P3: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-400', label: 'Low' },
};
```

## New Hooks

### useRecentParentIssues

```typescript
function useRecentParentIssues(boardData?: BoardDataResponse): RecentInteraction[]
```

- Derives recent parent issues from board columns
- Filters to items with sub_issues (parent issues)
- Sorts by most recently updated, limits to 8
- Returns empty array when boardData is undefined

### useNotifications

```typescript
function useNotifications(): {
  notifications: Notification[];
  unreadCount: number;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
}
```

- Aggregates agent workflow events and chore completion events
- Tracks read/unread state via localStorage timestamp
- Derives unread count from events newer than last-viewed

### useSidebarState

```typescript
function useSidebarState(): {
  isCollapsed: boolean;
  toggle: () => void;
}
```

- Reads initial state from `localStorage('sidebar-collapsed')`
- Persists on toggle
- Returns boolean + toggle function

## Component Props (New Components)

### AppLayout

```typescript
// No props — uses React Router Outlet and auth context internally
```

### Sidebar

```typescript
interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  selectedProject?: BoardProject;
  recentInteractions: RecentInteraction[];
  onProjectSelectorOpen: () => void;
}
```

### TopBar

```typescript
interface TopBarProps {
  isDarkMode: boolean;
  onToggleTheme: () => void;
  user?: User;
  notifications: Notification[];
  unreadCount: number;
  onMarkAllRead: () => void;
}
```

### Breadcrumb

```typescript
// No props — reads from React Router useLocation() and useMatches()
```

### ProjectSelector

```typescript
interface ProjectSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  projects: BoardProject[];
  selectedProjectId?: string;
  onSelect: (projectId: string) => void;
}
```

### NotificationBell

```typescript
interface NotificationBellProps {
  notifications: Notification[];
  unreadCount: number;
  onMarkAllRead: () => void;
}
```

## State Transitions

### Sidebar Collapse

```
User clicks toggle → isCollapsed flips → localStorage updated → CSS transition plays → layout reflows
```

### Auth Gate

```
App mounts → useAuth checks → 
  if unauthenticated: show LoginPage (no layout shell), store intended path in sessionStorage
  if authenticated: show AppLayout with Outlet → React Router renders matched route
  on login success: redirect to stored path or '/'
```

### Project Selection

```
User clicks project name in sidebar → ProjectSelector opens → 
  User selects project → onSelect fires → useProjects.selectProject() → 
  board data refetches → sidebar project name updates → selector closes
```

## Relationships

```
AppLayout
├── Sidebar
│   ├── NavLinks (from NavRoute[])
│   ├── RecentInteractions (from useRecentParentIssues)
│   └── ProjectSelector (from useProjects)
├── TopBar
│   ├── Breadcrumb (from useLocation)
│   ├── NotificationBell (from useNotifications)
│   ├── ThemeToggle (from useAppTheme)
│   └── UserAvatar (from useAuth)
├── <Outlet /> (React Router renders matched page)
└── ChatPopup (from useChat, useWorkflow — global)
```
