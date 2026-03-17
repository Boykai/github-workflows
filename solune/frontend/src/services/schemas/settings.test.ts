import { describe, it, expect } from 'vitest';
import { EffectiveUserSettingsSchema } from './settings';

const validSettings = {
  ai: { provider: 'copilot', model: 'gpt-4o', temperature: 0.7, agent_model: 'gpt-4o' },
  display: { theme: 'dark', default_view: 'chat', sidebar_collapsed: false },
  workflow: { default_repository: null, default_assignee: 'octocat', copilot_polling_interval: 30 },
  notifications: {
    task_status_change: true,
    agent_completion: true,
    new_recommendation: false,
    chat_mention: true,
  },
};

describe('EffectiveUserSettingsSchema', () => {
  it('parses valid complete settings', () => {
    const result = EffectiveUserSettingsSchema.parse(validSettings);
    expect(result).toEqual(validSettings);
  });

  it('accepts azure_openai as AI provider', () => {
    const data = { ...validSettings, ai: { ...validSettings.ai, provider: 'azure_openai' } };
    expect(EffectiveUserSettingsSchema.parse(data).ai.provider).toBe('azure_openai');
  });

  it('accepts light theme', () => {
    const data = {
      ...validSettings,
      display: { ...validSettings.display, theme: 'light' },
    };
    expect(EffectiveUserSettingsSchema.parse(data).display.theme).toBe('light');
  });

  it('accepts all default_view options', () => {
    for (const view of ['chat', 'board', 'settings'] as const) {
      const data = {
        ...validSettings,
        display: { ...validSettings.display, default_view: view },
      };
      expect(EffectiveUserSettingsSchema.parse(data).display.default_view).toBe(view);
    }
  });

  it('accepts nullable default_repository', () => {
    const withRepo = {
      ...validSettings,
      workflow: { ...validSettings.workflow, default_repository: 'my-org/my-repo' },
    };
    expect(EffectiveUserSettingsSchema.parse(withRepo).workflow.default_repository).toBe(
      'my-org/my-repo'
    );
  });

  it('rejects invalid AI provider', () => {
    const data = { ...validSettings, ai: { ...validSettings.ai, provider: 'openai' } };
    expect(() => EffectiveUserSettingsSchema.parse(data)).toThrow();
  });

  it('rejects invalid theme value', () => {
    const data = {
      ...validSettings,
      display: { ...validSettings.display, theme: 'blue' },
    };
    expect(() => EffectiveUserSettingsSchema.parse(data)).toThrow();
  });

  it('rejects missing ai section', () => {
    const { ai: _, ...rest } = validSettings;
    expect(() => EffectiveUserSettingsSchema.parse(rest)).toThrow();
  });

  it('rejects non-number temperature', () => {
    const data = { ...validSettings, ai: { ...validSettings.ai, temperature: 'high' } };
    expect(() => EffectiveUserSettingsSchema.parse(data)).toThrow();
  });

  it('rejects non-boolean notification preferences', () => {
    const data = {
      ...validSettings,
      notifications: { ...validSettings.notifications, task_status_change: 'yes' },
    };
    expect(() => EffectiveUserSettingsSchema.parse(data)).toThrow();
  });
});
