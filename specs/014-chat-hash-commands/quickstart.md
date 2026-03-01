# Quickstart: Enhance Chat # Commands — App-Wide Settings Control & #help Command with Test Coverage

**Feature**: 014-chat-hash-commands | **Date**: 2026-02-28

## Prerequisites

- Node.js 20+
- npm (ships with Node.js)

## Setup

### Frontend

```bash
cd frontend
npm ci
```

> **Note**: This feature is entirely frontend. No backend setup or changes required.

## Running Tests

### All Frontend Unit Tests

```bash
cd frontend
npm test
```

### Command System Tests Only

```bash
cd frontend

# Run all command-related tests
npx vitest run src/lib/commands/
npx vitest run src/hooks/useCommands.test.tsx
npx vitest run src/components/chat/CommandAutocomplete.test.tsx
npx vitest run src/components/chat/ChatInterface.test.tsx

# Run a specific test file
npx vitest run src/lib/commands/registry.test.ts
npx vitest run src/lib/commands/handlers/help.test.ts
npx vitest run src/lib/commands/handlers/settings.test.ts
```

### Watch Mode (re-runs on file changes)

```bash
cd frontend
npm run test:watch
```

### With Coverage

```bash
cd frontend
npm run test:coverage
```

## Linting and Type Checking

```bash
cd frontend

# Lint
npm run lint

# Type check
npm run type-check

# Build (also validates types)
npm run build
```

## Key Directories

| Path | Description |
|------|-------------|
| `frontend/src/lib/commands/registry.ts` | Command registry — single source of truth for all commands |
| `frontend/src/lib/commands/types.ts` | TypeScript type definitions for the command system |
| `frontend/src/lib/commands/handlers/help.ts` | `#help` command handler |
| `frontend/src/lib/commands/handlers/settings.ts` | Settings command handlers (`#theme`, `#language`, etc.) |
| `frontend/src/hooks/useCommands.ts` | React hook for command parsing, execution, and autocomplete |
| `frontend/src/components/chat/CommandAutocomplete.tsx` | Autocomplete overlay component |
| `frontend/src/components/chat/ChatInterface.tsx` | Main chat UI (modified to integrate commands) |
| `frontend/src/components/chat/SystemMessage.tsx` | System message display component |

## Workflow for This Feature

### 1. Foundation Phase (Command Registry & Types)
- Create `types.ts` with all command system interfaces
- Create `registry.ts` with the command map and helper functions
- Write `registry.test.ts` with registration, lookup, and filtering tests

### 2. Command Handlers Phase
- Implement `help.ts` handler (generates formatted command list from registry)
- Implement `settings.ts` handlers (theme, language, notifications, view)
- Write handler tests covering valid values, invalid values, and missing arguments

### 3. Hook Phase (useCommands)
- Create `useCommands.ts` hook with `parseCommand()`, `executeCommand()`, and `getFilteredCommands()`
- Integrate with `useTheme()` and `useSettings()` for the command context
- Write hook tests with `renderHook`

### 4. UI Integration Phase
- Create `CommandAutocomplete.tsx` component with keyboard navigation
- Create `SystemMessage.tsx` for displaying command responses
- Modify `ChatInterface.tsx` to intercept commands and render autocomplete
- Modify `useChat.ts` to support adding local system messages

### 5. Testing Phase
- Write integration tests for the full command flow in `ChatInterface.test.tsx`
- Verify all edge cases: bare `#`, invalid commands, case insensitivity, whitespace
- Run full test suite to confirm no regressions

### 6. Verification
- Run full suite: `cd frontend && npm test`
- Type check: `cd frontend && npm run type-check`
- Lint: `cd frontend && npm run lint`
- Build: `cd frontend && npm run build`
- Manual test: Run `npm run dev`, open chat, type `#help`, `#theme dark`, verify behavior
