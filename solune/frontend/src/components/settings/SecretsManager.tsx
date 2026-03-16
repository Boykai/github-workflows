/**
 * Secrets Manager component.
 *
 * Provides a CRUD UI for GitHub Actions environment secrets.
 * Supports:
 * - Displaying known (predefined) secrets with status indicators
 * - Adding / updating secrets via a secure password input
 * - Deleting secrets
 * - Custom secret form for arbitrary secret names
 * - Repository selector dropdown
 */

import { useState, useId } from 'react';
import { Eye, EyeOff, Trash2, Plus, RefreshCw } from 'lucide-react';
import { useSecrets, useSetSecret, useDeleteSecret } from '@/hooks/useSecrets';

/** Well-known secret names and their human-readable labels. */
const KNOWN_SECRETS: Array<{ name: string; label: string; description?: string }> = [
  { name: 'COPILOT_MCP_SENTRY_HOST', label: 'Sentry Host', description: 'Sentry instance URL' },
  {
    name: 'COPILOT_MCP_SENTRY_ACCESS_TOKEN',
    label: 'Sentry Access Token',
    description: 'Sentry API token',
  },
  { name: 'GITHUB_TOKEN', label: 'GitHub Token', description: 'GitHub Personal Access Token' },
];

interface SecretRowProps {
  name: string;
  label: string;
  description?: string;
  exists: boolean;
  owner: string;
  repo: string;
  env: string;
}

function SecretRow({ name, label, description, exists, owner, repo, env }: SecretRowProps) {
  const [value, setValue] = useState('');
  const [showValue, setShowValue] = useState(false);
  const [editing, setEditing] = useState(false);
  const inputId = useId();

  const { setSecret, isPending: isSetting } = useSetSecret();
  const { deleteSecret, isPending: isDeleting } = useDeleteSecret();

  const handleSave = async () => {
    if (!value.trim()) return;
    await setSecret({ owner, repo, env, name, value });
    setValue('');
    setEditing(false);
  };

  const handleDelete = async () => {
    await deleteSecret({ owner, repo, env, name });
  };

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-border/60 bg-background/30 p-4">
      <div className="flex items-center justify-between gap-2">
        <div className="flex flex-col gap-0.5 min-w-0">
          <span className="text-sm font-medium text-foreground">{label}</span>
          {description && (
            <span className="text-xs text-muted-foreground truncate">{description}</span>
          )}
          <code className="text-xs text-muted-foreground font-mono">{name}</code>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
              exists
                ? 'bg-emerald-100/80 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300'
                : 'bg-muted text-muted-foreground'
            }`}
            aria-label={exists ? 'Secret is set' : 'Secret is not set'}
          >
            {exists ? 'Set' : 'Not set'}
          </span>
          {exists && (
            <button
              type="button"
              className="celestial-focus inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-destructive focus-visible:outline-none transition-colors"
              onClick={handleDelete}
              disabled={isDeleting}
              aria-label={`Delete secret ${name}`}
              title={`Delete ${label}`}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
          <button
            type="button"
            className="celestial-focus inline-flex items-center gap-1 rounded-md border border-border bg-transparent px-2 py-1 text-xs font-medium text-foreground hover:bg-background/40 focus-visible:outline-none transition-colors"
            onClick={() => setEditing((e) => !e)}
            aria-expanded={editing}
            aria-controls={`secret-edit-${inputId}`}
          >
            {editing ? 'Cancel' : exists ? 'Update' : 'Set'}
          </button>
        </div>
      </div>

      {editing && (
        <div id={`secret-edit-${inputId}`} className="flex items-center gap-2">
          <div className="relative flex-1">
            <input
              id={inputId}
              type={showValue ? 'text' : 'password'}
              className="celestial-focus flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 pr-10 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={`Enter value for ${label}`}
              autoComplete="off"
              aria-label={`Value for ${label}`}
            />
            <button
              type="button"
              className="celestial-focus absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground focus-visible:outline-none"
              onClick={() => setShowValue((v) => !v)}
              tabIndex={0}
              aria-label={showValue ? 'Hide secret value' : 'Show secret value'}
            >
              {showValue ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          <button
            type="button"
            className="celestial-focus inline-flex h-9 items-center gap-1 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 focus-visible:outline-none disabled:opacity-50 transition-colors"
            onClick={handleSave}
            disabled={isSetting || !value.trim()}
          >
            {isSetting ? <RefreshCw className="h-3 w-3 animate-spin" /> : null}
            Save
          </button>
        </div>
      )}
    </div>
  );
}

const CUSTOM_SECRET_NAME_RE = /^[A-Z][A-Z0-9_]*$/;

interface SecretsManagerProps {
  owner: string;
  repo: string;
  env: string;
  /** List of owner/repo combos for the repo selector */
  repos?: Array<{ owner: string; repo: string }>;
  onRepoChange?: (owner: string, repo: string) => void;
}

export function SecretsManager({
  owner,
  repo,
  env,
  repos = [],
  onRepoChange,
}: SecretsManagerProps) {
  const { secrets, isLoading, refetch } = useSecrets(owner, repo, env);
  const { setSecret, isPending: isSettingCustom } = useSetSecret();

  const [customName, setCustomName] = useState('');
  const [customValue, setCustomValue] = useState('');
  const [showCustomValue, setShowCustomValue] = useState(false);
  const [customError, setCustomError] = useState('');

  const existingNames = new Set(secrets.map((s) => s.name));

  const handleAddCustom = async () => {
    const trimmedName = customName.trim().toUpperCase();
    if (!CUSTOM_SECRET_NAME_RE.test(trimmedName)) {
      setCustomError(
        'Secret name must start with an uppercase letter and contain only uppercase letters, digits, and underscores.'
      );
      return;
    }
    if (trimmedName.length > 255) {
      setCustomError('Secret name must be at most 255 characters.');
      return;
    }
    if (!customValue.trim()) {
      setCustomError('Secret value cannot be empty.');
      return;
    }
    setCustomError('');
    await setSecret({ owner, repo, env, name: trimmedName, value: customValue });
    setCustomName('');
    setCustomValue('');
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Repository selector */}
      {repos.length > 0 && (
        <div className="flex flex-col gap-2">
          <label htmlFor="secrets-repo-selector" className="text-sm font-medium text-foreground">
            Repository
          </label>
          <select
            id="secrets-repo-selector"
            className="celestial-focus flex h-9 w-full rounded-md border border-input bg-background text-foreground px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none"
            value={`${owner}/${repo}`}
            onChange={(e) => {
              const [o, r] = e.target.value.split('/');
              onRepoChange?.(o, r);
            }}
            aria-label="Select repository for secrets"
          >
            {repos.map(({ owner: o, repo: r }) => (
              <option key={`${o}/${r}`} value={`${o}/${r}`}>
                {o}/{r}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-foreground">Secrets</h3>
          <p className="text-sm text-muted-foreground">
            Manage GitHub Actions environment secrets for{' '}
            <code className="text-xs font-mono">
              {owner}/{repo}
            </code>{' '}
            ({env})
          </p>
        </div>
        <button
          type="button"
          className="celestial-focus inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-transparent px-2.5 text-sm text-muted-foreground hover:text-foreground focus-visible:outline-none transition-colors"
          onClick={() => refetch()}
          aria-label="Refresh secrets list"
          title="Refresh"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </div>

      {/* Loading */}
      {isLoading && (
        <p className="text-sm text-muted-foreground" role="status">
          Loading secrets…
        </p>
      )}

      {/* Known secrets */}
      {!isLoading && (
        <div className="flex flex-col gap-3">
          <h4 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Known Secrets
          </h4>
          {KNOWN_SECRETS.map((s) => (
            <SecretRow
              key={s.name}
              name={s.name}
              label={s.label}
              description={s.description}
              exists={existingNames.has(s.name)}
              owner={owner}
              repo={repo}
              env={env}
            />
          ))}
        </div>
      )}

      {/* Custom secrets */}
      {!isLoading && secrets.filter((s) => !KNOWN_SECRETS.some((k) => k.name === s.name)).length >
        0 && (
        <div className="flex flex-col gap-3">
          <h4 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Custom Secrets
          </h4>
          {secrets
            .filter((s) => !KNOWN_SECRETS.some((k) => k.name === s.name))
            .map((s) => (
              <SecretRow
                key={s.name}
                name={s.name}
                label={s.name}
                exists
                owner={owner}
                repo={repo}
                env={env}
              />
            ))}
        </div>
      )}

      {/* Add custom secret form */}
      {!isLoading && (
        <div className="flex flex-col gap-3 rounded-lg border border-dashed border-border/60 bg-background/20 p-4">
          <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            <Plus className="h-3.5 w-3.5" />
            Add Custom Secret
          </h4>
          <div className="flex flex-col gap-2">
            <input
              type="text"
              className="celestial-focus flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm font-mono transition-colors placeholder:text-muted-foreground focus-visible:outline-none"
              value={customName}
              onChange={(e) => {
                setCustomName(e.target.value.toUpperCase());
                setCustomError('');
              }}
              placeholder="SECRET_NAME"
              aria-label="Custom secret name"
              autoComplete="off"
            />
            <div className="relative">
              <input
                type={showCustomValue ? 'text' : 'password'}
                className="celestial-focus flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 pr-10 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none"
                value={customValue}
                onChange={(e) => setCustomValue(e.target.value)}
                placeholder="Secret value"
                aria-label="Custom secret value"
                autoComplete="off"
              />
              <button
                type="button"
                className="celestial-focus absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground focus-visible:outline-none"
                onClick={() => setShowCustomValue((v) => !v)}
                aria-label={showCustomValue ? 'Hide secret value' : 'Show secret value'}
              >
                {showCustomValue ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {customError && (
              <p className="text-xs text-destructive" role="alert">
                {customError}
              </p>
            )}
            <button
              type="button"
              className="celestial-focus inline-flex h-9 items-center justify-center gap-1.5 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 focus-visible:outline-none disabled:opacity-50 transition-colors"
              onClick={handleAddCustom}
              disabled={isSettingCustom || !customName.trim() || !customValue.trim()}
            >
              {isSettingCustom ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : null}
              Add Secret
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
