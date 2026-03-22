/**
 * AddAgentModal — modal dialog for creating or editing a Custom GitHub Agent.
 *
 * Simplified UX: only Name + System Prompt fields.
 * AI auto-generates description and tools from the prompt content.
 * "Raw content" toggle bypasses AI and uses exact text as-is.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { CheckCircle2 } from '@/lib/icons';
import { AgentIconCatalog } from '@/components/agents/AgentIconCatalog';
import { isCelestialIconName, type CelestialIconName } from '@/components/common/agentIcons';
import { ToolChips } from '@/components/tools/ToolChips';
import { ToolSelectorModal } from '@/components/tools/ToolSelectorModal';
import { useCreateAgent, useUpdateAgent } from '@/hooks/useAgents';
import { useToolsList } from '@/hooks/useTools';
import type { AgentConfig } from '@/services/api';
import { ToolsEditor } from './ToolsEditor';
import { Tooltip } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface AddAgentModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  editAgent?: AgentConfig | null;
}

const MAX_PROMPT_LENGTH = 30000;

export function AddAgentModal({ projectId, isOpen, onClose, editAgent }: AddAgentModalProps) {
  const isEditMode = !!editAgent;

  const [name, setName] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [aiEnhance, setAiEnhance] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toolsError, setToolsError] = useState<string | null>(null);
  const [successPrUrl, setSuccessPrUrl] = useState<string | null>(null);
  const [selectedToolIds, setSelectedToolIds] = useState<string[]>([]);
  const [selectedIconName, setSelectedIconName] = useState<CelestialIconName | null>(null);
  const [showToolSelector, setShowToolSelector] = useState(false);
  const [showCloseConfirm, setShowCloseConfirm] = useState(false);
  const [showEditToolSelector, setShowEditToolSelector] = useState(false);

  const createMutation = useCreateAgent(projectId);
  const updateMutation = useUpdateAgent(projectId);
  const { tools: availableTools } = useToolsList(projectId);

  const [snapshot, setSnapshot] = useState<{
    name: string;
    systemPrompt: string;
    tools: string[];
    iconName: CelestialIconName | null;
  } | null>(null);

  const isDirty = useMemo(() => {
    if (!isEditMode || !snapshot) return false;
    if (name !== snapshot.name) return true;
    if (systemPrompt !== snapshot.systemPrompt) return true;
    if (selectedIconName !== snapshot.iconName) return true;
    if (selectedToolIds.length !== snapshot.tools.length) return true;
    return selectedToolIds.some((id, index) => id !== snapshot.tools[index]);
  }, [isEditMode, name, selectedIconName, selectedToolIds, snapshot, systemPrompt]);

  // Clear tools error when tools are selected (render-time adjustment)
  if (selectedToolIds.length > 0 && toolsError) {
    setToolsError(null);
  }

  const resetAndClose = useCallback(() => {
    setName('');
    setSystemPrompt('');
    setAiEnhance(true);
    setError(null);
    setToolsError(null);
    setSuccessPrUrl(null);
    setSelectedToolIds([]);
    setSelectedIconName(null);
    setSnapshot(null);
    setShowCloseConfirm(false);
    setShowToolSelector(false);
    setShowEditToolSelector(false);
    onClose();
  }, [onClose]);

  const [prevIsOpen, setPrevIsOpen] = useState(false);
  const [prevEditAgentId, setPrevEditAgentId] = useState<string | undefined>(undefined);
  const editAgentId = editAgent?.id;
  if (isOpen && (!prevIsOpen || editAgentId !== prevEditAgentId)) {
    setPrevIsOpen(true);
    setPrevEditAgentId(editAgentId);
    setError(null);
    setToolsError(null);
    setSuccessPrUrl(null);
    setShowCloseConfirm(false);
    setShowToolSelector(false);
    setShowEditToolSelector(false);

    if (editAgent) {
      const nextIcon = isCelestialIconName(editAgent.icon_name) ? editAgent.icon_name : null;
      const nextTools = [...(editAgent.tools ?? [])];
      setName(editAgent.name);
      setSystemPrompt(editAgent.system_prompt || '');
      setSelectedToolIds(nextTools);
      setSelectedIconName(nextIcon);
      setSnapshot({
        name: editAgent.name,
        systemPrompt: editAgent.system_prompt || '',
        tools: nextTools,
        iconName: nextIcon,
      });
    } else {
      setName('');
      setSystemPrompt('');
      setAiEnhance(true);
      setSelectedToolIds([]);
      setSelectedIconName(null);
      setSnapshot(null);
    }
  } else if (!isOpen && prevIsOpen) {
    setPrevIsOpen(false);
    setPrevEditAgentId(undefined);
  } else if (editAgentId !== prevEditAgentId) {
    setPrevEditAgentId(editAgentId);
  }

  const handleSave = useCallback(async () => {
    setError(null);
    setToolsError(null);

    const trimmedName = name.trim();
    const trimmedPrompt = systemPrompt.trim();

    if (!trimmedName) {
      setError('Name is required');
      return false;
    }
    if (trimmedName.length > 100) {
      setError('Name must be 100 characters or fewer');
      return false;
    }
    if (!trimmedPrompt) {
      setError('System prompt is required');
      return false;
    }
    if (trimmedPrompt.length > MAX_PROMPT_LENGTH) {
      setError(`System prompt must be ${MAX_PROMPT_LENGTH.toLocaleString()} characters or fewer`);
      return false;
    }
    try {
      if (isEditMode && editAgent) {
        const result = await updateMutation.mutateAsync({
          agentId: editAgent.id,
          data: {
            name: trimmedName,
            system_prompt: trimmedPrompt,
            tools: selectedToolIds,
            ...(selectedIconName !== null || editAgent.icon_name != null
              ? { icon_name: selectedIconName }
              : {}),
          },
        });
        setSuccessPrUrl(result.pr_url);
        setSnapshot({
          name: trimmedName,
          systemPrompt: trimmedPrompt,
          tools: [...selectedToolIds],
          iconName: selectedIconName,
        });
      } else {
        const result = await createMutation.mutateAsync({
          name: trimmedName,
          system_prompt: trimmedPrompt,
          tools: selectedToolIds,
          icon_name: selectedIconName,
          raw: !aiEnhance,
        });
        setSuccessPrUrl(result.pr_url);
      }
      return true;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save agent');
      return false;
    }
  }, [
    aiEnhance,
    createMutation,
    editAgent,
    isEditMode,
    name,
    selectedIconName,
    selectedToolIds,
    systemPrompt,
    updateMutation,
  ]);

  const handleRequestClose = useCallback(() => {
    if (isDirty) {
      setShowCloseConfirm(true);
      return;
    }
    resetAndClose();
  }, [isDirty, resetAndClose]);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      if (event.defaultPrevented || showToolSelector || showEditToolSelector || showCloseConfirm) {
        return;
      }
      handleRequestClose();
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleRequestClose, isOpen, showCloseConfirm, showEditToolSelector, showToolSelector]);

  useEffect(() => {
    if (!isDirty) return;

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  if (!isOpen) return null;

  const isPending = createMutation.isPending || updateMutation.isPending;

  const selectedTools = selectedToolIds.map((id) => {
    const tool = availableTools.find((availableTool) => availableTool.id === id);
    return {
      id,
      name: tool?.name ?? id,
      description: tool?.description ?? '',
    };
  });

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await handleSave();
  };

  if (showCloseConfirm) {
    return (
      <div
        className="fixed inset-0 z-[120] flex items-center justify-center bg-black/55 px-4"
        role="dialog"
        aria-modal="true"
        aria-label="Unsaved changes confirmation"
      >
        <div
          className="celestial-panel celestial-fade-in w-full max-w-sm rounded-[1.5rem] border border-border/80 p-6 shadow-xl"
          role="presentation"
          onClick={(event) => event.stopPropagation()}
        >
          <h3 className="text-lg font-semibold">Unsaved Changes</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            You have unsaved changes. What would you like to do?
          </p>
          <div className="mt-6 flex justify-end gap-2">
            <button
              type="button"
              className="celestial-focus solar-action rounded-full px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              onClick={() => setShowCloseConfirm(false)}
            >
              Cancel
            </button>
            <button
              type="button"
              className="celestial-focus rounded-full bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive transition-colors hover:bg-destructive/20"
              onClick={resetAndClose}
            >
              Discard
            </button>
            <button
              type="button"
              className="celestial-focus rounded-full bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
              onClick={async () => {
                setShowCloseConfirm(false);
                await handleSave();
              }}
            >
              Save
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (successPrUrl) {
    return (
      <div
        className="fixed inset-0 z-[120] flex items-center justify-center bg-black/55 px-4"
        role="presentation"
        onClick={resetAndClose}
      >
        <div
          className="celestial-panel celestial-fade-in w-full max-w-md rounded-[1.6rem] border border-border/80 p-6 shadow-xl"
          role="presentation"
          onClick={(event) => event.stopPropagation()}
        >
          <div className="flex flex-col items-center gap-3 text-center">
            <CheckCircle2 className="h-8 w-8 text-primary" aria-hidden="true" />
            <h3 className="text-lg font-semibold">
              {isEditMode ? 'Agent Updated' : 'Agent Created'}
            </h3>
            <p className="text-sm text-muted-foreground">
              A pull request has been opened with the agent configuration files. It will appear in
              the catalog after merge to main.
            </p>
            <a
              href={successPrUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-primary underline-offset-4 hover:underline"
            >
              View Pull Request →
            </a>
            <button
              type="button"
              className="celestial-focus mt-2 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
              onClick={resetAndClose}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 z-[110] flex items-center justify-center bg-black/55 px-4 py-6"
      role="presentation"
      onClick={handleRequestClose}
    >
      <div
        className="celestial-panel celestial-fade-in relative flex max-h-[min(92vh,58rem)] w-full max-w-3xl flex-col overflow-hidden rounded-[1.7rem] border border-border/80 shadow-xl"
        role="presentation"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="border-b border-border/70 px-6 py-5">
          <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">
            {isEditMode ? 'Refine Agent' : 'Create Agent'}
          </p>
          <div className="mt-2 flex items-start justify-between gap-4">
            <div>
              <h2 className="font-display text-2xl font-medium">
                {isEditMode ? 'Edit Agent' : 'Add Agent'}
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Define the agent prompt, assign tools, and optionally choose a dedicated celestial
                icon.
              </p>
            </div>
            <button
              type="button"
              onClick={handleRequestClose}
              className="celestial-focus rounded-full border border-border/70 px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
              aria-label="Close"
            >
              Close
            </button>
          </div>
        </div>

        <div className="overflow-y-auto px-6 py-5">
          {isDirty && (
            <div className="solar-chip-warning mb-4 rounded-[1rem] p-3 text-sm">
              You have unsaved changes.
            </div>
          )}

          <form id="agent-form" onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div>
              <label htmlFor="agent-name" className="mb-1.5 block text-sm font-medium">
                Name
              </label>
              <Tooltip contentKey="agents.modal.nameField" side="right">
                <input
                  id="agent-name"
                  type="text"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="e.g., Security Reviewer"
                  className="w-full rounded-xl border border-border bg-background/72 px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary/40"
                  maxLength={100}
                />
              </Tooltip>
            </div>

            <div>
              <label htmlFor="agent-system-prompt" className="mb-1.5 block text-sm font-medium">
                System Prompt
                <span className="ml-2 font-normal text-muted-foreground">
                  {systemPrompt.length.toLocaleString()} / {MAX_PROMPT_LENGTH.toLocaleString()}
                </span>
              </label>
              <Tooltip contentKey="agents.modal.systemPrompt" side="right">
                <textarea
                  id="agent-system-prompt"
                  value={systemPrompt}
                  onChange={(event) => setSystemPrompt(event.target.value)}
                  placeholder="Detailed instructions for the agent's behavior..."
                  className="min-h-[220px] w-full resize-y rounded-[1.1rem] border border-border bg-background/72 px-3 py-3 font-mono text-xs leading-relaxed outline-none transition-colors focus:border-primary/40"
                  maxLength={MAX_PROMPT_LENGTH}
                />
              </Tooltip>
            </div>

            <div>
              <span className="mb-2 block text-sm font-medium">Celestial Icon</span>
              <p className="mb-3 text-xs text-muted-foreground">
                Choose a specific celestial icon, or leave it on automatic to use the diversified
                slug-based mapping for this agent.
              </p>
              <AgentIconCatalog
                slug={isEditMode ? editAgent?.slug : name}
                agentName={name || 'New Agent'}
                selectedIconName={selectedIconName}
                onSelect={setSelectedIconName}
              />
            </div>

            <div>
              <span className="mb-1 block text-sm font-medium">MCP Tools</span>
              {isEditMode ? (
                <ToolsEditor
                  tools={selectedToolIds}
                  onToolsChange={setSelectedToolIds}
                  error={toolsError ?? undefined}
                  projectId={projectId}
                  onSelectorOpenChange={setShowEditToolSelector}
                />
              ) : (
                <ToolChips
                  tools={selectedTools}
                  onRemove={(id) =>
                    setSelectedToolIds((previous) => previous.filter((toolId) => toolId !== id))
                  }
                  onAddClick={() => setShowToolSelector(true)}
                />
              )}
            </div>

            {!isEditMode && (
              <div className="flex items-center gap-2">
                <Tooltip contentKey="agents.modal.aiEnhanceToggle">
                  <button
                    type="button"
                    role="switch"
                    aria-checked={aiEnhance}
                    onClick={() => setAiEnhance((previous) => !previous)}
                    className={cn('relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors', aiEnhance ? 'bg-primary' : 'bg-muted')}
                  >
                    <span
                      className={cn('pointer-events-none inline-block h-4 w-4 transform rounded-full bg-background shadow-sm ring-0 transition-transform', aiEnhance ? 'translate-x-4' : 'translate-x-0')}
                    />
                  </button>
                </Tooltip>
                <span className="text-xs text-muted-foreground">
                  AI Enhance
                  <span className="ml-1 text-[10px]">
                    {aiEnhance
                      ? '— AI generates description, tools & enhances your prompt'
                      : '— uses exact text as-is, no AI enhancement'}
                  </span>
                </span>
              </div>
            )}

            {isPending && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <div className="h-3 w-3 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                {aiEnhance ? 'AI is enhancing and creating files...' : 'Creating agent files...'}
              </div>
            )}

            {error && (
              <div className="rounded-[1rem] bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="celestial-focus solar-action rounded-full px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                onClick={handleRequestClose}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="celestial-focus rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
                disabled={isPending}
              >
                {isPending ? 'Saving…' : isEditMode ? 'Update Agent' : 'Create Agent'}
              </button>
            </div>
          </form>
        </div>

        {!isEditMode && (
          <ToolSelectorModal
            isOpen={showToolSelector}
            onClose={() => setShowToolSelector(false)}
            onConfirm={(ids) => setSelectedToolIds(ids)}
            initialSelectedIds={selectedToolIds}
            projectId={projectId}
          />
        )}
      </div>
    </div>
  );
}
