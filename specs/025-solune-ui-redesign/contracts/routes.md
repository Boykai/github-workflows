# Route Contract: Solune UI Redesign

**Feature Branch**: `025-solune-ui-redesign`  
**Date**: 2026-03-06

> This feature is frontend-only. No new backend API endpoints are created.
> Existing backend APIs at `/api/v1/*` are consumed as-is.
> This contract defines the client-side route structure.

## Client-Side Routes

| Path | Page Component | Auth Required | Layout | Description |
|---|---|---|---|---|
| `/` | `AppPage` | Yes | `AppLayout` | Welcome/landing with quick-access cards |
| `/projects` | `ProjectsPage` | Yes | `AppLayout` | Project board (Kanban) with enhanced cards |
| `/pipeline` | `AgentsPipelinePage` | Yes | `AppLayout` | Pipeline visualization + agent config + activity |
| `/agents` | `AgentsPage` | Yes | `AppLayout` | Agent assignment map + catalog |
| `/chores` | `ChoresPage` | Yes | `AppLayout` | Chore catalog + creation + cleanup |
| `/settings` | `SettingsPage` | Yes | `AppLayout` | Application settings (restyled) |
| `/login` | `LoginPage` | No | None | Solune-branded login (implicit — unauthenticated gate) |
| `*` | `NotFoundPage` | No | `AppLayout` | 404 route fallback |

## Route Configuration

```tsx
<BrowserRouter>
  <Routes>
    {/* Unauthenticated */}
    <Route path="/login" element={<LoginPage />} />
    
    {/* Authenticated — wrapped in AppLayout */}
    <Route element={<AuthGate><AppLayout /></AuthGate>}>
      <Route index element={<AppPage />} />
      <Route path="projects" element={<ProjectsPage />} />
      <Route path="pipeline" element={<AgentsPipelinePage />} />
      <Route path="agents" element={<AgentsPage />} />
      <Route path="chores" element={<ChoresPage />} />
      <Route path="settings" element={<SettingsPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Route>
  </Routes>
</BrowserRouter>
```

## Navigation Items (Sidebar)

| Order | Path | Label | Icon (Lucide) |
|---|---|---|---|
| 1 | `/` | App | `LayoutDashboard` |
| 2 | `/projects` | Projects | `Kanban` |
| 3 | `/pipeline` | Agents Pipeline | `GitBranch` |
| 4 | `/agents` | Agents | `Bot` |
| 5 | `/chores` | Chores | `ListChecks` |
| 6 | `/settings` | Settings | `Settings` |

## Backend API Endpoints (Existing — No Changes)

The following existing endpoints are consumed by the frontend. None are modified.

| Endpoint | Method | Used By |
|---|---|---|
| `/api/v1/auth/github` | GET | Login redirect |
| `/api/v1/auth/callback` | GET | OAuth callback |
| `/api/v1/auth/me` | GET | useAuth |
| `/api/v1/auth/logout` | POST | useAuth |
| `/api/v1/projects` | GET | useProjects |
| `/api/v1/projects/{id}/board` | GET | useProjectBoard |
| `/api/v1/projects/{id}/board/move` | POST | Drag-and-drop |
| `/api/v1/chat/send` | POST | useChat |
| `/api/v1/chat/history` | GET | useChat |
| `/api/v1/workflow/config` | GET/PUT | useWorkflow, useAgentConfig |
| `/api/v1/workflow/agents` | GET | useAvailableAgents |
| `/api/v1/chores` | GET/POST | useChoresList |
| `/api/v1/chores/{id}` | GET/PUT/DELETE | Chore CRUD |
| `/api/v1/tasks/*` | Various | Task proposals |
| `/api/v1/settings/user` | GET/PUT | useSettings |
| `/api/v1/settings/global` | GET/PUT | useSettings |
| `/api/v1/cleanup/*` | Various | useCleanup |
| WebSocket `/api/v1/ws/{project_id}` | WS | useRealTimeSync |
