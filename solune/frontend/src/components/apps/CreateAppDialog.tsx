/**
 * CreateAppDialog — modal dialog for creating a new application.
 * Includes focus trapping, accessible labeling, and form validation.
 */

import { useEffect, useRef, useState } from 'react';
import { useCreateApp, friendlyErrorMessage } from '@/hooks/useApps';
import { cn } from '@/lib/utils';
import type { AppCreate } from '@/types/apps';

interface CreateAppDialogProps {
  onClose: () => void;
  onCreated: (appName: string) => void;
}

export function CreateAppDialog({ onClose, onCreated }: CreateAppDialogProps) {
  const createMutation = useCreateApp();
  const [createError, setCreateError] = useState<string | null>(null);
  const dialogRef = useRef<HTMLFormElement>(null);

  // Reset mutation state on mount
  useEffect(() => {
    createMutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Focus trap: cycle Tab within the dialog
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    const focusableSelector =
      'input:not([disabled]), textarea:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex="-1"])';

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key !== 'Tab') return;
      const focusable = Array.from(dialog!.querySelectorAll<HTMLElement>(focusableSelector));
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    dialog.addEventListener('keydown', handleKeyDown);
    const firstInput = dialog.querySelector<HTMLElement>('input, textarea');
    firstInput?.focus();
    return () => dialog.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setCreateError(null);

    const formData = new FormData(e.currentTarget);
    const name = (formData.get('name') as string).trim();
    const displayName = (formData.get('display_name') as string).trim();
    const description = (formData.get('description') as string).trim();
    const branch = (formData.get('branch') as string).trim();

    if (!name || !displayName || !branch) {
      setCreateError('Name, display name, and target branch are required.');
      return;
    }

    const payload: AppCreate = { name, display_name: displayName, description, branch };
    createMutation.mutate(payload, {
      onSuccess: (createdApp) => {
        onCreated(createdApp.name);
      },
      onError: (err) => {
        setCreateError(friendlyErrorMessage(err, 'Could not create app. Please try again.'));
      },
    });
  };

  return (
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onPointerDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      onKeyDown={(e) => {
        if (e.key === 'Escape') onClose();
      }}
    >
      <form
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-app-title"
        onSubmit={handleCreate}
        className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-zinc-900"
      >
        <h2
          id="create-app-title"
          className="mb-4 text-lg font-bold text-zinc-900 dark:text-zinc-100"
        >
          Create App
        </h2>
        {createError && (
          <div
            className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
            role="alert"
          >
            {createError}
          </div>
        )}
        <div className="space-y-4">
          <div>
            <label htmlFor="app-name" className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Name
            </label>
            <input
              id="app-name"
              name="name"
              type="text"
              required
              pattern="[a-z0-9][a-z0-9-]*[a-z0-9]"
              minLength={2}
              maxLength={64}
              placeholder="my-awesome-app"
              className={cn(
                'w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100',
                'focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500'
              )}
            />
            <p className="mt-1 text-xs text-zinc-400 dark:text-zinc-500">
              Lowercase letters, numbers, and hyphens only.
            </p>
          </div>
          <div>
            <label htmlFor="app-display-name" className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Display Name
            </label>
            <input
              id="app-display-name"
              name="display_name"
              type="text"
              required
              maxLength={128}
              placeholder="My Awesome App"
              className={cn(
                'w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100',
                'focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500'
              )}
            />
          </div>
          <div>
            <label htmlFor="app-description" className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Description
            </label>
            <textarea
              id="app-description"
              name="description"
              rows={2}
              placeholder="A brief description of your app…"
              className={cn(
                'w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100',
                'focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500'
              )}
            />
          </div>
          <div>
            <label htmlFor="app-branch" className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Target Branch
            </label>
            <input
              id="app-branch"
              name="branch"
              type="text"
              required
              maxLength={256}
              placeholder="parent-issue/my-feature"
              className={cn(
                'w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100',
                'focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500'
              )}
            />
            <p className="mt-1 text-xs text-zinc-400 dark:text-zinc-500">
              The parent issue branch where the app scaffold will be committed.
            </p>
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className={cn(
              'rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500'
            )}
          >
            {createMutation.isPending ? 'Creating…' : 'Create App'}
          </button>
        </div>
      </form>
    </div>
  );
}
