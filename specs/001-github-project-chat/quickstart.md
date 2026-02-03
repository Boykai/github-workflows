# Quickstart: GitHub Projects Chat Interface

**Date**: 2026-01-30
**Feature**: 001-github-project-chat

## Prerequisites

- Python 3.11+
- Node.js 18+ with npm
- GitHub account with at least one Project V2
- GitHub OAuth App credentials (Client ID + Secret)
- Azure OpenAI deployment (endpoint + API key)

## 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd codeagentworkflows

# Checkout feature branch
git checkout 001-github-project-chat
```

## 2. Backend Setup

### Install Dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configure Environment

Create `backend/.env`:

```env
# GitHub OAuth
GITHUB_CLIENT_ID=your_github_oauth_client_id
GITHUB_CLIENT_SECRET=your_github_oauth_client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/auth/github/callback

# Azure OpenAI
AZURE_AI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_AI_KEY=your_azure_openai_api_key
AZURE_AI_DEPLOYMENT_NAME=gpt-4o

# Session
SESSION_SECRET_KEY=generate_a_secure_random_key_here
SESSION_EXPIRE_HOURS=8

# Server
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:5173
```

### Create GitHub OAuth App

1. Go to GitHub → Settings → Developer Settings → OAuth Apps
2. Click "New OAuth App"
3. Fill in:
   - **Application name**: GitHub Projects Chat (Dev)
   - **Homepage URL**: http://localhost:5173
   - **Authorization callback URL**: http://localhost:8000/api/v1/auth/github/callback
4. Copy Client ID and generate Client Secret
5. Add to `.env` file

### Run Backend

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Verify at: http://localhost:8000/docs (OpenAPI docs)

## 3. Frontend Setup

### Install Dependencies

```bash
cd frontend
npm install
```

### Configure Environment

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

### Run Frontend

```bash
npm run dev
```

Access at: http://localhost:5173

## 4. End-to-End Test

### User Story 1: Authentication

1. Open http://localhost:5173
2. Click "Connect with GitHub"
3. Authorize the OAuth application
4. Verify you're redirected back and see your GitHub username

### User Story 1: Project Selection

1. After authentication, open the project dropdown
2. Verify you see your GitHub Projects (org/user/repo types)
3. Select a project
4. Verify the sidebar shows project board with tasks

### User Story 2: Task Creation

1. In the chat input, type: "Create a task to set up CI/CD pipeline with GitHub Actions"
2. Verify AI generates a task proposal with title and description
3. Click "Confirm" (or edit first)
4. Verify task appears in GitHub Project with "Todo" status

### User Story 3: Status Update (P2)

1. Type: "Move task 'Set up CI/CD pipeline' to In Progress"
2. Verify AI identifies the task and shows confirmation
3. Confirm the status change
4. Verify sidebar updates to reflect new status

## 5. Development Commands

### Backend

```bash
# Run tests
pytest

# Run with auto-reload
uvicorn src.main:app --reload

# Format code
black src/
isort src/

# Type check
mypy src/
```

### Frontend

```bash
# Run dev server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Lint
npm run lint

# Type check
npm run type-check
```

## 6. API Quick Reference

### Authentication Flow

```bash
# 1. Initiate OAuth
curl http://localhost:8000/api/v1/auth/github
# Returns redirect to GitHub

# 2. After callback, get current user
curl http://localhost:8000/api/v1/auth/me \
  -H "Cookie: session_id=YOUR_SESSION_COOKIE"
```

### Project Operations

```bash
# List projects
curl http://localhost:8000/api/v1/projects \
  -H "Cookie: session_id=YOUR_SESSION"

# Select project
curl -X POST http://localhost:8000/api/v1/projects/select \
  -H "Cookie: session_id=YOUR_SESSION" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "PVT_xxx"}'
```

### Chat Operations

```bash
# Send message
curl -X POST http://localhost:8000/api/v1/chat/messages \
  -H "Cookie: session_id=YOUR_SESSION" \
  -H "Content-Type: application/json" \
  -d '{"content": "Create a task for implementing user login"}'

# Confirm proposal
curl -X POST http://localhost:8000/api/v1/chat/proposals/{proposal_id}/confirm \
  -H "Cookie: session_id=YOUR_SESSION"
```

## 7. Troubleshooting

### OAuth Callback Error

**Problem**: GitHub redirects back with error
**Solution**: Check GITHUB_REDIRECT_URI matches exactly what's in GitHub OAuth App settings

### CORS Error in Browser

**Problem**: Browser blocks API requests
**Solution**: Ensure CORS_ORIGINS in backend .env includes frontend URL (http://localhost:5173)

### Azure OpenAI 401

**Problem**: AI requests fail with authentication error
**Solution**: 
1. Verify AZURE_AI_ENDPOINT format: `https://<resource-name>.openai.azure.com`
2. Check AZURE_AI_KEY is correct
3. Ensure deployment exists with name matching AZURE_AI_DEPLOYMENT_NAME

### GitHub GraphQL Rate Limit

**Problem**: Project list or task operations fail
**Solution**: Check GitHub API rate limit at https://api.github.com/rate_limit with your token

## 8. Next Steps

After completing quickstart validation:

1. Run `/speckit.tasks` to generate implementation task list
2. Implement foundational phase (project structure, dependencies)
3. Implement User Story 1 (authentication + project selection)
4. Implement User Story 2 (task creation via AI)
5. (Optional) Implement User Story 3 (status updates)
6. (Optional) Implement User Story 4 (real-time sync)
