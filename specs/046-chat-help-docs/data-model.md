# Data Model: Update Chat Help & Help Page for Comprehensive Chat Commands & Features

**Feature**: `046-chat-help-docs` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Entities

### CommandDefinition (existing — reference)

Represents a single registered slash command. Defined in `src/lib/commands/types.ts`. No changes to this entity — documented here for completeness.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | `string` | Required, unique, lowercase | Command name without the `/` prefix |
| `description` | `string` | Required, non-empty | Human-readable description shown in help output and autocomplete |
| `syntax` | `string` | Required, non-empty | Full syntax including `/` prefix and parameter placeholders |
| `handler` | `CommandHandler` | Required | Function that executes the command |
| `parameterSchema` | `ParameterSchema \| undefined` | Optional | Defines valid parameter types and values |
| `passthrough` | `boolean \| undefined` | Optional | When true, the command is forwarded to the backend |

**Validation Rules**:
- `name` is lowercase, unique within the registry
- `syntax` starts with `/`
- Commands are sorted alphabetically by `name` when retrieved via `getAllCommands()`

**Relationships**:
- Referenced by `helpHandler` → generates the command list in `/help` output
- Referenced by `HelpPage` → renders the Slash Commands table
- Referenced by `CommandAutocomplete` → provides autocomplete suggestions

---

### ParameterSchema (existing — reference, with labels enhancement)

Defines valid parameter values for a command. Defined in `src/lib/commands/types.ts`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `type` | `'enum' \| 'string' \| 'boolean'` | Required | Parameter type |
| `values` | `string[] \| undefined` | Required for `enum` type | Valid parameter values |
| `labels` | `Record<string, string> \| undefined` | Optional | Human-readable labels keyed by value (e.g., `{ en: 'English' }`) |

**Validation Rules**:
- When `type === 'enum'`, `values` must be a non-empty array
- When `labels` is provided, every key in `labels` should exist in `values`
- `labels` values are display strings for the Options column

**Enhancement for this feature**: The `/language` command registration should add `labels` to provide human-readable language names in the Options column:
```typescript
labels: { en: 'English', es: 'Spanish', fr: 'French', de: 'German', ja: 'Japanese', zh: 'Chinese' }
```

---

### ChatFeatureCard (new — Help page data)

Represents a feature card displayed in the Chat Features section of the Help page. This is a UI data structure defined as a constant array in `HelpPage.tsx`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `title` | `string` | Required, non-empty | Feature card heading |
| `description` | `string` | Required, non-empty | Feature explanation text |
| `icon` | `LucideIcon` | Required | Icon component from lucide-react |

**Instances** (7 cards):

| Title | Icon | Description Summary |
|-------|------|-------------------|
| @Pipeline Mentions | `AtSign` | Type `@` + pipeline name; autocomplete dropdown; inline token badges; validated on submit |
| File Attachments | `Paperclip` | Supported formats list; 10 MB limit; toolbar button; preview chips with status |
| Voice Input | `Mic` | Microphone button; Chrome/Edge recommended; live transcription; auto-stop |
| AI Enhance | `Sparkles` | Toolbar toggle; enriches messages; defaults to ON; persists across sessions |
| Task Proposals | `ListTodo` | AI proposes structured tasks; confirm to create; status change proposals |
| Message History | `History` | Arrow Up/Down to browse; draft preserved; history popover |
| Keyboard Shortcuts | `Keyboard` | Enter to send, Escape to dismiss, Tab to select, `/` and `@` triggers |

**Validation Rules**:
- Exactly 7 cards must be rendered
- Card descriptions must accurately reflect current application behavior

**Relationships**:
- Rendered in the Chat Features `<section>` of `HelpPage`
- Visually matches `FeatureGuideCard` styling (moonwell background, icon circle, responsive grid)

---

### FaqEntry (existing — reference)

Represents a question-and-answer pair in the Help page FAQ accordion. Defined in `src/types` and instantiated as `FAQ_ENTRIES` in `HelpPage.tsx`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `string` | Required, unique | Stable identifier for the entry |
| `question` | `string` | Required | FAQ question text |
| `answer` | `string` | Required | FAQ answer text |
| `category` | `string` | Required | Category for grouping (getting-started, agents-pipelines, chat-voice, settings-integration) |

**Corrections for this feature**:
- `chat-voice-1`: Answer must not reference `/clear` (does not exist); should reference `/agent` instead
- `chat-voice-2`: Answer must not claim "drag-and-drop"; should describe the attachment button click

---

### HelpOutputSection (new — /help handler data)

Represents the structure of the expanded `/help` command output. Not a TypeScript interface — this is the logical structure of the plain-text string returned by `helpHandler`.

| Section | Content | Dynamic? |
|---------|---------|----------|
| Header | `Available Commands:` | Static |
| Command List | `  /cmd  —  description` per registered command | Dynamic (from registry) |
| Separator | Blank line | Static |
| Chat Features Header | `Chat Features:` | Static |
| Feature Lines | `  {feature} — {description}` × 4 | Static |
| Separator | Blank line | Static |
| Tips Header | `Tips:` | Static |
| Tip Lines | `  • {tip text}` × 4 | Static |

**Validation Rules**:
- Command list section must remain dynamically generated
- Chat Features and Tips sections are static content
- All text must be plain text with no Markdown formatting

## Entity Relationships

```text
CommandDefinition (registry)
  ├── helpHandler() reads all commands ──→ HelpOutputSection.CommandList
  ├── HelpPage reads all commands ──→ Slash Commands table (4 columns)
  └── ParameterSchema ──→ Options column content

ChatFeatureCard[] (HelpPage constant)
  └── Rendered in ──→ Chat Features section (7 cards)

FaqEntry[] (HelpPage constant)
  └── Rendered in ──→ FAQ accordion
  └── chat-voice-1 and chat-voice-2 ──→ corrected text

HelpOutputSection (helpHandler return)
  └── Displayed in ──→ Chat message bubble (plain text)
```
