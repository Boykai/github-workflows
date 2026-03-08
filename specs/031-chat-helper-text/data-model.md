# Data Model: Update User Chat Helper Text for Comprehensive UX Guidance

**Feature**: 031-chat-helper-text | **Date**: 2026-03-08

## Overview

This feature has no database entities or API models. The "data model" consists of TypeScript type definitions for placeholder text configurations and the centralized constants that drive all chat input placeholder copy across the application.

## Entities

### ChatPlaceholderConfig

Defines the placeholder text configuration for a single chat input context.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `desktop` | `string` | Yes | Full descriptive placeholder displayed on viewports ≥768px |
| `mobile` | `string` | Yes | Shortened placeholder variant for viewports <768px |
| `ariaLabel` | `string` | Yes | Accessible label for the input field (announced by screen readers) |

**TypeScript definition:**

```typescript
interface ChatPlaceholderConfig {
  /** Full placeholder text for desktop viewports (≥768px) */
  desktop: string;
  /** Shortened placeholder text for mobile viewports (<768px) */
  mobile: string;
  /** Accessible label for screen readers — must convey the same guidance as the visible placeholder */
  ariaLabel: string;
}
```

### CyclingPlaceholderConfig (P3 — optional)

Extends the placeholder configuration with cycling example prompts for progressive capability discovery.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `examples` | `string[]` | Yes | Array of example prompts to cycle through (minimum 3) |
| `intervalMs` | `number` | No | Cycle interval in milliseconds (default: 5000) |
| `transitionMs` | `number` | No | Fade transition duration in milliseconds (default: 300) |

**TypeScript definition:**

```typescript
interface CyclingPlaceholderConfig {
  /** Example prompts to cycle through when input is empty and unfocused */
  examples: string[];
  /** Milliseconds between prompt transitions (default: 5000) */
  intervalMs?: number;
  /** Milliseconds for fade transition (default: 300) */
  transitionMs?: number;
}
```

## Centralized Constants

### CHAT_PLACEHOLDERS

Registry of all chat input placeholder configurations, keyed by chat context identifier.

| Key | Desktop Text | Mobile Text | Aria Label |
|-----|-------------|-------------|------------|
| `main` | "Ask a question, describe a task, use / for commands, or @ to select a pipeline…" | "Ask anything or use / and @ for more…" | "Chat input — ask questions, describe tasks, use slash commands, or mention pipelines" |
| `agentFlow` | "Describe what you'd like your agent to do…" | "Describe your agent…" | "Agent creation chat input" |
| `choreFlow` | "Add details or refine your request…" | "Add details…" | "Chore template chat input" |

### CYCLING_EXAMPLES (P3 — optional)

Example prompts for the main chat cycling placeholder animation.

| Index | Example Text |
|-------|-------------|
| 0 | "Try: 'Summarize the open issues for this sprint'" |
| 1 | "Try: 'Create an issue for updating the login page'" |
| 2 | "Try: '/ to see available commands'" |
| 3 | "Try: '@ to select a pipeline and run it'" |
| 4 | "Try: 'What's the status of my project?'" |

## State Transitions

N/A — placeholder text is static configuration with no state machine. The cycling placeholder (P3) has two visual states:

1. **Cycling** → Input is empty AND unfocused AND `prefers-reduced-motion` is not `reduce` → Cycles through examples at configured interval
2. **Static** → Input is focused OR non-empty OR `prefers-reduced-motion: reduce` → Shows the first example or the static desktop placeholder

## Validation Rules

| Rule | Applies To | Description |
|------|-----------|-------------|
| Desktop text ≤ 80 characters | `ChatPlaceholderConfig.desktop` | Ensures text fits within typical chat input widths (~500px at 14px font) without overflow |
| Mobile text ≤ 40 characters | `ChatPlaceholderConfig.mobile` | Ensures text fits within mobile chat input widths (~280px at 14px font) without overflow |
| Aria label matches visible text intent | `ChatPlaceholderConfig.ariaLabel` | Screen reader label must convey the same guidance as the visible placeholder |
| Examples array has ≥ 3 items | `CyclingPlaceholderConfig.examples` | Minimum variety for meaningful cycling |
| Interval ≥ 3000ms | `CyclingPlaceholderConfig.intervalMs` | Prevents rapid cycling that could be distracting or cause cognitive overload |

## Relationships

```
ChatPlaceholderConfig ──uses──▶ MentionInput.placeholder (main chat)
ChatPlaceholderConfig ──uses──▶ AgentChatFlow <input placeholder> (agent creation)
ChatPlaceholderConfig ──uses──▶ ChoreChatFlow <input placeholder> (chore template)
CyclingPlaceholderConfig ──extends──▶ ChatPlaceholderConfig.main (P3 only)
```
