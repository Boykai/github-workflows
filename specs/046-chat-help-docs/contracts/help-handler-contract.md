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
  • @Pipeline Mentions: Type @ to invoke a pipeline by name
  • File Attachments: Use the attachment button to add files (images, PDF, code, up to 10 MB)
  • Voice Input: Use the microphone button for speech-to-text (Chrome/Edge recommended)
  • AI Enhance: Toggle AI Enhance in the toolbar for smarter responses

Tips:
  • Type / to browse and autocomplete commands
  • You can also type help without the slash
  • Use Arrow Up/Down to browse previous messages
  • Visit the Help page for the full guide
```

### Format Rules

1. **Section headers** use the format `SectionName:\n` (no Markdown, no bold, no `#`).
2. **Command lines** use `  /syntax  —  description` (two-space indent, em-dash separator).
3. **Chat Features lines** use `  • FeatureName: description` (two-space indent, bullet character, colon separator).
4. **Tips lines** use `  • tip text` (two-space indent, bullet character).
5. **Section separators** are double newlines (`\n\n`) between the three sections.
6. **No Markdown syntax** anywhere in the output (FR-003).
7. **Dynamic content**: Only the command list section changes when commands are added/removed.
8. **Static content**: Chat Features and Tips sections are hardcoded strings.

## Behavioral Contract

| Scenario | Expected Behavior |
|----------|-------------------|
| User types `/help` | Returns success result with full expanded output |
| User types `help` (no slash) | Same output (alias handled by `parseCommand()` in registry) |
| New command is registered | Command list section includes it automatically; Chat Features and Tips unchanged |
| No commands registered | Output shows empty command list, still includes Chat Features and Tips |
| Arguments provided (`/help foo`) | Arguments are ignored; full output returned |

## Test Assertions

```typescript
// Section presence
expect(result.message).toContain('Chat Features:');
expect(result.message).toContain('Tips:');

// Chat Features content
expect(result.message).toContain('@Pipeline Mentions');
expect(result.message).toContain('File Attachments');
expect(result.message).toContain('Voice Input');
expect(result.message).toContain('AI Enhance');

// Tips content
expect(result.message).toContain('Type / to browse and autocomplete commands');
expect(result.message).toContain('help without the slash');
expect(result.message).toContain('Arrow Up/Down');
expect(result.message).toContain('Help page');
```
