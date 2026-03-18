/**
 * CreateAppDialog — Modal dialog for creating a new Solune application.
 * Extracted from AppsPage to keep the page under 250 lines.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, Sparkles } from 'lucide-react';
import { useCreateApp, useOwners, getErrorMessage } from '@/hooks/useApps';
import { isRateLimitApiError } from '@/utils/rateLimit';
import type { AppCreate, RepoType } from '@/types/apps';

const REPO_TYPE_OPTIONS: { value: RepoType; label: string }[] = [
  { value: 'same-repo', label: 'Same Repo' },
  { value: 'new-repo', label: 'New Repository' },
  { value: 'external-repo', label: 'External Repo' },
];

/** Derive a kebab-case slug from a display name. */
function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-{2,}/g, '-')
    .replace(/^-|-$/g, '');
}

interface CreateAppDialogProps {
  /** Called when the dialog closes (cancel or successful create). */
  onClose: () => void;
  /** Called on successful creation with a feedback message and new app name. */
  onSuccess: (message: string, appName: string) => void;
  /** Called on creation error with a feedback message. */
  onError: (message: string) => void;
  /** Initial repo type to pre-select (optional). */
  initialRepoType?: RepoType;
  /** Ref to the element that triggered opening — receives focus on close. */
  triggerRef?: React.RefObject<HTMLButtonElement | null>;
}

export function CreateAppDialog({
  onClose,
  onSuccess,
  onError,
  initialRepoType = 'same-repo',
  triggerRef,
}: CreateAppDialogProps) {
  const navigate = useNavigate();
  const createMutation = useCreateApp();
  const { data: owners } = useOwners();

  const [createError, setCreateError] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState('');
  const [aiEnhance, setAiEnhance] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [repoType, setRepoType] = useState<RepoType>(initialRepoType);
  const [repoOwner, setRepoOwner] = useState('');
  const [repoVisibility, setRepoVisibility] = useState<'public' | 'private'>('private');
  const [createProject, setCreateProject] = useState(true);
  const [azureClientId, setAzureClientId] = useState('');
  const [azureClientSecret, setAzureClientSecret] = useState('');

  const firstInputRef = useRef<HTMLInputElement>(null);

  // Set default owner when owners are loaded
  useEffect(() => {
    if (owners && owners.length > 0 && !repoOwner) {
      setRepoOwner(owners[0].login);
    }
  }, [owners, repoOwner]);

  // Focus first input on mount
  useEffect(() => {
    firstInputRef.current?.focus();
  }, []);

  // Escape key handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleClose();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleClose = useCallback(() => {
    createMutation.reset();
    onClose();
    requestAnimationFrame(() => triggerRef?.current?.focus());
  }, [createMutation, onClose, triggerRef]);

  const derivedName = useMemo(() => slugify(displayName.trim()), [displayName]);
  const derivedBranch = useMemo(
    () => (derivedName ? `app/${derivedName}` : ''),
    [derivedName],
  );

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setCreateError(null);

    const formData = new FormData(e.currentTarget);
    const trimmedDisplayName = displayName.trim();
    const description = String(formData.get('description') ?? '').trim();
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
      const trimmedAzureId = azureClientId.trim();
      const azureSecretPresent = azureClientSecret.trim().length > 0;
      if ((trimmedAzureId && !azureSecretPresent) || (!trimmedAzureId && azureSecretPresent)) {
        setCreateError('Azure Client ID and Client Secret must both be provided or both omitted.');
        return;
      }
      if (trimmedAzureId && azureSecretPresent) {
        payload.azure_client_id = trimmedAzureId;
        payload.azure_client_secret = azureClientSecret;
      }
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
      const branchOverride = String(formData.get('branch') ?? '').trim();
      payload.branch = branchOverride || derivedBranch;
      if (!payload.branch) {
        setCreateError('Target branch could not be derived. Please provide a display name.');
        return;
      }
    }

    createMutation.mutate(payload, {
      onSuccess: (createdApp) => {
        const lines: string[] = [];
        if (createdApp.repo_type === 'new-repo') {
          lines.push('✓ Repository created', '✓ Template files committed');
        } else if (createdApp.repo_type === 'external-repo') {
          lines.push('✓ External repository linked');
        } else {
          lines.push('✓ App created');
        }
        if (createdApp.parent_issue_url) {
          lines.push('✓ Pipeline started');
        }
        if (createdApp.warnings?.length) {
          for (const w of createdApp.warnings) {
            lines.push(`⚠ ${w}`);
          }
        }
        onClose();
        onSuccess(lines.join(' | '), createdApp.name);
        navigate(`/apps/${createdApp.name}`);
      },
      onError: (err) => {
        const msg = getErrorMessage(err, 'Could not create app. Please try again.');
        if (isRateLimitApiError(err)) {
          setCreateError('Rate limit reached. Please wait before trying again.');
        } else {
          setCreateError(msg);
        }
        onError(msg);
      },
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={handleClose}
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
              <span className="mb-1.5 block text-sm font-medium text-foreground/80">
                Repository Type
              </span>
              <div
                className="flex rounded-lg border border-border p-0.5"
                role="group"
                aria-label="Repository type"
              >
                {REPO_TYPE_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setRepoType(opt.value)}
                    aria-pressed={repoType === opt.value}
                    className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1 ${
                      repoType === opt.value
                        ? 'bg-primary text-primary-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Display Name */}
            <div>
              <label htmlFor="app-display-name" className="mb-1 block text-sm font-medium text-foreground/80">
                Display Name
              </label>
              <input
                ref={firstInputRef}
                id="app-display-name"
                name="display_name"
                type="text"
                required
                maxLength={128}
                placeholder="My Awesome App"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
              {derivedName && repoType !== 'new-repo' && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Name: <span className="font-mono">{derivedName}</span> · Branch: <span className="font-mono">{derivedBranch}</span>
                </p>
              )}
              {derivedName && repoType === 'new-repo' && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Repo name: <span className="font-mono">{derivedName}</span>
                </p>
              )}
            </div>

            {/* Description */}
            <div>
              <label htmlFor="app-description" className="mb-1 block text-sm font-medium text-foreground/80">
                Description
              </label>
              <textarea
                id="app-description"
                name="description"
                rows={3}
                placeholder={
                  aiEnhance
                    ? 'Describe your app in a few words or sentences — AI will generate a short repo description and a rich project overview from your input.'
                    : 'A brief description of your app…'
                }
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
              {aiEnhance && (
                <p className="mt-1 text-xs text-muted-foreground">
                  AI will produce a short repo description (≤350 chars) and a detailed project description.
                </p>
              )}
            </div>

            {/* New Repository-specific fields */}
            {repoType === 'new-repo' && (
              <div className="space-y-3 rounded-lg border border-border bg-muted/30 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  New Repository Settings
                </p>
                <div>
                  <label htmlFor="repo-owner" className="mb-1 block text-xs font-medium text-muted-foreground">
                    Owner
                  </label>
                  <select
                    id="repo-owner"
                    value={repoOwner}
                    onChange={(e) => setRepoOwner(e.target.value)}
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  >
                    {(owners ?? []).map((o) => (
                      <option key={o.login} value={o.login}>
                        {o.login} ({o.type})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-muted-foreground">Visibility</span>
                  <div
                    className="flex rounded-md border border-border p-0.5"
                    role="group"
                    aria-label="Repository visibility"
                  >
                    <button
                      type="button"
                      onClick={() => setRepoVisibility('private')}
                      aria-pressed={repoVisibility === 'private'}
                      className={`rounded px-2.5 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary ${
                        repoVisibility === 'private'
                          ? 'bg-muted text-foreground'
                          : 'text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      Private
                    </button>
                    <button
                      type="button"
                      onClick={() => setRepoVisibility('public')}
                      aria-pressed={repoVisibility === 'public'}
                      className={`rounded px-2.5 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary ${
                        repoVisibility === 'public'
                          ? 'bg-muted text-foreground'
                          : 'text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      Public
                    </button>
                  </div>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={createProject}
                    onChange={(e) => setCreateProject(e.target.checked)}
                    className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                  />
                  <span className="text-xs text-muted-foreground">
                    Create linked GitHub Project (with Solune default columns)
                  </span>
                </label>
                <div>
                  <label htmlFor="azure-client-id" className="mb-1 block text-xs font-medium text-muted-foreground">
                    Azure Client ID (optional)
                  </label>
                  <input
                    id="azure-client-id"
                    type="text"
                    value={azureClientId}
                    onChange={(e) => setAzureClientId(e.target.value)}
                    placeholder="00000000-0000-0000-0000-000000000000"
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label htmlFor="azure-client-secret" className="mb-1 block text-xs font-medium text-muted-foreground">
                    Azure Client Secret (optional)
                  </label>
                  <input
                    id="azure-client-secret"
                    type="password"
                    value={azureClientSecret}
                    onChange={(e) => setAzureClientSecret(e.target.value)}
                    placeholder="Enter client secret"
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
              </div>
            )}

            {/* External Repo URL field */}
            {repoType === 'external-repo' && (
              <div>
                <label htmlFor="external-repo-url" className="mb-1 block text-sm font-medium text-foreground/80">
                  Repository URL
                </label>
                <input
                  id="external-repo-url"
                  name="external_repo_url"
                  type="url"
                  required
                  placeholder="https://github.com/owner/repo"
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            )}

            {/* Branch field for same-repo and external-repo */}
            {(repoType === 'same-repo' || repoType === 'external-repo') && (
              <div>
                <label htmlFor="app-branch" className="mb-1 block text-sm font-medium text-foreground/80">
                  Target Branch
                </label>
                <input
                  id="app-branch"
                  name="branch"
                  type="text"
                  maxLength={256}
                  placeholder={derivedBranch || 'app/my-feature'}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  The branch where the app scaffold will be committed.
                </p>
              </div>
            )}

            {/* AI Enhance toggle */}
            <div className="flex items-center justify-between gap-3 rounded-md border border-border bg-muted/30 px-3 py-2">
              <div className="flex items-center gap-2">
                <Sparkles aria-hidden="true" className="h-4 w-4 text-primary" />
                <div>
                  <p className="text-sm font-medium text-foreground">AI Enhance</p>
                  <p className="text-xs text-muted-foreground">
                    {aiEnhance
                      ? 'AI generates a rich description and scaffold content'
                      : 'Your exact input is used as-is'}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setAiEnhance(!aiEnhance)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${aiEnhance ? 'bg-primary' : 'bg-muted'}`}
                role="switch"
                aria-checked={aiEnhance}
                aria-label="AI Enhance"
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${aiEnhance ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
            </div>

            {/* Advanced (collapsible) */}
            <div>
              <button
                type="button"
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1 rounded"
                onClick={() => setShowAdvanced(!showAdvanced)}
                aria-expanded={showAdvanced}
                aria-controls="advanced-options"
              >
                <ChevronDown
                  aria-hidden="true"
                  className={`h-3.5 w-3.5 transition-transform ${showAdvanced ? 'rotate-180' : ''}`}
                />
                Advanced options
              </button>
              {showAdvanced && (
                <div id="advanced-options" className="mt-3 space-y-3">
                  <div>
                    <label htmlFor="app-name" className="mb-1 block text-xs font-medium text-muted-foreground">
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
                      className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                    <p className="mt-1 text-xs text-muted-foreground">
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
              className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              onClick={handleClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:opacity-50"
            >
              {createMutation.isPending
                ? (repoType === 'new-repo' ? 'Creating Repository…' : aiEnhance ? 'AI Enhancing…' : 'Creating…')
                : repoType === 'new-repo' ? 'Create Repository & App' : 'Create App'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
