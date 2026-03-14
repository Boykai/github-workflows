/**
 * useUnsavedChanges — generic hook for unsaved-changes navigation guards.
 *
 * Registers a `beforeunload` event listener when dirty and activates
 * `useBlocker` from react-router-dom for SPA navigation blocking.
 */

import { useEffect } from 'react';
import { useBlocker } from 'react-router-dom';

interface UseUnsavedChangesOptions {
  isDirty: boolean;
  message?: string;
}

export function useUnsavedChanges({
  isDirty,
  message = 'You have unsaved changes — are you sure you want to leave?',
}: UseUnsavedChangesOptions) {
  // Browser-level guard (tab close, reload, external navigation)
  useEffect(() => {
    if (!isDirty) return;

    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      // Modern browsers ignore custom messages but still show a prompt
      e.returnValue = message;
      return message;
    };

    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [isDirty, message]);

  // SPA-level guard (react-router navigation)
  const blocker = useBlocker(isDirty);

  return { blocker, isBlocked: blocker.state === 'blocked' };
}
