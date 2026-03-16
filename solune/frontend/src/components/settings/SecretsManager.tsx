/**
 * Secrets Manager component.
 *
 * Manages GitHub environment secrets for MCP API keys. Provides a UI to
 * list, set, update, and delete secrets stored in a GitHub repository
 * environment (defaults to "copilot").
 */

import { useState, useCallback } from 'react';
import { SettingsSection } from './SettingsSection';
import { useSecrets, useSetSecret, useDeleteSecret } from '@/hooks/useSecrets';
import type { Project } from '@/types';

// ── Known Secrets ──

const KNOWN_SECRETS: Array<{ key: string; label: string }> = [
  { key: 'COPILOT_MCP_CONTEXT7_API_KEY', label: 'Context7 API Key' },
];

const SECRET_NAME_RE = /^[A-Z][A-Z0-9_]*$/;
const SECRET_NAME_MAX = 255;
const SECRET_VALUE_MAX = 65_536;
const DEFAULT_ENVIRONMENT = 'copilot';

// ── Component ──

interface SecretsManagerProps {
  projects?: Project[];
}

export function SecretsManager({ projects = [] }: SecretsManagerProps) {
  // Repository selection
  const [selectedRepo, setSelectedRepo] = useState('');
  const owner = selectedRepo ? selectedRepo.split('/')[0] : undefined;
  const repo = selectedRepo ? selectedRepo.split('/')[1] : undefined;

  // Environment
  const [environment] = useState(DEFAULT_ENVIRONMENT);

  // Secret CRUD hooks
  const { data: secretsData, isLoading: secretsLoading } = useSecrets(owner, repo, environment);
  const setSecretMutation = useSetSecret();
  const deleteSecretMutation = useDeleteSecret();

  // Editing state
  const [editingSecret, setEditingSecret] = useState<string | null>(null);
  const [secretValue, setSecretValue] = useState('');
  const [showValue, setShowValue] = useState(false);

  // Custom secret form
  const [customName, setCustomName] = useState('');
  const [customValue, setCustomValue] = useState('');
  const [customNameError, setCustomNameError] = useState('');

  // Build a set of existing secret names for quick lookup
  const existingSecrets = new Set(secretsData?.secrets?.map((s) => s.name) ?? []);

  const handleSetSecret = useCallback(
    async (name: string, value: string) => {
      if (!owner || !repo) return;
      await setSecretMutation.mutateAsync({
        owner,
        repo,
        env: environment,
        name,
        value,
      });
      setEditingSecret(null);
      setSecretValue('');
      setShowValue(false);
    },
    [owner, repo, environment, setSecretMutation]
  );

  const handleDeleteSecret = useCallback(
    async (name: string) => {
      if (!owner || !repo) return;
      await deleteSecretMutation.mutateAsync({
        owner,
        repo,
        env: environment,
        name,
      });
    },
    [owner, repo, environment, deleteSecretMutation]
  );

  const validateCustomName = (name: string): string => {
    if (!name) return 'Secret name is required';
    if (name.length > SECRET_NAME_MAX) return `Name must be at most ${SECRET_NAME_MAX} characters`;
    if (!SECRET_NAME_RE.test(name)) return 'Must be uppercase letters, digits, and underscores (e.g. MY_SECRET_KEY)';
    return '';
  };

  const handleAddCustomSecret = async () => {
    const error = validateCustomName(customName);
    if (error) {
      setCustomNameError(error);
      return;
    }
    if (!customValue) {
      setCustomNameError('Secret value is required');
      return;
    }
    if (customValue.length > SECRET_VALUE_MAX) {
      setCustomNameError('Value must be at most 64KB');
      return;
    }
    setCustomNameError('');
    await handleSetSecret(customName, customValue);
    setCustomName('');
    setCustomValue('');
  };

  // Build unique repo list from projects
  const repoOptions = Array.from(
    new Map(
      projects
        .filter((p) => p.owner_login && p.name)
        .map((p) => [`${p.owner_login}/${p.name}`, p])
    ).keys()
  );

  // No repositories state
  if (projects.length === 0) {
    return (
      <SettingsSection title="Environment Secrets" description="Manage MCP API keys stored as GitHub environment secrets." hideSave>
        <p className="text-sm text-muted-foreground">
          No repositories available. Please add a project to manage secrets.
        </p>
      </SettingsSection>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      {/* Repository Selector */}
      <SettingsSection title="Environment Secrets" description="Manage MCP API keys stored as GitHub environment secrets." hideSave>
        <div className="flex flex-col gap-2">
          <label htmlFor="secrets-repo" className="text-sm font-medium text-foreground">
            Repository
          </label>
          <select
            id="secrets-repo"
            className="celestial-focus flex h-9 w-full rounded-md border border-input bg-background text-foreground px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none"
            value={selectedRepo}
            onChange={(e) => setSelectedRepo(e.target.value)}
            aria-label="Repository"
          >
            <option value="">Select a repository…</option>
            {repoOptions.map((repoKey) => (
              <option key={repoKey} value={repoKey}>
                {repoKey}
              </option>
            ))}
          </select>
          <p className="text-xs text-muted-foreground">
            Environment: <code className="text-primary">{environment}</code>
          </p>
        </div>
      </SettingsSection>

      {/* Known Secrets */}
      {selectedRepo && (
        <SettingsSection
          title="Known Secrets"
          description="Predefined MCP API keys required by presets."
          hideSave
        >
          {secretsLoading ? (
            <p className="text-sm text-muted-foreground">Loading secrets…</p>
          ) : (
            <div className="flex flex-col gap-4">
              {KNOWN_SECRETS.map(({ key, label }) => {
                const isSet = existingSecrets.has(key);
                const isEditing = editingSecret === key;
                return (
                  <div key={key} className="flex flex-col gap-2 rounded-lg border border-border/60 p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-foreground">{label}</p>
                        <code className="text-xs text-muted-foreground">{key}</code>
                      </div>
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          isSet
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                        }`}
                      >
                        {isSet ? '✓ Set' : 'Not Set'}
                      </span>
                    </div>
                    {isEditing ? (
                      <div className="flex flex-col gap-2">
                        <div className="relative">
                          <input
                            type={showValue ? 'text' : 'password'}
                            className="celestial-focus flex h-9 w-full rounded-md border border-input bg-background text-foreground px-3 py-1 pr-16 text-sm shadow-sm transition-colors focus-visible:outline-none"
                            value={secretValue}
                            onChange={(e) => setSecretValue(e.target.value)}
                            placeholder="Enter secret value"
                            autoComplete="off"
                            aria-label={`Secret value for ${label}`}
                          />
                          <button
                            type="button"
                            className="celestial-focus absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground hover:text-foreground focus-visible:outline-none"
                            onClick={() => setShowValue(!showValue)}
                            aria-label={showValue ? 'Hide value' : 'Show value'}
                          >
                            {showValue ? 'Hide' : 'Show'}
                          </button>
                        </div>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            className="celestial-focus inline-flex items-center rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline-none disabled:opacity-50"
                            onClick={() => handleSetSecret(key, secretValue)}
                            disabled={!secretValue || setSecretMutation.isPending}
                          >
                            {setSecretMutation.isPending ? 'Saving…' : 'Save'}
                          </button>
                          <button
                            type="button"
                            className="celestial-focus inline-flex items-center rounded-md border border-input px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted focus-visible:outline-none"
                            onClick={() => {
                              setEditingSecret(null);
                              setSecretValue('');
                              setShowValue(false);
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <button
                          type="button"
                          className="celestial-focus inline-flex items-center rounded-md border border-input px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted focus-visible:outline-none"
                          onClick={() => {
                            setEditingSecret(key);
                            setSecretValue('');
                            setShowValue(false);
                          }}
                        >
                          {isSet ? 'Update' : 'Set'}
                        </button>
                        {isSet && (
                          <button
                            type="button"
                            className="celestial-focus inline-flex items-center rounded-md border border-destructive/50 px-3 py-1.5 text-xs font-medium text-destructive hover:bg-destructive/10 focus-visible:outline-none disabled:opacity-50"
                            onClick={() => handleDeleteSecret(key)}
                            disabled={deleteSecretMutation.isPending}
                          >
                            {deleteSecretMutation.isPending ? 'Removing…' : 'Remove'}
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </SettingsSection>
      )}

      {/* Custom Secrets */}
      {selectedRepo && (
        <SettingsSection
          title="Custom Secrets"
          description="Add custom environment secrets for MCP integrations."
          hideSave
        >
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label htmlFor="custom-secret-name" className="text-sm font-medium text-foreground">
                Secret Name
              </label>
              <input
                id="custom-secret-name"
                type="text"
                className="celestial-focus flex h-9 w-full rounded-md border border-input bg-background text-foreground px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none"
                value={customName}
                onChange={(e) => {
                  setCustomName(e.target.value.toUpperCase());
                  setCustomNameError('');
                }}
                placeholder="COPILOT_MCP_MY_API_KEY"
                autoComplete="off"
                aria-label="Custom secret name"
              />
              {customName && !customName.startsWith('COPILOT_MCP_') && (
                <p className="text-xs text-yellow-600 dark:text-yellow-400">
                  ⚠ GitHub Copilot only exposes secrets with the <code>COPILOT_MCP_</code> prefix to MCP servers.
                </p>
              )}
              {customNameError && (
                <p className="text-xs text-destructive">{customNameError}</p>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <label htmlFor="custom-secret-value" className="text-sm font-medium text-foreground">
                Secret Value
              </label>
              <input
                id="custom-secret-value"
                type="password"
                className="celestial-focus flex h-9 w-full rounded-md border border-input bg-background text-foreground px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none"
                value={customValue}
                onChange={(e) => setCustomValue(e.target.value)}
                placeholder="Enter secret value"
                autoComplete="off"
                aria-label="Custom secret value"
              />
            </div>
            <button
              type="button"
              className="celestial-focus inline-flex w-fit items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline-none disabled:opacity-50"
              onClick={handleAddCustomSecret}
              disabled={!customName || !customValue || setSecretMutation.isPending}
            >
              {setSecretMutation.isPending ? 'Adding…' : 'Add Custom Secret'}
            </button>
          </div>
        </SettingsSection>
      )}
    </div>
  );
}
