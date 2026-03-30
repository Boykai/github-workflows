# Feature Specification: Intelligent Chat Agent (Microsoft Agent Framework)

**Feature Branch**: `001-intelligent-chat-agent`  
**Created**: 2026-03-30  
**Status**: Draft  
**Input**: User description: "Replace the current completion-based AIAgentService (raw LLM calls + manual JSON parsing) with a Microsoft Agent Framework Agent that uses function tools to take actions, sessions for multi-turn memory, and middleware for logging/security. The priority-dispatch cascade in chat.py becomes the agent's natural reasoning — instead of hardcoded if/elif priority tiers, the agent decides which tool to call based on its instructions. The REST API contract stays the same so the frontend needs minimal changes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Natural Chat Interaction with Tool-Based Actions (Priority: P1)

A user sends a message in the Solune chat interface describing what they need (e.g., "Create a task for fixing the login bug" or "Move task #42 to done"). Instead of the system relying on hardcoded priority-dispatch logic to interpret the message, an intelligent agent reasons about the user's intent and invokes the appropriate tool — such as creating a task proposal, recommending an issue, or updating a task status — then returns a structured response the user can confirm or reject.

**Why this priority**: This is the core value proposition of the entire feature. Without the agent's ability to reason and invoke tools, none of the other user stories can function. It replaces the brittle priority-dispatch cascade with flexible, intent-driven action selection.

**Independent Test**: Can be fully tested by sending a chat message and verifying the agent selects the correct tool and returns an actionable proposal. Delivers intelligent action routing without hardcoded dispatch logic.

**Acceptance Scenarios**:

1. **Given** a user is in an active chat session with a project selected, **When** the user sends "Create a task for updating the README", **Then** the agent invokes the task creation tool and returns a task proposal with title, description, and difficulty for the user to confirm or reject.
2. **Given** a user is in an active chat session, **When** the user sends "Move task #15 to in-progress", **Then** the agent invokes the status update tool and returns a confirmation of the status change.
3. **Given** a user is in an active chat session, **When** the user sends an ambiguous message like "I have an idea about notifications", **Then** the agent asks 2–3 clarifying questions before proposing an action.
4. **Given** a user is in an active chat session, **When** the user sends a general conversational message with no actionable intent, **Then** the agent responds conversationally without invoking any tool.

---

### User Story 2 - Multi-Turn Conversation Memory (Priority: P2)

A user engages in a multi-turn conversation where earlier messages provide context for later requests. For example, the user says "My project uses React and TypeScript" and later asks "Create a task for adding unit tests." The agent remembers the earlier context and incorporates it into the task proposal (e.g., referencing React Testing Library, TypeScript types).

**Why this priority**: Multi-turn memory transforms the chat from a stateless command interface into a true conversational assistant. It is the second most impactful capability after core tool invocation, enabling richer and more natural interactions.

**Independent Test**: Can be tested by sending a sequence of messages where a later message depends on context from an earlier one, and verifying the agent's response reflects that context.

**Acceptance Scenarios**:

1. **Given** a user has sent "We use Python with FastAPI" in a previous message, **When** the user later sends "Create a task for adding API rate limiting", **Then** the agent's task proposal references Python/FastAPI conventions rather than generic language.
2. **Given** a user has been discussing a specific feature across multiple messages, **When** the user says "Now create an issue for that", **Then** the agent creates an issue recommendation based on the accumulated conversation context.
3. **Given** a user starts a new chat session, **When** the user sends a message, **Then** the agent does not carry over context from a previous session (session isolation).

---

### User Story 3 - Multiple AI Provider Support (Priority: P2)

An administrator configures Solune to use either GitHub Copilot or Azure OpenAI as the underlying AI provider. Regardless of the provider chosen, the chat agent behaves identically — the same tools are available, the same conversational patterns work, and users cannot distinguish which provider is active.

**Why this priority**: Provider flexibility is critical for deployment scenarios where one provider may be unavailable or where organizations have specific vendor requirements. It shares P2 priority because it is foundational for production readiness.

**Independent Test**: Can be tested by running the same set of chat interactions against both provider configurations and verifying identical behavioral outcomes.

**Acceptance Scenarios**:

1. **Given** the system is configured with `ai_provider=copilot`, **When** a user sends a chat message, **Then** the agent responds using the GitHub Copilot backend and all tools function correctly.
2. **Given** the system is configured with `ai_provider=azure_openai`, **When** a user sends the same chat message, **Then** the agent responds using the Azure OpenAI backend with equivalent behavior.
3. **Given** the system is configured with `ai_enhance=False`, **When** a user sends a chat message, **Then** the system bypasses the agent entirely and uses simple title-only generation (preserving current fallback behavior).

---

### User Story 4 - Real-Time Streaming Responses (Priority: P3)

A user sends a message and sees the agent's response appear progressively (token by token) in the chat interface, rather than waiting for the entire response to be generated before anything appears. This provides immediate feedback and a more responsive experience.

**Why this priority**: Streaming improves perceived performance and user experience but is additive — the system works fully without it. It can be delivered independently after core agent functionality is stable.

**Independent Test**: Can be tested by sending a message to the streaming endpoint and verifying that partial tokens arrive before the full response is complete, with the final assembled response matching what the non-streaming endpoint would return.

**Acceptance Scenarios**:

1. **Given** a user sends a message via the streaming-enabled chat interface, **When** the agent begins generating a response, **Then** tokens appear progressively in the chat bubble within 500ms of the first token being generated.
2. **Given** the streaming endpoint is unavailable or errors, **When** the frontend detects the failure, **Then** it falls back to the non-streaming endpoint and displays the complete response after generation finishes.

---

### User Story 5 - Signal Messenger Integration (Priority: P3)

A user interacts with Solune through Signal messenger. Messages sent via Signal are processed by the same intelligent agent, and responses are returned through Signal. The agent's full reasoning and tool capabilities are available, but responses are non-streaming (text only).

**Why this priority**: Signal integration extends the agent to an additional channel but depends on the core agent service being functional first. It is a parallel integration that can be developed and tested independently.

**Independent Test**: Can be tested by sending a message through the Signal integration layer and verifying the agent processes it and returns a correctly formatted text response.

**Acceptance Scenarios**:

1. **Given** a user sends a text message via Signal, **When** the message is received by the system, **Then** the agent processes it and returns a text response through Signal.
2. **Given** a user sends a message via Signal requesting an action (e.g., "Create a task for…"), **When** the agent processes the message, **Then** the response includes the action proposal in a readable text format.

---

### User Story 6 - Operational Observability (Priority: P3)

An operator or developer can observe agent behavior through structured logs that include timing information, token usage, and tool invocation details. Additionally, a security layer detects and blocks prompt injection attempts and validates tool arguments before execution.

**Why this priority**: Observability and security are operational concerns that enhance production readiness. They can be developed in parallel with other integration work and do not block core functionality.

**Independent Test**: Can be tested by triggering agent interactions and verifying that log entries contain expected timing/token data, and by sending known prompt injection patterns and verifying they are detected and blocked.

**Acceptance Scenarios**:

1. **Given** an agent processes a user message, **When** the interaction completes, **Then** structured logs are emitted containing response time, token count, and which tool (if any) was invoked.
2. **Given** a user sends a message containing a prompt injection attempt, **When** the security middleware evaluates the message, **Then** the injection is detected, the message is blocked, and a safe fallback response is returned.
3. **Given** the agent invokes a tool, **When** the middleware validates the tool's arguments, **Then** arguments that fail validation are rejected before the tool executes.

---

### Edge Cases

- What happens when the AI provider is temporarily unavailable? The system should return a user-friendly error message and not crash or hang.
- What happens when a user sends an extremely long message that exceeds token limits? The system should truncate or reject gracefully with a clear message.
- What happens when the agent invokes a tool but the tool fails (e.g., GitHub API is down)? The agent should report the failure to the user with a helpful message rather than silently failing.
- What happens when two users in different sessions send messages simultaneously? Sessions must be isolated; one user's context must not leak into another's.
- What happens when a user confirms a proposal but the underlying data has changed since the proposal was generated (e.g., task was deleted)? The system should detect staleness and inform the user.
- What happens when the conversation history grows very large within a single session? The system should manage context window limits by summarizing older messages rather than truncating abruptly.
- What happens when the system is configured with an invalid AI provider value? The system should fail at startup with a clear configuration error.
- What happens when the agent is uncertain about which tool to use? It should ask clarifying questions rather than guessing incorrectly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST route user messages to an intelligent agent that reasons about intent and selects the appropriate action, replacing the existing hardcoded priority-dispatch cascade.
- **FR-002**: System MUST expose the following agent tools: task proposal creation, issue recommendation creation, task status update, transcript analysis, clarifying question, project context retrieval, and pipeline list retrieval.
- **FR-003**: Each agent tool MUST receive runtime context (project identifier, authentication token, session identifier) without exposing that context to the language model's input schema.
- **FR-004**: System MUST support at least two AI provider backends (GitHub Copilot and Azure OpenAI) that are interchangeable via configuration without code changes.
- **FR-005**: System MUST maintain conversational memory within a session so that the agent can reference earlier messages when responding to subsequent ones.
- **FR-006**: System MUST isolate sessions so that one user's conversation context is never accessible to another user.
- **FR-007**: System MUST preserve the existing REST API contract — the ChatMessage schema and existing endpoints must remain unchanged for backwards compatibility.
- **FR-008**: System MUST provide a streaming endpoint that delivers response tokens progressively so users see partial responses as they are generated.
- **FR-009**: The frontend MUST support streaming responses with progressive rendering and fall back to the non-streaming endpoint if streaming fails.
- **FR-010**: System MUST process messages received via the Signal integration using the same agent capabilities (non-streaming).
- **FR-011**: The agent MUST ask 2–3 clarifying questions before taking action when the user's intent is ambiguous.
- **FR-012**: System MUST support a bypass mode (`ai_enhance=False`) that skips the agent and uses simple title-only generation, preserving current behavior for users who opt out.
- **FR-013**: System MUST emit structured logs for each agent interaction containing response timing, token usage, and tool invocation details.
- **FR-014**: System MUST include security middleware that detects prompt injection attempts and validates tool arguments before execution.
- **FR-015**: System MUST consolidate multiple prompt templates (task generation, issue generation, transcript analysis) into a single comprehensive agent instruction set.
- **FR-016**: System MUST deprecate (not delete) the existing AIAgentService, completion providers, and old prompt modules with deprecation warnings, to be removed in a future version.
- **FR-017**: The proposal confirm/reject flow MUST continue to work — tools return structured data that is converted into confirmable action proposals.
- **FR-018**: File and transcript uploads MUST continue to work alongside agent-based interactions, with uploaded content available as context for the agent's reasoning.
- **FR-019**: System MUST manage context window limits for long conversations by summarizing older messages rather than hard-truncating.
- **FR-020**: Tool registration design MUST accommodate future extensibility for additional tool types.

### Key Entities

- **Agent**: The central reasoning component that receives user messages, decides which tool to invoke based on its instructions and conversation context, and returns structured responses. Configured with a provider backend and a set of available tools.
- **Agent Session**: A stateful conversation container that maps to a Solune user session. Stores conversation history and accumulated context. Isolated per user.
- **Agent Tool**: A discrete, named function that the agent can invoke to perform an action (e.g., create a task, update status). Each tool has a defined input schema (visible to the agent) and receives runtime context (invisible to the agent).
- **Agent Provider**: An abstraction over the underlying AI model service (GitHub Copilot or Azure OpenAI). Created via a factory based on configuration. Interchangeable without affecting agent behavior.
- **Agent Middleware**: A processing layer that wraps agent execution to provide cross-cutting concerns: logging (timing, tokens) and security (injection detection, argument validation).
- **Chat Message**: The existing message data structure exchanged between frontend and backend. Includes optional `action_type` and `action_data` fields for confirmable proposals. Schema remains unchanged.
- **System Instructions**: A comprehensive prompt document that guides agent behavior including clarifying-question policy, difficulty assessment rules, tool usage guidance, and dynamic project context.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing chat interactions (task creation, issue recommendation, status update, transcript analysis) continue to work with identical user-facing behavior after migration — 100% functional parity with the current system.
- **SC-002**: Users can complete a multi-turn conversation where the agent correctly references context from at least 5 prior messages in the same session.
- **SC-003**: The agent correctly selects the appropriate tool for at least 95% of unambiguous user requests (measured against a test suite of representative messages).
- **SC-004**: Switching between AI providers produces equivalent responses for the same input — no provider-specific behavioral differences visible to users.
- **SC-005**: Streaming responses deliver the first visible token to the user within 2 seconds of sending a message, with progressive rendering completing within the total generation time.
- **SC-006**: All existing automated tests pass after migration, plus new tests covering agent tools, session management, and response conversion achieve at least 80% coverage of new code.
- **SC-007**: The system handles at least 50 concurrent chat sessions without session cross-contamination or performance degradation.
- **SC-008**: Prompt injection attempts from a standard test suite are detected and blocked with zero false negatives and less than 5% false positives.
- **SC-009**: The complete system (agent, tools, streaming, Signal integration) starts and operates correctly via the standard container-based deployment with no manual configuration beyond environment variables.
- **SC-010**: Deprecation warnings are emitted when any code path references the old AIAgentService, completion providers, or legacy prompt modules, providing clear migration guidance.

## Assumptions

- The Microsoft Agent Framework packages are stable and support the required features (function tools, sessions, middleware, streaming).
- The existing Solune database remains the source of truth for conversation history; the agent session state supplements but does not replace it.
- The GitHub Copilot provider supports per-request token passing or an equivalent mechanism for per-user authentication. If not supported, a bounded ephemeral agent pool (similar to the current connection pooling strategy) will be used.
- The `/agent` meta-command handling and proposal confirm/reject endpoints remain outside the agent's scope — they are handled directly by the API layer.
- MCP tool integration is explicitly out of scope for this version (deferred to v0.4.0), but the tool registration design should not preclude it.
- The frontend streaming implementation uses standard browser APIs and does not require additional dependencies.
- Performance baselines are based on standard web application expectations unless specific targets are provided.
