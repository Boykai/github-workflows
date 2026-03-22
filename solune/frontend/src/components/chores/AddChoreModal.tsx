import { ScrollText, Sparkles, X } from '@/lib/icons';

/**
 * AddChoreModal — modal dialog for creating a new chore.
 *
 * Provides name input, text area for template content, AI Enhance toggle,
 * Pipeline selector, sparse vs. rich input detection, and double-confirmation flow.
 */

import { useEffect, useState } from 'react';
import { useCreateChoreWithAutoMerge, useChoreTemplates } from '@/hooks/useChores';
import { ChoreChatFlow } from './ChoreChatFlow';
import { ConfirmChoreModal } from './ConfirmChoreModal';
import { PipelineSelector } from './PipelineSelector';
import type { ChoreTemplate } from '@/types';
import { cn } from '@/lib/utils';

interface AddChoreModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  initialTemplate?: ChoreTemplate | null;
}

/**
 * Sparse input heuristic matching backend's is_sparse_input():
 * - Rich indicators: headings (##), list markers (- *), ≥4 lines (≥3 newlines)
 * - If any rich indicator → RICH
 * - ≤15 words → SPARSE
 * - ≤40 words on single line → SPARSE
 * - Else → RICH
 */
function isSparseInput(text: string): boolean {
  const trimmed = text.trim();
  if (!trimmed) return true;

  const hasHeadings = /^#{1,6}\s/m.test(trimmed);
  const hasLists = /^[-*]\s/m.test(trimmed);
  const lines = trimmed.split('\n');
  const hasMultiLines = lines.length >= 4;

  if (hasHeadings || hasLists || hasMultiLines) return false;

  const words = trimmed.split(/\s+/).length;
  if (words <= 15) return true;

  if (lines.length === 1 && words <= 40) return true;

  return false;
}

export function AddChoreModal({ projectId, isOpen, onClose, initialTemplate }: AddChoreModalProps) {
  const [name, setName] = useState('');
  const [templateContent, setTemplateContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showChatFlow, setShowChatFlow] = useState(false);
  const [sparseContent, setSparseContent] = useState('');
  const [aiEnhance, setAiEnhance] = useState(true);
  const [agentPipelineId, setAgentPipelineId] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingContent, setPendingContent] = useState('');

  const createMutation = useCreateChoreWithAutoMerge(projectId);
  const { data: repoTemplates } = useChoreTemplates(isOpen ? projectId : null);

  const handleSelectTemplate = (template: ChoreTemplate) => {
    setName(template.name);
    setTemplateContent(template.content);
  };

  // Apply initialTemplate when modal opens with one pre-selected
  useEffect(() => {
    if (isOpen && initialTemplate) {
      setName(initialTemplate.name);
      setTemplateContent(initialTemplate.content);
    }
  }, [isOpen, initialTemplate]);

  // Close modal and reset all state on Escape key (document-level listener)
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        resetAndClose();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const createChore = async (_choreName: string, content: string) => {
    // Show double-confirmation modal
    setPendingContent(content);
    setShowConfirm(true);
  };

  const handleConfirmCreate = async () => {
    try {
      await createMutation.mutateAsync({
        name: name.trim(),
        template_content: pendingContent,
        ai_enhance_enabled: aiEnhance,
        agent_pipeline_id: agentPipelineId,
        auto_merge: true,
      });
      setShowConfirm(false);
      resetAndClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create chore';
      setError(message);
      setShowConfirm(false);
    }
  };

  const resetAndClose = () => {
    setName('');
    setTemplateContent('');
    setError(null);
    setShowChatFlow(false);
    setSparseContent('');
    setAiEnhance(true);
    setAgentPipelineId('');
    setShowConfirm(false);
    setPendingContent('');
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedName = name.trim();
    const trimmedContent = templateContent.trim();

    if (!trimmedName) {
      setError('Name is required');
      return;
    }
    if (trimmedName.length > 200) {
      setError('Name must be 200 characters or fewer');
      return;
    }
    if (!trimmedContent) {
      setError('Template content is required');
      return;
    }

    // Route sparse input through chat flow (US3)
    if (isSparseInput(trimmedContent)) {
      setSparseContent(trimmedContent);
      setShowChatFlow(true);
      return;
    }

    await createChore(trimmedName, trimmedContent);
  };

  const handleTemplateReady = async (content: string) => {
    await createChore(name.trim(), content);
  };

  const handleChatCancel = () => {
    setShowChatFlow(false);
    setSparseContent('');
  };

  const handleCancel = () => {
    resetAndClose();
  };

  // --- Confirmation Modal ---
  if (showConfirm) {
    return (
      <ConfirmChoreModal
        isOpen={showConfirm}
        choreName={name.trim()}
        isLoading={createMutation.isPending}
        onConfirm={handleConfirmCreate}
        onCancel={() => setShowConfirm(false)}
      />
    );
  }

  // --- Chat flow view ---
  if (showChatFlow) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="absolute inset-0 bg-black/50" onClick={handleCancel} role="presentation" />
        <div className="celestial-panel celestial-fade-in relative z-10 mx-4 w-full max-w-lg rounded-[1.4rem] border border-border shadow-xl">
          <div className="flex items-center justify-between p-4 border-b border-border">
            <h3 className="text-lg font-semibold text-foreground">Build Template — {name}</h3>
            <button
              className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground"
              onClick={handleCancel}
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="p-4">
            <ChoreChatFlow
              projectId={projectId}
              initialMessage={sparseContent}
              choreName={name.trim()}
              onTemplateReady={handleTemplateReady}
              onCancel={handleChatCancel}
              aiEnhance={aiEnhance}
            />
          </div>
        </div>
      </div>
    );
  }

  // --- Standard form view ---
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={handleCancel} role="presentation" />

      {/* Modal */}
      <div className="celestial-panel celestial-fade-in relative z-10 mx-4 w-full max-w-lg rounded-[1.4rem] border border-border shadow-xl">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h3 className="text-lg font-semibold text-foreground">Add Chore</h3>
          <button
            className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground"
            onClick={handleCancel}
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 flex flex-col gap-4">
          {/* Template picker */}
          {repoTemplates && repoTemplates.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium text-foreground">Start from a template</span>
              <div className="flex flex-wrap gap-2">
                {repoTemplates.map((tpl) => (
                  <button
                    key={tpl.path}
                    type="button"
                    onClick={() => handleSelectTemplate(tpl)}
                    className="rounded-md border border-input bg-background/56 px-2.5 py-1.5 text-left text-xs font-medium transition-colors hover:border-primary/40 hover:bg-primary/10"
                    title={tpl.about || tpl.name}
                  >
                    <span className="inline-flex items-center gap-2">
                      <ScrollText className="h-3.5 w-3.5 text-primary/70" />
                      {tpl.name}
                    </span>
                  </button>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">Or create a custom chore below</p>
            </div>
          )}

          {/* Name */}
          <div className="flex flex-col gap-1.5">
            <label htmlFor="chore-name" className="text-sm font-medium text-foreground">
              Name
            </label>
            <input
              id="chore-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Bug Bash, Dependency Update"
              className="flex h-9 w-full rounded-md border border-input bg-background/72 px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
              maxLength={200}
              // eslint-disable-next-line jsx-a11y/no-autofocus
              autoFocus
            />
          </div>

          {/* Template Content */}
          <div className="flex flex-col gap-1.5">
            <label htmlFor="chore-content" className="text-sm font-medium text-foreground">
              Template Content
            </label>
            <textarea
              id="chore-content"
              value={templateContent}
              onChange={(e) => setTemplateContent(e.target.value)}
              placeholder="Enter detailed markdown content or a brief description to start a guided chat..."
              rows={10}
              className="flex w-full rounded-md border border-input bg-background/72 px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring resize-y min-h-[120px]"
            />
            <p className="text-xs text-muted-foreground">
              Brief descriptions start a guided chat; detailed markdown creates the chore directly
            </p>
          </div>

          {/* AI Enhance Toggle */}
          <div className="flex items-center justify-between gap-3 rounded-md border border-input bg-muted/20 px-3 py-2">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <div>
                <p className="text-sm font-medium text-foreground">AI Enhance</p>
                <p className="text-xs text-muted-foreground">
                  {aiEnhance
                    ? 'AI generates full template content and metadata'
                    : 'Your exact input as body + AI-generated metadata only'}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setAiEnhance(!aiEnhance)}
              className={cn('relative inline-flex h-6 w-11 items-center rounded-full transition-colors', aiEnhance ? 'bg-primary' : 'bg-muted-foreground/30')}
              role="switch"
              aria-checked={aiEnhance}
            >
              <span
                className={cn('inline-block h-4 w-4 transform rounded-full bg-white transition-transform', aiEnhance ? 'translate-x-6' : 'translate-x-1')}
              />
            </button>
          </div>

          {/* Pipeline Selector */}
          <PipelineSelector
            projectId={projectId}
            value={agentPipelineId}
            onChange={setAgentPipelineId}
          />

          {/* Error */}
          {error && <p className="text-sm text-destructive">{error}</p>}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={handleCancel}
              className="rounded-full border border-input bg-background/72 px-3 py-1.5 text-sm font-medium transition-colors hover:bg-primary/10"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-3 py-1.5 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Chore'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
