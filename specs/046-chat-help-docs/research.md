# Research: Update Chat Help & Help Page for Comprehensive Chat Commands & Features

**Feature**: `046-chat-help-docs` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Research Tasks

### RT-001: Help Handler Output Format and Chat Rendering Constraints

**Decision**: Append two new blocks ("Chat Features" and "Tips") to the `/help` handler output as plain text with simple header/bullet formatting using whitespace indentation. The chat interface does not render Markdown, so no `**`, `#`, `*`, or backtick syntax is used.

**Rationale**: Inspecting `helpHandler()` in `solune/frontend/src/lib/commands/handlers/help.ts` confirms the output is a single string returned via `CommandResult.message`. The existing format uses `Available Commands:\n` as a header followed by `  /command  —  description` lines with two-space indentation. The comment in the source explicitly states: "Use plain text formatting since chat messages are rendered without a Markdown parser — literal ** markers would be shown to the user." Extending this pattern with `\n\nChat Features:\n  ...` and `\n\nTips:\n  ...` maintains visual consistency.

**Alternatives considered**:
- **Markdown formatting**: Rejected because the chat interface renders raw text — Markdown syntax characters would appear as literal text to users.
- **Structured response object (sections array)**: Rejected because the `CommandResult` interface expects a single `message: string`. Changing the interface would be a breaking change affecting all 6 command handlers and the chat rendering pipeline — far beyond the scope of a documentation feature.
- **HTML formatting**: Rejected because chat messages are rendered as plain text, not HTML.

**Key Implementation Details**:
- The `helpHandler` function receives `(_args: string, _context: CommandContext)` and returns `CommandResult`.
- The command list is dynamically generated via `getAllCommands()` — this must remain unchanged (FR-004).
- New blocks are static strings appended after the dynamic command list.
- Blank line (`\n\n`) separates sections for readability.

---

### RT-002: FeatureGuideCard Component Reusability for Chat Features Section

**Decision**: Reuse the existing `FeatureGuideCard` component from `solune/frontend/src/components/help/FeatureGuideCard.tsx` for the new Chat Features section on the Help page. Each of the seven chat features will be represented as a `FeatureGuideCard` with a title, description, icon (from Lucide React), and an `href` pointing to the chat route (`/`).

**Rationale**: The `FeatureGuideCard` component accepts `{ title: string; description: string; icon: React.ComponentType<{ className?: string }>; href: string }` and renders a styled card with moonwell background, hover lift animation, icon circle, and descriptive text. The existing "Getting Started" and "Feature Guides" sections on the Help page already use this component. Reusing it ensures visual consistency, avoids creating a new component, and follows the DRY principle (Constitution Principle V).

**Alternatives considered**:
- **New `ChatFeatureCard` component**: Rejected because the existing `FeatureGuideCard` already provides all needed functionality (title, description, icon, link). Creating a new component would introduce unnecessary duplication.
- **Simple list format (no cards)**: Rejected because the spec requires "seven feature cards" (FR-006, FR-007) and the card format matches the existing Help page visual language.
- **Accordion format (like FAQ)**: Rejected because feature descriptions are short enough for card format and don't benefit from expand/collapse behavior.

**Key Implementation Details**:
- `FeatureGuideCard` requires a `href` prop (it renders as a `<Link>` element). All Chat Features cards will link to `/` (the chat route).
- Grid layout: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3` for 7 cards (3+3+1 on desktop, 2+2+2+1 on tablet, single column on mobile).
- Icons sourced from Lucide React (already a project dependency): `AtSign`, `Paperclip`, `Mic`, `Sparkles`, `ListTodo`, `History`, `Keyboard`.
- Section positioned between FAQ and Feature Guides per spec assumption.

---

### RT-003: ParameterSchema-Driven Options Column Strategy

**Decision**: Add an "Options" column to the Slash Commands table that dynamically reads each command's `parameterSchema` property. A helper function `getOptionsDisplay(cmd: CommandDefinition): string` determines the display text based on the schema type, values, labels, and passthrough flag.

**Rationale**: The `CommandDefinition` interface already includes an optional `parameterSchema?: ParameterSchema` property where `ParameterSchema` has `{ type: 'enum' | 'string' | 'boolean'; values?: string[]; labels?: Record<string, string> }`. Five of the six commands have `parameterSchema` defined in the registry. The `/language` command currently lacks `labels` in its registry entry (they exist as `LANGUAGE_LABELS` in the handler file) — this needs to be added to `registry.ts` to enable the dynamic label display (FR-011).

**Alternatives considered**:
- **Hardcoded options map in HelpPage**: Rejected because it would duplicate the `parameterSchema` data already in the registry, creating a maintenance burden when commands change. The dynamic approach is required by FR-010.
- **Show raw `values` array without labels**: Rejected for the language command because raw codes (`en`, `es`, `fr`) are not user-friendly. FR-011 explicitly requires label-enhanced display.
- **Tooltip on hover instead of column**: Rejected because the spec explicitly requires an "Options" column (FR-009) and the table format provides better scannability.

**Key Implementation Details**:
- Current registry state:
  - `/help`: no `parameterSchema` → display `"—"`
  - `/theme`: `{ type: 'enum', values: ['light', 'dark', 'system'] }` → display `"light, dark, system"`
  - `/language`: `{ type: 'enum', values: ['en', 'es', 'fr', 'de', 'ja', 'zh'] }` → needs `labels` added → display `"en (English), es (Spanish), ..."`
  - `/notifications`: `{ type: 'enum', values: ['on', 'off'] }` → display `"on, off"`
  - `/view`: `{ type: 'enum', values: ['chat', 'board', 'settings'] }` → display `"chat, board, settings"`
  - `/agent`: `passthrough: true`, no `parameterSchema` → display `"<description> [#status-column] (admin only)"`
- `labels` must be added to the language command registration in `registry.ts` to match the existing `LANGUAGE_LABELS` in `handlers/settings.ts`.

---

### RT-004: FAQ Entry Correction Verification

**Decision**: Correct two FAQ entries in `HelpPage.tsx`:
1. `chat-voice-1`: Replace mention of `/clear` (non-existent command) with `/agent`.
2. `chat-voice-2`: Remove "drag-and-drop" claim; replace with "click the attachment button in the chat toolbar".

**Rationale**: Codebase audit confirms:
- There is no `/clear` command in the registry (`registry.ts` registers only: help, theme, language, notifications, view, agent). The FAQ answer says "Common ones include /help, /theme, and /clear" — `/clear` must be replaced with `/agent`.
- File attachment is triggered only via the paperclip button in `ChatToolbar.tsx`. There is no drag-and-drop handler for file uploads. The FAQ says "click the attachment icon in the chat input or drag-and-drop files" — the "or drag-and-drop files" must be removed.

**Alternatives considered**:
- **Add a `/clear` command to match the FAQ**: Rejected because the spec scope is documentation-only — no new commands. The issue explicitly states "No new slash commands."
- **Add drag-and-drop to match the FAQ**: Rejected for the same reason — out of scope. The FAQ should reflect actual behavior.
- **Remove the FAQ entries entirely**: Rejected because the questions are valid and useful; only the answers need correction.

**Key Implementation Details**:
- `chat-voice-1` current answer: `'Type / in the chat to see all available commands. Common ones include /help, /theme, and /clear. See the Slash Commands section below for the full list.'`
- `chat-voice-1` corrected answer: `'Type / in the chat to see all available commands. Common ones include /help, /theme, and /agent. See the Slash Commands section below for the full list.'`
- `chat-voice-2` current answer: `'Yes — click the attachment icon in the chat input or drag-and-drop files. Supported formats include images, PDFs, markdown, and code files up to 10 MB each.'`
- `chat-voice-2` corrected answer: `'Yes — click the attachment button in the chat toolbar to add files. Supported formats include images, PDFs, markdown, and code files up to 10 MB each.'`

---

### RT-005: Help Page Test Infrastructure

**Decision**: Create a new test file `HelpPage.test.tsx` following the existing page test patterns (e.g., `AppsPage.test.tsx`, `ProjectsPage.test.tsx`). Use `@testing-library/react` with `render` + `screen` queries. The existing `help.test.ts` unit test file will be extended with additional assertions.

**Rationale**: No `HelpPage.test.tsx` currently exists. The Help page has no component tests. The existing page test files use `@testing-library/react` with `render()` and `screen.getByText()` / `screen.queryByText()` patterns. The `helpHandler` unit tests in `help.test.ts` use pure function testing (call handler, assert on `result.message` string) — this pattern is ideal for testing the expanded text output.

**Alternatives considered**:
- **E2E tests with Playwright**: Rejected as overkill for verifying rendered text content. Unit and component tests are faster and more maintainable.
- **Snapshot tests**: Rejected because they test too broadly and break on any unrelated styling change. Specific assertions are more robust.
- **Testing in `useChat.test.tsx`**: Rejected because the help handler tests should remain isolated from the chat hook integration layer.

**Key Implementation Details**:
- `HelpPage.test.tsx` needs to mock `useOnboarding` (returns `{ restart: vi.fn() }`) since `HelpPage` calls it.
- `getAllCommands()` is auto-populated from the registry import side effect — no mocking needed.
- FAQ assertions use `queryByText(/\/clear/)` for absence checks and `getByText(/\/agent/)` for presence checks.
- Chat Features cards can be verified by checking for card titles: "@Pipeline Mentions", "File Attachments", "Voice Input", etc.

---

### RT-006: Lucide React Icon Availability for Chat Features Cards

**Decision**: Use the following Lucide React icons for the seven Chat Features cards: `AtSign` (@Pipeline Mentions), `Paperclip` (File Attachments), `Mic` (Voice Input), `Sparkles` (AI Enhance), `ListTodo` (Task Proposals), `History` (Message History), `Keyboard` (Keyboard Shortcuts).

**Rationale**: Lucide React is already a project dependency used extensively across the codebase (e.g., `HelpPage.tsx` imports `Play`, `Kanban`, `GitBranch`, `Bot`, `Wrench`, `ListChecks`, `Settings`, `Boxes`, `LayoutDashboard`). All seven selected icons are available in the Lucide icon set. The icon choices are semantically meaningful: `AtSign` for @mentions, `Paperclip` for attachments, `Mic` for voice, `Sparkles` for AI enhance (matches the existing toolbar button), `ListTodo` for task proposals, `History` for message history, `Keyboard` for shortcuts.

**Alternatives considered**:
- **Custom SVG icons**: Rejected because Lucide already provides suitable icons, and custom SVGs would add maintenance overhead.
- **No icons (text-only cards)**: Rejected because `FeatureGuideCard` requires an `icon` prop and the visual design relies on the icon circle for card identity.

---

## Summary of Resolved Unknowns

All items from the Technical Context that could have been NEEDS CLARIFICATION were resolved through direct codebase inspection:

| Unknown | Resolution | Source |
|---------|------------|--------|
| Chat rendering format | Plain text only — no Markdown | `help.ts` source comment + `CommandResult.message` type |
| `parameterSchema.labels` availability | Present in handler (`LANGUAGE_LABELS`) but missing from registry entry — must be added | `registry.ts` vs `handlers/settings.ts` |
| `FeatureGuideCard` API | `{ title, description, icon, href }` — fully compatible | `FeatureGuideCard.tsx` source |
| FAQ entry IDs | `chat-voice-1` and `chat-voice-2` confirmed stable | `HelpPage.tsx` lines 56–71 |
| Test infrastructure | Vitest + @testing-library/react; `createCommandContext` factory available | `help.test.ts`, `AppsPage.test.tsx` |
| Lucide icon availability | All 7 icons confirmed available in `lucide-react` | Lucide icon set |
| Existing `/clear` command | Confirmed non-existent — only 6 commands registered | `registry.ts` lines 98–143 |
| Drag-and-drop support | Confirmed not implemented — button picker only | Codebase audit in parent issue |
