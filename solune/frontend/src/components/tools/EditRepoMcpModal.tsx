import { useCallback, useEffect, useId, useRef, useState } from 'react';
import type { RepoMcpServerConfig, RepoMcpServerUpdate } from '@/types';
import { validateMcpJson } from './UploadMcpModal';

interface EditRepoMcpModalProps {
  isOpen: boolean;
  server: RepoMcpServerConfig | null;
  isSubmitting: boolean;
  submitError: string | null;
  onClose: () => void;
  onSave: (serverName: string, data: RepoMcpServerUpdate) => Promise<unknown>;
}

function buildConfigContent(server: RepoMcpServerConfig) {
  return `${JSON.stringify(
    {
      mcpServers: {
        [server.name]: server.config,
      },
    },
    null,
    2
  )}\n`;
}

export function EditRepoMcpModal({
  isOpen,
  server,
  isSubmitting,
  submitError,
  onClose,
  onSave,
}: EditRepoMcpModalProps) {
  const titleId = useId();
  const nameInputRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState('');
  const [configContent, setConfigContent] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleClose = useCallback(() => {
    setValidationError(null);
    onClose();
  }, [onClose]);

  const [prevIsOpen, setPrevIsOpen] = useState(isOpen);
  const [prevServerId, setPrevServerId] = useState(server?.name);
  if (isOpen && (isOpen !== prevIsOpen || server?.name !== prevServerId)) {
    setPrevIsOpen(true);
    setPrevServerId(server?.name);
    if (server) {
      setName(server.name);
      setConfigContent(buildConfigContent(server));
      setValidationError(null);
    }
  } else if (!isOpen && prevIsOpen) {
    setPrevIsOpen(false);
    setPrevServerId(undefined);
  } else if (server?.name !== prevServerId) {
    setPrevServerId(server?.name);
  }

  // Focus name input when modal opens
  useEffect(() => {
    if (isOpen && server) {
      nameInputRef.current?.focus();
    }
  }, [isOpen, server]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        handleClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleClose, isOpen]);

  if (!isOpen || !server) {
    return null;
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setValidationError(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setValidationError('Name is required');
      return;
    }

    const error = validateMcpJson(configContent);
    if (error) {
      setValidationError(error);
      return;
    }

    try {
      const parsed = JSON.parse(configContent) as { mcpServers?: Record<string, unknown> };
      const serverEntries = Object.keys(parsed.mcpServers ?? {});
      if (serverEntries.length !== 1) {
        setValidationError('Repository MCP editing supports exactly one MCP server entry');
        return;
      }
    } catch {
      setValidationError('Invalid JSON syntax');
      return;
    }

    try {
      await onSave(server.name, {
        name: trimmedName,
        config_content: configContent,
      });
      handleClose();
    } catch {
      // submitError is surfaced by the parent mutation state
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="presentation">
      <button
        type="button"
        className="absolute inset-0 bg-black/50"
        aria-label="Close dialog"
        onClick={handleClose}
      />
      <div
        className="celestial-panel celestial-fade-in relative w-full max-w-lg max-h-[85vh] overflow-y-auto rounded-[1.4rem] border border-border p-6 shadow-lg"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        <h2 id={titleId} className="mb-4 text-lg font-semibold">
          Edit Repository MCP
        </h2>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="rounded-xl border border-primary/20 bg-primary/5 p-3 text-sm text-muted-foreground">
            Update this MCP directly in the repository config files already present in the repo.
          </div>

          <div>
            <label htmlFor="repo-mcp-name" className="mb-1 block text-sm font-medium">
              Name
            </label>
            <input
              id="repo-mcp-name"
              ref={nameInputRef}
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="w-full rounded-md border border-border bg-background/72 px-3 py-2 text-sm"
              maxLength={100}
            />
          </div>

          <div>
            <label htmlFor="repo-mcp-config" className="mb-1 block text-sm font-medium">
              MCP Configuration
            </label>
            <textarea
              id="repo-mcp-config"
              value={configContent}
              onChange={(event) => {
                setConfigContent(event.target.value);
                setValidationError(null);
              }}
              className="w-full rounded-md border border-border bg-background/72 px-3 py-2 text-xs font-mono leading-relaxed min-h-[180px] resize-y"
            />
          </div>

          {validationError && (
            <div className="rounded-md bg-destructive/10 p-2 text-sm text-destructive">
              {validationError}
            </div>
          )}

          {submitError && (
            <div className="rounded-md bg-destructive/10 p-2 text-sm text-destructive">
              {submitError}
            </div>
          )}

          {isSubmitting && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <div className="h-3 w-3 rounded-full border-2 border-primary border-t-transparent animate-spin" />
              Saving repository MCP...
            </div>
          )}

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
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Saving…' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
