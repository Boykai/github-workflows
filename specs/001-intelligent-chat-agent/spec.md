# Feature Specification: Intelligent Chat Agent (Microsoft Agent Framework)

**Feature Branch**: `001-intelligent-chat-agent`  
**Created**: 2026-03-29  
**Status**: Draft  
**Input**: User description: "Replace the current completion-based AIAgentService with a Microsoft Agent Framework Agent that uses function tools, sessions for multi-turn memory, and middleware for logging/security."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Chat with Intelligent Agent (Priority: P1)

A user opens the Solune chat interface and sends a natural-language message. Instead of hitting a rigid priority-dispatch cascade, the message is routed to an intelligent agent that reasons about the user's intent and decides which action to take — creating a task proposal, recommending a GitHub issue, updating a task status, or simply answering a question. The agent asks 2–3 clarifying questions before committing to an action when the request is ambiguous. The user experience remains identical: the same chat input, the same response format, and the same confirm/reject flow for proposals.

**Why this priority**: This is the core value of the migration — replacing the hardcoded priority dispatch with agent-driven reasoning. Without this, no other story delivers value.

**Independent Test**: Can be fully tested by sending a chat message and verifying the agent selects the correct tool and returns a well-formed response. Delivers intelligent intent detection as the foundational capability.

**Acceptance Scenarios**:

1. **Given** a user is in a project chat session, **When** they send "Create a task for updating the homepage banner", **Then** the agent invokes the task-proposal tool and returns a structured proposal for the user to confirm or reject.
2. **Given** a user sends an ambiguous message like "I need something for the login page", **When** the agent cannot determine whether this is a task or a feature request, **Then** the agent asks 2–3 targeted clarifying questions before taking action.
3. **Given** a user sends "Mark the authentication task as done", **When** the agent processes the message, **Then** it invokes the status-update tool and confirms the status change.
4. **Given** the `ai_enhance` flag is set to false, **When** a user sends a message, **Then** the system bypasses the agent and uses simple title-only generation (preserving current behavior).

---

### User Story 2 — Multi-Turn Conversation Memory (Priority: P2)

A user has a multi-message conversation with the agent. Across multiple turns, the agent remembers prior context — for example, if the user said "My project uses React" in an earlier message, the agent references that when generating a task proposal two messages later. The conversation history is maintained per session so each user's context is isolated.

**Why this priority**: Multi-turn memory transforms the agent from a stateless command processor into a conversational assistant. It is essential for the clarifying-questions flow (P1) to work well and significantly improves the quality of generated proposals.

**Independent Test**: Can be tested by sending a sequence of messages across multiple turns and verifying the agent's responses reflect previously provided context. Delivers coherent multi-turn conversations.

**Acceptance Scenarios**:

1. **Given** a user previously said "We use a monorepo with TypeScript", **When** they later ask "Create a task for adding linting", **Then** the generated proposal references TypeScript and monorepo context.
2. **Given** a user starts a new session, **When** they send a message, **Then** no prior session context bleeds into the new conversation.
3. **Given** two users are chatting concurrently in different project sessions, **When** each sends messages, **Then** their conversation contexts remain fully isolated from each other.

---

### User Story 3 — Streaming Responses (Priority: P3)

A user sends a message and sees the agent's response appear progressively in the chat interface — tokens stream in as the agent generates them, rather than waiting for the full response to complete. This gives immediate feedback and makes the experience feel responsive, especially for longer agent outputs.

**Why this priority**: Streaming is additive UX polish. The core functionality works without it (non-streaming responses), but it significantly improves perceived responsiveness.

**Independent Test**: Can be tested by sending a message via the streaming endpoint and verifying tokens arrive incrementally. Delivers real-time progressive rendering in the chat UI.

**Acceptance Scenarios**:

1. **Given** a user sends a message, **When** the streaming endpoint is used, **Then** tokens appear progressively in the chat interface as the agent generates them.
2. **Given** the streaming endpoint is unavailable or errors, **When** a user sends a message, **Then** the frontend falls back to the non-streaming endpoint and the user still receives a complete response.

---

### User Story 4 — Multiple AI Provider Support (Priority: P3)

An operator configures the system to use either GitHub Copilot or Azure OpenAI as the backing AI provider. Switching providers requires only a configuration change (environment variable). The user experience is identical regardless of which provider is active — same tools, same conversation flow, same response format.

**Why this priority**: Provider flexibility is an operational concern rather than a user-facing feature, but it is critical for deployment flexibility and vendor independence.

**Independent Test**: Can be tested by running the same conversation scenario with each provider and verifying identical behavior. Delivers provider-agnostic deployment.

**Acceptance Scenarios**:

1. **Given** the system is configured with `ai_provider=copilot`, **When** a user sends a message, **Then** the agent responds using the GitHub Copilot backend.
2. **Given** the system is configured with `ai_provider=azure_openai`, **When** a user sends the same message, **Then** the agent responds identically using the Azure OpenAI backend.
3. **Given** an invalid `ai_provider` value is configured, **When** the system starts, **Then** it fails with a clear error message indicating the unsupported provider.

---

### User Story 5 — Signal Chat Integration (Priority: P4)

A user interacts with the Solune agent via the Signal messaging channel. Messages sent through Signal are routed to the same intelligent agent (non-streaming mode) and the response is sent back via Signal. The same tool set, clarifying-question flow, and multi-turn memory apply.

**Why this priority**: Signal is a secondary channel. The primary web chat must work first, and Signal integration is a matter of routing messages through the same agent service.

**Independent Test**: Can be tested by sending a message via Signal and verifying the agent responds with the correct tool invocation. Delivers parity between web chat and Signal channels.

**Acceptance Scenarios**:

1. **Given** a user sends a text message via Signal, **When** the agent processes it, **Then** the response is delivered back through Signal in the same format as web chat (minus streaming).
2. **Given** a user has an ongoing Signal conversation, **When** they send a follow-up message, **Then** the agent retains context from earlier messages in that session.

---

### User Story 6 — Observability and Safety (Priority: P4)

An operator can observe agent behavior through structured logging that captures timing, token usage, and tool invocations for every agent interaction. Additionally, a safety layer detects and blocks prompt-injection attempts and validates tool arguments before execution.

**Why this priority**: Observability and security are cross-cutting concerns that are essential for production readiness but do not affect core functionality.

**Independent Test**: Can be tested by sending messages and verifying log entries contain timing and token data, and by sending adversarial inputs to verify they are blocked. Delivers production-grade monitoring and safety.

**Acceptance Scenarios**:

1. **Given** a user sends a message, **When** the agent processes it, **Then** structured logs capture request timing, token count, and which tool was invoked.
2. **Given** a user sends a message containing a prompt-injection attempt, **When** the safety layer evaluates it, **Then** the injection is detected and the request is blocked with an appropriate user-facing message.
3. **Given** a tool is invoked with invalid or malicious arguments, **When** the argument-validation layer checks them, **Then** the invocation is rejected before execution.

---

### Edge Cases

- What happens when the agent cannot match any tool to the user's intent? The agent MUST respond conversationally and ask for clarification rather than failing silently or returning an error.
- What happens when a tool invocation fails mid-execution (e.g., GitHub API is unreachable)? The agent MUST return a graceful error message to the user and log the failure for operators.
- What happens when a session expires or is not found? The system MUST create a new session transparently and inform the user that prior context is unavailable.
- What happens when the AI provider rate-limits or times out? The system MUST return a user-friendly message indicating temporary unavailability and suggest retrying.
- What happens when multiple tools are equally relevant? The agent MUST prefer the clarifying-questions tool to disambiguate before acting.
- What happens when a user sends a `/agent` meta-command? The system MUST continue to handle meta-commands outside the agent (preserving current behavior).
- What happens when a user confirms or rejects a proposal? The existing confirm/reject endpoints MUST remain functional and unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST route all user chat messages through the intelligent agent for intent detection and tool selection, replacing the existing priority-dispatch cascade.
- **FR-002**: System MUST expose the following function tools to the agent: task-proposal creation, issue-recommendation creation, task-status update, transcript analysis, clarifying-question asking, project-context retrieval, and pipeline-list retrieval.
- **FR-003**: System MUST support a clarifying-questions policy where the agent asks 2–3 targeted questions before committing to an action when the user's intent is ambiguous.
- **FR-004**: System MUST maintain per-session conversation memory so the agent can reference prior messages within the same session.
- **FR-005**: System MUST isolate session state between different users and different project contexts.
- **FR-006**: System MUST support both GitHub Copilot and Azure OpenAI as interchangeable AI provider backends, selectable via configuration.
- **FR-007**: System MUST provide a streaming endpoint that delivers agent response tokens progressively via server-sent events.
- **FR-008**: The frontend MUST support progressive rendering of streamed tokens with a fallback to the non-streaming endpoint.
- **FR-009**: System MUST preserve the existing REST API contract — the ChatMessage schema MUST remain unchanged, and the streaming endpoint MUST be additive (not replacing the existing endpoint).
- **FR-010**: System MUST continue to handle `/agent` meta-commands, proposal confirm/reject flows, and file uploads outside the agent's reasoning loop.
- **FR-011**: System MUST bypass the agent and use simple title-only generation when `ai_enhance=False`.
- **FR-012**: System MUST route Signal chat messages through the same agent service in non-streaming mode.
- **FR-013**: System MUST include logging middleware that captures timing, token count, and tool invocation details for every agent interaction.
- **FR-014**: System MUST include security middleware that detects prompt-injection attempts and validates tool arguments before execution.
- **FR-015**: System MUST add deprecation warnings to the old AIAgentService, CompletionProvider, and legacy prompt modules, keeping them functional until removal in a future version.
- **FR-016**: System MUST retain the `identify_target_task()` function from the old service layer, as it is reused by the task-status-update tool.
- **FR-017**: Tools MUST return structured data that is converted into `action_type` and `action_data` fields on ChatMessage for the confirm/reject flow.
- **FR-018**: System MUST inject runtime context (project ID, authentication tokens, session ID) into tool invocations without exposing these values to the language model's schema.

### Key Entities

- **Agent**: The intelligent reasoning component that receives user messages, decides which tool to invoke, and produces responses. Configured with system instructions and a set of function tools.
- **Agent Session**: A stateful conversation context tied to a Solune session ID. Holds multi-turn message history and any accumulated state (e.g., user-provided project details).
- **Function Tool**: A discrete action the agent can invoke — e.g., create a task proposal, recommend an issue, update task status. Each tool accepts typed inputs and returns structured output.
- **Agent Provider**: A factory that creates the appropriate agent instance based on the configured AI backend (GitHub Copilot or Azure OpenAI).
- **Middleware**: Cross-cutting components that wrap agent execution to provide logging, timing, and security enforcement.
- **ChatMessage**: The existing response schema sent to the frontend, containing message content plus optional `action_type` and `action_data` for confirm/reject flows.
- **System Instructions**: A comprehensive prompt that guides agent behavior, including clarifying-question policy, difficulty assessment rules, tool-usage guidance, and dynamic project context.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can send a chat message and receive an intelligent, context-aware response within 5 seconds (excluding network latency) for non-streaming interactions.
- **SC-002**: The agent correctly identifies user intent and selects the appropriate tool for at least 90% of unambiguous messages (task creation, issue recommendation, status update, transcript analysis).
- **SC-003**: Multi-turn conversations retain context across at least 10 consecutive messages within a session, verified by the agent referencing earlier user-provided details.
- **SC-004**: Streaming responses begin delivering tokens to the user within 1 second of the request, providing immediate visual feedback.
- **SC-005**: All existing chat functionality (proposals, confirm/reject, file upload, `/agent` commands) continues to work without regression after the migration.
- **SC-006**: Switching between AI providers requires only a configuration change and produces functionally identical user-facing behavior.
- **SC-007**: All existing unit tests continue to pass, and new tests cover at least the core agent service, each function tool, and the chat API integration.
- **SC-008**: The system remains deployable via Docker with `docker compose up --build` and passes end-to-end health checks.
- **SC-009**: Operators can observe agent behavior through structured logs that include timing, token usage, and tool-invocation details for 100% of agent interactions.
- **SC-010**: The safety layer blocks 100% of known prompt-injection patterns and rejects tool invocations with invalid arguments.

## Assumptions

- The Microsoft Agent Framework packages (`agent-framework-core`, `agent-framework-github-copilot`, `agent-framework-azure-ai`) are stable and support Python.
- The `GitHubCopilotAgent` supports per-run token passing or can be wrapped with a bounded ephemeral agent pool (similar to the current `CopilotClientPool`).
- Solune's existing SQLite database remains the source of truth for conversation history; the agent session state supplements but does not replace it.
- The existing frontend ChatMessage schema is sufficient for all new agent response types (no schema changes needed).
- The `/agent` meta-command, proposal confirm/reject endpoints, and file-upload handling remain outside the agent's reasoning loop and are not refactored in this version.
- Old service layers (AIAgentService, CompletionProvider, legacy prompts) are deprecated with warnings but not removed — removal is planned for v0.3.0.
- MCP tool integration is out of scope for this version (planned for v0.4.0) but the tool-registration design should accommodate future MCP tools.
