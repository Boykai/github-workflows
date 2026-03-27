# Data Model: Add 9 GitHub Copilot Slash Commands to Solune Chat

**Feature**: 001-copilot-slash-commands | **Date**: 2026-03-27

## Entity Definitions

### 1. CommandDefinition (Frontend — Modified)

**File**: `solune/frontend/src/lib/commands/types.ts`
**Change type**: Add optional `category` field

```typescript
export interface CommandDefinition {
  name: string;
  description: string;
  syntax: string;
  handler: CommandHandler;
  parameterSchema?: ParameterSchema;
  passthrough?: boolean;
  category?: 'solune' | 'copilot';  // NEW — enables categorical grouping in autocomplete
}
```

**Field details**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Command name without leading `/` (e.g., `"explain"`) |
| `description` | `string` | Yes | Short description shown in help/autocomplete |
| `syntax` | `string` | Yes | Usage syntax shown in help (e.g., `"/explain <code or question>"`) |
| `handler` | `CommandHandler` | Yes | Function executed when command runs locally |
| `parameterSchema` | `ParameterSchema` | No | Schema for parameter validation/autocomplete |
| `passthrough` | `boolean` | No | When `true`, forward to backend instead of local execution |
| `category` | `'solune' \| 'copilot'` | No | Grouping category for autocomplete dropdown. Defaults to `'solune'` when unset |

**Validation rules**:
- `category` accepts only `'solune'` or `'copilot'` — no other values
- All existing commands default to `'solune'` (via explicit tagging or fallback logic)
- All 9 new Copilot commands must have `category: 'copilot'`

---

### 2. CopilotCommand (Backend — New conceptual entity)

**File**: `solune/backend/src/services/copilot_commands.py`
**Change type**: New — represented as data structures (set + dict), not a class

This is not a persisted entity — it's a runtime constant set and prompt mapping.

```python
COPILOT_COMMANDS: set[str] = {
    "explain", "fix", "doc", "tests", "setupTests",
    "new", "newNotebook", "search", "startDebugging",
}

COPILOT_COMMAND_PROMPTS: dict[str, str] = {
    "explain": "You are a coding assistant...",
    "fix": "You are a code repair assistant...",
    # ... (9 entries)
}
```

**Field details**:

| Field | Type | Description |
|-------|------|-------------|
| `COPILOT_COMMANDS` | `set[str]` | Canonical set of 9 command names (without `/` prefix) |
| `COPILOT_COMMAND_PROMPTS` | `dict[str, str]` | Maps each command name to its intent-specific system prompt |

**Validation rules**:
- Every key in `COPILOT_COMMAND_PROMPTS` must exist in `COPILOT_COMMANDS`
- Every entry in `COPILOT_COMMANDS` must have a corresponding prompt in `COPILOT_COMMAND_PROMPTS`
- Command names are case-sensitive (lowercase), matching is done after lowering user input

---

### 3. ChatMessage (Backend — Read Only)

**File**: `solune/backend/src/models/chat.py`
**Change type**: No modification — reused as-is

```python
class ChatMessage(BaseModel):
    message_id: UUID = Field(default_factory=uuid4)
    session_id: UUID = Field(...)
    sender_type: SenderType = Field(...)
    content: str = Field(..., max_length=100000)
    action_type: ActionType | None = Field(default=None)
    action_data: dict[str, Any] | None = Field(default=None)
    timestamp: datetime = Field(default_factory=utcnow)
```

**Usage in this feature**:
- `_handle_copilot_command()` creates a `ChatMessage(session_id=..., sender_type=SenderType.ASSISTANT, content=<copilot_response>)` and calls `add_message()` to persist it
- The user's input message is already persisted by `send_message()` before dispatch

---

### 4. ParsedCommand (Frontend — Read Only)

**File**: `solune/frontend/src/lib/commands/types.ts`
**Change type**: No modification — reused as-is

```typescript
export interface ParsedCommand {
  isCommand: boolean;
  name: string | null;
  args: string;
  raw: string;
}
```

**Usage in this feature**:
- `parseCommand("/explain What is a closure?")` → `{ isCommand: true, name: "explain", args: "What is a closure?", raw: "..." }`
- The registry's `getCommand("explain")` returns the `CommandDefinition` with `passthrough: true`

---

## Relationships

```text
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│                                                                 │
│  User types "/explain What is a closure?"                       │
│         │                                                       │
│         ▼                                                       │
│  parseCommand() → ParsedCommand { name: "explain", args: ... }  │
│         │                                                       │
│         ▼                                                       │
│  getCommand("explain") → CommandDefinition                      │
│    { passthrough: true, category: 'copilot' }                   │
│         │                                                       │
│         ▼                                                       │
│  useChat forwards raw content to POST /chat/messages            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                         BACKEND                                 │
│                                                                 │
│  send_message() dispatch chain:                                 │
│         │                                                       │
│  Priority 0.0: _handle_agent_command() → None (not /agent)      │
│         │                                                       │
│  Priority 0.1: _handle_copilot_command()                        │
│         │  is_copilot_command("/explain What is a closure?")     │
│         │  → ("explain", "What is a closure?")                  │
│         │                                                       │
│         ▼                                                       │
│  execute_copilot_command("explain", "What is a closure?", token)│
│         │  messages = [                                         │
│         │    {"role": "system", "content": EXPLAIN_PROMPT},     │
│         │    {"role": "user", "content": "What is a closure?"}  │
│         │  ]                                                    │
│         ▼                                                       │
│  CopilotCompletionProvider.complete(messages, github_token=...) │
│         │                                                       │
│         ▼                                                       │
│  ChatMessage(sender_type=ASSISTANT, content=response)           │
│  → add_message() → return to user                              │
└─────────────────────────────────────────────────────────────────┘
```

## State Transitions

No state machines in this feature. Commands are stateless request-response operations:

1. **User submits command** → message persisted as `SenderType.USER`
2. **Backend processes command** → calls `CopilotCompletionProvider.complete()`
3. **Response persisted** → `ChatMessage(sender_type=SenderType.ASSISTANT)` via `add_message()`
4. **Response returned** → displayed in chat UI

Error state: If `CopilotCompletionProvider.complete()` throws, the handler catches the exception and returns a generic error `ChatMessage` instead.
