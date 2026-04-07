# Feature Specification: Intelligent Chat Agent (Microsoft Agent Framework) v0.2.0

**Feature Branch**: `002-intelligent-chat-agent`  
**Created**: 2026-04-07  
**Status**: Draft  
**Input**: User description: "Replace the current completion-based AIAgentService (raw LLM calls + manual JSON parsing) with a Microsoft Agent Framework Agent that uses function tools to take actions, sessions for multi-turn memory, and middleware for logging/security. The priority-dispatch cascade in chat.py becomes the agent's natural reasoning — instead of hardcoded if/elif priority tiers, the agent decides which tool to call based on its instructions. The REST API contract stays the same so the frontend needs minimal changes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Intelligent Tool Selection for Chat Actions (Priority: P1)

A project member sends a natural-language message in the chat interface. Instead of the system matching the message against a fixed set of if/elif rules, the agent reads the message, reasons about the user's intent, and autonomously decides which action to take — create a task proposal, recommend a GitHub issue, update a task's status, analyse a transcript, or simply respond conversationally. The user experiences a single, coherent assistant rather than a set of disconnected command handlers.

**Why this priority**: This is the central behavioural change of v0.2.0. Every other story depends on the agent's ability to reason about which tool to invoke. Proving that the agent reliably selects the right action replaces the brittle priority-dispatch logic and validates the entire architectural shift.

**Independent Test**: Can be fully tested by sending a variety of message types (task description, feature idea, status-change request, general question) and verifying the agent responds with the correct action type each time.

**Acceptance Scenarios**:

1. **Given** a user describes a piece of work (e.g., "Add pagination to the task list"), **When** the agent processes the message, **Then** it initiates a task-creation flow (clarifying questions followed by a task proposal).
2. **Given** a user describes a feature idea (e.g., "We should support PDF export"), **When** the agent processes the message, **Then** it initiates an issue-recommendation flow.
3. **Given** a user asks to change a task's status (e.g., "Move the login task to Done"), **When** the agent processes the message, **Then** it initiates a status-update flow.
4. **Given** a user sends a general conversational message (e.g., "What can you help me with?"), **When** the agent processes the message, **Then** it responds conversationally without invoking any action tool.
5. **Given** a user sends an ambiguous message that could match multiple actions, **When** the agent processes it, **Then** it asks a clarifying question to determine the user's intent rather than guessing incorrectly.

---

### User Story 2 — Multi-Turn Conversation Memory (Priority: P1)

A user chats with the agent across several messages in the same session. The agent remembers earlier context — project details, preferences, prior decisions — so the user never needs to repeat themselves. When the user says "Create a component for that" after previously discussing a feature, the agent knows what "that" refers to.

**Why this priority**: Multi-turn memory is the foundational capability that distinguishes an intelligent agent from a stateless prompt-response system. Without session continuity, every other story degrades to single-shot behaviour and the user experience is no better than the existing system.

**Independent Test**: Can be tested by sending a sequence of related messages in one session and verifying the agent's responses correctly reference earlier context without the user restating it.

**Acceptance Scenarios**:

1. **Given** a user states context in an earlier message (e.g., "My project uses React and Node.js"), **When** they send a follow-up that references that context implicitly (e.g., "Create a component for the dashboard"), **Then** the agent uses the earlier context in its response and proposal.
2. **Given** a user starts a new session, **When** they send a message, **Then** no context from a previous or different user's session leaks into the response.
3. **Given** a long session with many messages, **When** the user continues chatting, **Then** the agent still references the most relevant prior context without noticeable delay or degraded quality.

---

### User Story 3 — Clarifying Questions Before Action (Priority: P1)

When a user requests an action (task creation, issue recommendation), the agent asks 2–3 targeted clarifying questions before committing to a proposal. The questions address gaps in the request — difficulty level, acceptance criteria, priority, or scope boundaries. Once the user answers, the agent produces a well-formed proposal incorporating those answers.

**Why this priority**: Clarifying questions are what make the agent feel collaborative rather than prescriptive. They prevent low-quality proposals and reduce the reject-revise cycle, directly improving task and issue quality.

**Independent Test**: Can be tested by sending a brief task description, verifying the agent asks relevant clarifying questions, providing answers, and confirming the resulting proposal incorporates those answers.

**Acceptance Scenarios**:

1. **Given** a user sends a task description with minimal detail (e.g., "Add dark mode"), **When** the agent processes it, **Then** it asks at least two clarifying questions before generating a task proposal.
2. **Given** a user provides a highly detailed request with all necessary information, **When** the agent processes it, **Then** it may skip clarifying questions and proceed directly to generating a proposal.
3. **Given** the agent has asked clarifying questions and the user responds, **When** the agent generates a proposal, **Then** the proposal reflects the user's answers accurately.
4. **Given** a user sends a very brief message (fewer than five words), **When** the agent processes it, **Then** the agent asks for more detail rather than generating an incomplete proposal.

---

### User Story 4 — Proposal Confirm/Reject Flow (Priority: P1)

After the agent generates a proposal (task, issue, or status change), the user reviews it and either confirms or rejects it. Confirmed proposals result in the corresponding external action (task created on board, issue created in GitHub, status updated). Rejected proposals prompt the agent to ask how to adjust.

**Why this priority**: The confirm/reject flow is the critical handoff between agent reasoning and real-world side effects. Without it, the agent either acts without consent or cannot complete actions at all. This flow preserves user control over all mutations.

**Independent Test**: Can be tested by triggering a proposal, confirming it, and verifying the action was taken — then repeating with a rejection and verifying no action occurs.

**Acceptance Scenarios**:

1. **Given** the agent presents a task proposal, **When** the user confirms it, **Then** a task is created on the project board with the proposed title, description, and difficulty.
2. **Given** the agent presents an issue recommendation, **When** the user confirms it, **Then** a GitHub issue is created with the recommended title, body, and labels.
3. **Given** the agent presents any proposal, **When** the user rejects it, **Then** no external action is taken and the agent asks how to revise the proposal.
4. **Given** the agent presents a status-change proposal, **When** the user confirms it, **Then** the task's status is updated on the project board.

---

### User Story 5 — Provider-Agnostic AI Backend (Priority: P2)

An administrator configures the system to use either GitHub Copilot or Azure OpenAI as the underlying AI provider. The chat experience, available tools, and conversation behaviour are identical regardless of the active provider. Switching providers requires only a configuration change, not code changes.

**Why this priority**: Provider flexibility is a deployment requirement. Some environments require Azure-hosted models for compliance while others prefer the Copilot integration. Supporting both from day one prevents a costly migration later.

**Independent Test**: Can be tested by configuring each provider in turn and running the same set of chat interactions, verifying equivalent tool selections and proposal structures.

**Acceptance Scenarios**:

1. **Given** the system is configured with the Copilot provider, **When** a user chats with the agent, **Then** the agent responds correctly using all available tools.
2. **Given** the system is configured with the Azure OpenAI provider, **When** a user performs the same interactions, **Then** the results are functionally equivalent to the Copilot provider.
3. **Given** an administrator switches providers via configuration, **When** existing sessions continue, **Then** the agent continues to function without data loss or session corruption.

---

### User Story 6 — Transcript Analysis (Priority: P2)

A user uploads a meeting transcript (text or file attachment). The agent analyses the content and produces a structured summary containing key decisions, action items, and follow-ups. The user can then convert any action item into a task proposal with a single confirmation step.

**Why this priority**: Transcript analysis is a high-value capability that demonstrates the agent's ability to handle longer-form input and chain multiple tools. It differentiates the system from a simple chatbot.

**Independent Test**: Can be tested by uploading a sample transcript, reviewing the generated summary, and optionally converting an action item into a task.

**Acceptance Scenarios**:

1. **Given** a user uploads a transcript, **When** the agent processes it, **Then** it returns a structured summary with key decisions, action items, and follow-ups.
2. **Given** the agent has produced action items, **When** the user requests a task from a specific item, **Then** the agent generates a pre-filled task proposal based on that action item.
3. **Given** the uploaded content cannot be interpreted as a transcript, **When** the agent processes it, **Then** it informs the user that the content is not a recognisable transcript format.

---

### User Story 7 — Real-Time Streaming Responses (Priority: P3)

A user sends a message in the web chat interface and sees the agent's response appear progressively, token by token, rather than waiting for the complete response. This provides immediate feedback that the agent is working and reduces perceived latency.

**Why this priority**: Streaming is an additive UX improvement that does not change functional behaviour. It can be delivered independently once the core agent is stable, and it significantly improves the perceived responsiveness of the experience.

**Independent Test**: Can be tested by sending a message in the browser and observing that response text appears incrementally before the full response is complete.

**Acceptance Scenarios**:

1. **Given** a user sends a message via the web chat interface, **When** the agent begins responding, **Then** text appears progressively within 2 seconds of the request.
2. **Given** streaming is in progress, **When** a connection interruption occurs, **Then** the interface falls back to the non-streaming endpoint and displays the complete response once available.
3. **Given** a user interacts via the Signal integration, **When** the agent responds, **Then** the full response is delivered as a single message (Signal does not support streaming).

---

### User Story 8 — Signal Chat Integration (Priority: P2)

A user sends a text message via the Signal messaging integration. The agent processes the message using the same reasoning and tools as the web chat, but responds with a single complete message (non-streaming). The experience is functionally equivalent to the web chat for all action types.

**Why this priority**: Signal is an existing supported channel. Maintaining compatibility ensures that the agent migration does not break an active user workflow. It also validates that the agent's interface is channel-agnostic.

**Independent Test**: Can be tested by sending messages through the Signal integration and verifying the agent responds with correct actions and proposals.

**Acceptance Scenarios**:

1. **Given** a user sends a task-related message via Signal, **When** the agent processes it, **Then** the response includes the same proposal structure as the web interface.
2. **Given** a user confirms a proposal via Signal, **When** the system processes the confirmation, **Then** the corresponding external action is taken (task/issue created, status changed).
3. **Given** the agent encounters an error during processing, **When** it responds via Signal, **Then** the user receives a clear, friendly error message.

---

### User Story 9 — Observability and Security (Priority: P3)

An operator reviews structured logs to monitor agent performance — response times, token usage, and which tools are being invoked. The system automatically detects and blocks prompt-injection attempts, and validates all tool arguments before execution, preventing the agent from being manipulated into performing unintended actions.

**Why this priority**: Observability and security are non-functional requirements essential for production readiness. They do not change user-facing behaviour but are critical for operational confidence and compliance.

**Independent Test**: Can be tested by sending chat messages and verifying structured log entries appear with timing and token data, and by sending known prompt-injection patterns and verifying they are blocked.

**Acceptance Scenarios**:

1. **Given** a user sends a chat message, **When** the agent processes it, **Then** a structured log entry is created containing response time, token count, and tool(s) invoked.
2. **Given** a message contains a known prompt-injection pattern, **When** the system evaluates it, **Then** the injection is detected and the message is rejected with a safe, user-facing explanation.
3. **Given** a tool receives arguments that violate its expected schema, **When** the validation layer checks them, **Then** the invocation is blocked and an error is logged.

---

### Edge Cases

- **AI provider unreachable (timeout, rate limit, outage):** The system returns a user-friendly error message, does not leave the session in a broken state, and retries internally with exponential back-off before surfacing the error.

- **Message does not match any known tool capability:** The agent responds conversationally rather than failing or invoking an incorrect tool.

- **Concurrent status changes to the same task:** Changes are applied in order of receipt. If the first change invalidates the second, the second user is notified of the conflict.

- **`ai_enhance=False` configuration flag set:** The system bypasses the agent entirely and uses simple title-only generation, preserving existing behaviour for environments that do not want AI-enhanced features.

- **Very large conversation history:** The system summarises older context to keep the working window within model context limits while retaining the most relevant information.

- **Tool invocation with missing user permissions:** The agent informs the user of the missing permissions and does not perform the action.

- **Simultaneous streaming and non-streaming requests in the same session:** Both request types operate correctly without interfering with each other or corrupting session state.

- **Empty or whitespace-only messages:** The agent responds with a helpful prompt asking the user to describe what they need.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow the agent to autonomously decide which tool to invoke based on message content and conversation context, replacing the current hardcoded priority-dispatch cascade.
- **FR-002**: System MUST support the following agent tools: create task proposal, create issue recommendation, update task status, analyse transcript, ask clarifying question, get project context, and get pipeline list.
- **FR-003**: System MUST maintain multi-turn conversation memory within a session so the agent can reference information from earlier messages without the user repeating it.
- **FR-004**: System MUST isolate conversation context between sessions — no context from one session may leak into another.
- **FR-005**: System MUST support both GitHub Copilot and Azure OpenAI as interchangeable AI provider backends, selectable through configuration without code changes.
- **FR-006**: System MUST preserve the existing REST API contract so the frontend requires only additive changes (new streaming endpoint).
- **FR-007**: System MUST expose a streaming endpoint that delivers agent responses progressively via server-sent events.
- **FR-008**: System MUST support the Signal chat integration using the same agent logic in non-streaming mode.
- **FR-009**: System MUST ask 2–3 targeted clarifying questions before acting on task-creation and issue-recommendation requests when the user's message lacks sufficient detail.
- **FR-010**: System MUST support the confirm/reject flow for all proposals — proposals generate structured recommendations, only confirmed proposals result in external side effects.
- **FR-011**: System MUST log each agent interaction with timing, token count, and tool invocation details.
- **FR-012**: System MUST detect and block prompt-injection attempts before they reach the agent's reasoning layer.
- **FR-013**: System MUST validate tool arguments against their expected schemas before execution.
- **FR-014**: System MUST bypass the agent and use simple title-only generation when `ai_enhance=False` is configured.
- **FR-015**: System MUST inject runtime context (project identifier, authentication token, session identifier) into tool invocations without exposing this context to the language model's visible schema.
- **FR-016**: System MUST handle AI provider failures (timeouts, rate limits, service outages) gracefully by returning user-friendly error messages and preserving session state.
- **FR-017**: System MUST deprecate existing direct-LLM service layers and per-action prompt modules with deprecation warnings, retaining them until v0.3.0.
- **FR-018**: System MUST continue to support `/agent` meta-command handling, file upload processing, and proposal confirm/reject endpoints without modification to their external behaviour.
- **FR-019**: System MUST support progressive rendering of streaming responses in the web frontend, with automatic fallback to non-streaming if the streaming connection fails.
- **FR-020**: System MUST keep the existing conversation history storage as the source of truth and synchronise summaries into agent session state rather than replacing the storage layer.

### Key Entities

- **Agent Session**: A multi-turn conversation context bound to a specific user session. Contains conversation history summaries, active state, and provider configuration. Maps one-to-one with the application's existing session concept.
- **Agent Tool**: A discrete capability the agent can invoke (e.g., create task proposal, analyse transcript). Each tool has a defined input schema visible to the language model and runtime context requirements invisible to it.
- **Tool Invocation Context**: Runtime data (project identifier, authentication token, session identifier) passed to tools at execution time, invisible to the language model's schema.
- **Agent Provider**: An abstraction over the underlying AI service (GitHub Copilot or Azure OpenAI). Responsible for model communication and interchangeable via configuration.
- **Proposal**: A structured action recommendation (task, issue, or status change) generated by the agent, awaiting user confirmation or rejection before any external action is performed.
- **Agent Middleware**: A processing layer that intercepts agent interactions for cross-cutting concerns — logging, security (prompt-injection detection), and validation (tool argument checking).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a task-creation flow (message → clarifying questions → proposal → confirmation → task created) in under 2 minutes of active interaction time.
- **SC-002**: The agent correctly selects the appropriate tool for at least 95% of user messages that match a known capability, as measured by evaluation against a representative message set.
- **SC-003**: Multi-turn conversations maintain context accurately — the agent correctly references earlier context in at least 90% of follow-up messages within the same session.
- **SC-004**: Switching between AI providers produces functionally equivalent responses — the same test interactions yield the same tool selections and proposal structures with both providers.
- **SC-005**: Streaming responses begin appearing in the web interface within 2 seconds of the user sending a message.
- **SC-006**: All existing chat interactions (task creation, issue recommendation, status change, transcript analysis) continue to work without regression after migration.
- **SC-007**: 100% of existing automated tests pass after migration, and new tests cover all agent tools, session management, and response conversion.
- **SC-008**: Known prompt-injection patterns are blocked with zero successful injections reaching the agent during testing.
- **SC-009**: Every agent interaction produces a structured log entry containing response time, token count, and tool invocation details.
- **SC-010**: The system operates correctly when deployed via container orchestration with both AI provider configurations, completing end-to-end chat flows without errors.
- **SC-011**: The Signal integration delivers agent responses to text messages with equivalent quality to the web chat interface.

## Assumptions

- The Microsoft Agent Framework packages are stable and support the required features: function tools, sessions, middleware, and streaming.
- The existing ChatMessage schema is sufficient to carry agent responses without breaking changes; the streaming endpoint is purely additive.
- The existing conversation history storage (SQLite) is adequate for v0.2.0 and does not need to be replaced.
- Existing utility functions for task identification are reusable by the new agent tools without modification.
- Per-user authentication with the GitHub Copilot provider can be handled through per-run token passing or a bounded ephemeral pool if the framework does not support per-run tokens natively.
- MCP tool integration is explicitly out of scope for v0.2.0 (deferred to v0.4.0), but the design should accommodate future MCP tools.
- Deprecation means adding warnings only — actual removal of old layers is deferred to v0.3.0.
- Performance targets (2-second streaming start, sub-2-minute task creation) are based on standard web application expectations and current system behaviour.
