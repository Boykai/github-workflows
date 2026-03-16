# Research: Update Chat Help & Help Page for Comprehensive Chat Commands & Features

**Feature**: `046-chat-help-docs` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Research Tasks

### RT-001: Help Handler Output Format and Plain-Text Constraints

**Decision**: Append Chat Features and Tips blocks to the existing `/help` handler output using the same plain-text formatting style (indented lines with em-dash separators). No Markdown, no HTML, no ANSI codes.

**Rationale**: The existing `helpHandler` in `help.ts` constructs a plain-text string with `Available Commands:\n` followed by indented command lines. The `ChatInterface.tsx` renders messages without a Markdown parser — literal `**`, `#`, or `*` characters would appear as-is in the chat bubble. The expanded output must follow the same pattern to maintain visual consistency. Research of the chat message rendering pipeline confirms that `message` from `CommandResult` is rendered as plain text in a `<pre>`-like context.

**Alternatives considered**:
- **Markdown formatting**: Rejected because the chat interface does not parse Markdown. Bold markers (`**`) and headers (`#`) would render literally.
- **Structured result object (sections array)**: Rejected because it would require changes to `CommandResult` type and the chat rendering pipeline — violating the minimal-change constraint.
- **Separate `/features` command**: Rejected because the spec explicitly requires appending to `/help` output, and adding new commands is out of scope.

**Key Implementation Details**:
- Format: `\n\nChat Features:\n  {feature} — {description}` for each of the 4 features
- Format: `\n\nTips:\n  • {tip text}` for each of the 4 tips
- The bullet character `•` (U+2022) is safe for plain text and renders correctly in all modern browsers
- The command list remains dynamically generated from `getAllCommands()`; only the Chat Features and Tips blocks are static

---

### RT-002: FeatureGuideCard Reuse Strategy for Chat Features Section

**Decision**: Create informational (non-navigable) feature cards for the Chat Features section by defining a simple inline card component within HelpPage.tsx that mirrors the FeatureGuideCard visual style but renders as a `<div>` instead of a `<Link>`. This avoids modifying the existing `FeatureGuideCard` component which is purpose-built for navigation.

**Rationale**: The existing `FeatureGuideCard` component (`src/components/help/FeatureGuideCard.tsx`, 35 lines) requires an `href` prop and wraps content in a `<Link>` element. The Chat Features cards are informational — they describe capabilities but don't link to a specific page. Two approaches were evaluated:

1. **Add an optional `href` prop** to `FeatureGuideCard` (render `<div>` when no `href`): Clean but modifies a shared component for one consumer's needs, potentially affecting other usages.
2. **Inline card component in HelpPage**: Uses the same Tailwind classes (`moonwell`, `rounded-[1.25rem]`, `border-border/50`, icon circle) but as a `<div>`. Slightly duplicates styling but is self-contained and zero-risk to existing cards.

Approach 2 is chosen because it follows the DRY-is-preferable-to-wrong-abstraction principle from the constitution (Principle V). The duplication is minimal (~10 lines of Tailwind classes) and confined to a single file.

**Alternatives considered**:
- **Use FeatureGuideCard with `href="#"` or `href=""`**: Rejected because it would create clickable cards that navigate nowhere, harming UX and accessibility (screen readers would announce "link" with no destination).
- **Create a new shared `InfoCard` component**: Rejected as premature abstraction — only one consumer exists. If future Help page sections need similar cards, a shared component can be extracted then.

**Key Implementation Details**:
- Chat Features array: 7 objects with `title: string`, `description: string`, `icon: LucideIcon`
- Icons from lucide-react: `AtSign` (@Pipeline Mentions), `Paperclip` (File Attachments), `Mic` (Voice Input), `Sparkles` (AI Enhance), `ListTodo` (Task Proposals), `History` (Message History), `Keyboard` (Keyboard Shortcuts)
- Grid: `grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3` for responsive layout
- Card styling: matches FeatureGuideCard moonwell + border + icon circle pattern

---

### RT-003: ParameterSchema-Driven Options Column

**Decision**: Derive the Options column content from `cmd.parameterSchema` using a helper function that handles three cases: enum with labels, enum without labels, and passthrough commands with admin-only notation.

**Rationale**: The `ParameterSchema` interface (`types.ts`) defines `type: 'enum' | 'string' | 'boolean'`, optional `values: string[]`, and optional `labels: Record<string, string>`. Currently, all registered commands use `type: 'enum'` except `/help` (no schema) and `/agent` (passthrough, no schema). The Options column must handle:

1. **Enum with values, no labels** (current: `/theme`, `/notifications`, `/view`): Display values joined by ", " → e.g., "light, dark, system"
2. **Enum with values and labels** (potential future: `/language` could add labels): Display as "value (Label)" → e.g., "en (English), es (Spanish)"
3. **No parameterSchema** (`/help`): Display "—"
4. **Passthrough** (`/agent`): Display syntax parameters + "(admin only)" badge

Currently, no command uses `labels` — the `/language` command has `values: ['en', 'es', 'fr', 'de', 'ja', 'zh']` but no `labels` map. The spec requires showing language names (FR-011), so the implementation should add `labels` to the `/language` command registration in `registry.ts`.

**Alternatives considered**:
- **Hardcode options per command**: Rejected because it would break the dynamic contract — new commands with `parameterSchema` wouldn't appear in the Options column automatically.
- **Render schema as JSON**: Rejected as developer-unfriendly; users need human-readable option values.

**Key Implementation Details**:
- Add `labels` to the `/language` command registration: `labels: { en: 'English', es: 'Spanish', fr: 'French', de: 'German', ja: 'Japanese', zh: 'Chinese' }`
- Helper function signature: `getCommandOptions(cmd: CommandDefinition): string`
- The function checks `cmd.passthrough` first (for admin-only badge), then `cmd.parameterSchema?.type === 'enum'`, then falls back to "—"
- Render in a `<td>` with `text-xs text-muted-foreground` styling

---

### RT-004: FAQ Entry Corrections — /clear and Drag-and-Drop

**Decision**: Fix two specific FAQ entries in the `FAQ_ENTRIES` array within `HelpPage.tsx`: (1) replace `/clear` reference with `/agent` in `chat-voice-1`, and (2) remove "drag-and-drop" from `chat-voice-2` and replace with "click the attachment button in the chat toolbar".

**Rationale**: Codebase audit confirms:
- **No `/clear` command exists**: The command registry (`registry.ts`) registers exactly 6 commands: help, theme, language, notifications, view, agent. There is no `clear` handler, no `clearHandler` export, and no registration with name `'clear'`. The FAQ entry `chat-voice-1` references `/clear` as a "common" command — this is factually incorrect.
- **No drag-and-drop file support**: The `ChatToolbar.tsx` file upload uses a hidden `<input type="file">` triggered by a paperclip button click. `ChatInterface.tsx` has no `onDrop` or `onDragOver` handlers. The `FilePreviewChips.tsx` component only renders files from the button picker. The FAQ entry `chat-voice-2` claims "drag-and-drop files" — this is factually incorrect.

**Alternatives considered**:
- **Remove the FAQ entries entirely**: Rejected because the questions themselves are valid user questions — only the answers need correction.
- **Add a `/clear` command to match the FAQ**: Rejected because the spec explicitly states no new slash commands, and adding functionality to match incorrect documentation inverts the correct fix.
- **Add drag-and-drop support**: Rejected because it's a feature change, not a documentation fix. The spec scope is documentation only.

**Key Implementation Details**:
- `chat-voice-1` answer change: `'Type / in the chat to see all available commands. Common ones include /help, /theme, and /clear.'` → `'Type / in the chat to see all available commands. Common ones include /help, /theme, and /agent. See the Slash Commands section below for the full list.'`
- `chat-voice-2` answer change: `'Yes — click the attachment icon in the chat input or drag-and-drop files. Supported formats include images, PDFs, markdown, and code files up to 10 MB each.'` → `'Yes — click the attachment button in the chat toolbar to select files. Supported formats include images, PDFs, markdown, and code files up to 10 MB each.'`

---

### RT-005: Test Strategy for Documentation Changes

**Decision**: Use Vitest + @testing-library/react for component tests (HelpPage) and pure function unit tests (helpHandler). No E2E tests — the changes are rendered content, not interactive behavior.

**Rationale**: The existing test infrastructure supports both approaches:
- `help.test.ts` (50 lines) already tests the help handler as a pure function — calling `helpHandler()` and asserting on the returned `message` string. Extending these tests to verify new Chat Features and Tips content is straightforward string assertions.
- The project uses `@testing-library/react` with happy-dom for component rendering tests. No `HelpPage.test.tsx` exists yet, but the test utilities (`src/test/test-utils.tsx`, `src/test/factories.ts`) provide the necessary infrastructure.

**Alternatives considered**:
- **Snapshot tests**: Rejected because snapshot tests are brittle for content changes — every text tweak would update snapshots, providing low signal.
- **E2E tests (Playwright)**: Rejected as overkill for documentation content verification. The changes involve no API calls, no user interactions, and no state management.
- **Skip tests entirely**: Rejected because the spec explicitly requires tests (FR-018–FR-022, User Story 5).

**Key Implementation Details**:
- `help.test.ts` additions: 2 new `it` blocks — one for Chat Features content, one for Tips content
- `HelpPage.test.tsx` creation: ~6-8 test cases covering Chat Features section (7 cards), Options column, FAQ corrections, and footer note
- Test rendering of HelpPage requires wrapping in `MemoryRouter` (react-router-dom) and mocking `useOnboarding` hook
- All assertions use `screen.getByText()` / `screen.queryByText()` from @testing-library/react
