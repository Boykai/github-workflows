import { z } from 'zod';

const AIPreferencesSchema = z.object({
  provider: z.enum(['copilot', 'azure_openai']),
  model: z.string(),
  temperature: z.number(),
  agent_model: z.string(),
});

const DisplayPreferencesSchema = z.object({
  theme: z.enum(['dark', 'light']),
  default_view: z.enum(['chat', 'board', 'settings']),
  sidebar_collapsed: z.boolean(),
});

const WorkflowDefaultsSchema = z.object({
  default_repository: z.string().nullable(),
  default_assignee: z.string(),
  copilot_polling_interval: z.number(),
});

const NotificationPreferencesSchema = z.object({
  task_status_change: z.boolean(),
  agent_completion: z.boolean(),
  new_recommendation: z.boolean(),
  chat_mention: z.boolean(),
});

export const EffectiveUserSettingsSchema = z.object({
  ai: AIPreferencesSchema,
  display: DisplayPreferencesSchema,
  workflow: WorkflowDefaultsSchema,
  notifications: NotificationPreferencesSchema,
});