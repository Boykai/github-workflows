/**
 * BulkModelUpdateDialog — two-step confirmation dialog for updating
 * all agent models at once.
 *
 * Step 1: Select a target model.
 * Step 2: Review affected agents and confirm.
 */

import { useState } from 'react';
import { useBulkUpdateModels } from '@/hooks/useAgents';
import { ModelSelector } from '@/components/pipeline/ModelSelector';
import type { AgentConfig } from '@/services/api';

interface BulkModelUpdateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agents: AgentConfig[];
  projectId: string;
  onSuccess: () => void;
}

export function BulkModelUpdateDialog({
  open,
  onOpenChange,
  agents,
  projectId,
  onSuccess,
}: BulkModelUpdateDialogProps) {
  const [step, setStep] = useState<1 | 2>(1);
  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);
  const [selectedModelName, setSelectedModelName] = useState<string>('');

  const mutation = useBulkUpdateModels(projectId);

  const handleClose = () => {
    setStep(1);
    setSelectedModelId(null);
    setSelectedModelName('');
    onOpenChange(false);
  };

  const handleConfirm = () => {
    if (!selectedModelId || !selectedModelName) return;
    mutation.mutate(
      { targetModelId: selectedModelId, targetModelName: selectedModelName },
      {
        onSuccess: () => {
          handleClose();
          onSuccess();
        },
      }
    );
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="presentation"
    >
      <button
        type="button"
        className="absolute inset-0 cursor-default"
        aria-label="Close bulk model update dialog"
        onClick={handleClose}
      />
      <div
        className="celestial-panel celestial-fade-in relative bg-card rounded-lg border border-border shadow-lg p-6 w-full max-w-md max-h-[80vh] overflow-y-auto"
        role="dialog"
        aria-modal="true"
        aria-label="Bulk model update dialog"
      >
        {step === 1 && (
          <>
            <h3 className="text-lg font-semibold mb-1">Update All Agent Models</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Select the target model to apply to all {agents.length} agent
              {agents.length === 1 ? '' : 's'}.
            </p>
            <div className="mb-4">
              <ModelSelector
                selectedModelId={selectedModelId}
                onSelect={(id, name) => {
                  setSelectedModelId(id);
                  setSelectedModelName(name);
                }}
              />
            </div>
            {selectedModelName && (
              <p className="mb-4 text-sm">
                Selected: <span className="font-medium">{selectedModelName}</span>
              </p>
            )}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                className="celestial-focus px-4 py-2 text-sm font-medium rounded-md bg-muted hover:bg-muted/80 text-muted-foreground"
                onClick={handleClose}
              >
                Cancel
              </button>
              <button
                type="button"
                className="celestial-focus px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                disabled={!selectedModelId}
                onClick={() => setStep(2)}
              >
                Next
              </button>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <h3 className="text-lg font-semibold mb-1">Confirm Bulk Update</h3>
            <p className="text-sm text-muted-foreground mb-3">
              Update all agents to <span className="font-medium">{selectedModelName}</span>?
            </p>
            <div className="mb-4 rounded-md border border-border/60 bg-background/50 p-3 max-h-48 overflow-y-auto">
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                {agents.length} agent{agents.length === 1 ? '' : 's'} will be updated
              </p>
              <ul className="space-y-1">
                {agents.map((agent) => (
                  <li key={agent.id} className="flex items-center justify-between text-sm">
                    <span className="truncate">{agent.name}</span>
                    <span className="shrink-0 ml-2 text-xs text-muted-foreground">
                      {agent.default_model_name || 'No model'} → {selectedModelName}
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            {mutation.isError && (
              <div className="mb-3 text-sm text-destructive bg-destructive/10 rounded-md p-2">
                {mutation.error?.message || 'Bulk update failed'}
              </div>
            )}

            <div className="flex justify-end gap-2">
              <button
                type="button"
                className="celestial-focus px-4 py-2 text-sm font-medium rounded-md bg-muted hover:bg-muted/80 text-muted-foreground"
                onClick={() => setStep(1)}
              >
                Back
              </button>
              <button
                type="button"
                className="celestial-focus px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                disabled={mutation.isPending}
                onClick={handleConfirm}
              >
                {mutation.isPending ? 'Updating…' : 'Confirm'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
