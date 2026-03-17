/**
 * AppsPage — Solune application management page.
 * Displays a card grid of managed applications with create dialog
 * and navigation to the detail view.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ChevronDown, GitBranch, Plus, RefreshCw, Sparkles } from 'lucide-react';
import { useApps, useCreateApp, useOwners, useStartApp, useStopApp, useDeleteApp, getErrorMessage } from '@/hooks/useApps';
import { AppCard } from '@/components/apps/AppCard';
import { AppDetailView } from '@/components/apps/AppDetailView';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { useConfirmation } from '@/hooks/useConfirmation';
import { isRateLimitApiError } from '@/utils/rateLimit';
import type { AppCreate, RepoType } from '@/types/apps';

const REPO_TYPE_OPTIONS: { value: RepoType; label: string }[] = [
  { value: 'same-repo', label: 'Same Repo' },
  { value: 'new-repo', label: 'New Repository' },
  { value: 'external-repo', label: 'External Repo' },
];

export function AppsPage() {
  const { appName } = useParams<{ appName?: string }>();
  const navigate = useNavigate();
  const { data: apps, isLoading, error, refetch } = useApps();
  const createMutation = useCreateApp();
  const startMutation = useStartApp();
  const stopMutation = useStopApp();
  const deleteMutation = useDeleteApp();
  const { confirm } = useConfirmation();
  const { data: owners } = useOwners();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState('');
  const [aiEnhance, setAiEnhance] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [repoType, setRepoType] = useState<RepoType>('same-repo');
  const [repoOwner, setRepoOwner] = useState('');
  const [repoVisibility, setRepoVisibility] = useState<'public' | 'private'>('private');
  const [createProject, setCreateProject] = useState(true);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const createButtonRef = useRef<HTMLButtonElement>(null);
  const successTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const errorTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Set default owner when owners are loaded
  useEffect(() => {
    if (owners && owners.length > 0 && !repoOwner) {
      setRepoOwner(owners[0].login);
    }
  }, [owners, repoOwner]);

  useEffect(() => {
    return () => {
      clearTimeout(successTimerRef.current);
      clearTimeout(errorTimerRef.current);
    };
  }, []);

  const showSuccess = useCallback((message: string) => {
    setSuccessMessage(message);
    clearTimeout(successTimerRef.current);
    successTimerRef.current = setTimeout(() => setSuccessMessage(null), 3000);
  }, []);

  const showError = useCallback((message: string) => {
    setActionError(message);
    clearTimeout(errorTimerRef.current);
    errorTimerRef.current = setTimeout(() => setActionError(null), 5000);
  }, []);

  const openCreateDialog = (initialRepoType?: RepoType) => {
    createMutation.reset();
    setCreateError(null);
    setDisplayName('');
    setAiEnhance(true);
    setShowAdvanced(false);
    setRepoType(initialRepoType ?? 'same-repo');
    setRepoVisibility('private');
    setCreateProject(true);
    if (owners && owners.length > 0) {
      setRepoOwner(owners[0].login);
    }
    setShowCreateDialog(true);
  };

  const closeCreateDialog = useCallback(() => {
    createMutation.reset();
    setCreateError(null);
    setDisplayName('');
    setShowCreateDialog(false);
    createButtonRef.current?.focus();
  }, [createMutation]);

  /** Derive a kebab-case slug from a display name. */
  const slugify = (text: string): string =>
    text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/-{2,}/g, '-')
      .replace(/^-|-$/g, '');

  const derivedName = useMemo(() => slugify(displayName.trim()), [displayName]);
  const derivedBranch = useMemo(
    () => (derivedName ? `app/${derivedName}` : ''),
    [derivedName],
  );

  // Document-level Escape key handler for the create dialog
  useEffect(() => {
    if (!showCreateDialog) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeCreateDialog();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [showCreateDialog, closeCreateDialog]);

  const handleStart = useCallback(async (name: string) => {
    startMutation.mutate(name, {
      onSuccess: () => showSuccess(`App "${name}" started successfully.`),
      onError: (err) => showError(getErrorMessage(err, `Could not start app "${name}".`)),
    });
  }, [startMutation, showSuccess, showError]);

  const handleStop = useCallback(async (name: string) => {
    const confirmed = await confirm({
      title: 'Stop App',
      description: `Stop app "${name}"? The app will no longer be accessible until restarted.`,
      variant: 'warning',
      confirmLabel: 'Stop App',
    });
    if (confirmed) {
      stopMutation.mutate(name, {
        onSuccess: () => showSuccess(`App "${name}" stopped successfully.`),
        onError: (err) => showError(getErrorMessage(err, `Could not stop app "${name}".`)),
      });
    }
  }, [confirm, stopMutation, showSuccess, showError]);

  const handleDelete = useCallback(async (name: string) => {
    const confirmed = await confirm({
      title: 'Delete App',
      description: `Delete app "${name}"? This action cannot be undone.`,
      variant: 'danger',
      confirmLabel: 'Delete App',
    });
    if (confirmed) {
      deleteMutation.mutate(name, {
        onSuccess: () => showSuccess(`App "${name}" deleted successfully.`),
        onError: (err) => showError(getErrorMessage(err, `Could not delete app "${name}".`)),
      });
    }
  }, [confirm, deleteMutation, showSuccess, showError]);

  // Detail view for a specific app
  if (appName) {
    return (
      <ErrorBoundary>
        <div className="mx-auto max-w-5xl px-6 py-8">
          <AppDetailView appName={appName} onBack={() => navigate('/apps')} />
        </div>
      </ErrorBoundary>
    );
  }

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setCreateError(null);

    const formData = new FormData(e.currentTarget);
    const trimmedDisplayName = displayName.trim();
    const description = String(formData.get('description') ?? '').trim();
    // Use overrides from advanced section if provided, otherwise use derived values
    const nameOverride = String(formData.get('name') ?? '').trim();
    const name = nameOverride || derivedName;

    if (!name || !trimmedDisplayName) {
      setCreateError('Display name is required.');
      return;
    }

    const payload: AppCreate = {
      name,
      display_name: trimmedDisplayName,
      description,
      ai_enhance: aiEnhance,
      repo_type: repoType,
    };

    if (repoType === 'new-repo') {
      if (!repoOwner) {
        setCreateError('Repository owner is required for new repository.');
        return;
      }
      payload.repo_owner = repoOwner;
      payload.repo_visibility = repoVisibility;
      payload.create_project = createProject;
    } else if (repoType === 'external-repo') {
      const url = String(formData.get('external_repo_url') ?? '').trim();
      if (!url) {
        setCreateError('External repository URL is required.');
        return;
      }
      payload.external_repo_url = url;
      const branchOverride = String(formData.get('branch') ?? '').trim();
      payload.branch = branchOverride || derivedBranch;
      if (!payload.branch) {
        setCreateError('Target branch could not be derived.');
        return;
      }
    } else {
      // same-repo
      const branchOverride = String(formData.get('branch') ?? '').trim();
      payload.branch = branchOverride || derivedBranch;
      if (!payload.branch) {
        setCreateError('Target branch could not be derived. Please provide a display name.');
        return;
      }
    }

    createMutation.mutate(payload, {
      onSuccess: (createdApp) => {
        closeCreateDialog();
        showSuccess(`App "${createdApp.display_name}" created successfully.`);
        navigate(`/apps/${createdApp.name}`);
      },
      onError: (err) => {
        setCreateError(getErrorMessage(err, 'Could not create app. Please try again.'));
      },
    });
  };

  const isRateLimited = error ? isRateLimitApiError(error) : false;

  return (
    <ErrorBoundary>
      <div className="mx-auto max-w-5xl px-6 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Apps</h1>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              Create, manage, and preview your applications.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-300 px-3 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:border-zinc-600 dark:text-zinc-300 dark:hover:bg-zinc-800"
              onClick={() => openCreateDialog('new-repo')}
            >
              <GitBranch aria-hidden="true" className="h-4 w-4" /> New Repository
            </button>
            <button
              ref={createButtonRef}
              type="button"
              className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2"
              onClick={() => openCreateDialog()}
            >
              <Plus aria-hidden="true" className="h-4 w-4" /> Create App
            </button>
          </div>
        </div>

        {/* Success feedback */}
        {successMessage && (
          <div
            className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300"
            role="status"
          >
            {successMessage}
          </div>
        )}

        {/* Action error feedback */}
        {actionError && (
          <div
            className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-300"
            role="alert"
          >
            {actionError}
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="flex min-h-[30vh] items-center justify-center" aria-busy="true" aria-live="polite">
            <CelestialLoader size="md" label="Loading apps…" />
          </div>
        )}

        {/* Error state */}
        {!isLoading && error && (
          <div className="flex min-h-[30vh] flex-col items-center justify-center" aria-live="polite">
            <p className="mb-3 text-sm text-zinc-500 dark:text-zinc-400">
              {isRateLimited
                ? 'You have exceeded the API rate limit. Please wait a moment before trying again.'
                : 'Could not load applications. Please try again.'}
            </p>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
              onClick={() => refetch()}
            >
              <RefreshCw aria-hidden="true" className="h-3.5 w-3.5" /> Retry
            </button>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && (!apps || apps.length === 0) && (
          <div className="flex min-h-[30vh] flex-col items-center justify-center rounded-xl border border-dashed border-zinc-300 dark:border-zinc-700 dark:bg-zinc-900/50">
            <p className="mb-2 text-sm text-zinc-500 dark:text-zinc-400">No applications yet.</p>
            <button
              type="button"
              className="text-sm font-medium text-emerald-600 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:text-emerald-400"
              onClick={() => openCreateDialog()}
            >
              Create your first app →
            </button>
          </div>
        )}

        {/* App grid */}
        {!isLoading && !error && apps && apps.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {apps.map((app) => (
              <AppCard
                key={app.name}
                app={app}
                onSelect={(name) => navigate(`/apps/${name}`)}
                onStart={handleStart}
                onStop={handleStop}
                onDelete={handleDelete}
                isStartPending={startMutation.isPending}
                isStopPending={stopMutation.isPending}
                isDeletePending={deleteMutation.isPending}
              />
            ))}
          </div>
        )}

        {/* Create dialog */}
        {showCreateDialog && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
              className="absolute inset-0 bg-black/40 backdrop-blur-sm"
              onClick={closeCreateDialog}
              role="presentation"
              aria-hidden="true"
            />

            {/* Dialog */}
            <div
              role="dialog"
              aria-modal="true"
              aria-labelledby="create-app-dialog-title"
              className="relative z-10"
            >
              <form
                onSubmit={handleCreate}
                className="w-full max-w-md rounded-xl border border-border/80 bg-card p-6 shadow-xl max-h-[85vh] overflow-y-auto"
              >
                <h2 id="create-app-dialog-title" className="mb-4 text-lg font-bold text-foreground">
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
                  {/* Repo Type Selector */}
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                      Repository Type
                    </label>
                    <div className="flex rounded-lg border border-zinc-300 dark:border-zinc-700 p-0.5">
                      {REPO_TYPE_OPTIONS.map((opt) => (
                        <button
                          key={opt.value}
                          type="button"
                          onClick={() => setRepoType(opt.value)}
                          className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                            repoType === opt.value
                              ? 'bg-emerald-600 text-white shadow-sm'
                              : 'text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-200'
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Display Name */}
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
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                    />
                    {derivedName && repoType !== 'new-repo' && (
                      <p className="mt-1 text-xs text-zinc-400">
                        Name: <span className="font-mono">{derivedName}</span> · Branch: <span className="font-mono">{derivedBranch}</span>
                      </p>
                    )}
                    {derivedName && repoType === 'new-repo' && (
                      <p className="mt-1 text-xs text-zinc-400">
                        Repo name: <span className="font-mono">{derivedName}</span>
                      </p>
                    )}
                  </div>

                  {/* Description */}
                  <div>
                    <label htmlFor="app-description" className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                      Description
                    </label>
                    <textarea
                      id="app-description"
                      name="description"
                      rows={2}
                      placeholder="A brief description of your app…"
                      className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                    />
                  </div>

                  {/* New Repository-specific fields */}
                  {repoType === 'new-repo' && (
                    <div className="space-y-3 rounded-lg border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-700 dark:bg-zinc-800/50">
                      <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                        New Repository Settings
                      </p>
                      {/* Owner selector */}
                      <div>
                        <label htmlFor="repo-owner" className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">
                          Owner
                        </label>
                        <select
                          id="repo-owner"
                          value={repoOwner}
                          onChange={(e) => setRepoOwner(e.target.value)}
                          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                        >
                          {(owners ?? []).map((o) => (
                            <option key={o.login} value={o.login}>
                              {o.login} ({o.type})
                            </option>
                          ))}
                        </select>
                      </div>
                      {/* Visibility toggle */}
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-zinc-600 dark:text-zinc-400">
                          Visibility
                        </span>
                        <div className="flex rounded-md border border-zinc-300 dark:border-zinc-600 p-0.5">
                          <button
                            type="button"
                            onClick={() => setRepoVisibility('private')}
                            className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                              repoVisibility === 'private'
                                ? 'bg-zinc-700 text-white dark:bg-zinc-500'
                                : 'text-zinc-500 hover:text-zinc-700 dark:text-zinc-400'
                            }`}
                          >
                            Private
                          </button>
                          <button
                            type="button"
                            onClick={() => setRepoVisibility('public')}
                            className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                              repoVisibility === 'public'
                                ? 'bg-zinc-700 text-white dark:bg-zinc-500'
                                : 'text-zinc-500 hover:text-zinc-700 dark:text-zinc-400'
                            }`}
                          >
                            Public
                          </button>
                        </div>
                      </div>
                      {/* Create project checkbox */}
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={createProject}
                          onChange={(e) => setCreateProject(e.target.checked)}
                          className="h-4 w-4 rounded border-zinc-300 text-emerald-600 focus:ring-emerald-500"
                        />
                        <span className="text-xs text-zinc-600 dark:text-zinc-400">
                          Create linked GitHub Project (with Solune default columns)
                        </span>
                      </label>
                    </div>
                  )}

                  {/* External Repo URL field */}
                  {repoType === 'external-repo' && (
                    <div>
                      <label htmlFor="external-repo-url" className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                        Repository URL
                      </label>
                      <input
                        id="external-repo-url"
                        name="external_repo_url"
                        type="url"
                        required
                        placeholder="https://github.com/owner/repo"
                        className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                      />
                    </div>
                  )}

                  {/* Branch field for same-repo and external-repo */}
                  {(repoType === 'same-repo' || repoType === 'external-repo') && (
                    <div>
                      <label htmlFor="app-branch" className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                        Target Branch
                      </label>
                      <input
                        id="app-branch"
                        name="branch"
                        type="text"
                        maxLength={256}
                        placeholder={derivedBranch || 'app/my-feature'}
                        className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                      />
                      <p className="mt-1 text-xs text-zinc-400">
                        The branch where the app scaffold will be committed.
                      </p>
                    </div>
                  )}

                  {/* AI Enhance toggle */}
                  <div className="flex items-center justify-between gap-3 rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-800/50">
                    <div className="flex items-center gap-2">
                      <Sparkles aria-hidden="true" className="h-4 w-4 text-emerald-500" />
                      <div>
                        <p className="text-sm font-medium text-zinc-700 dark:text-zinc-200">AI Enhance</p>
                        <p className="text-xs text-zinc-400">
                          {aiEnhance
                            ? 'AI generates a rich description and scaffold content'
                            : 'Your exact input is used as-is'}
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setAiEnhance(!aiEnhance)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${aiEnhance ? 'bg-emerald-500' : 'bg-zinc-300 dark:bg-zinc-600'}`}
                      role="switch"
                      aria-checked={aiEnhance}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${aiEnhance ? 'translate-x-6' : 'translate-x-1'}`} />
                    </button>
                  </div>

                  {/* Advanced (collapsible) — for name override */}
                  <div>
                    <button
                      type="button"
                      className="flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"
                      onClick={() => setShowAdvanced(!showAdvanced)}
                    >
                      <ChevronDown
                        aria-hidden="true"
                        className={`h-3.5 w-3.5 transition-transform ${showAdvanced ? 'rotate-180' : ''}`}
                      />
                      Advanced options
                    </button>
                    {showAdvanced && (
                      <div className="mt-3 space-y-3">
                        <div>
                          <label htmlFor="app-name" className="mb-1 block text-xs font-medium text-zinc-500 dark:text-zinc-400">
                            Name override
                          </label>
                          <input
                            id="app-name"
                            name="name"
                            type="text"
                            pattern="[a-z0-9][a-z0-9-]*[a-z0-9]"
                            minLength={2}
                            maxLength={64}
                            placeholder={derivedName || 'my-awesome-app'}
                            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                          />
                          <p className="mt-1 text-xs text-zinc-400">
                            Lowercase letters, numbers, and hyphens only.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <div className="mt-6 flex justify-end gap-3">
                  <button
                    type="button"
                    className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-500 focus-visible:ring-offset-2 dark:text-zinc-400 dark:hover:bg-zinc-800"
                    onClick={closeCreateDialog}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createMutation.isPending}
                    className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 disabled:opacity-50"
                  >
                    {createMutation.isPending
                      ? (repoType === 'new-repo' ? 'Creating Repository…' : aiEnhance ? 'AI Enhancing…' : 'Creating…')
                      : repoType === 'new-repo' ? 'Create Repository & App' : 'Create App'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}
