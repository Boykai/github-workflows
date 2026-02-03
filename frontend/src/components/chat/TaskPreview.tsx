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
    <div className="task-preview">
      <div className="preview-header">
        <span className="preview-label">Task Preview</span>
      </div>

      <div className="preview-content">
        <h3 className="preview-title">{proposal.proposed_title}</h3>

        <div className="preview-description">
          {proposal.proposed_description.length > 500
            ? `${proposal.proposed_description.slice(0, 500)}...`
            : proposal.proposed_description}
        </div>
      </div>

      <div className="preview-actions">
        <button onClick={onReject} className="reject-button">
          Cancel
        </button>
        <button onClick={onConfirm} className="confirm-button">
          Create Task
        </button>
      </div>
    </div>
  );
}
