# Feature Specification: Intelligent Chat Agent (Microsoft Agent Framework)

**Feature Branch**: `001-intelligent-chat-agent`  
**Created**: 2026-03-29  
**Status**: Draft  
**Input**: User description: "Replace the current completion-based AIAgentService with a Microsoft Agent Framework Agent that uses function tools, sessions for multi-turn memory, and middleware for logging/security. The priority-dispatch cascade becomes the agent's natural reasoning. The REST API contract stays the same so the frontend needs minimal changes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Chat-Driven Task Creation (Priority: P1)

A project member opens the chat interface and describes a piece of work in natural language (e.g., "Add a dark-mode toggle to the settings page"). The agent asks 2–3 clarifying questions (difficulty, acceptance criteria, assignee preference) before presenting a structured task proposal. The user reviews the proposal and confirms or rejects it. On confirmation the task is created in the project board.

**Why this priority**: Task creation from chat is the most frequently used action today. Replacing the current rigid prompt-and-parse flow with an agent that reasons about which tool to call is the core value of v0.2.0 — it proves the new architecture end-to-end.

**Independent Test**: Can be fully tested by sending a chat message describing work, answering the agent's follow-up questions, confirming the proposal, and verifying the task appears on the project board.

**Acceptance Scenarios**:

1. **Given** a user is in an active chat session, **When** they describe a task in free-form text, **Then** the agent asks at least one clarifying question before producing a task proposal.
2. **Given** the agent has presented a task proposal, **When** the user confirms it, **Then** a task is created on the project board with the proposed title, description, and difficulty.
3. **Given** the agent has presented a task proposal, **When** the user rejects it, **Then** no task is created and the agent asks how to adjust the proposal.
4. **Given** a user provides a very brief message (fewer than five words), **When** the agent processes it, **Then** the agent asks for more detail rather than generating an incomplete proposal.

---

### User Story 2 — Multi-Turn Conversation Memory (Priority: P1)

A user chats with the agent over several messages within the same session. Earlier context (e.g., "My project uses React and TypeScript") is retained so the user does not have to repeat information. When the user later says "Create a component for that," the agent understands what "that" refers to from conversation history.

**Why this priority**: Multi-turn memory is the foundational capability that makes the agent feel intelligent rather than stateless. Without it, every other story degrades to the existing single-shot behaviour.

**Independent Test**: Can be tested by sending a sequence of related messages in one session and verifying the agent's responses reference earlier context without the user restating it.

**Acceptance Scenarios**:

1. **Given** a user has provided context in a previous message (e.g., project technology stack), **When** they send a follow-up message that references that context implicitly, **Then** the agent responds correctly using the earlier information.
2. **Given** a user starts a new session, **When** they send a message, **Then** no stale context from a different session leaks into the response.
3. **Given** a session has accumulated many messages, **When** the user continues chatting, **Then** the agent still references the most relevant prior context without noticeable delay.

---

### User Story 3 — Feature Request to GitHub Issue (Priority: P2)

A user describes a feature idea in chat (e.g., "We should let users export reports as PDF"). The agent recognises the intent as a feature request, asks clarifying questions about scope and priority, and produces a structured issue recommendation. On confirmation the issue is created in the connected GitHub repository.

**Why this priority**: Issue creation is the second-most-used chat action. Moving it to agent-based reasoning removes the brittle intent-detection heuristic currently in place.

**Independent Test**: Can be tested by sending a feature-request message, answering the agent's follow-up questions, confirming the recommendation, and verifying a GitHub issue is created with the expected fields.

**Acceptance Scenarios**:

1. **Given** a user describes a feature idea, **When** the agent processes the message, **Then** it asks clarifying questions about scope, user story, and priority before generating an issue recommendation.
2. **Given** the agent presents an issue recommendation, **When** the user confirms, **Then** a GitHub issue is created with the recommended title, body, and labels.
3. **Given** the user rejects the recommendation, **When** they provide feedback, **Then** the agent revises the recommendation accordingly.

---

### User Story 4 — Task Status Update via Chat (Priority: P2)

A user asks the agent to change a task's status (e.g., "Move the dark-mode task to In Review"). The agent identifies the correct task and target status, confirms the change with the user, and updates the task on the project board.

**Why this priority**: Status updates are a frequent lightweight action. Supporting them through the agent eliminates context-switching to the board UI.

**Independent Test**: Can be tested by sending a status-change request, confirming the proposed change, and verifying the task's status is updated on the board.

**Acceptance Scenarios**:

1. **Given** a user requests a status change with an unambiguous task reference, **When** the agent processes the request, **Then** it confirms the intended task and target status before applying the change.
2. **Given** a user provides an ambiguous task reference, **When** the agent processes it, **Then** it presents a short list of matching tasks and asks the user to choose.
3. **Given** the target status is invalid for the task's current workflow state, **When** the agent attempts the update, **Then** it informs the user of the valid transitions.

---

### User Story 5 — Transcript Analysis (Priority: P3)

A user uploads a meeting transcript (text or file). The agent analyses the content and produces a summary with extracted action items, decisions, and follow-ups. The user can then convert any action item into a task proposal with a single confirmation.

**Why this priority**: Transcript analysis is a high-value but less frequent action. It demonstrates the agent's ability to handle longer-form input and chain multiple tool calls.

**Independent Test**: Can be tested by uploading a sample transcript, reviewing the generated summary and action items, and optionally converting one action item into a task.

**Acceptance Scenarios**:

1. **Given** a user uploads a transcript, **When** the agent processes it, **Then** it returns a summary containing key decisions, action items, and follow-ups.
2. **Given** the agent has produced action items from a transcript, **When** the user asks to create a task from a specific action item, **Then** the agent generates a task proposal pre-filled with information from that action item.
3. **Given** the uploaded content is not a valid transcript (e.g., random binary data), **When** the agent processes it, **Then** it informs the user that the content could not be interpreted as a transcript.

---

### User Story 6 — Real-Time Streaming Responses (Priority: P3)

A user sends a message in the chat interface and sees the agent's response appear progressively (token by token) rather than waiting for the full response. This provides immediate feedback that the agent is working and reduces perceived latency.

**Why this priority**: Streaming is an additive UX improvement that does not change functional behaviour. It can be delivered independently after the core agent is stable.

**Independent Test**: Can be tested by sending a message in the browser and observing that response text appears incrementally before the full response is complete.

**Acceptance Scenarios**:

1. **Given** a user sends a message via the web chat interface, **When** the agent begins responding, **Then** text appears progressively within 2 seconds of the request.
2. **Given** streaming is in progress, **When** a network interruption occurs, **Then** the interface falls back to a non-streaming request and displays the complete response once available.
3. **Given** a user interacts via the Signal integration (non-streaming channel), **When** the agent responds, **Then** the full response is delivered as a single message without degradation.

---

### User Story 7 — Provider-Agnostic AI Backend (Priority: P2)

An administrator configures the system to use either GitHub Copilot or Azure OpenAI as the underlying AI provider. The chat experience is identical regardless of which provider is active — the same tools, instructions, and conversation behaviour apply.

**Why this priority**: Provider flexibility is a deployment requirement. Some environments mandate Azure-hosted models for compliance reasons while others prefer the Copilot integration.

**Independent Test**: Can be tested by switching the AI provider configuration and verifying that the same chat interactions produce equivalent results with both providers.

**Acceptance Scenarios**:

1. **Given** the system is configured with the Copilot provider, **When** a user chats, **Then** the agent responds correctly using all available tools.
2. **Given** the system is configured with the Azure OpenAI provider, **When** a user chats, **Then** the agent responds identically to the Copilot provider experience.
3. **Given** an administrator switches providers, **When** existing sessions continue, **Then** conversation history is preserved and the agent continues seamlessly.

---

### User Story 8 — Observability and Security (Priority: P3)

An operator reviews logs to see timing, token usage, and tool invocation details for each agent interaction. The system detects and blocks prompt-injection attempts before they reach the agent, and validates all tool arguments before execution.

**Why this priority**: Observability and security are non-functional requirements that are essential for production readiness but do not change user-facing behaviour. They can be layered in after the core agent is functional.

**Independent Test**: Can be tested by sending chat messages and verifying that structured log entries appear with timing and token data, and by sending known prompt-injection patterns and verifying they are blocked.

**Acceptance Scenarios**:

1. **Given** a user sends a chat message, **When** the agent processes it, **Then** a structured log entry is created containing response time, token count, and tool(s) invoked.
2. **Given** a message contains a known prompt-injection pattern, **When** the system processes it, **Then** the injection is detected and the message is rejected with a safe user-facing explanation.
3. **Given** a tool receives arguments that violate its expected schema, **When** the system validates them, **Then** the invocation is blocked and an error is logged.

---

### Edge Cases

- What happens when the AI provider is unreachable (network timeout, rate limit, service outage)?  
  The system returns a user-friendly error message and does not leave the session in a broken state. Retries are handled internally with exponential back-off before surfacing the error.

- What happens when a user sends a message that does not match any known tool capability?  
  The agent responds conversationally (general-purpose chat) rather than failing or invoking an incorrect tool.

- What happens when two users reference the same task simultaneously for a status change?  
  The system applies changes in order of receipt. If the first change makes the second invalid, the second user is notified of the conflict.

- What happens when the `ai_enhance=False` configuration flag is set?  
  The system bypasses the agent entirely and uses simple title-only generation, preserving existing behaviour for environments that do not want AI-enhanced features.

- What happens when a session's conversation history grows very large?  
  The system summarises older context to keep the working window within the model's context limits while retaining the most relevant information.

- What happens when the agent attempts to call a tool that requires permissions the user does not have?  
  The agent returns an explanation of the missing permissions and does not perform the action.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow the agent to decide which tool to invoke based on the user's message content and conversation context, replacing the current hardcoded priority-dispatch cascade.
- **FR-002**: System MUST support the following agent tools: create task proposal, create issue recommendation, update task status, analyse transcript, ask clarifying question, get project context, and get pipeline list.
- **FR-003**: System MUST maintain multi-turn conversation memory within a session so the agent can reference information from earlier messages.
- **FR-004**: System MUST map each user session to an agent session, ensuring conversation isolation between different users and sessions.
- **FR-005**: System MUST support both GitHub Copilot and Azure OpenAI as interchangeable AI provider backends, selectable via configuration.
- **FR-006**: System MUST preserve the existing REST API contract so the frontend requires only additive changes (streaming endpoint).
- **FR-007**: System MUST deliver agent responses progressively to the web interface, providing immediate visual feedback as the response is generated.
- **FR-008**: System MUST continue to support the Signal chat integration using the same agent logic in non-streaming mode.
- **FR-009**: System MUST ask 2–3 clarifying questions before taking action on task creation and issue recommendation requests, unless the user's message provides sufficient detail.
- **FR-010**: System MUST support the confirm/reject flow for proposals — the agent generates a proposal, the user confirms or rejects, and only confirmed proposals result in external actions (task creation, issue creation, status change).
- **FR-011**: System MUST log each agent interaction with timing, token count, and tool invocation details.
- **FR-012**: System MUST detect and block prompt-injection attempts before they reach the agent.
- **FR-013**: System MUST validate tool arguments against their expected schemas before execution.
- **FR-014**: System MUST bypass the agent and use simple title-only generation when the `ai_enhance=False` configuration flag is set.
- **FR-015**: System MUST provide tools with the necessary operational context (active project, user identity, session) automatically, without requiring users to supply this information in their messages.
- **FR-016**: System MUST handle AI provider failures (timeouts, rate limits, outages) gracefully by returning user-friendly error messages without corrupting session state.
- **FR-017**: System MUST deprecate the existing AIAgentService, completion providers, and per-action prompt modules with deprecation warnings, retaining them for backward compatibility until v0.3.0.
- **FR-018**: System MUST support the existing `/agent` meta-command handling, file upload processing, and proposal confirm/reject endpoints without modification.
- **FR-019**: System MUST support the frontend displaying streaming responses progressively, with a fallback to the non-streaming endpoint if streaming fails.
- **FR-020**: System MUST keep the existing conversation history storage as the source of truth, synchronising relevant context into agent sessions rather than replacing the storage layer.

### Key Entities

- **Agent Session**: Represents a multi-turn conversation context bound to a specific user session. Contains conversation history summaries, active tool state, and provider-agnostic configuration. Maps one-to-one with the existing application session.
- **Agent Tool**: A discrete capability the agent can invoke (e.g., create task proposal, analyse transcript). Each tool has a defined input schema, runtime context requirements, and a structured output format.
- **Operational Context**: The set of runtime information (active project, user identity, session) that tools need to act on behalf of the user. Provided automatically so users never need to supply it manually.
- **Agent Provider**: The underlying AI service (GitHub Copilot or Azure OpenAI) that powers the agent's reasoning. Interchangeable via configuration without affecting the user experience.
- **Proposal**: A structured action recommendation (task, issue, or status change) generated by the agent and awaiting user confirmation or rejection before execution.
- **Interaction Safeguards**: The set of cross-cutting protections applied to every agent interaction: logging (timing, token usage), security (prompt-injection detection), and validation (tool argument checking).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a task-creation flow (message → clarifying questions → proposal → confirmation → task created) in under 2 minutes of active interaction time.
- **SC-002**: The agent correctly selects the appropriate tool for at least 95% of user messages that match a known capability, as measured by manual evaluation of a representative message set.
- **SC-003**: Multi-turn conversations maintain context accurately — the agent correctly references earlier context in at least 90% of follow-up messages within the same session.
- **SC-004**: Switching between AI providers produces functionally equivalent responses — the same set of test interactions yields the same tool selections and proposal structures with both providers.
- **SC-005**: Streaming responses begin arriving at the frontend within 2 seconds of the user sending a message.
- **SC-006**: All existing chat interactions (task creation, issue recommendation, status change, transcript analysis) continue to work without regression after the migration.
- **SC-007**: All existing automated tests pass after the migration, and new tests cover every agent capability and session behaviour.
- **SC-008**: Known prompt-injection patterns are blocked with zero successful injections reaching the agent in testing.
- **SC-009**: Every agent interaction produces a structured log entry containing response time, token count, and tool invocation details.
- **SC-010**: The complete system can be built and deployed from source, completing an end-to-end chat flow without errors using both supported AI provider configurations.
- **SC-011**: The Signal integration delivers agent responses to text messages with the same quality as the web chat interface.

## Assumptions

- The Microsoft Agent Framework packages are stable and support the required features (function tools, sessions, middleware, streaming).
- The existing chat message schema is sufficient to carry agent responses — no schema changes are needed for the core flow; streaming is additive.
- The existing conversation history storage is adequate for v0.2.0 and does not need to be replaced.
- The task-identification utility from the current service layer is reusable by the new task status update capability without modification.
- Per-user authentication with the GitHub Copilot provider can be handled through per-run token passing or a bounded ephemeral agent pool if the framework does not support per-run tokens natively.
- MCP tool integration is explicitly out of scope for v0.2.0 and deferred to v0.4.0, but the tool registration design should accommodate future MCP tools.
- The deprecation of old service layers (AIAgentService, completion providers, per-action prompts) means adding deprecation warnings only — actual removal is deferred to v0.3.0.
- Performance targets (2-second streaming start, sub-2-minute task creation) are based on standard web application expectations and current system behaviour.
