# Research: Intelligent Chat Agent (Microsoft Agent Framework)

**Feature**: 001-intelligent-chat-agent | **Date**: 2026-04-07

## Research Tasks

This document resolves all NEEDS CLARIFICATION items from the Technical Context and researches best practices for each technology choice and integration point.

---

### R1: Microsoft Agent Framework Package Selection

**Question**: Which `agent-framework-*` packages are needed and what are their stable versions?

**Decision**: Use three packages:
- `agent-framework-core` — core Agent, AgentSession, AIFunction, middleware abstractions
- `agent-framework-github-copilot` — `GitHubCopilotAgent` wrapping the Copilot SDK
- `agent-framework-azure-ai` — `AzureOpenAIResponsesClient` for Azure OpenAI backend

**Rationale**: The framework uses a monorepo with separate PyPI packages per provider. Installing only the needed packages avoids pulling in unused providers (Anthropic, Foundry, etc.). The `agent-framework-core` package is the foundation; provider packages are thin wrappers.

**Alternatives considered**:
- `agent-framework` (all-in-one): Rejected — pulls in all providers, increases image size, and introduces unused transitive dependencies
- Stay with raw Copilot SDK + OpenAI SDK: Rejected — manual tool dispatch, no session abstraction, no middleware pipeline; the issue explicitly mandates Agent Framework

**Version strategy**: Pin to `>=1.0.0,<2` for core (production-ready v1.0 shipped April 2026). Use `--pre` flag for `agent-framework-github-copilot` if still in preview at implementation time.

---

### R2: Agent Framework Tool Registration Pattern

**Question**: How should existing service methods be converted to agent tools?

**Decision**: Use the `AIFunction` wrapper (or `@kernel_function` / `@tool` decorator pattern from Agent Framework) to wrap each action as a callable tool. Each tool is a standalone async Python function with type-annotated parameters. Runtime context (project_id, github_token, session_id) is injected via `FunctionInvocationContext.kwargs` — these parameters are invisible to the LLM's JSON schema.

**Rationale**: The Agent Framework generates JSON schemas from function signatures automatically. Only parameters with type annotations appear in the schema sent to the LLM. Context injection via kwargs keeps authentication tokens and internal IDs out of the model's input space, preventing accidental leakage.

**Alternatives considered**:
- Pass context as regular function parameters: Rejected — would expose tokens and IDs to the LLM, violating security requirements (FR-003)
- Use a global/module-level context object: Rejected — breaks session isolation (FR-006) when concurrent users call the same tool

**Tool mapping** (from existing methods to new tools):

| Current Method | New Tool Function | Parameters (LLM-visible) | Context (injected) |
|---|---|---|---|
| `generate_task_from_description()` | `create_task_proposal(title, description)` | title: str, description: str | project_id, session_id |
| `detect_feature_request_intent()` + `generate_issue_recommendation()` | `create_issue_recommendation(title, user_story, acceptance_criteria, labels, priority, size)` | title, user_story, acceptance_criteria, labels, priority, size | project_id, github_token, pipeline_id |
| `parse_status_change_request()` | `update_task_status(task_reference, target_status)` | task_reference: str, target_status: str | project_id, current_tasks, status_columns |
| `analyze_transcript()` | `analyze_transcript(transcript_content)` | transcript_content: str | project_id, session_id |
| *(new)* | `ask_clarifying_question(question)` | question: str | — |
| *(new)* | `get_project_context()` | — | project_id |
| *(new)* | `get_pipeline_list()` | — | project_id |

---

### R3: Agent Provider Factory Design

**Question**: How should the provider factory select between Copilot and Azure OpenAI agents?

**Decision**: Create a `create_agent()` factory function in `agent_provider.py` that reads `settings.ai_provider` and returns the appropriate `Agent` instance:

- `ai_provider="copilot"` → `GitHubCopilotAgent` from `agent_framework.github`
- `ai_provider="azure_openai"` → `Agent` with `AzureOpenAIResponsesClient` from `agent_framework.azure_ai`

Both agents receive the same tool list and system instructions. The factory is called once at service initialization (singleton pattern, matching the existing `get_ai_agent_service()` approach).

**Rationale**: The Agent Framework's provider abstraction means the same `Agent` interface works regardless of backend. The factory pattern matches the existing `create_completion_provider()` in `completion_providers.py`, making migration intuitive.

**Alternatives considered**:
- Runtime provider switching per-request: Rejected — unnecessary complexity; provider is a deployment-time decision
- Abstract base class hierarchy: Rejected — Agent Framework already provides the abstraction; wrapping it adds no value (Constitution Principle V: Simplicity)

---

### R4: Per-User Authentication with Copilot Provider

**Question**: Does `GitHubCopilotAgent` support per-request token passing for user-specific Copilot access?

**Decision**: If `GitHubCopilotAgent` supports passing a GitHub token per `agent.run()` invocation (e.g., via run options or context), use that directly. If not, use a bounded ephemeral agent pool (similar to the existing `CopilotClientPool` with `BoundedDict` and `asyncio.Lock`), keyed by token hash, with FIFO eviction at capacity 50.

**Rationale**: The existing `CopilotClientPool` in `completion_providers.py` already solves this problem for the raw SDK. The same pattern applies — each unique GitHub token maps to one agent instance. The pool is thread-safe via asyncio.Lock and memory-safe via BoundedDict.

**Alternatives considered**:
- Single shared agent with a service account token: Rejected — loses per-user Copilot entitlements and audit trail
- Unbounded agent cache: Rejected — memory leak risk with many users; the existing 50-entry bounded dict is proven

---

### R5: Session Management — AgentSession ↔ Solune Session Mapping

**Question**: How should Agent Framework sessions map to Solune's existing session system?

**Decision**: Maintain a `dict[UUID, AgentSession]` mapping in `ChatAgentService`, keyed by Solune `session_id`. On each `run()` call:
1. Look up or create an `AgentSession` for the given `session_id`
2. Pass the session to `agent.run(session=session, ...)`
3. After the run, persist a summary of the agent's state to Solune's SQLite chat history (via `chat_store.py`)

Solune's SQLite remains the source of truth for conversation history. AgentSession holds the in-memory working state that the framework needs for tool context and multi-turn reasoning.

**Rationale**: The spec explicitly states "Keep Solune's SQLite as source of truth, sync summaries into AgentSession.state — don't replace the storage layer." This dual approach preserves existing backup/recovery semantics while giving the agent framework the stateful session it needs.

**Alternatives considered**:
- Replace SQLite with AgentSession persistence: Rejected — loses existing audit trail, backup mechanisms, and chat_store query capabilities
- Replay full chat history into AgentSession on every request: Rejected — expensive for long conversations; summarization is more efficient (FR-019)

---

### R6: Streaming Implementation Pattern

**Question**: What is the best approach for SSE streaming from Agent Framework to the frontend?

**Decision**: Add a `POST /chat/messages/stream` endpoint that:
1. Calls `agent.run(stream=True)` (or equivalent streaming API from Agent Framework)
2. Wraps the async generator in FastAPI's `EventSourceResponse` (from `sse-starlette` package)
3. Emits `data:` events with partial token content and a final `data: [DONE]` sentinel
4. Frontend uses `ReadableStream` / `fetch()` with streaming body to read SSE events

**Rationale**: SSE is unidirectional (server → client), which matches the use case (user sends message, server streams response). It's simpler than WebSockets for this pattern, works through proxies/CDNs, and has native browser support. The `sse-starlette` package is already compatible with FastAPI.

**Alternatives considered**:
- WebSockets: Rejected — bidirectional not needed for response streaming; adds connection management complexity; the project already has WebSocket infra for other features but SSE is simpler for this use case
- Long polling: Rejected — higher latency, more HTTP overhead, poorer UX for progressive rendering

**New dependency**: `sse-starlette>=2.0.0,<3` — lightweight SSE response wrapper for Starlette/FastAPI.

---

### R7: System Instructions Consolidation

**Question**: How should the three separate prompt modules be unified into one agent instruction set?

**Decision**: Create `src/prompts/agent_instructions.py` containing a single `AGENT_SYSTEM_INSTRUCTIONS` string that:
1. Defines the agent's persona and role (Solune project assistant)
2. Lists available tools with usage guidance (when to use each)
3. Includes clarifying-question policy (ask 2–3 questions when intent is ambiguous before acting)
4. Includes difficulty assessment rubric (for task proposals)
5. Uses `{project_name}`, `{status_columns}`, `{current_tasks_summary}` template variables for dynamic context injection at runtime

**Rationale**: The current system has three separate prompt files (`task_generation.py`, `issue_generation.py`, `transcript_analysis.py`) each with system prompts for different actions. With the agent framework, the agent receives one comprehensive instruction set and decides which tool to call — the tool-specific guidance is embedded in the instructions rather than dispatched by code.

**Alternatives considered**:
- Keep separate prompts and swap them per tool call: Rejected — defeats the purpose of agent-based reasoning; the agent needs holistic instructions to decide *which* tool to call
- No system prompt (rely on tool descriptions only): Rejected — insufficient guidance for clarifying-question policy, difficulty assessment, and project-specific context

---

### R8: Middleware Architecture

**Question**: What middleware pattern should be used for logging and security?

**Decision**: Implement two middleware classes extending Agent Framework's `AgentMiddleware` base:

1. **`LoggingAgentMiddleware`**: Wraps `agent.run()` to capture:
   - Start/end timestamps → response time
   - Token counts (from agent response metadata)
   - Tool invocation name and duration
   - Emits structured log entries via existing `logging_utils.get_logger()`

2. **`SecurityMiddleware`**: Inspects user input before agent processing:
   - Pattern-based prompt injection detection (instruction override attempts, role-play escapes)
   - Tool argument validation (type checking, length limits, forbidden characters)
   - Returns safe fallback response if injection detected; logs the attempt

**Rationale**: Agent Framework provides a `process()` method pattern for middleware that intercepts agent invocations. This is cleaner than wrapping at the HTTP layer (which can't see tool-level details) or at the tool level (which would require decorating every tool).

**Alternatives considered**:
- HTTP middleware only: Rejected — can't observe tool invocations or token counts
- Per-tool validation decorators: Rejected — repetitive, violates DRY; middleware handles it uniformly

---

### R9: Frontend Streaming Implementation

**Question**: How should the React frontend consume SSE streaming responses?

**Decision**: Add a `sendMessageStream()` method to `chatApi` in `api.ts` that:
1. Uses `fetch()` with `{ method: 'POST', body: JSON.stringify(data) }`
2. Reads `response.body` as a `ReadableStream` via `getReader()`
3. Decodes SSE `data:` lines, accumulating tokens into the message content
4. Calls an `onToken` callback for progressive rendering in `MessageBubble`
5. On error or stream failure, falls back to `sendMessage()` (non-streaming)

**Rationale**: Standard browser `ReadableStream` API avoids new dependencies. The `EventSource` API doesn't support POST requests, so `fetch` + manual SSE parsing is the standard pattern. Fallback to non-streaming ensures reliability.

**Alternatives considered**:
- EventSource API: Rejected — only supports GET requests; our endpoint is POST
- Third-party SSE library (e.g., `eventsource-polyfill`): Rejected — adds dependency for functionality achievable with native APIs
- WebSocket: Rejected — same reasoning as R6

---

### R10: Deprecation Strategy

**Question**: How should old modules be deprecated without breaking existing functionality?

**Decision**: Add Python `warnings.warn()` calls with `DeprecationWarning` category at module level and in class `__init__` methods:

- `ai_agent.py`: Warning in `AIAgentService.__init__()` — "Use ChatAgentService instead. Will be removed in v0.3.0."
- `completion_providers.py`: Warning in `create_completion_provider()` — "Use agent_provider.create_agent() instead. Will be removed in v0.3.0."
- `task_generation.py`, `issue_generation.py`, `transcript_analysis.py`: Module-level warning on import — "Use agent_instructions.py instead. Will be removed in v0.3.0."

Keep `identify_target_task()` from `ai_agent.py` — it's reused by the `update_task_status` tool for task matching logic.

**Rationale**: The issue explicitly states "Deprecate, don't delete — old service layer gets warnings, removed in v0.3.0." `DeprecationWarning` is the standard Python mechanism and is visible in test output and logs.

**Alternatives considered**:
- Delete immediately: Rejected — breaks any external consumers or scripts referencing old modules
- No deprecation warnings (just comments): Rejected — invisible to users; warnings provide runtime notification
