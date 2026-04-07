# Quickstart: Intelligent Chat Agent (Microsoft Agent Framework)

**Feature Branch**: `001-intelligent-chat-agent`  
**Date**: 2026-04-07  
**Prerequisites**: Python 3.12+, Node.js 20+, Docker (optional)

## 1. Install New Dependencies

```bash
cd solune/backend

# Add agent framework packages to pyproject.toml
# (these replace github-copilot-sdk for agent functionality)
pip install agent-framework-core>=1.0 \
            agent-framework-github-copilot>=1.0 \
            agent-framework-azure-ai>=1.0 \
            sse-starlette>=2.0
```

Or add to `pyproject.toml` under `[project.dependencies]`:

```toml
"agent-framework-core>=1.0",
"agent-framework-github-copilot>=1.0",
"agent-framework-azure-ai>=1.0",
"sse-starlette>=2.0",
```

## 2. Configuration

No new environment variables are required for the default (Copilot) provider. The existing `AI_PROVIDER` setting selects the backend:

```bash
# Use GitHub Copilot (default — no changes needed)
AI_PROVIDER=copilot

# Use Azure OpenAI (requires existing Azure settings)
AI_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

## 3. New Files Overview

After implementation, the following new files exist:

| File | Purpose |
|------|---------|
| `src/services/agent_tools.py` | `@tool`-decorated functions for agent capabilities |
| `src/services/agent_provider.py` | Factory: creates Agent for configured provider |
| `src/services/chat_agent.py` | `ChatAgentService`: session management + response conversion |
| `src/services/agent_middleware.py` | Logging and security middleware |
| `src/prompts/agent_instructions.py` | Unified system instructions for the agent |
| `tests/unit/test_agent_tools.py` | Unit tests for each tool function |
| `tests/unit/test_chat_agent.py` | Unit tests for ChatAgentService |

## 4. Architecture Overview

```
User Message
    │
    ▼
chat.py (send_message endpoint)
    │
    ├── ai_enhance=False → simple title generation (unchanged)
    ├── /agent command → agent creator (unchanged)
    │
    └── ai_enhance=True
        │
        ▼
    ChatAgentService.run(content, session_id, github_token, ...)
        │
        ├── Get/create AgentSession for session_id
        ├── Inject runtime context via function_invocation_kwargs
        │
        ▼
    Agent.run(message, session=agent_session)
        │
        ├── Agent reasons about which tool to call
        ├── Middleware: SecurityMiddleware → LoggingMiddleware
        │
        ├── Tool: create_task_proposal()
        ├── Tool: create_issue_recommendation()
        ├── Tool: update_task_status()
        ├── Tool: analyze_transcript()
        ├── Tool: ask_clarifying_question()
        ├── Tool: get_project_context()
        └── Tool: get_pipeline_list()
        │
        ▼
    AgentResponse
        │
        ▼
    ChatAgentService converts → ChatMessage
        │
        ▼
    Response to user (same ChatMessage schema)
```

## 5. Running Tests

```bash
cd solune/backend

# Run all unit tests
pytest tests/unit/ -v

# Run only new agent tests
pytest tests/unit/test_agent_tools.py tests/unit/test_chat_agent.py -v

# Run chat API tests (updated mock targets)
pytest tests/unit/test_api_chat.py -v
```

## 6. Manual Verification Checklist

### Basic Chat Flow
1. Start the backend: `uvicorn src.main:app --reload`
2. Open the web UI and navigate to chat
3. Send: "Add a dark-mode toggle to the settings page"
4. Verify: Agent asks a clarifying question (e.g., difficulty)
5. Answer the question
6. Verify: Agent produces a task proposal with title + description
7. Click Confirm → task appears on the project board

### Feature Request Flow
1. Send: "We should let users export reports as PDF"
2. Verify: Agent asks clarifying questions about scope/priority
3. Answer questions
4. Verify: Agent produces an issue recommendation
5. Confirm → GitHub issue is created

### Status Change Flow
1. Send: "Move the dark-mode task to In Review"
2. Verify: Agent identifies the task and confirms the change
3. Confirm → task status is updated

### Multi-Turn Memory
1. Send: "My project uses React and TypeScript"
2. Send: "Create a component for that"
3. Verify: Agent understands "that" refers to the previous context

### Streaming (after streaming endpoint is implemented)
1. Send any message via the streaming endpoint
2. Verify: Text appears progressively in the chat bubble
3. Verify: Final message has correct action_type/action_data

### Provider Switch
1. Set `AI_PROVIDER=azure_openai` with valid Azure credentials
2. Repeat the basic chat flow
3. Verify: Same behaviour as Copilot provider

### Signal Integration
1. Send a text message via Signal
2. Verify: Agent responds with a text message
3. Send "CONFIRM" or "REJECT" for pending proposals

## 7. Deprecation Notes

The following modules now emit `DeprecationWarning` on import/instantiation:

- `src/services/ai_agent.py` → `AIAgentService` — use `ChatAgentService` instead
- `src/services/completion_providers.py` → `CopilotCompletionProvider`, `AzureOpenAICompletionProvider` — replaced by `agent_provider.py`
- `src/prompts/task_generation.py` — replaced by `agent_instructions.py`
- `src/prompts/issue_generation.py` — replaced by `agent_instructions.py`
- `src/prompts/transcript_analysis.py` — replaced by `agent_instructions.py`

**Exception**: `identify_target_task()` in `ai_agent.py` is NOT deprecated — it is reused by the `update_task_status` tool.

These modules will be removed in v0.3.0.

## 8. Implementation Order

```
Phase 1: Foundation (Steps 1–4) — can be done in parallel after step 1
  Step 1: Install packages (pyproject.toml)
  Step 2: Create agent_tools.py (parallel)
  Step 3: Create agent_provider.py (parallel)
  Step 4: Create agent_instructions.py (parallel)

Phase 2: Integration (Steps 5–8) — depends on Phase 1
  Step 5: Create chat_agent.py (depends on 1–4)
  Step 6: Refactor chat.py (depends on 5)
  Step 7: Add streaming endpoint (parallel with 6)
  Step 8: Update signal_chat.py (depends on 5)

Phase 3: Polish (Steps 9–12) — depends on Phase 2
  Step 9: Add agent_middleware.py (parallel)
  Step 10: Write/update tests (depends on 5–8)
  Step 11: Add deprecation warnings (depends on 10)
  Step 12: Frontend streaming (parallel with 9–11)
```
