/**
 * Centralized tooltip content registry.
 *
 * Every tooltip string in the application is stored here, keyed by a
 * hierarchical dot-notation identifier: `{area}.{section}.{element}`.
 * This makes content easy to audit, update, and prepare for future
 * localization — no tooltip copy lives inside component files.
 */

/** A single tooltip content entry. */
export interface TooltipEntry {
  /** Concise explanation of the element's purpose and consequences (required). */
  summary: string;
  /** Optional bolded heading for complex features (progressive disclosure). */
  title?: string;
  /** Optional URL for a "Learn more" link (progressive disclosure tier 2). */
  learnMoreUrl?: string;
}

// ---------------------------------------------------------------------------
// Registry
// ---------------------------------------------------------------------------

export const tooltipContent: Record<string, TooltipEntry> = {
  // ── Board ────────────────────────────────────────────────────────────
  'board.toolbar.refreshButton': {
    summary: 'Manually refresh the board data. The board also auto-refreshes every 5 minutes.',
  },
  'board.toolbar.cleanUpButton': {
    title: 'Repository Clean Up',
    summary:
      "Remove stale Solune-generated branches, pull requests, and orphaned issues while preserving 'main', external assets, and items linked to open issues on the project board.",
  },
  'board.toolbar.filterButton': {
    summary: 'Filter board items by labels, assignees, or milestones to focus on specific work.',
  },
  'board.toolbar.sortButton': {
    summary: 'Sort board items by created date, updated date, priority, or title.',
  },
  'board.toolbar.groupByButton': {
    summary: 'Group board items by label, assignee, or milestone for a categorized view.',
  },
  'board.toolbar.clearAllButton': {
    summary: 'Reset all active filters, sorting, and grouping back to the default view.',
  },

  // ── Chat ─────────────────────────────────────────────────────────────
  'chat.toolbar.aiEnhanceToggle': {
    title: 'AI Enhance',
    summary:
      'When enabled, your messages are automatically refined by AI before being sent — improving clarity and detail for better agent responses.',
  },
  'chat.toolbar.attachButton': {
    summary: 'Attach files (images, PDFs, text, code) to provide additional context for the agent.',
  },
  'chat.toolbar.voiceButton': {
    summary: 'Use your microphone to dictate a message instead of typing.',
  },
  'chat.toolbar.sendButton': {
    summary: 'Send your message to the agent for processing.',
  },
  'chat.interface.historyToggle': {
    summary: 'Show or hide previous conversations for this project.',
  },

  // ── Agents ───────────────────────────────────────────────────────────
  'agents.card.editButton': {
    summary: "Open the agent editor to modify this agent's name, system prompt, tools, and icon.",
  },
  'agents.card.deleteButton': {
    summary:
      'Opens a PR to remove this agent from the repository. The catalog updates only after that PR is merged into main.',
  },
  'agents.card.iconButton': {
    summary: 'Choose a custom icon for this agent from the icon catalog.',
  },
  'agents.card.modelSelector': {
    title: 'Pipeline Model',
    summary:
      'Set the default AI model used when this agent runs in a pipeline. Different models vary in speed, cost, and capability.',
  },
  'agents.panel.searchInput': {
    summary: 'Search agents by name, slug, description, or assigned tools.',
  },
  'agents.panel.sortButton': {
    summary: 'Sort agents alphabetically by name or by pipeline usage count.',
  },
  'agents.panel.bulkUpdateButton': {
    title: 'Bulk Model Update',
    summary:
      'Change the default AI model for multiple agents at once. This affects which model each selected agent uses in pipeline runs.',
  },
  'agents.panel.addAgentButton': {
    summary: 'Create a new custom agent with a name, system prompt, tools, and icon.',
  },
  'agents.modal.systemPrompt': {
    title: 'System Prompt',
    summary:
      "Detailed instructions that define the agent's behavior, expertise, and response style. A well-crafted prompt is the most important factor in agent quality.",
  },
  'agents.modal.toolsEditor': {
    title: 'Agent Tools',
    summary:
      'Select which MCP tools this agent can use. Tools give agents capabilities like reading files, running commands, or accessing APIs.',
  },
  'agents.modal.nameField': {
    summary:
      'A descriptive name for the agent (e.g., "Security Reviewer"). This appears in the agent catalog and pipeline configuration.',
  },
  'agents.modal.aiEnhanceToggle': {
    title: 'AI Enhance',
    summary:
      'When enabled, the system prompt is automatically refined by AI for clarity and effectiveness before saving.',
  },

  // ── Pipeline ─────────────────────────────────────────────────────────
  'pipeline.stage.modelSelector': {
    title: 'AI Model Selection',
    summary:
      'Choose which language model powers this pipeline stage. Different models vary in speed, cost, and capability.',
  },
  'pipeline.stage.deleteButton': {
    summary:
      'Remove this stage from the pipeline. Agents assigned to this stage will be unassigned.',
  },
  'pipeline.stage.lockIcon': {
    summary: "This stage's position in the pipeline is locked and cannot be reordered.",
  },
  'pipeline.stage.parallelGroup': {
    title: 'Grouped Stage',
    summary:
      'Agents in this stage are treated as a coordinated group. The pipeline completes the entire group before advancing to the next stage.',
  },
  'pipeline.stage.sequentialGroup': {
    title: 'Sequential Stage',
    summary:
      'A single agent stage runs after the previous stage completes and finishes before the next stage begins.',
  },
  'pipeline.stage.addAgentButton': {
    summary:
      'Assign an agent to this pipeline stage. Adding another agent to a populated stage groups them together into a coordinated group.',
  },
  'pipeline.agent.parallelHint': {
    summary: 'These agents are grouped in the same stage.',
  },
  'pipeline.agent.sequentialHint': {
    summary: 'This agent runs after the previous completes.',
  },
  'pipeline.board.addStageButton': {
    summary:
      'Add a new stage to the pipeline. Stages define the sequential workflow that items move through.',
  },
  'pipeline.board.savePipelineButton': {
    title: 'Save Pipeline',
    summary:
      'Persist the current pipeline configuration. Unsaved changes will be lost if you navigate away.',
  },
  'pipeline.board.deletePipelineButton': {
    summary: 'Permanently delete this pipeline configuration. This action cannot be undone.',
  },
  'pipeline.board.modelDropdown': {
    title: 'Pipeline-Level Model',
    summary:
      'Set a default AI model for all stages in this pipeline. Individual stage models override this setting.',
  },
  'pipeline.board.createButton': {
    summary: 'Create a new pipeline configuration to define a custom agent workflow.',
  },

  // ── Chores ───────────────────────────────────────────────────────────
  'chores.card.executeButton': {
    title: 'Trigger Chore',
    summary:
      'Run this chore immediately, outside of its normal schedule. Useful for testing or one-off runs.',
  },
  'chores.card.editButton': {
    summary: "Modify this chore's name, description, schedule, and configuration.",
  },
  'chores.card.deleteButton': {
    summary: 'Permanently remove this chore. Any scheduled runs will be cancelled.',
  },
  'chores.card.statusToggle': {
    summary:
      'Pause or activate this chore. Paused chores will not run on their schedule until reactivated.',
  },
  'chores.card.aiEnhanceToggle': {
    title: 'AI Enhance',
    summary:
      'When enabled, the chore description is refined by AI for clarity and actionability before execution.',
  },
  'chores.card.pipelineSelector': {
    summary: 'Choose which pipeline configuration this chore uses when it runs.',
  },
  'chores.panel.searchInput': {
    summary: 'Search chores by name or template path.',
  },
  'chores.panel.sortButton': {
    summary: 'Sort chores by name or creation date.',
  },
  'chores.panel.addChoreButton': {
    summary: 'Create a new scheduled chore from a template or custom configuration.',
  },

  // ── Settings ─────────────────────────────────────────────────────────
  'settings.general.themeToggle': {
    summary: 'Switch between light and dark theme for the application.',
  },
  'settings.models.addButton': {
    summary: 'Add a new AI model configuration to make it available for agents and pipelines.',
  },
  'settings.ai.temperatureSlider': {
    title: 'Temperature',
    summary:
      'Controls randomness in AI responses. Lower values (0.0) produce more deterministic output; higher values (1.0+) increase creativity.',
  },
  'settings.ai.modelProvider': {
    summary: 'Select the AI model provider (e.g., OpenAI, Anthropic) for the default model.',
  },

  // ── Tools ────────────────────────────────────────────────────────────
  'tools.card.editButton': {
    summary: "Edit this MCP tool's configuration, including its name, URL, and target repository.",
  },
  'tools.card.resyncButton': {
    summary: "Re-sync this tool's configuration with GitHub to pick up any changes.",
  },
  'tools.card.deleteButton': {
    summary: 'Remove this MCP tool configuration. Agents using this tool will lose access to it.',
  },
  'tools.panel.searchInput': {
    summary: 'Search tools by name or description.',
  },
  'tools.panel.addToolButton': {
    summary: 'Add a new MCP tool configuration to make it available for agents.',
  },
};
