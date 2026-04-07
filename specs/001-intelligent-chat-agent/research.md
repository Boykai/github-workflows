# Research: Intelligent Chat Agent (Microsoft Agent Framework)

**Feature Branch**: `001-intelligent-chat-agent`  
**Date**: 2026-04-07  
**Status**: Complete — all NEEDS CLARIFICATION resolved

## R1: Agent Framework Package Selection

**Decision**: Use `agent-framework-core`, `agent-framework-github-copilot`, and `agent-framework-azure-ai` as three separate packages (not the umbrella `agent-framework` meta-package).

**Rationale**: The meta-package pulls in all provider integrations (Anthropic, Ollama, etc.) which are unnecessary. Pinning individual packages reduces the dependency surface and Docker image size. All three packages reached stable 1.0 in April 2026, so no `--pre` flag is needed.

**Alternatives considered**:
- `agent-framework` (umbrella) — rejected: too many transitive dependencies for two providers.
- Staying on `github-copilot-sdk` + `openai` — rejected: loses function-tool calling, session management, and middleware capabilities the spec requires.

---

## R2: Function Tool Pattern — `@tool` Decorator vs Manual Registration

**Decision**: Use the `@tool` decorator on standalone async functions in `agent_tools.py`. Inject runtime context (project_id, github_token, session_id) via `FunctionInvocationContext.kwargs`.

**Rationale**: The `@tool` decorator auto-generates the JSON schema from type hints, keeping tool definitions DRY. The `FunctionInvocationContext` parameter is excluded from the LLM-visible schema, so sensitive runtime data (tokens, IDs) is invisible to the model. This matches the framework's recommended pattern from [Microsoft Learn docs](https://learn.microsoft.com/en-us/agent-framework/agents/tools/function-tools).

**Alternatives considered**:
- Class-based tools with `__call__` — rejected: adds boilerplate without benefit; the framework prefers decorated functions.
- Passing context as tool parameters — rejected: would expose runtime secrets in the LLM tool schema.

**Tool mapping** (current method → new tool):

| Current Method | New Tool Function | Notes |
|---|---|---|
| `generate_task_from_description()` | `create_task_proposal(title, description)` | Returns structured dict for confirm/reject flow |
| `detect_feature_request_intent()` + `generate_issue_recommendation()` | `create_issue_recommendation(title, user_story, ...)` | Single tool replaces detect + generate pair |
| `parse_status_change_request()` | `update_task_status(task_reference, target_status)` | Reuses existing `identify_target_task()` utility |
| `analyze_transcript()` | `analyze_transcript(transcript_content)` | Accepts transcript text, returns summary + action items |
| *(new)* | `ask_clarifying_question(question)` | Agent calls this to ask follow-up before acting |
| *(new)* | `get_project_context()` | Returns active project metadata for grounding |
| *(new)* | `get_pipeline_list()` | Returns available CI/CD pipelines |

---

## R3: Agent Provider Factory — GitHubCopilotAgent vs Agent + AzureOpenAIResponsesClient

**Decision**: Create a factory function `create_agent()` in `agent_provider.py` that returns:
- `ai_provider="copilot"` → `GitHubCopilotAgent` (from `agent_framework.github`)
- `ai_provider="azure_openai"` → `Agent` with `AzureOpenAIResponsesClient` (from `agent_framework.azure`)

Both receive the same tools list and system instructions, ensuring identical behaviour regardless of backend.

**Rationale**: The Agent Framework provides dedicated provider classes that handle authentication, streaming, and model specifics internally. `GitHubCopilotAgent` wraps the Copilot SDK and manages per-user token passing. `AzureOpenAIResponsesClient` handles Azure AD or API key auth. Using the framework's abstractions means we no longer maintain `CopilotCompletionProvider`, `AzureOpenAICompletionProvider`, or `CopilotClientPool`.

**Alternatives considered**:
- Single `Agent` class with swappable client — rejected: `GitHubCopilotAgent` has Copilot-specific session handling that `Agent` alone does not provide.
- Keep existing `CompletionProvider` and add Agent Framework as a third option — rejected: would require maintaining three code paths instead of one; the spec mandates replacement.

---

## R4: Session Management — AgentSession ↔ Solune Session Mapping

**Decision**: Map each Solune `session_id` (UUID) to an `AgentSession` instance held in an in-memory dictionary inside `ChatAgentService`. On first message in a session, create a new `AgentSession(session_id=str(solune_session_id))`. Persist session state summaries to SQLite alongside existing chat history; restore on cache miss.

**Rationale**: The Agent Framework's `AgentSession` tracks conversation context, tool invocation history, and shared state. Solune's SQLite database remains the source of truth (FR-020). The in-memory dict provides fast access; eviction uses LRU with a configurable max size (default: 200 sessions). Session summaries are synced to SQLite periodically and on session close.

**Alternatives considered**:
- Replace SQLite with AgentSession persistence — rejected: spec FR-020 explicitly keeps existing storage as source of truth.
- External session store (Redis) — rejected: over-engineering for single-tenant deployment; SQLite is sufficient.
- No caching (create fresh session per request) — rejected: would lose multi-turn context (FR-003).

---

## R5: System Instructions Strategy — Unified vs Per-Action Prompts

**Decision**: Single comprehensive system instruction in `agent_instructions.py` that covers all agent behaviours: clarifying-questions policy, tool usage guidance, difficulty assessment, output formatting, and dynamic project context injection. Replaces separate `task_generation.py`, `issue_generation.py`, and `transcript_analysis.py` prompts.

**Rationale**: The Agent Framework agent has one system instruction that governs all interactions. Per-action prompts become unnecessary because the agent selects tools based on reasoning, not explicit routing. The unified prompt consolidates the clarifying-questions policy (2–3 questions before acting), JSON output schemas for each tool, and the difficulty assessment rubric. Dynamic context (project name, available labels, branches) is injected at runtime via template variables.

**Alternatives considered**:
- Keep per-action prompts and switch system instructions per request — rejected: the agent's tool-calling paradigm makes this unnecessary; switching prompts mid-session would confuse multi-turn context.
- Minimal system prompt with tool-level instructions — rejected: testing shows that detailed system instructions improve tool selection accuracy (SC-002 target: 95%).

---

## R6: Streaming Implementation — SSE vs WebSocket

**Decision**: Add a new `POST /api/v1/chat/messages/stream` endpoint using Server-Sent Events (SSE) via the `sse-starlette` library. The existing `POST /api/v1/chat/messages` endpoint remains unchanged for backward compatibility.

**Rationale**: SSE is the simplest transport for server-to-client streaming. FastAPI's `EventSourceResponse` (from `sse-starlette`) wraps an async generator that yields agent response chunks. The Agent Framework's `agent.run(stream=True)` returns an async iterator of message fragments. WebSocket would require client-side changes to the connection model; SSE works over standard HTTP and the frontend only needs `ReadableStream` or `EventSource`.

**Alternatives considered**:
- WebSocket — rejected: overkill for unidirectional streaming; would require new connection management on both sides.
- Long polling — rejected: higher latency and more complex error handling.
- Modify existing endpoint to optionally stream — rejected: mixing streaming and non-streaming in one endpoint complicates error handling and backward compatibility.

---

## R7: Per-User Auth with Copilot Provider

**Decision**: Pass the user's GitHub OAuth token per-run via `function_invocation_kwargs` on each `agent.run()` call. `GitHubCopilotAgent` uses this token for the Copilot API call. If the framework does not support per-run token injection, fall back to a bounded ephemeral agent pool keyed by hashed token (similar to the current `CopilotClientPool` pattern).

**Rationale**: The current system already maps each request to a user token. The Agent Framework's `GitHubCopilotAgent` accepts authentication context through its `run()` kwargs. This avoids creating a separate agent instance per user while maintaining user-scoped authentication.

**Alternatives considered**:
- One agent per user — rejected: memory-intensive; agent initialisation is non-trivial.
- Shared static token — rejected: violates per-user authentication requirement.
- Agent pool with FIFO eviction — acceptable fallback if per-run injection is not supported; mirrors current `CopilotClientPool` (max 50 clients, SHA256-hashed keys).

---

## R8: Middleware Architecture — Logging and Security

**Decision**: Implement two `FunctionMiddleware` subclasses in `agent_middleware.py`:
1. `LoggingMiddleware` — records timing, token count, tool name, and session ID for each tool invocation; emits structured log entries.
2. `SecurityMiddleware` — validates tool arguments against expected schemas; detects prompt-injection patterns in user messages before they reach the agent.

**Rationale**: The Agent Framework's middleware pipeline processes every tool invocation, making it the natural place for cross-cutting concerns. `FunctionMiddleware.process(context, next)` receives the `FunctionInvocationContext` with full access to arguments, function metadata, and kwargs. Middleware is registered on the agent at construction time and applies to all tools uniformly.

**Alternatives considered**:
- Per-tool validation decorators — rejected: duplicates validation logic across tools.
- FastAPI middleware — rejected: operates at HTTP level, not tool-invocation level; cannot inspect tool arguments.
- Post-hoc logging — rejected: misses timing data and cannot block malicious invocations before they execute.

---

## R9: Response Conversion — AgentResponse → ChatMessage

**Decision**: `ChatAgentService` converts `AgentResponse.messages` into `ChatMessage` objects by:
1. Extracting text content → `ChatMessage.content`
2. Detecting tool calls in the response → set `action_type` (TASK_CREATE, ISSUE_CREATE, STATUS_UPDATE) and `action_data` (proposal dict)
3. Generating `message_id`, `session_id`, `sender_type=ASSISTANT`, `timestamp`

**Rationale**: The existing frontend expects `ChatMessage` with `action_type` and `action_data` for the confirm/reject UI. The conversion layer isolates the Agent Framework's response format from the API contract, ensuring FR-006 (stable API contract) is maintained.

**Alternatives considered**:
- Return AgentResponse directly — rejected: breaks existing frontend contract.
- Modify ChatMessage schema — rejected: spec FR-006 explicitly requires schema stability.

---

## R10: Deprecation Strategy

**Decision**: Add `warnings.warn("...", DeprecationWarning, stacklevel=2)` to the `__init__` methods of `AIAgentService`, `CopilotCompletionProvider`, `AzureOpenAICompletionProvider`, and to the module-level functions in `task_generation.py`, `issue_generation.py`, and `transcript_analysis.py`. Keep `identify_target_task()` in `ai_agent.py` without deprecation (reused by `update_task_status` tool).

**Rationale**: FR-017 requires deprecation warnings but not deletion. The old code path remains functional for any external consumers. Removal is deferred to v0.3.0. The `identify_target_task()` utility is still needed by the new task status tool.

**Alternatives considered**:
- Immediate deletion — rejected: spec says "deprecate, don't delete."
- No warnings — rejected: consumers need advance notice of the v0.3.0 removal.

---

## R11: Frontend Streaming Integration

**Decision**: Add a `sendMessageStream()` function in `api.ts` that calls `POST /api/v1/chat/messages/stream` and reads the response as a `ReadableStream`. Progressive rendering in the chat interface appends tokens as they arrive. Falls back to the existing non-streaming `sendMessage()` if the stream connection fails or errors.

**Rationale**: The `ReadableStream` API is natively supported in all modern browsers. SSE parsing on the client is straightforward: split on `data:` lines, parse JSON fragments, and append to the message bubble. The fallback ensures graceful degradation (FR-019).

**Alternatives considered**:
- `EventSource` API — rejected: does not support POST requests natively; would require a polyfill.
- Replace existing endpoint — rejected: breaks backward compatibility; the non-streaming endpoint must remain for Signal and non-browser clients.
