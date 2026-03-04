# Quickstart: Enhance #help and General # Commands UX

**Feature**: 018-help-commands-ux | **Date**: 2026-03-04

## Prerequisites

- Node.js 18+ with npm
- Repository cloned and dependencies installed: `cd frontend && npm install`

## Development

```bash
# Start frontend dev server
cd frontend
npm run dev

# Run all frontend tests
npm run test

# Run only command-related tests
npx vitest run src/lib/commands/ src/hooks/useCommands.test.tsx

# Type check
npm run type-check

# Lint
npm run lint
```

## Files to Modify

### 1. Add `category` field to CommandDefinition type

**File**: `frontend/src/lib/commands/types.ts`

Add optional `category?: string` field to `CommandDefinition` interface.

### 2. Create helper utilities

**File**: `frontend/src/lib/commands/helpers.ts` (new)

Implement:
- `levenshteinDistance(a, b)` — edit distance between two strings
- `findClosestCommands(input, maxDistance)` — fuzzy match against registered commands
- `truncateInput(input, maxLength)` — truncate long input for error messages

### 3. Add `getCommandsByCategory()` to registry

**File**: `frontend/src/lib/commands/registry.ts`

Add new export that groups commands by their `category` field (defaulting to "General").

### 4. Add `category` to existing command registrations

**File**: `frontend/src/lib/commands/registry.ts`

Add `category: 'Settings'` to theme, language, notifications, view commands.
Add `category: 'Workflow'` to agent command.
Help command uses default "General" (no explicit category needed).

### 5. Refactor help handler

**File**: `frontend/src/lib/commands/handlers/help.ts`

- When `args` is empty: generate categorized listing using `getCommandsByCategory()`
- When `args` is non-empty: look up specific command and show detailed info
- Strip leading `#` from arg to handle `#help #theme`

### 6. Update unknown-command handling

**File**: `frontend/src/hooks/useCommands.ts`

- Import `findClosestCommands` and `truncateInput` from helpers
- When command not found: check for fuzzy matches and include "Did you mean?" suggestion

### 7. Update test factory

**File**: `frontend/src/test/factories/index.ts`

Add optional `category` to `createCommandDefinition` factory.

### 8. Extend tests

**Files**:
- `frontend/src/lib/commands/handlers/help.test.ts` — categorized output, single-command help
- `frontend/src/lib/commands/helpers.test.ts` (new) — Levenshtein distance, fuzzy matching
- `frontend/src/hooks/useCommands.test.tsx` — "Did you mean?" in unknown command responses

## Verification

After implementing all changes:

```bash
# Run targeted tests
cd frontend
npx vitest run src/lib/commands/ src/hooks/useCommands.test.tsx

# Run full test suite
npm run test

# Type check
npm run type-check

# Lint
npm run lint
```

### Manual verification

1. Start the dev server (`npm run dev`)
2. Open the chat interface
3. Type `#help` → verify categorized output with General, Settings, Workflow sections
4. Type `#help theme` → verify single-command detail view
5. Type `#help #theme` → verify same result (leading # stripped)
6. Type `#help nonexistent` → verify "not found" message
7. Type `#hep` → verify "Did you mean #help?" suggestion
8. Type `#theme` (no arg) → verify usage hint with valid options
9. Type `#theme purple` → verify invalid value error with valid options
10. Type `#` → verify "Type #help" prompt
