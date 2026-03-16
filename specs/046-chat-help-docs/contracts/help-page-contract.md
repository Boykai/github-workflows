# Contract: Help Page Component

**Feature**: `046-chat-help-docs` | **Date**: 2026-03-16 | **Data Model**: [data-model.md](../data-model.md)

## Overview

This contract defines the changes to the `HelpPage` component: a new Chat Features section with seven cards, an enriched Slash Commands table with an Options column, a footer note, and two FAQ corrections.

## Component API

**File**: `solune/frontend/src/pages/HelpPage.tsx`

```tsx
export function HelpPage(): JSX.Element;
```

The component takes no props. It internally calls `getAllCommands()` from the command registry and `useOnboarding()` for tour replay.

## Section Layout Contract

The Help page renders sections in this order:

```text
1. Hero (CelestialCatalogHero)
2. Getting Started (3 FeatureGuideCards)
3. Frequently Asked Questions (FaqAccordion)
4. Chat Features (7 FeatureGuideCards)          ← NEW
5. Feature Guides (8 FeatureGuideCards)
6. Slash Commands (table + footer note)         ← MODIFIED
```

## Chat Features Section Contract

### Section Structure

```tsx
<section>
  <h2>Chat Features</h2>
  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
    {CHAT_FEATURES.map((feature) => (
      <FeatureGuideCard key={feature.title} {...feature} />
    ))}
  </div>
</section>
```

### CHAT_FEATURES Data

| # | Title | Icon | Description | href |
|---|-------|------|-------------|------|
| 1 | @Pipeline Mentions | `AtSign` | Type `@` followed by a pipeline name to trigger autocomplete. Select from the dropdown to insert an inline mention token. Validated on submit. | `/` |
| 2 | File Attachments | `Paperclip` | Use the toolbar attachment button to add files. Supports images (PNG, JPEG, GIF, WebP, SVG), documents (PDF, TXT, MD), and data files (CSV, JSON, YAML, ZIP). 10 MB per-file limit. | `/` |
| 3 | Voice Input | `Mic` | Click the microphone button for speech-to-text. Chrome and Edge recommended. Live interim transcription displayed while speaking. Auto-stops on speech end. | `/` |
| 4 | AI Enhance | `Sparkles` | Toggle the AI Enhance button in the toolbar to enrich messages before sending. Defaults to ON. Persists across sessions. | `/` |
| 5 | Task Proposals | `ListTodo` | AI proposes structured tasks with title, description, and pipeline badge. Confirm to create a GitHub issue. Status change proposals show current-to-target flow. | `/` |
| 6 | Message History | `History` | Use Arrow Up/Down keys to browse previously sent messages. Your current draft is preserved when navigating. Use the history popover for quick recall. | `/` |
| 7 | Keyboard Shortcuts | `Keyboard` | Enter to send, Escape to dismiss autocomplete, Tab to select highlighted option, `/` to trigger commands, `@` to trigger pipeline mentions. | `/` |

### Validation Rules

- Exactly 7 cards must be rendered (FR-006).
- Each card's description must match the content specified above (FR-008).
- Cards must be wrapped in `FeatureGuideCard` component (FR-007).
- Grid must reflow to single column on mobile screens.

## Enriched Commands Table Contract

### Table Structure

```tsx
<table>
  <thead>
    <tr>
      <th>Command</th>
      <th>Syntax</th>
      <th>Description</th>
      <th>Options</th>           {/* ← NEW COLUMN */}
    </tr>
  </thead>
  <tbody>
    {commands.map((cmd) => (
      <tr key={cmd.name}>
        <td>{cmd.name}</td>
        <td>{cmd.syntax}</td>
        <td>{cmd.description}</td>
        <td>{getOptionsDisplay(cmd)}</td>  {/* ← NEW CELL */}
      </tr>
    ))}
  </tbody>
</table>
```

### Options Display Logic

```typescript
function getOptionsDisplay(cmd: CommandDefinition): string {
  if (cmd.passthrough) {
    return '<description> [#status-column] (admin only)';
  }
  if (!cmd.parameterSchema || cmd.parameterSchema.type !== 'enum' || !cmd.parameterSchema.values) {
    return '—';
  }
  const { values, labels } = cmd.parameterSchema;
  if (labels) {
    return values.map((v) => `${v} (${labels[v] ?? v})`).join(', ');
  }
  return values.join(', ');
}
```

### Expected Options Column Values

| Command | Options Display |
|---------|-----------------|
| `/agent` | `<description> [#status-column] (admin only)` |
| `/help` | `—` |
| `/language` | `en (English), es (Spanish), fr (French), de (German), ja (Japanese), zh (Chinese)` |
| `/notifications` | `on, off` |
| `/theme` | `light, dark, system` |
| `/view` | `chat, board, settings` |

### Footer Note

Below the table (outside the `<table>` element):

```tsx
<p className="mt-3 text-xs text-muted-foreground">
  Type <code className="rounded bg-muted px-1 font-mono">/</code> in chat to autocomplete
  commands. You can also type{' '}
  <code className="rounded bg-muted px-1 font-mono">help</code> without the slash.
</p>
```

## FAQ Corrections Contract

### chat-voice-1

**Before**: `'Type / in the chat to see all available commands. Common ones include /help, /theme, and /clear. See the Slash Commands section below for the full list.'`

**After**: `'Type / in the chat to see all available commands. Common ones include /help, /theme, and /agent. See the Slash Commands section below for the full list.'`

**Change**: Replace `/clear` with `/agent` (FR-016).

### chat-voice-2

**Before**: `'Yes — click the attachment icon in the chat input or drag-and-drop files. Supported formats include images, PDFs, markdown, and code files up to 10 MB each.'`

**After**: `'Yes — click the attachment button in the chat toolbar to add files. Supported formats include images, PDFs, markdown, and code files up to 10 MB each.'`

**Change**: Remove "drag-and-drop" claim; replace with "click the attachment button in the chat toolbar" (FR-017).

## Test Assertions

```tsx
// Chat Features section
expect(screen.getByText('Chat Features')).toBeInTheDocument();
expect(screen.getByText('@Pipeline Mentions')).toBeInTheDocument();
expect(screen.getByText('File Attachments')).toBeInTheDocument();
expect(screen.getByText('Voice Input')).toBeInTheDocument();
expect(screen.getByText('AI Enhance')).toBeInTheDocument();
expect(screen.getByText('Task Proposals')).toBeInTheDocument();
expect(screen.getByText('Message History')).toBeInTheDocument();
expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();

// Options column
expect(screen.getByText('Options')).toBeInTheDocument();
expect(screen.getByText('light, dark, system')).toBeInTheDocument();
expect(screen.getByText(/en \(English\)/)).toBeInTheDocument();

// Footer note
expect(screen.getByText(/autocomplete commands/)).toBeInTheDocument();

// FAQ corrections
expect(screen.queryByText(/\/clear/)).not.toBeInTheDocument();
expect(screen.queryByText(/drag-and-drop/i)).not.toBeInTheDocument();
```
