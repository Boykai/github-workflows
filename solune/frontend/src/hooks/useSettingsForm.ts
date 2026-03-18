/**
 * Generic settings-form hook.
 *
 * Clones `serverState` into local state on mount / when server changes,
 * exposes a per-field setter, an `isDirty` flag, and a `reset` function.
 *
 * Usage:
 * ```ts
 * const { localState, setField, isDirty, reset } = useSettingsForm(settings);
 * // setField('theme', 'dark');
 * // isDirty  → true
 * // reset()  → reverts to current server state
 * ```
 */

import { useState, useCallback } from 'react';

export interface UseSettingsFormReturn<T extends object> {
  /** Mutable local copy of the server state. */
  localState: T;
  /** Set a single field value. */
  setField: <K extends keyof T>(key: K, value: T[K]) => void;
  /** `true` when any field differs from `serverState`. */
  isDirty: boolean;
  /** Revert local state to `serverState`. */
  reset: () => void;
}

export function useSettingsForm<T extends object>(serverState: T): UseSettingsFormReturn<T> {
  const [localState, setLocalState] = useState<T>({ ...serverState });

  // Re-sync when server state changes (e.g. after a successful save
  // or when a different user is selected).
  const [prevServerState, setPrevServerState] = useState(serverState);
  const keys = Object.keys(serverState) as Array<keyof T & string>;
  const serverChanged = keys.some((k) => serverState[k] !== prevServerState[k]);
  if (serverChanged) {
    setPrevServerState(serverState);
    setLocalState({ ...serverState });
  }

  const setField = useCallback(<K extends keyof T>(key: K, value: T[K]) => {
    setLocalState((prev) => ({ ...prev, [key]: value }));
  }, []);

  const reset = useCallback(() => {
    setLocalState({ ...serverState });
  }, [serverState]);

  // isDirty: shallow compare each key
  const isDirty = keys.some((k) => localState[k] !== serverState[k]);

  return { localState, setField, isDirty, reset };
}
