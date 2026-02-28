/**
 * useIOSLifecycle — persists and restores user session state across
 * iOS app lifecycle transitions (background / resume / termination).
 *
 * On web this hook is a no-op.
 *
 * @see specs/014-native-ios-support/contracts/capacitor-plugins.md
 */

import { useEffect, useCallback } from 'react';
import {
  isNativePlatform,
  getAppPlugin,
  getPreferencesPlugin,
} from '@/services/capacitor';

/* ------------------------------------------------------------------ */
/*  Data contract (matches contracts/capacitor-plugins.md)            */
/* ------------------------------------------------------------------ */

export interface IOSSessionState {
  activeSection: 'board' | 'settings' | 'chat';
  scrollPositions: Record<string, number>;
  formDraft: Record<string, unknown> | null;
  lastSavedAt: string;
  appVersion: string;
}

const SESSION_STATE_KEY = 'ios_session_state';
const APP_VERSION = '0.1.0';

/* ------------------------------------------------------------------ */
/*  Hook                                                              */
/* ------------------------------------------------------------------ */

export function useIOSLifecycle(
  activeSection: 'board' | 'settings' | 'chat',
  onRestoreSection?: (section: 'board' | 'settings' | 'chat') => void,
) {
  /** Persist the current navigation state to Preferences. */
  const saveState = useCallback(async () => {
    if (!isNativePlatform()) return;

    try {
      const Preferences = await getPreferencesPlugin();

      const state: IOSSessionState = {
        activeSection,
        scrollPositions: {
          board: document.querySelector('main')?.scrollTop ?? 0,
        },
        formDraft: null,
        lastSavedAt: new Date().toISOString(),
        appVersion: APP_VERSION,
      };

      await Preferences.set({
        key: SESSION_STATE_KEY,
        value: JSON.stringify(state),
      });
    } catch {
      // Graceful degradation — state save failure is non-critical
    }
  }, [activeSection]);

  /** Restore state from Preferences, discarding stale data. */
  const restoreState = useCallback(async (): Promise<IOSSessionState | null> => {
    if (!isNativePlatform()) return null;

    try {
      const Preferences = await getPreferencesPlugin();
      const { value } = await Preferences.get({ key: SESSION_STATE_KEY });
      if (!value) return null;

      const state: IOSSessionState = JSON.parse(value);

      // Discard saved state if app version has changed
      if (state.appVersion !== APP_VERSION) {
        await Preferences.remove({ key: SESSION_STATE_KEY });
        return null;
      }

      return state;
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    if (!isNativePlatform()) return;

    let cleanup: (() => void) | undefined;

    (async () => {
      try {
        const App = await getAppPlugin();

        const handle = await App.addListener('appStateChange', ({ isActive }) => {
          if (!isActive) {
            saveState();
          }
        });

        cleanup = () => {
          handle.remove();
        };

        // Attempt to restore state on first mount
        const saved = await restoreState();
        if (saved && onRestoreSection) {
          onRestoreSection(saved.activeSection);
        }
      } catch {
        // Plugin not available — running on web
      }
    })();

    return () => {
      cleanup?.();
    };
  }, [saveState, restoreState, onRestoreSection]);
}
