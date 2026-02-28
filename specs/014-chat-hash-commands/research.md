# Research: Enhance Chat # Commands — App-Wide Settings Control & #help Command with Test Coverage

**Feature**: 014-chat-hash-commands | **Date**: 2026-02-28

## Research Task 1: Client-Side Command Interception Architecture

### Decision
Intercept `#`-prefixed messages (and the `help` keyword) in the `useChat` hook's `sendMessage` function before calling `chatApi.sendMessage()`. A new `useCommands` hook provides `parseCommand()` and `executeCommand()` functions. When a command is detected, `executeCommand()` is called instead of the API, and a system message is inserted directly into the local message list.

### Rationale
The existing `useChat.ts` hook calls `chatApi.sendMessage({ content })` via a React Query mutation. The interception point is the `sendMessage` callback exposed to `ChatInterface.tsx`. By checking the input against the command registry before invoking the mutation, we avoid any network request for commands. This approach:
- Requires minimal changes to the existing chat flow (one conditional check)
- Keeps command logic decoupled in its own hook (`useCommands`)
- Preserves the existing AI chat path unchanged for non-command messages
- Allows system messages to appear instantly without API round-trips

### Alternatives Considered
- **Backend command processing**: Rejected because commands are UI-only actions (theme, help) that don't need server involvement; adding backend endpoints would increase latency and complexity unnecessarily
- **Middleware in the API service layer**: Rejected because intercepting at the fetch/API level would couple command logic to the transport layer rather than the UI layer
- **Custom event system**: Rejected for over-engineering; a simple function call in the hook is sufficient

---

## Research Task 2: Command Registry Design Pattern

### Decision
Implement a command registry as a plain TypeScript `Map<string, CommandDefinition>` in `frontend/src/lib/commands/registry.ts`. Each `CommandDefinition` includes `name`, `description`, `syntax`, `handler`, and optional `parameterSchema`. The registry is the single source of truth for `#help` output, autocomplete suggestions, and command execution.

### Rationale
A `Map`-based registry is the simplest data structure that satisfies all requirements:
- O(1) lookup by command name for execution
- Iterable for `#help` output and autocomplete filtering
- Adding a new command requires only one `registry.set()` call
- No framework dependency — works with any state management approach
- Type-safe with TypeScript generics

The registry module exports both the map and convenience functions (`getCommand`, `getAllCommands`, `filterCommands`) to keep consumer code clean.

### Alternatives Considered
- **Class-based registry with decorator pattern**: Rejected per YAGNI; a map with factory functions achieves the same result with less abstraction
- **JSON configuration file**: Rejected because handler functions cannot be stored in JSON; a TypeScript module provides both data and behavior
- **Redux slice for command definitions**: Rejected because command definitions are static (not reactive state); a plain module is simpler and faster

---

## Research Task 3: Settings Integration via Existing Store

### Decision
Settings command handlers dispatch updates through the existing `settingsApi.updateUserSettings()` and TanStack Query cache invalidation, plus the `ThemeProvider` context for theme changes. No new state management is introduced.

### Rationale
The codebase already has:
- `settingsApi.updateUserSettings(data)` → calls `PATCH /api/v1/settings/user` → returns updated settings
- TanStack Query cache key `['settings', 'user']` → automatic re-renders across the app
- `ThemeProvider` with `useTheme()` → `setTheme()` for theme changes persisted to localStorage
- `useSettings` hook with `updateUserSettings` mutation → already handles optimistic updates

Settings commands can call the same mutation/setter that the Settings page uses, ensuring consistency. Theme is the one setting handled via Context API (ThemeProvider) rather than the API; the handler will call `setTheme()` directly.

### Alternatives Considered
- **New Zustand store for command-driven settings**: Rejected because the existing TanStack Query + Context pattern already provides reactive updates app-wide; adding another store would fragment state management
- **Direct localStorage manipulation**: Rejected because only theme uses localStorage; other settings (language, notifications) are server-persisted via the API; inconsistent approaches would be confusing
- **Custom event bus for cross-component settings updates**: Rejected because TanStack Query cache invalidation already triggers re-renders in all consuming components

---

## Research Task 4: Autocomplete Overlay Best Practices

### Decision
Implement the autocomplete overlay as a `CommandAutocomplete` React component rendered above the chat input. Use `useState` for open/closed state and highlighted index, driven by keyboard events (ArrowUp, ArrowDown, Enter, Escape) and input change events. Filter commands by prefix match against the registry.

### Rationale
Best practices for autocomplete overlays in React:
- **Positioning**: Render above the input using CSS `position: absolute` with `bottom: 100%` — consistent with common chat autocomplete patterns (Slack, Discord)
- **Filtering**: Case-insensitive prefix match on command names — simple and predictable
- **Keyboard navigation**: Standard patterns — Arrow keys cycle through items, Enter selects, Escape dismisses, Tab can also select
- **Performance**: With <20 commands, filtering is instantaneous; no debouncing needed
- **Accessibility**: Use `role="listbox"` and `role="option"` with `aria-activedescendant` for screen reader support
- **Dismissal**: Close on Escape, on clicking outside, on deleting the `#` character, or on submitting

The existing UI uses Tailwind CSS and follows a clean component pattern — the autocomplete overlay will use the same styling conventions.

### Alternatives Considered
- **Radix UI Combobox/Popover**: Rejected because the chat input is a textarea (not a standard input), making Radix combobox integration complex; a custom overlay is simpler for this specific use case
- **Third-party autocomplete library (e.g., downshift)**: Rejected to avoid a new dependency; the command list is small and the interaction pattern is straightforward
- **Rendering in a portal**: Rejected for simplicity; the overlay is always positioned relative to the chat input, so a portal adds complexity without benefit

---

## Research Task 5: System Message Display Pattern

### Decision
Display command responses (help output, confirmation messages, error messages) as system messages in the chat message list. Use the existing `SenderType.SYSTEM` type and render them with a distinct visual style (no avatar, centered or left-aligned, muted background).

### Rationale
The backend already defines `SenderType.SYSTEM = "system"` in `models/chat.py`. The frontend `ChatMessage` type includes `sender_type` which can be `"system"`. Currently, system messages are not extensively used in the UI, but the data model supports them.

For client-side commands, system messages are created locally (not sent to the backend) and inserted into the local message array. They are ephemeral — they appear in the current chat session but are not persisted to the backend message store, since commands are stateless UI actions.

### Alternatives Considered
- **Toast notifications for command responses**: Rejected because toasts are transient and hard to reference later; inline chat messages provide persistent context and are consistent with the conversational interface
- **Dedicated command output panel**: Rejected because it would fragment the user's attention; keeping responses inline in the chat flow is more natural
- **Persisting system messages to backend**: Rejected for now — commands are lightweight UI actions that don't need server storage; this can be added later if needed

---

## Research Task 6: Testing Strategy for Command System

### Decision
Use Vitest + React Testing Library for all command system tests. Test at three levels: (1) pure function unit tests for registry and handlers, (2) hook tests for `useCommands` with `renderHook`, (3) component integration tests for `ChatInterface` with command flow.

### Rationale
The existing test infrastructure provides:
- `vitest` as the test runner (configured in `vitest.config.ts`)
- `@testing-library/react` for component testing
- `happy-dom` as the DOM environment
- `createMockApi()` factory in `setup.ts` for mocking API calls
- `renderWithProviders()` in `test-utils.tsx` for wrapping components with providers
- Test factories in `src/test/factories/index.ts` for creating test data

Test coverage should include:
- **Registry tests**: Registration, lookup, filtering, iteration
- **Parser tests**: Command extraction, argument parsing, whitespace normalization, case insensitivity, edge cases (bare `#`, mid-sentence `#`, `help` keyword)
- **Handler tests**: Help output contains all commands, settings handlers call correct API methods, error handling for invalid values
- **Hook tests**: `useCommands` returns correct results, `executeCommand` dispatches to handlers, autocomplete filtering works
- **Component tests**: Autocomplete appears on `#`, keyboard navigation works, command submission shows system message, non-commands pass through to AI

### Alternatives Considered
- **Playwright E2E tests**: Deferred — useful for full integration testing but not needed for the initial implementation; unit and component tests provide faster feedback
- **Snapshot tests**: Rejected per existing convention — test behavior, not implementation details
- **MSW (Mock Service Worker)**: Not needed — the existing `vi.mock()` pattern with `createMockApi()` is sufficient and already established

---

## Research Task 7: Available Settings and Valid Values

### Decision
Support the following settings commands in the initial implementation, based on the existing settings infrastructure:

| Command | Setting | Valid Values | Storage |
|---------|---------|-------------|---------|
| `#theme` | UI theme | `light`, `dark`, `system` | ThemeProvider (localStorage) |
| `#language` | Display language | `en`, `es`, `fr`, `de`, `ja`, `zh` | settingsApi (user prefs) |
| `#notifications` | Notification toggle | `on`, `off` | settingsApi (user prefs) |
| `#view` | Default view | `chat`, `board`, `settings` | settingsApi (user prefs) |

### Rationale
These settings map directly to existing UI controls:
- **Theme**: `ThemeProvider.tsx` already supports `light`, `dark`, `system` via `useTheme().setTheme()`
- **Language**: User preferences support language selection (referenced in settings components)
- **Notifications**: `NotificationPreferences.tsx` component exists for notification management
- **Default view**: `App.tsx` reads `default_view` from user settings to determine initial navigation

Each handler validates the value against the allowed set and returns a clear error message listing valid options if the value is invalid.

### Alternatives Considered
- **Supporting all settings via commands**: Rejected for MVP — complex settings (AI model selection, MCP configuration, project-specific settings) require multi-step interaction that doesn't fit the single-command pattern; these can be added incrementally
- **Dynamic settings discovery from API**: Rejected because the valid values need to be known client-side for instant validation; hardcoding the initial set is simpler and the registry makes adding more trivial

---

## Research Task 8: Command Parsing Edge Cases

### Decision
Command parsing follows these rules:
1. A message is a command if it starts with `#` (after trimming leading whitespace) OR is exactly `help` (case-insensitive)
2. Command name is extracted as the first word after `#`, lowercased
3. Arguments are everything after the command name, trimmed and whitespace-normalized
4. A bare `#` (no command name) triggers a helpful message directing to `#help`
5. Commands are case-insensitive: `#Theme`, `#THEME`, `#theme` are all equivalent
6. Multiple spaces between command and arguments are collapsed: `#theme   dark` → command `theme`, arg `dark`
7. `#` mid-sentence (e.g., "change #theme dark") is NOT treated as a command — only messages starting with `#`
8. Unknown commands display an error with a suggestion to type `#help`

### Rationale
These rules are directly derived from the spec (FR-001, FR-016, FR-017, FR-020) and edge cases section. The parsing logic is a pure function that can be thoroughly unit-tested.

### Alternatives Considered
- **Regex-based parsing**: Considered but simple string split is clearer and more maintainable for this use case
- **Supporting `#` mid-sentence as a command trigger**: Rejected per spec — only messages starting with `#` are commands; mid-sentence `#` is common in natural language (e.g., "issue #42")
- **Supporting multiple commands per message**: Rejected per spec assumption — one command per message is the scope
