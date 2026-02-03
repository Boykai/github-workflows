# GitHub Projects Chat Interface

A web-based chat interface for managing GitHub Projects V2 through natural language interactions. Users can authenticate via GitHub OAuth, select projects, create tasks via conversational AI, and update task statuses - all through a simple chat interface.

## Features

- **GitHub OAuth Authentication**: Secure login with GitHub OAuth 2.0
- **Project Selection**: Browse and select from your GitHub Projects V2 boards
- **Natural Language Task Creation**: Describe tasks in plain English; AI generates structured GitHub tasks
- **Status Updates via Chat**: Update task status using natural language commands
- **Real-Time Sync**: Live updates via WebSocket with polling fallback
- **Responsive UI**: Modern React interface with TanStack Query for state management

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │────▶│  GitHub API     │
│  React + Vite   │     │    FastAPI      │     │  GraphQL V2     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Azure OpenAI   │
                        │  (Task Gen AI)  │
                        └─────────────────┘
```

## Prerequisites

- Node.js 18+
- Python 3.11+
- GitHub OAuth App credentials (see [GitHub OAuth Setup](#github-oauth-setup))
- Azure OpenAI API credentials (optional, for AI task generation)

## GitHub OAuth Setup

To enable GitHub login, you need to create a GitHub OAuth App:

1. Go to **GitHub Settings** → **Developer settings** → **OAuth Apps** → **New OAuth App**
   (Direct link: https://github.com/settings/developers)

2. Fill in the application details:
   - **Application name**: `Projects Chat` (or any name you prefer)
   - **Homepage URL**: `http://localhost:3003`
   - **Authorization callback URL**: `http://localhost:8000/api/v1/auth/github/callback`

3. Click **Register application**

4. On the next page:
   - Copy the **Client ID**
   - Click **Generate a new client secret** and copy the secret

5. Add these values to your `backend/.env` file:
   ```
   GITHUB_CLIENT_ID=your_client_id_here
   GITHUB_CLIENT_SECRET=your_client_secret_here
   ```

> **Note:** Keep your client secret secure! Never commit it to version control.

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd codeagentworkflows
```

### 2. Configure Environment

Copy the example environment files and fill in your credentials:

```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env
```

**Required Environment Variables:**

Backend (`backend/.env`):
```env
# GitHub OAuth (Required - see GitHub OAuth Setup section)
GITHUB_CLIENT_ID=your_github_oauth_client_id
GITHUB_CLIENT_SECRET=your_github_oauth_client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/auth/github/callback

# Azure OpenAI (Optional - for AI task generation)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Session configuration
SESSION_SECRET_KEY=generate_a_random_32_char_string

# Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:3003,http://localhost:5173,http://localhost:3000
FRONTEND_URL=http://localhost:3003

# Cache configuration
CACHE_TTL_SECONDS=300
```

Frontend (`frontend/.env`) - Optional:
```env
VITE_API_BASE_URL=/api/v1
VITE_BACKEND_URL=http://localhost:8000/api/v1
```

### 3. Install Dependencies

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

**Frontend:**
```bash
cd frontend
npm install
```

### 4. Run Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 5. Access the Application

Open http://localhost:3003 in your browser (or the port shown in the Vite output).

> **Note:** The frontend runs on port 3003 by default (configured in the Vite proxy). If port 3003 is busy, Vite will automatically use the next available port.

## Docker Setup

Build and run with Docker Compose:

```bash
docker-compose up --build
```

Access at http://localhost:3003

## Running Tests

### Backend Tests
```bash
cd backend
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pytest tests/ -v
```

### Frontend E2E Tests
```bash
cd frontend
npm run test:e2e          # Run all E2E tests
npm run test:e2e:headed   # Run with browser visible
npm run test:e2e:report   # View test report
```

## API Documentation

When running in development mode, API documentation is available at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Usage

### Authentication Flow
1. Click "Login with GitHub"
2. Authorize the OAuth app
3. You'll be redirected back, logged in

### Creating Tasks
1. Select a project from the dropdown
2. Type a task description in the chat, e.g.:
   - "Create a task to fix the login bug on mobile"
   - "Add a task for implementing dark mode"
3. Review the AI-generated task proposal
4. Click "Confirm" to create the task in GitHub

### Updating Task Status
1. Type a status change command, e.g.:
   - "Move the login bug task to In Progress"
   - "Mark 'Implement dark mode' as Done"
2. Confirm the status change proposal

## Project Structure

```
codeagentworkflows/
├── backend/
│   ├── src/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # Pydantic models
│   │   ├── services/     # Business logic
│   │   ├── prompts/      # AI prompt templates
│   │   ├── config.py     # Configuration
│   │   └── main.py       # FastAPI app
│   ├── tests/            # Backend tests
│   └── pyproject.toml    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── services/     # API client
│   │   └── types/        # TypeScript types
│   ├── package.json      # NPM dependencies
│   └── vite.config.ts    # Vite configuration
├── specs/                # Feature specifications
└── docker-compose.yml    # Docker orchestration
```

## Development

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Linting and Formatting

```bash
# Backend
cd backend
ruff check .
black .

# Frontend
cd frontend
npm run lint
npm run format
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Troubleshooting

### Common Issues

**OAuth callback fails / Login doesn't work:**
- Verify you have created a GitHub OAuth App (see [GitHub OAuth Setup](#github-oauth-setup))
- Ensure `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` are correctly set in `backend/.env`
- Verify `GITHUB_REDIRECT_URI` matches your GitHub OAuth app settings exactly
- Check that `FRONTEND_URL` in `.env` matches your frontend URL (e.g., `http://localhost:3003`)
- Ensure cookies are enabled in your browser
- Restart the backend server after updating `.env`

**"401 Unauthorized" after GitHub login:**
- The session cookie may not be set correctly
- Check browser developer tools → Application → Cookies for `session_id`
- Ensure the backend `CORS_ORIGINS` includes your frontend URL

**Azure OpenAI errors:**
- Check your `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_API_KEY` are correct
- Verify the deployment name matches your Azure configuration
- Azure OpenAI is optional - the app works without it (AI features disabled)

**Rate limiting:**
- GitHub API has rate limits; the app tracks remaining calls
- If limits are hit, wait for the reset window

**WebSocket connection issues:**
- The app automatically falls back to polling
- Check browser console for connection errors

**Port already in use:**
- Kill existing processes: `lsof -ti:8000 | xargs kill -9` (backend) or `lsof -ti:3003 | xargs kill -9` (frontend)
- Or let Vite automatically use the next available port
