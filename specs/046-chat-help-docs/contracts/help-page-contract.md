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
4. Chat Features (7 informational cards)          ← NEW
5. Feature Guides (8 FeatureGuideCards)
6. Slash Commands (table + footer note)            ← MODIFIED
```

## Chat Features Section Contract

### Section Structure

```tsx
<section>
  <h2>Chat Features</h2>
  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
    {CHAT_FEATURES.map((feature) => (
      <div key={feature.title} className="moonwell ...">
        <Icon />
        <h4>{feature.title}</h4>
        <p>{feature.description}</p>
      </div>
    ))}
  </div>
</section>
```

### CHAT_FEATURES Data

| # | Title | Icon | Description |
|---|-------|------|-------------|
| 1 | @Pipeline Mentions | `AtSign` | Type `@` followed by a pipeline name to trigger autocomplete. Select from the dropdown to insert an inline mention token. Validated on submit. |
| 2 | File Attachments | `Paperclip` | Use the toolbar attachment button to add files. Supports images (PNG, JPEG, GIF, WebP, SVG), documents (PDF, TXT, MD), and data files (CSV, JSON, YAML, ZIP). 10 MB per-file limit. |
| 3 | Voice Input | `Mic` | Click the microphone button for speech-to-text. Chrome and Edge recommended. Shows live interim transcription and auto-stops when speech ends. |
| 4 | AI Enhance | `Sparkles` | Toggle AI Enhance in the toolbar to enrich messages before sending. Defaults to ON and persists across sessions. |
| 5 | Task Proposals | `ListTodo` | AI proposes structured tasks with title, description, and pipeline badge. Confirm to create a GitHub issue. Status change proposals show a current-to-target flow. |
| 6 | Message History | `History` | Press Arrow Up/Down to browse previously sent messages. Your current draft is preserved. Use the history popover for quick recall. |
| 7 | Keyboard Shortcuts | `Keyboard` | Enter to send, Escape to dismiss autocomplete, Tab to select highlighted option, `/` to trigger commands, `@` to trigger mentions. |

### Card Rendering

Cards are rendered as non-navigable `<div>` elements (not `<Link>`) since Chat Features are informational, not navigation targets. Visual styling mirrors `FeatureGuideCard` (moonwell background, icon circle, title + description).

## Enriched Slash Commands Table Contract

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
        <td>{getCommandOptions(cmd)}</td>  {/* ← NEW CELL */}
      </tr>
    ))}
  </tbody>
</table>
```

### Options Column Logic

```typescript
function getCommandOptions(cmd: CommandDefinition): string {
  if (cmd.passthrough) {
    return '<description> [#status-column] (admin only)';
  }
  if (cmd.parameterSchema?.type === 'enum' && cmd.parameterSchema.values) {
    if (cmd.parameterSchema.labels) {
      return cmd.parameterSchema.values
        .map((v) => `${v} (${cmd.parameterSchema!.labels![v]})`)
        .join(', ');
    }
    return cmd.parameterSchema.values.join(', ');
  }
  return '—';
}
```

### Options Column Expected Values

| Command | Options |
|---------|---------|
| `/agent` | `<description> [#status-column]` + "(admin only)" |
| `/help` | — |
| `/language` | en (English), es (Spanish), fr (French), de (German), ja (Japanese), zh (Chinese) |
| `/notifications` | on, off |
| `/theme` | light, dark, system |
| `/view` | chat, board, settings |

**Note**: The `/language` command registration in `registry.ts` must be updated to include `labels` for human-readable language names.

### Footer Note

Below the commands table:

```tsx
<p className="mt-3 text-xs text-muted-foreground">
  Type <code>/</code> in chat to autocomplete commands. You can also type{' '}
  <code>help</code> without the slash.
</p>
```

## FAQ Corrections Contract

### chat-voice-1

**Before**:
> Type / in the chat to see all available commands. Common ones include /help, /theme, and /clear. See the Slash Commands section below for the full list.

**After**:
> Type / in the chat to see all available commands. Common ones include /help, /theme, and /agent. See the Slash Commands section below for the full list.

**Change**: Replace `/clear` with `/agent` — `/clear` does not exist in the command registry.

### chat-voice-2

**Before**:
> Yes — click the attachment icon in the chat input or drag-and-drop files. Supported formats include images, PDFs, markdown, and code files up to 10 MB each.

**After**:
> Yes — click the attachment button in the chat toolbar to select files. Supported formats include images, PDFs, markdown, and code files up to 10 MB each.

**Change**: Remove "drag-and-drop" claim (not implemented) and replace "attachment icon in the chat input" with "attachment button in the chat toolbar".

## Test Contract

```typescript
describe('HelpPage', () => {
  it('renders Chat Features section with 7 cards', () => {
    render(<HelpPage />, { wrapper: MemoryRouter });
    expect(screen.getByText('Chat Features')).toBeInTheDocument();
    expect(screen.getByText('@Pipeline Mentions')).toBeInTheDocument();
    expect(screen.getByText('File Attachments')).toBeInTheDocument();
    expect(screen.getByText('Voice Input')).toBeInTheDocument();
    expect(screen.getByText('AI Enhance')).toBeInTheDocument();
    expect(screen.getByText('Task Proposals')).toBeInTheDocument();
    expect(screen.getByText('Message History')).toBeInTheDocument();
    expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
  });

  it('commands table has Options column', () => {
    render(<HelpPage />, { wrapper: MemoryRouter });
    expect(screen.getByText('Options')).toBeInTheDocument();
    expect(screen.getByText(/light, dark, system/)).toBeInTheDocument();
  });

  it('FAQ chat-voice-1 does not reference /clear', () => {
    render(<HelpPage />, { wrapper: MemoryRouter });
    expect(screen.queryByText(/\/clear/)).not.toBeInTheDocument();
  });

  it('FAQ chat-voice-2 does not reference drag-and-drop', () => {
    render(<HelpPage />, { wrapper: MemoryRouter });
    expect(screen.queryByText(/drag-and-drop/i)).not.toBeInTheDocument();
  });
});
```
