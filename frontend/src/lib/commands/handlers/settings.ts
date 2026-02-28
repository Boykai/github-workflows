/**
 * Handlers for settings commands (#theme, #language, #notifications, #view).
 */

import type { CommandResult, CommandContext } from '../types';

// ── #theme ──────────────────────────────────────────────────────────────────

const VALID_THEMES = ['light', 'dark', 'system'] as const;

export function themeHandler(args: string, context: CommandContext): CommandResult {
  const value = args.trim().toLowerCase();

  if (!value) {
    return {
      success: false,
      message: 'Missing value for #theme. Usage: #theme <light|dark|system>',
      clearInput: false,
    };
  }

  if (!VALID_THEMES.includes(value as (typeof VALID_THEMES)[number])) {
    return {
      success: false,
      message: `Invalid value '${args.trim()}' for theme. Valid options: ${VALID_THEMES.join(', ')}`,
      clearInput: false,
    };
  }

  const oldTheme = context.currentTheme;
  context.setTheme(value);

  return {
    success: true,
    message: `✓ Theme changed from ${oldTheme} to ${value}`,
    clearInput: true,
  };
}

// ── #language ───────────────────────────────────────────────────────────────

const VALID_LANGUAGES = ['en', 'es', 'fr', 'de', 'ja', 'zh'] as const;
const LANGUAGE_LABELS: Record<string, string> = {
  en: 'English',
  es: 'Spanish',
  fr: 'French',
  de: 'German',
  ja: 'Japanese',
  zh: 'Chinese',
};

export function languageHandler(args: string, context: CommandContext): CommandResult {
  const value = args.trim().toLowerCase();

  if (!value) {
    return {
      success: false,
      message: 'Missing value for #language. Usage: #language <en|es|fr|de|ja|zh>',
      clearInput: false,
    };
  }

  if (!VALID_LANGUAGES.includes(value as (typeof VALID_LANGUAGES)[number])) {
    return {
      success: false,
      message: `Invalid value '${args.trim()}' for language. Valid options: ${VALID_LANGUAGES.join(', ')}`,
      clearInput: false,
    };
  }

  const label = LANGUAGE_LABELS[value] ?? value;
  context.updateSettings({ display: { theme: value as 'light' | 'dark' } });

  return {
    success: true,
    message: `✓ Language changed to ${label} (${value})`,
    clearInput: true,
  };
}

// ── #notifications ──────────────────────────────────────────────────────────

const VALID_NOTIFICATION_VALUES = ['on', 'off'] as const;

export function notificationsHandler(args: string, context: CommandContext): CommandResult {
  const value = args.trim().toLowerCase();

  if (!value) {
    return {
      success: false,
      message: 'Missing value for #notifications. Usage: #notifications <on|off>',
      clearInput: false,
    };
  }

  if (!VALID_NOTIFICATION_VALUES.includes(value as (typeof VALID_NOTIFICATION_VALUES)[number])) {
    return {
      success: false,
      message: `Invalid value '${args.trim()}' for notifications. Valid options: on, off`,
      clearInput: false,
    };
  }

  const enabled = value === 'on';
  const oldValue = context.currentSettings?.notifications?.task_status_change ? 'on' : 'off';
  context.updateSettings({
    notifications: {
      task_status_change: enabled,
      agent_completion: enabled,
      new_recommendation: enabled,
      chat_mention: enabled,
    },
  });

  return {
    success: true,
    message: `✓ Notifications changed from ${oldValue} to ${value}`,
    clearInput: true,
  };
}

// ── #view ───────────────────────────────────────────────────────────────────

const VALID_VIEWS = ['chat', 'board', 'settings'] as const;

export function viewHandler(args: string, context: CommandContext): CommandResult {
  const value = args.trim().toLowerCase();

  if (!value) {
    return {
      success: false,
      message: 'Missing value for #view. Usage: #view <chat|board|settings>',
      clearInput: false,
    };
  }

  if (!VALID_VIEWS.includes(value as (typeof VALID_VIEWS)[number])) {
    return {
      success: false,
      message: `Invalid value '${args.trim()}' for view. Valid options: ${VALID_VIEWS.join(', ')}`,
      clearInput: false,
    };
  }

  const oldView = context.currentSettings?.display?.default_view ?? 'chat';
  context.updateSettings({ display: { default_view: value as 'chat' | 'board' | 'settings' } });

  return {
    success: true,
    message: `✓ Default view changed from ${oldView} to ${value}`,
    clearInput: true,
  };
}
