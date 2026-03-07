/**
 * AddAgentModal — modal dialog for creating or editing a Custom GitHub Agent.
 *
 * Simplified UX: only Name + System Prompt fields.
 * AI auto-generates description and tools from the prompt content.
 * "Raw content" toggle bypasses AI and uses exact text as-is.
 */

import { useCallback, useEffect, useState } from 'react';
import { useCreateAgent, useUpdateAgent } from '@/hooks/useAgents';
import { useToolsList } from '@/hooks/useTools';
import { ToolChips } from '@/components/tools/ToolChips';
import { ToolSelectorModal } from '@/components/tools/ToolSelectorModal';
import type { AgentConfig } from '@/services/api';

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
  const [successPrUrl, setSuccessPrUrl] = useState<string | null>(null);
  const [selectedToolIds, setSelectedToolIds] = useState<string[]>([]);
  const [showToolSelector, setShowToolSelector] = useState(false);

  const createMutation = useCreateAgent(projectId);
  const updateMutation = useUpdateAgent(projectId);
  const { tools: availableTools } = useToolsList(projectId);

  const resetAndClose = useCallback(() => {
    setName('');
    setSystemPrompt('');
    setAiEnhance(true);
    setError(null);
    setSuccessPrUrl(null);
    setSelectedToolIds([]);
    onClose();
  }, [onClose]);

  // Pre-populate fields in edit mode
  useEffect(() => {
    if (isOpen && editAgent) {
      setName(editAgent.name);
      setSystemPrompt(editAgent.system_prompt || '');
      setSelectedToolIds(editAgent.tools ?? []);
    }
  }, [isOpen, editAgent]);

  // Escape key handler
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') resetAndClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, resetAndClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedName = name.trim();
    const trimmedPrompt = systemPrompt.trim();

    if (!trimmedName) { setError('Name is required'); return; }
    if (trimmedName.length > 100) { setError('Name must be 100 characters or fewer'); return; }
    if (!trimmedPrompt) { setError('System prompt is required'); return; }
    if (trimmedPrompt.length > MAX_PROMPT_LENGTH) {
      setError(`System prompt must be ${MAX_PROMPT_LENGTH.toLocaleString()} characters or fewer`);
      return;
    }

    try {
      if (isEditMode && editAgent) {
        const result = await updateMutation.mutateAsync({
          agentId: editAgent.id,
          data: {
            name: trimmedName,
            system_prompt: trimmedPrompt,
            tools: selectedToolIds,
          },
        });
        setSuccessPrUrl(result.pr_url);
      } else {
        const result = await createMutation.mutateAsync({
          name: trimmedName,
          system_prompt: trimmedPrompt,
          tools: selectedToolIds,
          raw: !aiEnhance,
        });
        setSuccessPrUrl(result.pr_url);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to save agent';
      setError(message);
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  // Success state
  if (successPrUrl) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="presentation" onClick={resetAndClose}>
        <div className="bg-card rounded-lg border border-border shadow-lg p-6 w-full max-w-md" role="presentation" onClick={(e) => e.stopPropagation()}>
          <div className="flex flex-col items-center gap-3 text-center">
            <span className="text-3xl">✅</span>
            <h3 className="text-lg font-semibold">{isEditMode ? 'Agent Updated' : 'Agent Created'}</h3>
            <p className="text-sm text-muted-foreground">
              A pull request has been opened with the agent configuration files. It will appear in the catalog after merge to main.
            </p>
            <a
              href={successPrUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:underline"
            >
              View Pull Request →
            </a>
            <button
              className="mt-2 px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
              onClick={resetAndClose}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Form
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="presentation" onClick={resetAndClose}>
      <div className="bg-card rounded-lg border border-border shadow-lg p-6 w-full max-w-lg max-h-[80vh] overflow-y-auto" role="presentation" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">
          {isEditMode ? 'Edit Agent' : 'Add Agent'}
        </h2>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Name */}
          <div>
            <label htmlFor="agent-name" className="block text-sm font-medium mb-1">Name</label>
            <input
              id="agent-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Security Reviewer"
              className="w-full px-3 py-2 text-sm border border-border rounded-md bg-background"
              maxLength={100}
            />
          </div>

          {/* System Prompt */}
          <div>
            <label htmlFor="agent-system-prompt" className="block text-sm font-medium mb-1">
              System Prompt
              <span className="text-muted-foreground font-normal ml-2">
                {systemPrompt.length.toLocaleString()} / {MAX_PROMPT_LENGTH.toLocaleString()}
              </span>
            </label>
            <textarea
              id="agent-system-prompt"
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="Detailed instructions for the agent's behavior..."
              className="w-full px-3 py-2 text-sm border border-border rounded-md bg-background min-h-[200px] resize-y font-mono text-xs leading-relaxed"
              maxLength={MAX_PROMPT_LENGTH}
            />
          </div>

          {/* Add Tools */}
          <div>
            <span className="block text-sm font-medium mb-1">MCP Tools</span>
            <ToolChips
              tools={selectedToolIds.map((id) => {
                const t = availableTools.find((tool) => tool.id === id);
                return { id, name: t?.name ?? id, description: t?.description ?? '' };
              })}
              onRemove={(id) => setSelectedToolIds((prev) => prev.filter((tid) => tid !== id))}
              onAddClick={() => setShowToolSelector(true)}
            />
          </div>

          {/* Raw content toggle */}
          {!isEditMode && (
            <div className="flex items-center gap-2">
              <button
                type="button"
                role="switch"
                aria-checked={aiEnhance}
                onClick={() => setAiEnhance(!aiEnhance)}
                className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                  aiEnhance ? 'bg-primary' : 'bg-muted'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-background shadow-sm ring-0 transition-transform ${
                    aiEnhance ? 'translate-x-4' : 'translate-x-0'
                  }`}
                />
              </button>
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

          {/* Status indicator */}
          {isPending && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <div className="h-3 w-3 rounded-full border-2 border-primary border-t-transparent animate-spin" />
              {aiEnhance ? 'AI is enhancing & creating files...' : 'Creating agent files...'}
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="text-sm text-destructive bg-destructive/10 rounded-md p-2">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              className="px-4 py-2 text-sm font-medium rounded-md bg-muted hover:bg-muted/80 text-muted-foreground"
              onClick={resetAndClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              disabled={isPending}
            >
              {isPending ? 'Saving…' : isEditMode ? 'Update Agent' : 'Create Agent'}
            </button>
          </div>
        </form>

        {/* Tool Selector Modal */}
        <ToolSelectorModal
          isOpen={showToolSelector}
          onClose={() => setShowToolSelector(false)}
          onConfirm={(ids) => setSelectedToolIds(ids)}
          initialSelectedIds={selectedToolIds}
          projectId={projectId}
        />
      </div>
    </div>
  );
}
