# Quickstart: MCP Configuration Support

**Feature**: 012-mcp-settings-config  
**Date**: 2026-02-28

## Overview

This feature adds MCP (Model Context Protocol) configuration management to the Settings page. Authenticated users can add, view, and remove MCP server configurations scoped to their GitHub account.

## Prerequisites

- Docker and Docker Compose (existing dev setup)
- GitHub OAuth app configured (existing)
- Node.js 18+ and Python 3.11+ (existing)

## Development Setup

```bash
# From repo root — start all services
docker-compose up -d

# Or run frontend/backend separately for dev:
cd backend && pip install -r requirements.txt && uvicorn src.main:app --reload
cd frontend && npm install && npm run dev
```

The database migration (`006_add_mcp_configurations.sql`) runs automatically on backend startup.

## Key Files to Modify/Create

### Backend

| File | Action | Purpose |
|------|--------|---------|
| `backend/src/migrations/006_add_mcp_configurations.sql` | Create | Database table for MCP configs |
| `backend/src/models/mcp.py` | Create | Pydantic models (request/response) |
| `backend/src/services/mcp_store.py` | Create | Database CRUD operations |
| `backend/src/api/mcp.py` | Create | API endpoints (GET, POST, DELETE) |
| `backend/src/api/__init__.py` | Modify | Register MCP router |

### Frontend

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/types/index.ts` | Modify | Add MCP TypeScript types |
| `frontend/src/services/api.ts` | Modify | Add MCP API client methods |
| `frontend/src/hooks/useMcpSettings.ts` | Create | React hook for MCP state management |
| `frontend/src/components/settings/McpSettings.tsx` | Create | MCP settings UI component |
| `frontend/src/pages/SettingsPage.tsx` | Modify | Add McpSettings section |

## Implementation Order

1. **Database migration** — Create `mcp_configurations` table
2. **Backend models** — Pydantic models with validation (including SSRF check)
3. **Backend store** — CRUD operations against SQLite
4. **Backend API** — REST endpoints with auth dependency
5. **Frontend types** — TypeScript interfaces
6. **Frontend API client** — `mcpApi` methods in `api.ts`
7. **Frontend hook** — `useMcpSettings` for async state
8. **Frontend component** — `McpSettings` UI with inline feedback
9. **Settings page integration** — Add `McpSettings` to `SettingsPage`

## Testing the Feature

### Manual Testing

1. Start the app and authenticate via GitHub OAuth
2. Navigate to Settings page
3. Verify the "MCP Configurations" section appears
4. Add an MCP with name "Test MCP" and URL "https://example.com/mcp"
5. Verify it appears in the list with success feedback
6. Remove the MCP and confirm the deletion prompt
7. Verify the empty state appears when no MCPs configured

### API Testing (curl)

```bash
# List MCPs (requires session cookie)
curl -b cookies.txt http://localhost:8000/api/v1/settings/mcps

# Add an MCP
curl -b cookies.txt -X POST http://localhost:8000/api/v1/settings/mcps \
  -H "Content-Type: application/json" \
  -d '{"name": "Test MCP", "endpoint_url": "https://example.com/mcp"}'

# Delete an MCP
curl -b cookies.txt -X DELETE http://localhost:8000/api/v1/settings/mcps/{mcp_id}
```

### Validation Test Cases

- Empty name → inline error "Name is required"
- Invalid URL → inline error "Please enter a valid URL"
- Private IP URL (e.g., `http://192.168.1.1/api`) → server error "URL points to a private or reserved IP address"
- More than 25 MCPs → server error "Maximum of 25 MCP configurations per user reached"
- Expired session → re-authentication prompt
