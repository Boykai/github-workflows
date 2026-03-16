# Quickstart: Update Chat Help & Help Page for Comprehensive Chat Commands & Features

**Feature**: `046-chat-help-docs` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Prerequisites

- Node.js 20+ with `npm`
- Git repository cloned
- Access to `solune/frontend/` directory

## Setup

### Frontend Environment

```bash
cd solune/frontend
npm ci
```

No new dependencies are required — this feature uses only existing packages.

## Development Workflow

### Running the Dev Server

```bash
cd solune/frontend
npm run dev
```

The development server starts at `http://localhost:5173` with hot module replacement.

### Running Tests

```bash
cd solune/frontend

# Run all unit tests
npx vitest run

# Run tests in watch mode (recommended during development)
npx vitest

# Run help handler tests specifically
npx vitest run src/lib/commands/handlers/help.test.ts

# Run Help page component tests specifically
npx vitest run src/pages/HelpPage.test.tsx

# Run TypeScript type checking
npx tsc --noEmit
```

### Linting

```bash
cd solune/frontend

# Run ESLint on changed files
npx eslint src/lib/commands/handlers/help.ts src/pages/HelpPage.tsx src/lib/commands/registry.ts

# Run all linters
npm run lint
```

## File Overview

### Files to Modify

| File | Change | Lines (est.) |
|------|--------|-------------|
| `src/lib/commands/handlers/help.ts` | Append Chat Features + Tips blocks to output | ~20 added |
| `src/pages/HelpPage.tsx` | Chat Features section, Options column, FAQ fixes | ~60 added |
| `src/lib/commands/registry.ts` | Add `labels` to `/language` parameterSchema | ~5 modified |

### Files to Create

| File | Purpose | Lines (est.) |
|------|---------|-------------|
| `src/pages/HelpPage.test.tsx` | Component tests for Chat Features, Options, FAQ | ~80 |

### Test Files to Update

| File | Change |
|------|--------|
| `src/lib/commands/handlers/help.test.ts` | Add tests for Chat Features and Tips sections |

### Reference Files (read-only)

| File | Why Referenced |
|------|---------------|
| `src/lib/commands/types.ts` | `CommandDefinition`, `ParameterSchema`, `CommandResult` types |
| `src/lib/commands/registry.ts` | `getAllCommands()`, command registrations |
| `src/components/help/FeatureGuideCard.tsx` | Card styling reference (moonwell, icon circle) |
| `src/components/chat/ChatToolbar.tsx` | Toolbar buttons reference |
| `src/components/chat/MentionAutocomplete.tsx` | @mention behavior reference |
| `src/components/chat/VoiceInputButton.tsx` | Voice feature reference |
| `src/test/factories.ts` | `createCommandContext()` test factory |

## Implementation Order

1. **`registry.ts`** — Add `labels` to `/language` parameterSchema (enables Options column for language codes)
2. **`help.ts`** — Append Chat Features and Tips blocks to handler output
3. **`help.test.ts`** — Add tests for expanded output
4. **`HelpPage.tsx`** — Chat Features section + Options column + FAQ fixes + footer note
5. **`HelpPage.test.tsx`** — Create component tests

## Verification Checklist

```bash
# 1. TypeScript type check
cd solune/frontend && npx tsc --noEmit

# 2. Help handler tests
npx vitest run src/lib/commands/handlers/help.test.ts

# 3. Help page tests
npx vitest run src/pages/HelpPage.test.tsx

# 4. Full test suite
npx vitest run

# 5. ESLint
npx eslint src/lib/commands/handlers/help.ts src/pages/HelpPage.tsx src/lib/commands/registry.ts

# 6. Production build
npm run build
```

## Key Decisions

- **No new dependencies**: All icons (`AtSign`, `Paperclip`, `Mic`, `Sparkles`, `ListTodo`, `History`, `Keyboard`) are from existing `lucide-react` package.
- **Plain text only for `/help`**: Chat does not render Markdown — output uses whitespace and Unicode bullet (•).
- **Non-navigable cards**: Chat Features cards are `<div>` elements (not `<Link>`) because they are informational, not navigation links.
- **Dynamic Options column**: Driven by `parameterSchema` for forward compatibility with future commands.
- **`labels` addition to `/language`**: Required by FR-011 to show human-readable language names (e.g., "en (English)").
