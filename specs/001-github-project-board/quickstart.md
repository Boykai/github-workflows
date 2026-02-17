# Quickstart: Real-Time GitHub Project Board

**Date**: 2026-02-16  
**Feature**: 001-github-project-board

## Overview

This feature adds a `/project-board` route displaying a Kanban-style board with real-time GitHub Project V2 data. Users select a project from a dropdown, view issues organized by status columns with rich metadata, and click cards for details.

## Prerequisites

- Docker and Docker Compose installed
- GitHub OAuth app configured (existing setup)
- GitHub account with access to at least one GitHub Project V2

## Quick Start

```bash
# 1. Start the application
docker-compose up -d

# 2. Open the app
open http://localhost:5173

# 3. Authenticate with GitHub

# 4. Navigate to Project Board (sidebar link)

# 5. Select a project from the dropdown
```

## Development Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"

# Run development server
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/board/projects` | List available projects with status fields |
| GET | `/api/v1/board/projects/{id}` | Get board data (columns + items) for a project |

## Key Components

### Backend

| File | Purpose |
|------|---------|
| `backend/src/api/board.py` | Board API router |
| `backend/src/models/board.py` | Pydantic models for board data |
| `backend/src/services/github_projects.py` | Extended GraphQL queries |

### Frontend

| File | Purpose |
|------|---------|
| `frontend/src/pages/ProjectBoardPage.tsx` | Page component with project selector |
| `frontend/src/components/board/ProjectBoard.tsx` | Board layout with columns |
| `frontend/src/components/board/BoardColumn.tsx` | Column with header and cards |
| `frontend/src/components/board/IssueCard.tsx` | Issue card with metadata badges |
| `frontend/src/components/board/IssueDetailModal.tsx` | Detail modal for issue |
| `frontend/src/hooks/useProjectBoard.ts` | Data fetching hook with 15s polling |

## Testing

### Backend Tests

```bash
cd backend
pytest tests/unit/test_board.py -v
```

### Frontend Tests

```bash
cd frontend
npm run test
```

## Architecture Notes

### Data Flow

```
GitHub Projects V2 GraphQL API
         │
         ▼
   Backend (FastAPI)
   /api/v1/board/*
         │
         ▼
   Frontend (React)
   useProjectBoard hook
   (15s polling interval)
         │
         ▼
   ProjectBoard components
```

### Polling Strategy

- Initial fetch on project selection
- Auto-refresh every 15 seconds
- Subtle loading indicator during refresh
- Retains previous data on error
- Uses React Query's `refetchInterval`

### Rate Limits

- 240 requests/hour per user (15s polling)
- Well within GitHub's 5,000 points/hour limit
- Exponential backoff on rate limit errors
