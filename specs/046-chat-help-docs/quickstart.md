# Quickstart: Update Chat Help & Help Page for Comprehensive Chat Commands & Features

**Feature**: `046-chat-help-docs` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Prerequisites

- Node.js 20+ with `npm`
- Git repository cloned with full history
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

# Run ESLint
npx eslint src/lib/commands/handlers/help.ts src/pages/HelpPage.tsx src/lib/commands/registry.ts

# Run all linters via pre-commit hook
npm run lint
```

## File Overview

### Files to Modify

| File | Change | Lines (est.) |
|------|--------|-------------|
| `src/lib/commands/handlers/help.ts` | Append Chat Features + Tips blocks to output | ~20 added |
| `src/pages/HelpPage.tsx` | Chat Features section, Options column, FAQ fixes | ~60 added |
| `src/lib/commands/registry.ts` | Add `labels` to `/language` parameterSchema | ~5 modified |
| `src/lib/commands/handlers/help.test.ts` | Add tests for expanded output | ~25 added |

### Files to Create

| File | Purpose | Lines (est.) |
|------|---------|-------------|
| `src/pages/HelpPage.test.tsx` | Component tests for Chat Features, Options, FAQ | ~80 |

### Reference Files (read-only)

| File | Why |
|------|-----|
| `src/lib/commands/types.ts` | `CommandDefinition`, `ParameterSchema`, `CommandResult` types |
| `src/lib/commands/registry.ts` | `getAllCommands()`, command registrations |
| `src/components/help/FeatureGuideCard.tsx` | Card component API: `{ title, description, icon, href }` |
| `src/components/help/FaqAccordion.tsx` | FAQ rendering component |
| `src/types/index.ts` | `FaqEntry` type |
| `src/test/factories.ts` | `createCommandContext()` test factory |

## Verification Checklist

### Automated

1. `npx vitest run src/lib/commands/handlers/help.test.ts` — expanded `/help` output
2. `npx vitest run src/pages/HelpPage.test.tsx` — Chat Features section, Options column, FAQ corrections
3. `npx tsc --noEmit` — zero TypeScript errors
4. `npm run lint` — ESLint clean

### Manual

1. Start dev server: `npm run dev`
2. Open chat and type `/help` → verify "Chat Features" and "Tips" sections appear
3. Type `help` (no slash) → verify identical output
4. Navigate to `/help` page → verify Chat Features section with 7 cards
5. Verify commands table has 4 columns (Command, Syntax, Description, Options)
6. Verify `/theme` Options shows "light, dark, system"
7. Verify `/language` Options shows "en (English), es (Spanish), ..."
8. Verify footer note below commands table
9. Verify FAQ `chat-voice-1` references `/agent` not `/clear`
10. Verify FAQ `chat-voice-2` says "attachment button" not "drag-and-drop"
