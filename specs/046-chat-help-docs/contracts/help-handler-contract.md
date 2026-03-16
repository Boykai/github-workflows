# Contract: Help Command Handler

**Feature**: `046-chat-help-docs` | **Date**: 2026-03-16 | **Data Model**: [data-model.md](../data-model.md)

## Overview

This contract defines the expanded output format of the `/help` command handler. The handler is modified to append "Chat Features" and "Tips" sections after the existing dynamic command list.

## Function Signature

**File**: `solune/frontend/src/lib/commands/handlers/help.ts`

```typescript
export function helpHandler(_args: string, _context: CommandContext): CommandResult;
```

### Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `_args` | `string` | Command arguments (unused — `/help` takes no arguments) |
| `_context` | `CommandContext` | Runtime context with theme/settings (unused) |

### Output

```typescript
interface CommandResult {
  success: true;
  message: string;   // Expanded plain-text output (see format below)
  clearInput: true;
}
```

## Output Format Contract

The `message` string follows this exact structure:

```text
Available Commands:
  /agent <description> [#status-column]  —  Create a custom agent for your project (admin only)
  /help  —  Show all available commands
  /language <en|es|fr|de|ja|zh>  —  Change the display language
  /notifications <on|off>  —  Toggle notifications on or off
  /theme <light|dark|system>  —  Change the UI theme
  /view <chat|board|settings>  —  Set the default view

Chat Features:
  @Pipeline Mentions — Type @ to invoke a pipeline by name
  File Attachments — Use the attachment button to add files (images, PDF, code, up to 10 MB)
  Voice Input — Use the microphone button for speech-to-text (Chrome/Edge recommended)
  AI Enhance — Toggle AI Enhance in the toolbar for smarter responses

Tips:
  • Type / to browse and autocomplete commands
  • You can also type help without the slash
  • Use Arrow Up/Down to browse previous messages
  • Visit the Help page for the full guide
```

### Format Rules

1. **Command list** (lines 2–7): Dynamically generated from `getAllCommands()`, sorted alphabetically. Format: `  {syntax}  —  {description}`.
2. **Blank separator**: One empty line between the command list and the Chat Features header.
3. **Chat Features header**: `Chat Features:` (no indentation).
4. **Feature lines** (4): Two-space indent, em-dash separator: `  {name} — {description}`.
5. **Blank separator**: One empty line between Chat Features and Tips.
6. **Tips header**: `Tips:` (no indentation).
7. **Tip lines** (4): Two-space indent, bullet character (U+2022): `  • {tip text}`.

### Invariants

- The command list is **dynamic** — adding a new command via `registerCommand()` automatically includes it.
- The Chat Features and Tips sections are **static** — they do not change when commands are added or removed.
- All text is **plain text** — no Markdown, HTML, or ANSI formatting.
- The function signature, return type, and `clearInput: true` behavior remain unchanged.

## Test Contract

```typescript
describe('helpHandler', () => {
  it('output includes Chat Features section', () => {
    const result = helpHandler('', context);
    expect(result.message).toContain('Chat Features:');
    expect(result.message).toContain('@Pipeline Mentions');
    expect(result.message).toContain('File Attachments');
    expect(result.message).toContain('Voice Input');
    expect(result.message).toContain('AI Enhance');
  });

  it('output includes Tips section', () => {
    const result = helpHandler('', context);
    expect(result.message).toContain('Tips:');
    expect(result.message).toContain('Type / to browse and autocomplete commands');
    expect(result.message).toContain('help without the slash');
    expect(result.message).toContain('Arrow Up/Down');
    expect(result.message).toContain('Help page');
  });
});
```
