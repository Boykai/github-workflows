# Quickstart: Add GitHub Copilot Slash Commands to Solune Chat

**Feature Branch**: `001-copilot-slash-commands`
**Date**: 2026-03-25

## Prerequisites

- Node.js 20+ (CI) or 22+ (devcontainer)
- Python 3.12+ (CI) or 3.13+ (devcontainer)
- npm and pip available

## Setup

### Frontend

```bash
cd solune/frontend
npm install
```

### Backend

```bash
cd solune/backend
pip install -e ".[dev]"
```

## Development Workflow

### Adding a New Local Command

1. **Create or extend a handler file** in `solune/frontend/src/lib/commands/handlers/`:

```typescript
// handlers/session.ts
import type { CommandContext, CommandResult } from '../types';

export async function clearHandler(_args: string, context: CommandContext): Promise<CommandResult> {
  await context.clearChat();
  return { success: true, message: '🗑️ Chat cleared.', clearInput: true };
}
```

2. **Register in the command registry** (`solune/frontend/src/lib/commands/registry.ts`):

```typescript
import { clearHandler } from './handlers/session';

registerCommand({
  name: 'clear',
  description: 'Clear all chat messages',
  syntax: '/clear',
  handler: clearHandler,
});
```

3. **The command automatically appears in**:
   - `/help` output (via `getAllCommands()`)
   - HelpPage table (via `getAllCommands()`)
   - Chat autocomplete (`/cl...` suggestions)

### Adding a New Passthrough Command

1. **Create a stub handler** that returns `passthrough: true`:

```typescript
// handlers/advanced.ts
import type { CommandResult } from '../types';

export function modelHandler(): CommandResult {
  return { success: true, message: '', clearInput: true, passthrough: true };
}
```

2. **Register with `passthrough: true`**:

```typescript
registerCommand({
  name: 'model',
  description: 'Show or switch the AI model',
  syntax: '/model [MODEL]',
  handler: modelHandler,
  passthrough: true,
});
```

3. **The backend handles the command** via the existing `POST /api/v1/chat/messages` endpoint. The AI service interprets the `/model` prefix in the message content.

### Extending CommandContext (if needed)

If a local command needs access to chat state or actions not in the current `CommandContext`:

1. **Add the field to `CommandContext`** in `types.ts`:

```typescript
export interface CommandContext {
  // ... existing fields ...
  clearChat: () => Promise<void>;  // NEW
  messages: ChatMessage[];          // NEW
}
```

2. **Provide the value in `useCommands.ts`**:

```typescript
const buildContext = useCallback(
  (): CommandContext => ({
    // ... existing fields ...
    clearChat,   // from useChat
    messages,    // from useChat
  }),
  [/* ... deps ... */]
);
```

## Testing

### Frontend Tests

```bash
cd solune/frontend

# Run all tests
npm run test

# Run specific command tests
npm run test -- src/lib/commands/registry.test.ts
npm run test -- src/lib/commands/handlers/settings.test.ts
npm run test -- src/lib/commands/handlers/help.test.ts

# Lint
npm run lint

# Type check
npm run build
```

### Backend Tests

```bash
cd solune/backend

# Run all tests
pytest -q

# Run chat-specific tests
pytest -q tests/unit/test_api_chat.py tests/unit/test_chat_store.py

# Lint
ruff check src/ tests/
ruff format --check src/ tests/

# Type check
pyright src/
```

## Key Files

| File | Purpose |
|------|---------|
| `solune/frontend/src/lib/commands/types.ts` | Type definitions (CommandDefinition, CommandContext, CommandResult) |
| `solune/frontend/src/lib/commands/registry.ts` | Command registry — register new commands here |
| `solune/frontend/src/lib/commands/handlers/*.ts` | Command handler implementations |
| `solune/frontend/src/hooks/useCommands.ts` | Hook providing command execution to components |
| `solune/frontend/src/hooks/useChat.ts` | Main chat hook — dispatches commands vs. messages |
| `solune/frontend/src/pages/HelpPage.tsx` | Help page — reads from registry automatically |
| `solune/frontend/src/components/chat/CommandAutocomplete.tsx` | Autocomplete overlay |
| `solune/backend/src/api/chat.py` | Backend chat API routes |
| `solune/backend/src/services/chat_store.py` | Chat message persistence |

## Implementation Order

1. **Phase 1**: Extend `CommandContext` with `clearChat` and `messages` (if needed)
2. **Phase 2**: Create handler files (`session.ts`, `monitoring.ts`, `advanced.ts`)
3. **Phase 3**: Add `/experimental` handler to existing `settings.ts`
4. **Phase 4**: Register all 11 in-scope new commands in `registry.ts`
5. **Phase 5**: Add tests for each handler file
6. **Phase 6**: Verify HelpPage and `/help` display all 17 in-scope commands
7. **Phase 7**: End-to-end verification with dev server
