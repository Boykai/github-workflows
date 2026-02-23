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

import { useState, useEffect, useCallback, useRef } from 'react';

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

export function useSettingsForm<T extends object>(
  serverState: T,
): UseSettingsFormReturn<T> {
  const [localState, setLocalState] = useState<T>({ ...serverState });
  const serverRef = useRef(serverState);

  // Re-sync when server state changes (e.g. after a successful save
  // or when a different user is selected).
  useEffect(() => {
    // Only re-sync if the server state actually changed (shallow key compare).
    const prev = serverRef.current;
    const keys = Object.keys(serverState) as Array<keyof T & string>;
    const changed = keys.some(
      (k) => serverState[k] !== prev[k],
    );
    if (changed) {
      setLocalState({ ...serverState });
      serverRef.current = serverState;
    }
  }, [serverState]);

  const setField = useCallback(<K extends keyof T>(key: K, value: T[K]) => {
    setLocalState((prev) => ({ ...prev, [key]: value }));
  }, []);

  const reset = useCallback(() => {
    setLocalState({ ...serverState });
  }, [serverState]);

  // isDirty: shallow compare each key
  const keys = Object.keys(serverState) as Array<keyof T & string>;
  const isDirty = keys.some(
    (k) => localState[k] !== serverState[k],
  );

  return { localState, setField, isDirty, reset };
}
