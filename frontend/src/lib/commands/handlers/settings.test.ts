/**
 * Unit tests for settings command handlers.
 */
import { describe, it, expect, vi } from 'vitest';
import { themeHandler, languageHandler, notificationsHandler, viewHandler } from './settings';
import { createCommandContext } from '@/test/factories';

describe('themeHandler', () => {
  it('valid value applies setting and returns confirmation', () => {
    const setTheme = vi.fn();
    const context = createCommandContext({ setTheme, currentTheme: 'light' });
    const result = themeHandler('dark', context);

    expect(result.success).toBe(true);
    expect(result.clearInput).toBe(true);
    expect(result.message).toContain('Theme changed from light to dark');
    expect(setTheme).toHaveBeenCalledWith('dark');
  });

  it('invalid value returns error listing valid options', () => {
    const context = createCommandContext();
    const result = themeHandler('rainbow', context);

    expect(result.success).toBe(false);
    expect(result.clearInput).toBe(false);
    expect(result.message).toContain('rainbow');
    expect(result.message).toContain('light');
    expect(result.message).toContain('dark');
    expect(result.message).toContain('system');
  });

  it('missing argument returns usage message', () => {
    const context = createCommandContext();
    const result = themeHandler('', context);

    expect(result.success).toBe(false);
    expect(result.clearInput).toBe(false);
    expect(result.message).toContain('Missing value');
    expect(result.message).toContain('#theme');
  });

  it('accepts all valid values: light, dark, system', () => {
    for (const value of ['light', 'dark', 'system']) {
      const setTheme = vi.fn();
      const context = createCommandContext({ setTheme });
      const result = themeHandler(value, context);
      expect(result.success).toBe(true);
      expect(setTheme).toHaveBeenCalledWith(value);
    }
  });

  it('setting to same value still succeeds', () => {
    const setTheme = vi.fn();
    const context = createCommandContext({ setTheme, currentTheme: 'dark' });
    const result = themeHandler('dark', context);

    expect(result.success).toBe(true);
    expect(result.message).toContain('dark to dark');
  });
});

describe('languageHandler', () => {
  it('valid value returns confirmation', () => {
    const updateSettings = vi.fn().mockResolvedValue({});
    const context = createCommandContext({ updateSettings });
    const result = languageHandler('fr', context);

    expect(result.success).toBe(true);
    expect(result.clearInput).toBe(true);
    expect(result.message).toContain('French');
    expect(result.message).toContain('fr');
    expect(updateSettings).toHaveBeenCalled();
  });

  it('invalid value returns error listing valid options', () => {
    const context = createCommandContext();
    const result = languageHandler('xx', context);

    expect(result.success).toBe(false);
    expect(result.message).toContain('xx');
    expect(result.message).toContain('en');
  });

  it('missing argument returns usage message', () => {
    const context = createCommandContext();
    const result = languageHandler('', context);

    expect(result.success).toBe(false);
    expect(result.message).toContain('Missing value');
  });

  it('accepts all valid languages', () => {
    for (const lang of ['en', 'es', 'fr', 'de', 'ja', 'zh']) {
      const updateSettings = vi.fn().mockResolvedValue({});
      const context = createCommandContext({ updateSettings });
      const result = languageHandler(lang, context);
      expect(result.success).toBe(true);
    }
  });
});

describe('notificationsHandler', () => {
  it('on value enables notifications', () => {
    const updateSettings = vi.fn().mockResolvedValue({});
    const context = createCommandContext({ updateSettings });
    const result = notificationsHandler('on', context);

    expect(result.success).toBe(true);
    expect(result.message).toContain('on');
    expect(updateSettings).toHaveBeenCalledWith(expect.objectContaining({
      notifications: expect.objectContaining({ task_status_change: true }),
    }));
  });

  it('off value disables notifications', () => {
    const updateSettings = vi.fn().mockResolvedValue({});
    const context = createCommandContext({ updateSettings });
    const result = notificationsHandler('off', context);

    expect(result.success).toBe(true);
    expect(result.message).toContain('off');
    expect(updateSettings).toHaveBeenCalledWith(expect.objectContaining({
      notifications: expect.objectContaining({ task_status_change: false }),
    }));
  });

  it('invalid value returns error', () => {
    const context = createCommandContext();
    const result = notificationsHandler('maybe', context);

    expect(result.success).toBe(false);
    expect(result.message).toContain('maybe');
    expect(result.message).toContain('on');
    expect(result.message).toContain('off');
  });

  it('missing argument returns usage message', () => {
    const context = createCommandContext();
    const result = notificationsHandler('', context);
    expect(result.success).toBe(false);
    expect(result.message).toContain('Missing value');
  });
});

describe('viewHandler', () => {
  it('valid value updates default view', () => {
    const updateSettings = vi.fn().mockResolvedValue({});
    const context = createCommandContext({ updateSettings });
    const result = viewHandler('chat', context);

    expect(result.success).toBe(true);
    expect(result.message).toContain('chat');
    expect(updateSettings).toHaveBeenCalledWith(expect.objectContaining({
      display: expect.objectContaining({ default_view: 'chat' }),
    }));
  });

  it('invalid value returns error', () => {
    const context = createCommandContext();
    const result = viewHandler('dashboard', context);

    expect(result.success).toBe(false);
    expect(result.message).toContain('dashboard');
    expect(result.message).toContain('chat');
    expect(result.message).toContain('board');
    expect(result.message).toContain('settings');
  });

  it('missing argument returns usage message', () => {
    const context = createCommandContext();
    const result = viewHandler('', context);
    expect(result.success).toBe(false);
    expect(result.message).toContain('Missing value');
  });

  it('accepts all valid views', () => {
    for (const view of ['chat', 'board', 'settings']) {
      const updateSettings = vi.fn().mockResolvedValue({});
      const context = createCommandContext({ updateSettings });
      const result = viewHandler(view, context);
      expect(result.success).toBe(true);
    }
  });
});

describe('concurrent/edge-case settings (US6)', () => {
  it('concurrent rapid settings updates apply correctly', () => {
    const setTheme = vi.fn();
    const context = createCommandContext({ setTheme });

    themeHandler('light', context);
    themeHandler('dark', context);
    themeHandler('system', context);

    expect(setTheme).toHaveBeenCalledTimes(3);
    expect(setTheme).toHaveBeenNthCalledWith(1, 'light');
    expect(setTheme).toHaveBeenNthCalledWith(2, 'dark');
    expect(setTheme).toHaveBeenNthCalledWith(3, 'system');
  });
});
