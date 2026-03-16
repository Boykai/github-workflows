# Data Model: Update Chat Help & Help Page for Comprehensive Chat Commands & Features

**Feature**: `046-chat-help-docs` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Entities

### CommandDefinition (existing — extended usage)

Represents a registered slash command in the chat command system. This entity already exists in `solune/frontend/src/lib/commands/types.ts`. No structural changes are required; the plan extends how its `parameterSchema` property is consumed.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | `string` | Required, unique, lowercase | Command name without the `/` prefix (e.g., `"help"`, `"theme"`) |
| `description` | `string` | Required, non-empty | Human-readable description shown in help output and autocomplete |
| `syntax` | `string` | Required, starts with `/` | Usage syntax including parameter placeholders (e.g., `"/theme <light\|dark\|system>"`) |
| `handler` | `CommandHandler` | Required | Function that executes the command logic |
| `parameterSchema` | `ParameterSchema \| undefined` | Optional | Defines valid parameter types, values, and display labels |
| `passthrough` | `boolean \| undefined` | Optional, defaults to `false` | When `true`, the frontend forwards the message to the backend instead of executing locally |

**Validation Rules**:
- `name` must be unique across all registered commands (enforced by Map key in registry).
- `syntax` must start with `/` followed by the command name.
- When `parameterSchema` is defined with `type: 'enum'`, `values` must be a non-empty array of valid options.

**State Transitions**: N/A — command definitions are static configuration registered at module load time.

**Relationships**:
- Referenced by `helpHandler()` via `getAllCommands()` to generate the command list.
- Referenced by `HelpPage` via `getAllCommands()` to render the Slash Commands table.
- `parameterSchema` drives the new Options column in the Slash Commands table.

---

### ParameterSchema (existing — extended with labels)

Defines the valid parameter structure for a command. Already exists in `types.ts`. The `labels` property exists in the interface but is not currently set on the `/language` command's registry entry — this plan adds it.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `type` | `'enum' \| 'string' \| 'boolean'` | Required | Determines how the parameter is validated |
| `values` | `string[] \| undefined` | Required when `type === 'enum'` | Array of valid values for enum parameters |
| `labels` | `Record<string, string> \| undefined` | Optional, keys must match `values` entries | Human-readable display labels for enum values (e.g., `{ en: 'English', es: 'Spanish' }`) |

**Validation Rules**:
- When `type === 'enum'`, `values` must be defined and non-empty.
- When `labels` is defined, every key in `labels` should correspond to an entry in `values`.
- When `labels` is defined, the Options column displays `"value (Label)"` format.

**State Transitions**: N/A — static configuration.

**Relationships**:
- Contained within `CommandDefinition.parameterSchema`.
- Consumed by `getOptionsDisplay()` helper in `HelpPage.tsx` to render the Options column.

---

### FaqEntry (existing — content corrected)

Represents a question-and-answer pair in the Help page FAQ accordion. Already exists as a type in `solune/frontend/src/types/index.ts` and is instantiated as the `FAQ_ENTRIES` array in `HelpPage.tsx`. Two entries are corrected by this plan.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `string` | Required, unique | Stable identifier for the FAQ entry (e.g., `"chat-voice-1"`) |
| `question` | `string` | Required, non-empty | The question displayed as the accordion header |
| `answer` | `string` | Required, non-empty | The answer displayed when the accordion item is expanded |
| `category` | `string` | Required | Grouping category (e.g., `"getting-started"`, `"chat-voice"`, `"settings-integration"`) |

**Validation Rules**:
- `id` must be unique across all FAQ entries.
- `answer` must accurately reflect current application behavior (no references to non-existent features).

**State Transitions**: N/A — static content data.

**Corrected Entries**:
- `chat-voice-1`: Answer changed from referencing `/clear` to referencing `/agent`.
- `chat-voice-2`: Answer changed from "drag-and-drop" to "click the attachment button in the chat toolbar".

---

### ChatFeatureCard (new data structure — not a new component)

Represents a chat feature entry in the `CHAT_FEATURES` constant array defined in `HelpPage.tsx`. Uses the same shape as the existing `FEATURE_GUIDES` array to enable reuse of the `FeatureGuideCard` component.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `title` | `string` | Required, non-empty | Feature name displayed as the card heading (e.g., "@Pipeline Mentions") |
| `description` | `string` | Required, non-empty | Feature description displayed as card body text |
| `icon` | `React.ComponentType<{ className?: string }>` | Required | Lucide React icon component |
| `href` | `string` | Required, valid route path | Navigation target when the card is clicked (all cards link to `"/"`) |

**Validation Rules**:
- Exactly seven entries must be defined (FR-006).
- Each entry's `description` must match the spec-defined content (FR-008).

**State Transitions**: N/A — static content data.

**Relationships**:
- Consumed by `FeatureGuideCard` component for rendering.
- Array defined as a module-level constant in `HelpPage.tsx`, following the `FEATURE_GUIDES` pattern.

---

### HelpOutput (implicit — string output structure)

Represents the structured plain-text output of the `/help` command handler. Not a TypeScript type — this documents the output format contract.

| Section | Format | Content |
|---------|--------|---------|
| Header | `Available Commands:\n` | Static header line |
| Command List | `  /cmd  —  description\n` per command | Dynamically generated from `getAllCommands()` |
| Separator | `\n\n` | Blank line between sections |
| Chat Features Header | `Chat Features:\n` | Static header line |
| Chat Features | `  • Feature: description\n` per feature | Four static feature lines |
| Separator | `\n\n` | Blank line between sections |
| Tips Header | `Tips:\n` | Static header line |
| Tips | `  • tip text\n` per tip | Four static tip lines |

**Validation Rules**:
- All text is plain text — no Markdown syntax (FR-003).
- Command list is dynamic; Chat Features and Tips are static (FR-004).
- Chat Features section contains exactly 4 items (FR-001).
- Tips section contains exactly 4 items (FR-002).

## Entity Relationship Diagram

```
CommandDefinition (registry.ts)
├── name, description, syntax, handler
├── parameterSchema?: ParameterSchema
│   ├── type: 'enum' | 'string' | 'boolean'
│   ├── values?: string[]
│   └── labels?: Record<string, string>  ← added to /language
└── passthrough?: boolean

HelpPage.tsx
├── uses getAllCommands() → CommandDefinition[]
│   ├── Slash Commands table (name, syntax, description, options)
│   └── Options column ← reads parameterSchema
├── CHAT_FEATURES[] → FeatureGuideCard (7 cards)
├── FAQ_ENTRIES[] → FaqAccordion
│   ├── chat-voice-1 ← corrected (no /clear)
│   └── chat-voice-2 ← corrected (no drag-and-drop)
└── FEATURE_GUIDES[] → FeatureGuideCard (existing)

helpHandler (help.ts)
├── uses getAllCommands() → dynamic command list
├── appends Chat Features block (4 items, static)
└── appends Tips block (4 items, static)
```
