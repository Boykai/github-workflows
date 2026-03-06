# Component Interface Contracts: Solune UI Redesign

**Feature Branch**: `025-solune-ui-redesign`  
**Date**: 2026-03-06

## Layout Components

### AppLayout
```typescript
// No props — wraps React Router <Outlet />, instantiates global state
// Renders: Sidebar, TopBar, ChatPopup, <Outlet />
// Hooks used: useAuth, useProjects, useChat, useWorkflow, useAppTheme,
//             useSidebarState, useNotifications, useRecentParentIssues
```

### Sidebar
```typescript
interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  selectedProject?: { project_id: string; name: string; owner_login: string };
  recentInteractions: Array<{
    item_id: string;
    title: string;
    number?: number;
    repository?: { owner: string; name: string };
  }>;
  onProjectSelectorOpen: () => void;
}
```

### TopBar
```typescript
interface TopBarProps {
  isDarkMode: boolean;
  onToggleTheme: () => void;
  user?: { login: string; avatar_url: string };
  notifications: Array<{
    id: string;
    type: 'agent' | 'chore';
    title: string;
    timestamp: string;
    read: boolean;
  }>;
  unreadCount: number;
  onMarkAllRead: () => void;
}
```

### Breadcrumb
```typescript
// No props — derives breadcrumb segments from useLocation().pathname
// Maps path segments to labels using NAV_ROUTES constant
```

### ProjectSelector
```typescript
interface ProjectSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  projects: Array<{ project_id: string; name: string; owner_login: string }>;
  selectedProjectId?: string;
  onSelect: (projectId: string) => void;
  isLoading?: boolean;
}
```

### NotificationBell
```typescript
interface NotificationBellProps {
  notifications: Array<{
    id: string;
    type: 'agent' | 'chore';
    title: string;
    timestamp: string;
    read: boolean;
    source?: string;
  }>;
  unreadCount: number;
  onMarkAllRead: () => void;
}
```

## Page Components

### AppPage
```typescript
// No props — static welcome/landing page with CTA cards
// Uses: useNavigate() for card click navigation
```

### ProjectsPage
```typescript
// No props — reads project context from AppLayout (shared via context or props drilling)
// Hooks used: useProjectBoard, useBoardRefresh, useRealTimeSync, useAgentConfig, useAvailableAgents
// Renders: page header, toolbar, ProjectBoard, IssueDetailModal
```

### AgentsPipelinePage
```typescript
// No props — reads project context from parent
// Hooks used: useProjectBoard (for columns), useAgentConfig, useAvailableAgents, useWorkflow
// Renders: pipeline visualization, AgentConfigRow, AddAgentPopover, AgentPresetSelector, AgentSaveBar, activity feed
```

### AgentsPage
```typescript
// No props — reads project context from parent
// Hooks used: useAvailableAgents, useAgentConfig
// Renders: assignment map grid, AgentsPanel/AgentCard grid, AddAgentModal
```

### ChoresPage
```typescript
// No props — reads project context from parent
// Hooks used: useChoresList, useChoreTemplates, useCleanup
// Renders: ChoresPanel, AddChoreModal, ChoreChatFlow, CleanUpButton, CleanUpConfirmModal, CleanUpSummary, CleanUpAuditHistory
```

### SettingsPage
```typescript
interface SettingsPageProps {
  projects?: Array<{ project_id: string; name: string }>;
  selectedProjectId?: string;
}
// Hooks used: useUserSettings, useGlobalSettings
// Renders: PrimarySettings, AdvancedSettings (existing — restyled)
```

## Enhanced Existing Components

### IssueCard (Enhanced)
```typescript
// Props unchanged: { item: BoardItem; onClick: (item: BoardItem) => void }
// Visual changes only:
//   - Priority badge: filled bg with PRIORITY_COLORS mapping instead of border-only
//   - Description snippet: truncate item.body to ~80 chars
//   - Assignee: avatar + name instead of avatar only
//   - Date: render item creation/update date
//   - Label pills: pastel background colors
//   - Softer shadows, 0.5rem radius
```

### BoardColumn (Enhanced)
```typescript
// Props unchanged: { column: BoardColumnType; onCardClick: (item: BoardItem) => void }
// Visual changes:
//   - Header: already has item count badge (existing)
//   - Add "+" button in header (scaffolding — "Coming soon" tooltip)
```

### ProjectBoard (Enhanced)
```typescript
// Props unchanged: { boardData: BoardDataResponse; onCardClick: (item: BoardItem) => void }
// Visual changes:
//   - "Add new column" button after last column (scaffolding — "Coming soon" tooltip)
```
