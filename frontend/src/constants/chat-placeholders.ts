/**
 * Centralized chat input placeholder copy registry.
 *
 * Every chat placeholder string is stored here, keyed by chat context.
 * This makes copy easy to audit, update, and prepare for future
 * localization — no placeholder copy lives inside component files.
 */

/** Configuration for a single chat input's placeholder text. */
export interface ChatPlaceholderConfig {
  /** Full placeholder text for desktop viewports (≥640px, Tailwind `sm` breakpoint) */
  desktop: string;
  /** Shortened placeholder text for mobile viewports (<640px) */
  mobile: string;
  /** Accessible label for screen readers */
  ariaLabel: string;
}

// ---------------------------------------------------------------------------
// Registry
// ---------------------------------------------------------------------------

export const CHAT_PLACEHOLDERS: Record<string, ChatPlaceholderConfig> = {
  main: {
    desktop: 'Ask a question, describe a task, use / for commands, or @ to select a pipeline\u2026',
    mobile: 'Ask anything or use / and @ for more\u2026',
    ariaLabel: 'Chat input — ask questions, describe tasks, use slash commands, or mention pipelines',
  },
  agentFlow: {
    desktop: "Describe what you'd like your agent to do\u2026",
    mobile: 'Describe your agent\u2026',
    ariaLabel: 'Agent creation chat input',
  },
  choreFlow: {
    desktop: 'Add details or refine your request\u2026',
    mobile: 'Add details\u2026',
    ariaLabel: 'Chore template chat input',
  },
};

/** P3: Example prompts for cycling placeholder animation in main chat */
export const CYCLING_EXAMPLES: string[] = [
  "Try: 'Summarize the open issues for this sprint'",
  "Try: 'Create an issue for updating the login page'",
  "Try: '/ to see available commands'",
  "Try: '@ to select a pipeline and run it'",
  "Try: 'What's the status of my project?'",
];
