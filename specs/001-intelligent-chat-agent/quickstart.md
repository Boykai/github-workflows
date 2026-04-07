# Quickstart: Intelligent Chat Agent (Microsoft Agent Framework)

**Feature**: 001-intelligent-chat-agent | **Date**: 2026-04-07

## Prerequisites

- Python 3.12+
- Node.js 20+ (frontend)
- Docker & Docker Compose (for containerized deployment)
- GitHub OAuth app credentials (for Copilot provider)
- *Optional*: Azure OpenAI resource (for Azure provider)

## 1. Install Dependencies

### Backend

```bash
cd solune/backend

# Install agent framework packages
pip install agent-framework-core>=1.0.0
pip install agent-framework-github-copilot --pre   # Preview until GA
pip install agent-framework-azure-ai>=1.0.0
pip install sse-starlette>=2.0.0                    # SSE streaming support

# Or via pyproject.toml (recommended — packages are added to dependencies):
pip install -e ".[dev]"
```

### Frontend

No new dependencies required. Streaming uses native browser `ReadableStream` API.

## 2. Configuration

The agent feature uses the **same environment variables** as the existing AI service. No new configuration is required.

### Required (existing)

```env
# .env
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
SESSION_SECRET_KEY=your_session_secret

# AI Provider (unchanged)
AI_PROVIDER=copilot          # or "azure_openai"
COPILOT_MODEL=gpt-4o         # Model for Copilot provider
```

### Optional (existing — for Azure provider)

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_azure_key
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### Behavior Flags (existing)

- `ai_enhance=true` (request body): Uses the intelligent agent (default)
- `ai_enhance=false` (request body): Bypasses agent, uses simple title-only generation

## 3. Run the Application

### Development (local)

```bash
# Backend
cd solune/backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd solune/frontend
npm run dev
```

### Docker

```bash
docker compose up --build
```

## 4. Verify the Agent

### Basic Chat (non-streaming)

```bash
# After authenticating and selecting a project in the UI:
curl -X POST http://localhost:8000/api/v1/chat/messages \
  -H "Content-Type: application/json" \
  -H "Cookie: session_id=<your-session-cookie>" \
  -d '{"content": "Create a task for fixing the login page", "ai_enhance": true}'
```

Expected: Agent returns a `ChatMessage` with `action_type: "task_create"` and a proposal in `action_data`.

### Streaming Chat

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/messages/stream \
  -H "Content-Type: application/json" \
  -H "Cookie: session_id=<your-session-cookie>" \
  -d '{"content": "Create a task for adding unit tests"}'
```

Expected: SSE events stream progressively:
```
data: {"type": "token", "content": "I'll"}
data: {"type": "token", "content": " create"}
data: {"type": "action", "action_type": "task_create", "action_data": {...}}
data: {"type": "done", "message_id": "uuid"}
```

### Multi-Turn Memory

1. Send: `"My project uses React and TypeScript"`
2. Send: `"Create a task for adding unit tests"`
3. Verify: The task proposal references React Testing Library and TypeScript types (not generic language)

### Clarifying Questions

```bash
curl -X POST http://localhost:8000/api/v1/chat/messages \
  -H "Content-Type: application/json" \
  -H "Cookie: session_id=<your-session-cookie>" \
  -d '{"content": "I have an idea about notifications"}'
```

Expected: Agent asks 2–3 clarifying questions before proposing an action.

### Provider Switch

```bash
# Restart backend with Azure provider
AI_PROVIDER=azure_openai uvicorn src.main:app --reload
```

Verify: Same chat interactions produce equivalent behavior.

## 5. Run Tests

```bash
cd solune/backend

# All unit tests (existing + new)
pytest tests/unit/ -v

# Agent-specific tests only
pytest tests/unit/test_agent_tools.py tests/unit/test_chat_agent.py -v

# Updated chat API tests
pytest tests/unit/test_api_chat.py -v
```

## 6. Key Files Reference

| File | Purpose |
|------|---------|
| `src/services/agent_tools.py` | Tool functions decorated for Agent Framework |
| `src/services/agent_provider.py` | Factory: Copilot vs Azure OpenAI agent creation |
| `src/services/chat_agent.py` | ChatAgentService: session management, response conversion |
| `src/services/agent_middleware.py` | Logging and security middleware |
| `src/prompts/agent_instructions.py` | Unified system instructions for the agent |
| `src/api/chat.py` | Refactored: single `agent_service.run()` replaces priority dispatch |

## 7. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "AI features are not configured" | No valid AI provider credentials | Set `GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET` or Azure credentials |
| Agent returns generic responses | System instructions not loaded | Check `agent_instructions.py` is importable |
| Streaming endpoint returns 404 | Route not registered | Verify `chat.py` router includes `/messages/stream` |
| "DeprecationWarning: AIAgentService" | Old service still referenced | Migrate to `ChatAgentService` — warning is expected during transition |
| Multi-turn context not working | AgentSession not persisted | Check `ChatAgentService` session mapping for the session_id |

## 8. Architecture Overview

```
User ──► Frontend (React)
              │
              ├─ POST /chat/messages         (non-streaming)
              └─ POST /chat/messages/stream   (SSE streaming)
                    │
                    ▼
            FastAPI (chat.py)
                    │
                    ▼
          ChatAgentService.run()
                    │
                    ├─► SecurityMiddleware (input validation)
                    ├─► Agent.run() (Agent Framework)
                    │     ├─► Tool: create_task_proposal
                    │     ├─► Tool: create_issue_recommendation
                    │     ├─► Tool: update_task_status
                    │     ├─► Tool: analyze_transcript
                    │     ├─► Tool: ask_clarifying_question
                    │     ├─► Tool: get_project_context
                    │     └─► Tool: get_pipeline_list
                    ├─► LoggingMiddleware (timing, tokens)
                    │
                    ▼
            ChatMessage (response)
                    │
                    ├─► SQLite (persist)
                    └─► Frontend (render)
```
