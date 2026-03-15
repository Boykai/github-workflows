/**
 * AppsPage — Solune application management page.
 * Displays a card grid of managed applications with create dialog
 * and navigation to the detail view.
 */

import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { useApps, useCreateApp, useStartApp, useStopApp, useDeleteApp } from '@/hooks/useApps';
import { AppCard } from '@/components/apps/AppCard';
import { AppDetailView } from '@/components/apps/AppDetailView';
import type { AppCreate } from '@/types/apps';

export function AppsPage() {
  const { appName } = useParams<{ appName?: string }>();
  const navigate = useNavigate();
  const { data: apps, isLoading } = useApps();
  const createMutation = useCreateApp();
  const startMutation = useStartApp();
  const stopMutation = useStopApp();
  const deleteMutation = useDeleteApp();
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  // Detail view for a specific app
  if (appName) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-8">
        <AppDetailView appName={appName} onBack={() => navigate('/apps')} />
      </div>
    );
  }

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const name = (formData.get('name') as string).trim();
    const displayName = (formData.get('display_name') as string).trim();
    const description = (formData.get('description') as string).trim();
    const branch = (formData.get('branch') as string).trim();

    if (!name || !displayName || !branch) return;

    const payload: AppCreate = { name, display_name: displayName, description, branch };
    createMutation.mutate(payload, {
      onSuccess: () => setShowCreateDialog(false),
    });
  };

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Apps</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Create, manage, and preview your applications.
          </p>
        </div>
        <button
          type="button"
          className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
          onClick={() => setShowCreateDialog(true)}
        >
          <Plus className="h-4 w-4" /> New App
        </button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex min-h-[30vh] items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-zinc-300 border-t-emerald-500" />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && (!apps || apps.length === 0) && (
        <div className="flex min-h-[30vh] flex-col items-center justify-center rounded-xl border border-dashed border-zinc-300 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900/50">
          <p className="mb-2 text-sm text-zinc-500 dark:text-zinc-400">No applications yet.</p>
          <button
            type="button"
            className="text-sm font-medium text-emerald-600 hover:underline dark:text-emerald-400"
            onClick={() => setShowCreateDialog(true)}
          >
            Create your first app →
          </button>
        </div>
      )}

      {/* App grid */}
      {apps && apps.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {apps.map((app) => (
            <AppCard
              key={app.name}
              app={app}
              onSelect={(name) => navigate(`/apps/${name}`)}
              onStart={(name) => startMutation.mutate(name)}
              onStop={(name) => stopMutation.mutate(name)}
              onDelete={(name) => deleteMutation.mutate(name)}
            />
          ))}
        </div>
      )}

      {/* Create dialog */}
      {showCreateDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <form
            onSubmit={handleCreate}
            className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-zinc-900"
          >
            <h2 className="mb-4 text-lg font-bold text-zinc-900 dark:text-zinc-100">
              Create New App
            </h2>
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
                  className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                />
                <p className="mt-1 text-xs text-zinc-400">
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
                  className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
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
                  className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
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
                  className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                />
                <p className="mt-1 text-xs text-zinc-400">
                  The parent issue branch where the app scaffold will be committed.
                </p>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
                onClick={() => setShowCreateDialog(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
              >
                {createMutation.isPending ? 'Creating…' : 'Create App'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
