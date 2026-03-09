/**
 * UploadMcpModal — modal dialog for uploading/pasting MCP configuration JSON.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import type { McpToolConfig, McpToolConfigCreate, McpToolConfigUpdate } from '@/types';

interface UploadMcpModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (data: McpToolConfigCreate) => Promise<unknown>;
  onUpdate: (toolId: string, data: McpToolConfigUpdate) => Promise<unknown>;
  isSubmitting: boolean;
  submitError: string | null;
  existingNames?: string[];
  editingTool?: McpToolConfig | null;
  initialDraft?: Partial<McpToolConfigCreate> | null;
}

const MAX_CONFIG_SIZE = 262144; // 256 KB

export function validateMcpJson(content: string): string | null {
  if (!content.trim()) return 'Configuration content is required';
  if (new Blob([content]).size > MAX_CONFIG_SIZE) return 'Configuration exceeds 256 KB limit';

  let data: unknown;
  try {
    data = JSON.parse(content);
  } catch {
    return 'Invalid JSON syntax';
  }

  if (typeof data !== 'object' || data === null || Array.isArray(data)) {
    return 'Configuration must be a JSON object';
  }

  const obj = data as Record<string, unknown>;
  const mcpServers = obj.mcpServers;
  if (typeof mcpServers !== 'object' || mcpServers === null || Array.isArray(mcpServers)) {
    return "Configuration must contain a 'mcpServers' object";
  }

  const servers = mcpServers as Record<string, unknown>;
  if (Object.keys(servers).length === 0) {
    return "'mcpServers' must contain at least one server entry";
  }

  for (const [name, cfg] of Object.entries(servers)) {
    if (typeof cfg !== 'object' || cfg === null || Array.isArray(cfg)) {
      return `Server '${name}' must be an object`;
    }
    const serverCfg = cfg as Record<string, unknown>;
    let serverType = serverCfg.type as string | undefined;

    // Infer type from fields when not explicitly specified
    if (serverType === undefined || serverType === null) {
      if (serverCfg.command) {
        serverType = 'stdio';
      } else if (serverCfg.url) {
        serverType = 'http';
      }
    }

    if (
      serverType !== 'http' &&
      serverType !== 'stdio' &&
      serverType !== 'local' &&
      serverType !== 'sse'
    ) {
      return `Server '${name}' must have 'type' of 'http', 'stdio', 'local', or 'sse', or include a 'command' or 'url' field`;
    }
    if ((serverType === 'http' || serverType === 'sse') && !serverCfg.url) {
      return `Server '${name}' must have a 'url' field`;
    }
    if ((serverType === 'stdio' || serverType === 'local') && !serverCfg.command) {
      return `Server '${name}' must have a 'command' field`;
    }
  }

  return null;
}

export function UploadMcpModal({
  isOpen,
  onClose,
  onUpload,
  onUpdate,
  isSubmitting,
  submitError,
  existingNames = [],
  editingTool = null,
  initialDraft = null,
}: UploadMcpModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [configContent, setConfigContent] = useState('');
  const [githubRepoTarget, setGithubRepoTarget] = useState('');
  const [mode, setMode] = useState<'paste' | 'file'>('paste');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null);
  const [multiServerWarning, setMultiServerWarning] = useState<string | null>(null);
  const isEditMode = editingTool !== null;
  const reservedNames = useMemo(
    () => existingNames.filter((existingName) => existingName !== editingTool?.name),
    [editingTool?.name, existingNames]
  );

  const resetForm = useCallback(() => {
    setName('');
    setDescription('');
    setConfigContent('');
    setGithubRepoTarget('');
    setMode('paste');
    setValidationError(null);
    setDuplicateWarning(null);
    setMultiServerWarning(null);
  }, []);

  const handleClose = useCallback(() => {
    resetForm();
    onClose();
  }, [onClose, resetForm]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, handleClose]);

  useEffect(() => {
    if (!isOpen) return;
    if (editingTool) {
      setName(editingTool.name);
      setDescription(editingTool.description);
      setConfigContent(editingTool.config_content);
      setGithubRepoTarget(editingTool.github_repo_target);
      setMode('paste');
      setValidationError(null);
      setDuplicateWarning(null);
      setMultiServerWarning(null);
      return;
    }
    if (initialDraft) {
      setName(initialDraft.name ?? '');
      setDescription(initialDraft.description ?? '');
      setConfigContent(initialDraft.config_content ?? '');
      setGithubRepoTarget(initialDraft.github_repo_target ?? '');
      setMode('paste');
      setValidationError(null);
      setDuplicateWarning(null);
      setMultiServerWarning(null);
      return;
    }
    resetForm();
  }, [editingTool, initialDraft, isOpen, resetForm]);

  useEffect(() => {
    if (name.trim() && reservedNames.includes(name.trim())) {
      setDuplicateWarning(`A tool named "${name.trim()}" already exists`);
    } else {
      setDuplicateWarning(null);
    }
  }, [name, reservedNames]);

  // Auto-populate name from mcpServers key when name is empty
  useEffect(() => {
    if (name.trim()) return; // Don't overwrite user-entered names
    if (!configContent.trim()) {
      setMultiServerWarning(null);
      return;
    }

    try {
      const parsed = JSON.parse(configContent);
      if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
        const servers = parsed.mcpServers;
        if (typeof servers === 'object' && servers !== null && !Array.isArray(servers)) {
          const keys = Object.keys(servers);
          if (keys.length > 0) {
            setName(keys[0]);
          }
          if (keys.length > 1) {
            setMultiServerWarning(
              `Multiple servers detected (${keys.join(', ')}). Using "${keys[0]}" as the name.`
            );
          } else {
            setMultiServerWarning(null);
          }
        } else {
          setMultiServerWarning(null);
        }
      } else {
        setMultiServerWarning(null);
      }
    } catch {
      setMultiServerWarning(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [configContent]);

  if (!isOpen) return null;

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > MAX_CONFIG_SIZE) {
      setValidationError('File exceeds 256 KB limit');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const text = reader.result as string;
      setConfigContent(text);
      setValidationError(null);
    };
    reader.readAsText(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setValidationError('Name is required');
      return;
    }
    if (trimmedName.length > 100) {
      setValidationError('Name must be 100 characters or fewer');
      return;
    }

    const error = validateMcpJson(configContent);
    if (error) {
      setValidationError(error);
      return;
    }

    try {
      if (editingTool) {
        await onUpdate(editingTool.id, {
          name: trimmedName,
          description: description.trim(),
          config_content: configContent,
          github_repo_target: githubRepoTarget.trim(),
        });
      } else {
        await onUpload({
          name: trimmedName,
          description: description.trim(),
          config_content: configContent,
          github_repo_target: githubRepoTarget.trim(),
        });
      }
      handleClose();
    } catch {
      // Submit error is shown via submitError prop
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="presentation"
      onClick={handleClose}
    >
      <div
        className="celestial-panel celestial-fade-in w-full max-w-lg max-h-[85vh] overflow-y-auto rounded-[1.4rem] border border-border p-6 shadow-lg"
        role="presentation"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-semibold mb-4">
          {isEditMode ? 'Edit MCP Configuration' : 'Upload MCP Configuration'}
        </h2>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="rounded-xl border border-primary/20 bg-primary/5 p-3 text-sm text-muted-foreground">
            Saving a tool now syncs its configuration to both `.copilot/mcp.json` and
            `.vscode/mcp.json` for GitHub agents and local editors.
          </div>

          {/* Name */}
          <div>
            <label htmlFor="tool-name" className="block text-sm font-medium mb-1">
              Name
            </label>
            <input
              id="tool-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Sentry MCP"
              className="w-full rounded-md border border-border bg-background/72 px-3 py-2 text-sm"
              maxLength={100}
            />
            {duplicateWarning && <p className="mt-1 text-xs text-amber-600">{duplicateWarning}</p>}
            {multiServerWarning && (
              <p className="mt-1 text-xs text-amber-600">{multiServerWarning}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label htmlFor="tool-description" className="block text-sm font-medium mb-1">
              Description <span className="text-muted-foreground font-normal">(optional)</span>
            </label>
            <textarea
              id="tool-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of this MCP configuration"
              className="w-full rounded-md border border-border bg-background/72 px-3 py-2 text-sm min-h-[60px] resize-y"
              maxLength={500}
            />
          </div>

          {/* Config Content */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label
                htmlFor={mode === 'paste' ? 'mcp-config-textarea' : 'mcp-config-file'}
                className="block text-sm font-medium"
              >
                MCP Configuration
              </label>
              <button
                type="button"
                className="text-xs text-primary hover:underline"
                onClick={() => setMode(mode === 'paste' ? 'file' : 'paste')}
              >
                {mode === 'paste' ? 'Upload file instead' : 'Paste JSON instead'}
              </button>
            </div>
            {mode === 'paste' ? (
              <textarea
                id="mcp-config-textarea"
                value={configContent}
                onChange={(e) => {
                  setConfigContent(e.target.value);
                  setValidationError(null);
                }}
                placeholder={
                  '{\n  "mcpServers": {\n    "my-server": {\n      "type": "http",\n      "url": "https://example.com/mcp"\n    }\n  }\n}'
                }
                className="w-full rounded-md border border-border bg-background/72 px-3 py-2 text-xs font-mono leading-relaxed min-h-[140px] resize-y"
              />
            ) : (
              <input
                id="mcp-config-file"
                type="file"
                accept=".json,application/json"
                onChange={handleFileUpload}
                className="w-full rounded-md border border-border bg-background/72 px-3 py-2 text-sm"
              />
            )}
          </div>

          {/* GitHub Repo Target */}
          <div>
            <label htmlFor="tool-repo" className="block text-sm font-medium mb-1">
              GitHub Repository{' '}
              <span className="text-muted-foreground font-normal">(optional, auto-detected)</span>
            </label>
            <input
              id="tool-repo"
              type="text"
              value={githubRepoTarget}
              onChange={(e) => setGithubRepoTarget(e.target.value)}
              placeholder="owner/repo"
              className="w-full rounded-md border border-border bg-background/72 px-3 py-2 text-sm"
            />
          </div>

          {/* Validation Error */}
          {validationError && (
            <div className="text-sm text-destructive bg-destructive/10 rounded-md p-2">
              {validationError}
            </div>
          )}

          {/* Upload Error (from server) */}
          {submitError && (
            <div className="text-sm text-destructive bg-destructive/10 rounded-md p-2">
              {submitError}
            </div>
          )}

          {/* Loading indicator */}
          {isSubmitting && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <div className="h-3 w-3 rounded-full border-2 border-primary border-t-transparent animate-spin" />
              {isEditMode
                ? 'Saving and syncing to GitHub...'
                : 'Uploading and syncing to GitHub...'}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              className="rounded-full border border-border bg-background/72 px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-primary/10 hover:text-foreground"
              onClick={handleClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? isEditMode
                  ? 'Saving…'
                  : 'Uploading…'
                : isEditMode
                  ? 'Save Changes'
                  : 'Upload'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
