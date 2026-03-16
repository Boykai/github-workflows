/**
 * Unit tests for globalSettingsSchema utilities: flatten, toUpdate, and schema validation.
 */

import { describe, it, expect } from 'vitest';
import { globalSettingsSchema, DEFAULTS, flatten, toUpdate } from './globalSettingsSchema';
import type { GlobalSettings as GlobalSettingsType } from '@/types';

const fullSettings: GlobalSettingsType = {
  ai: { provider: 'copilot', model: 'gpt-4o', temperature: 0.7 },
  display: { theme: 'dark', default_view: 'board', sidebar_collapsed: true },
  workflow: {
    default_repository: 'owner/repo',
    default_assignee: 'octocat',
    copilot_polling_interval: 120,
  },
  notifications: {
    task_status_change: false,
    agent_completion: true,
    new_recommendation: false,
    chat_mention: true,
  },
  allowed_models: ['gpt-4o', 'gpt-3.5'],
};

describe('globalSettingsSchema', () => {
  describe('schema validation', () => {
    it('validates default values', () => {
      const result = globalSettingsSchema.safeParse(DEFAULTS);
      expect(result.success).toBe(true);
    });

    it('rejects temperature below 0', () => {
      const result = globalSettingsSchema.safeParse({ ...DEFAULTS, temperature: -0.1 });
      expect(result.success).toBe(false);
    });

    it('rejects temperature above 2', () => {
      const result = globalSettingsSchema.safeParse({ ...DEFAULTS, temperature: 2.1 });
      expect(result.success).toBe(false);
    });

    it('accepts temperature at boundaries (0 and 2)', () => {
      expect(globalSettingsSchema.safeParse({ ...DEFAULTS, temperature: 0 }).success).toBe(true);
      expect(globalSettingsSchema.safeParse({ ...DEFAULTS, temperature: 2 }).success).toBe(true);
    });

    it('rejects negative polling interval', () => {
      const result = globalSettingsSchema.safeParse({
        ...DEFAULTS,
        copilot_polling_interval: -1,
      });
      expect(result.success).toBe(false);
    });

    it('accepts polling interval of 0', () => {
      const result = globalSettingsSchema.safeParse({
        ...DEFAULTS,
        copilot_polling_interval: 0,
      });
      expect(result.success).toBe(true);
    });

    it('rejects non-integer polling interval', () => {
      const result = globalSettingsSchema.safeParse({
        ...DEFAULTS,
        copilot_polling_interval: 30.5,
      });
      expect(result.success).toBe(false);
    });

    it('rejects invalid provider', () => {
      const result = globalSettingsSchema.safeParse({ ...DEFAULTS, provider: 'openai' });
      expect(result.success).toBe(false);
    });

    it('rejects invalid theme', () => {
      const result = globalSettingsSchema.safeParse({ ...DEFAULTS, theme: 'auto' });
      expect(result.success).toBe(false);
    });
  });

  describe('flatten', () => {
    it('flattens a full settings object into form state', () => {
      const result = flatten(fullSettings);
      expect(result).toEqual({
        provider: 'copilot',
        model: 'gpt-4o',
        temperature: 0.7,
        theme: 'dark',
        default_view: 'board',
        sidebar_collapsed: true,
        default_repository: 'owner/repo',
        default_assignee: 'octocat',
        copilot_polling_interval: 120,
        task_status_change: false,
        agent_completion: true,
        new_recommendation: false,
        chat_mention: true,
        allowed_models: 'gpt-4o, gpt-3.5',
      });
    });

    it('handles null nested ai object with defaults', () => {
      const settings = { ...fullSettings, ai: null } as unknown as GlobalSettingsType;
      const result = flatten(settings);
      expect(result.provider).toBe(DEFAULTS.provider);
      expect(result.model).toBe(DEFAULTS.model);
      expect(result.temperature).toBe(DEFAULTS.temperature);
    });

    it('handles null nested display object with defaults', () => {
      const settings = { ...fullSettings, display: null } as unknown as GlobalSettingsType;
      const result = flatten(settings);
      expect(result.theme).toBe(DEFAULTS.theme);
      expect(result.default_view).toBe(DEFAULTS.default_view);
      expect(result.sidebar_collapsed).toBe(DEFAULTS.sidebar_collapsed);
    });

    it('handles null nested workflow object with defaults', () => {
      const settings = { ...fullSettings, workflow: null } as unknown as GlobalSettingsType;
      const result = flatten(settings);
      expect(result.default_repository).toBe('');
      expect(result.default_assignee).toBe(DEFAULTS.default_assignee);
      expect(result.copilot_polling_interval).toBe(DEFAULTS.copilot_polling_interval);
    });

    it('handles null nested notifications object with defaults', () => {
      const settings = {
        ...fullSettings,
        notifications: null,
      } as unknown as GlobalSettingsType;
      const result = flatten(settings);
      expect(result.task_status_change).toBe(DEFAULTS.task_status_change);
      expect(result.agent_completion).toBe(DEFAULTS.agent_completion);
    });

    it('handles null allowed_models array', () => {
      const settings = {
        ...fullSettings,
        allowed_models: null,
      } as unknown as GlobalSettingsType;
      const result = flatten(settings);
      expect(result.allowed_models).toBe('');
    });

    it('handles null default_repository as empty string', () => {
      const settings = {
        ...fullSettings,
        workflow: { ...fullSettings.workflow, default_repository: null },
      };
      const result = flatten(settings);
      expect(result.default_repository).toBe('');
    });
  });

  describe('toUpdate', () => {
    it('converts form state to update payload with correct nesting', () => {
      const formState = flatten(fullSettings);
      const result = toUpdate(formState);
      expect(result).toEqual({
        ai: { provider: 'copilot', model: 'gpt-4o', temperature: 0.7 },
        display: { theme: 'dark', default_view: 'board', sidebar_collapsed: true },
        workflow: {
          default_repository: 'owner/repo',
          default_assignee: 'octocat',
          copilot_polling_interval: 120,
        },
        notifications: {
          task_status_change: false,
          agent_completion: true,
          new_recommendation: false,
          chat_mention: true,
        },
        allowed_models: ['gpt-4o', 'gpt-3.5'],
      });
    });

    it('trims whitespace from allowed_models entries', () => {
      const formState = { ...DEFAULTS, allowed_models: '  gpt-4o ,  gpt-3.5  ,  claude  ' };
      const result = toUpdate(formState);
      expect(result.allowed_models).toEqual(['gpt-4o', 'gpt-3.5', 'claude']);
    });

    it('filters empty entries from allowed_models', () => {
      const formState = { ...DEFAULTS, allowed_models: 'gpt-4o,,, ,gpt-3.5,' };
      const result = toUpdate(formState);
      expect(result.allowed_models).toEqual(['gpt-4o', 'gpt-3.5']);
    });

    it('returns empty array for empty allowed_models string', () => {
      const formState = { ...DEFAULTS, allowed_models: '' };
      const result = toUpdate(formState);
      expect(result.allowed_models).toEqual([]);
    });

    it('converts empty default_repository to null', () => {
      const formState = { ...DEFAULTS, default_repository: '' };
      const result = toUpdate(formState);
      expect(result.workflow.default_repository).toBeNull();
    });

    it('preserves non-empty default_repository', () => {
      const formState = { ...DEFAULTS, default_repository: 'my-org/my-repo' };
      const result = toUpdate(formState);
      expect(result.workflow.default_repository).toBe('my-org/my-repo');
    });
  });
});
