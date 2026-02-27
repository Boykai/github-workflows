/**
 * Task preview component for AI-generated task proposals.
 */

import type { AITaskProposal } from '@/types';

interface TaskPreviewProps {
  proposal: AITaskProposal;
  onConfirm: () => void;
  onReject: () => void;
}

export function TaskPreview({ proposal, onConfirm, onReject }: TaskPreviewProps) {
  return (
    <div className="bg-muted/50 border border-border rounded-lg overflow-hidden max-w-[500px] self-start ml-11">
      <div className="bg-primary text-primary-foreground px-4 py-2 text-xs font-medium">
        <span>Task Preview</span>
      </div>

      <div className="p-4">
        <h3 className="text-base font-semibold text-foreground mb-3">{proposal.proposed_title}</h3>

        <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
          {proposal.proposed_description.length > 500
            ? `${proposal.proposed_description.slice(0, 500)}...`
            : proposal.proposed_description}
        </div>
      </div>

      <div className="flex gap-2 p-3 bg-background border-t border-border">
        <button onClick={onReject} className="flex-1 py-2 px-4 rounded-md text-sm font-medium cursor-pointer transition-colors bg-muted text-muted-foreground border border-border hover:bg-border">
          Cancel
        </button>
        <button onClick={onConfirm} className="flex-1 py-2 px-4 rounded-md text-sm font-medium cursor-pointer transition-colors bg-green-500 text-white border-none hover:bg-green-600">
          Create Task
        </button>
      </div>
    </div>
  );
}
