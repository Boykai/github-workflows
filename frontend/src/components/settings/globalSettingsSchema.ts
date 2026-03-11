import { z } from 'zod';
import type { GlobalSettings as GlobalSettingsType, GlobalSettingsUpdate } from '@/types';

export const globalSettingsSchema = z.object({
  provider: z.enum(['copilot', 'azure_openai']),
  model: z.string(),
  temperature: z.number().min(0).max(2),
  theme: z.enum(['light', 'dark']),
  default_view: z.enum(['chat', 'board', 'settings']),
  sidebar_collapsed: z.boolean(),
  default_repository: z.string(),
  default_assignee: z.string(),
  copilot_polling_interval: z.number().int().min(0),
  task_status_change: z.boolean(),
  agent_completion: z.boolean(),
  new_recommendation: z.boolean(),
  chat_mention: z.boolean(),
  allowed_models: z.string(),
});

export type GlobalFormState = z.infer<typeof globalSettingsSchema>;

export const DEFAULTS: GlobalFormState = {
  provider: 'copilot',
  model: 'gpt-4o',
  temperature: 0.7,
  theme: 'light',
  default_view: 'chat',
  sidebar_collapsed: false,
  default_repository: '',
  default_assignee: '',
  copilot_polling_interval: 60,
  task_status_change: true,
  agent_completion: true,
  new_recommendation: true,
  chat_mention: true,
  allowed_models: '',
};

export function flatten(s: GlobalSettingsType): GlobalFormState {
  return {
    provider: s.ai.provider,
    model: s.ai.model,
    temperature: s.ai.temperature,
    theme: s.display.theme,
    default_view: s.display.default_view,
    sidebar_collapsed: s.display.sidebar_collapsed,
    default_repository: s.workflow.default_repository ?? '',
    default_assignee: s.workflow.default_assignee,
    copilot_polling_interval: s.workflow.copilot_polling_interval,
    task_status_change: s.notifications.task_status_change,
    agent_completion: s.notifications.agent_completion,
    new_recommendation: s.notifications.new_recommendation,
    chat_mention: s.notifications.chat_mention,
    allowed_models: s.allowed_models.join(', '),
  };
}

export function toUpdate(f: GlobalFormState): GlobalSettingsUpdate {
  return {
    ai: { provider: f.provider, model: f.model, temperature: f.temperature },
    display: {
      theme: f.theme,
      default_view: f.default_view,
      sidebar_collapsed: f.sidebar_collapsed,
    },
    workflow: {
      default_repository: f.default_repository || null,
      default_assignee: f.default_assignee,
      copilot_polling_interval: f.copilot_polling_interval,
    },
    notifications: {
      task_status_change: f.task_status_change,
      agent_completion: f.agent_completion,
      new_recommendation: f.new_recommendation,
      chat_mention: f.chat_mention,
    },
    allowed_models: f.allowed_models
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean),
  };
}
