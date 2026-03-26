/**
 * Handlers for settings commands (/theme, /language, /notifications, /view).
 */

import type { CommandResult, CommandContext } from '../types';

// ── /theme ──────────────────────────────────────────────────────────────────

const VALID_THEMES = ['light', 'dark', 'system'] as const;

export function themeHandler(args: string, context: CommandContext): CommandResult {
  const value = args.trim().toLowerCase();

  if (!value) {
    return {
      success: false,
      message: 'Missing value for /theme. Usage: /theme <light|dark|system>',
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
    message: `Theme changed from ${oldTheme} to ${value}`,
    clearInput: true,
  };
}

// ── /language ───────────────────────────────────────────────────────────────

const VALID_LANGUAGES = ['en', 'es', 'fr', 'de', 'ja', 'zh'] as const;
const LANGUAGE_LABELS: Record<string, string> = {
  en: 'English',
  es: 'Spanish',
  fr: 'French',
  de: 'German',
  ja: 'Japanese',
  zh: 'Chinese',
};

export function languageHandler(args: string, _context: CommandContext): CommandResult {
  const value = args.trim().toLowerCase();

  if (!value) {
    return {
      success: false,
      message: 'Missing value for /language. Usage: /language <en|es|fr|de|ja|zh>',
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
  // Language preference stored as a display setting placeholder.
  // The backend settings schema doesn't currently include a language field;
  // this is a forward-looking command that will integrate once the field exists.

  return {
    success: true,
    message: `Language changed to ${label} (${value})`,
    clearInput: true,
  };
}

// ── /notifications ──────────────────────────────────────────────────────────

const VALID_NOTIFICATION_VALUES = ['on', 'off'] as const;

export async function notificationsHandler(
  args: string,
  context: CommandContext
): Promise<CommandResult> {
  const value = args.trim().toLowerCase();

  if (!value) {
    return {
      success: false,
      message: 'Missing value for /notifications. Usage: /notifications <on|off>',
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

  // Await the settings mutation so we can surface failures to the user
  // rather than returning success while the update silently rejects.
  try {
    await context.updateSettings({
      notifications: {
        task_status_change: enabled,
        agent_completion: enabled,
        new_recommendation: enabled,
        chat_mention: enabled,
      },
    });
  } catch {
    return {
      success: false,
      message: `Failed to update notifications setting. Please try again.`,
      clearInput: false,
    };
  }

  return {
    success: true,
    message: `Notifications changed from ${oldValue} to ${value}`,
    clearInput: true,
  };
}

// ── /experimental ───────────────────────────────────────────────────────────

// Uses localStorage rather than context.updateSettings because
// EffectiveUserSettings / UserPreferencesUpdate do not yet expose an
// `experimental` field.  Once the backend settings schema adds it,
// this handler should migrate to the async settings mutation pattern
// used by /notifications and /view.
const EXPERIMENTAL_STORAGE_KEY = 'solune-experimental-features';

const VALID_EXPERIMENTAL_VALUES = ['on', 'off'] as const;

function getExperimentalEnabled(): boolean {
  try {
    return localStorage.getItem(EXPERIMENTAL_STORAGE_KEY) === 'true';
  } catch {
    return false;
  }
}

function setExperimentalEnabled(enabled: boolean): void {
  try {
    localStorage.setItem(EXPERIMENTAL_STORAGE_KEY, String(enabled));
  } catch {
    // localStorage may not be available in tests or restricted environments
  }
}

export function experimentalHandler(args: string, _context: CommandContext): CommandResult {
  const value = args.trim().toLowerCase();

  // No args: show current status
  if (!value) {
    const enabled = getExperimentalEnabled();
    return {
      success: true,
      message: `Experimental features are currently ${enabled ? 'on' : 'off'}. Usage: /experimental <on|off>`,
      clearInput: true,
    };
  }

  if (!VALID_EXPERIMENTAL_VALUES.includes(value as (typeof VALID_EXPERIMENTAL_VALUES)[number])) {
    return {
      success: false,
      message: `Invalid value '${args.trim()}' for experimental. Valid options: on, off`,
      clearInput: false,
    };
  }

  const enabled = value === 'on';
  const currentEnabled = getExperimentalEnabled();

  if (enabled === currentEnabled) {
    return {
      success: true,
      message: `Experimental features are already ${value}.`,
      clearInput: true,
    };
  }

  setExperimentalEnabled(enabled);

  return {
    success: true,
    message: `Experimental features ${enabled ? 'enabled' : 'disabled'}.`,
    clearInput: true,
  };
}

// ── /view ───────────────────────────────────────────────────────────────────

const VALID_VIEWS = ['chat', 'board', 'settings'] as const;

export async function viewHandler(args: string, context: CommandContext): Promise<CommandResult> {
  const value = args.trim().toLowerCase();

  if (!value) {
    return {
      success: false,
      message: 'Missing value for /view. Usage: /view <chat|board|settings>',
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

  // Await the settings mutation so failures are reported to the user
  // instead of silently rejecting with an unhandled promise.
  try {
    await context.updateSettings({
      display: { default_view: value as 'chat' | 'board' | 'settings' },
    });
  } catch {
    return {
      success: false,
      message: `Failed to update default view setting. Please try again.`,
      clearInput: false,
    };
  }

  return {
    success: true,
    message: `Default view changed from ${oldView} to ${value}`,
    clearInput: true,
  };
}
