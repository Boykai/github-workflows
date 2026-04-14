/**
 * Status change preview component for confirming status updates.
 */

interface StatusChangePreviewProps {
  taskTitle: string;
  currentStatus: string;
  targetStatus: string;
  onConfirm: () => void;
  onReject: () => void;
}

export function StatusChangePreview({
  taskTitle,
  currentStatus,
  targetStatus,
  onConfirm,
  onReject,
}: StatusChangePreviewProps) {
  return (
    <div className="status-change-preview">
      <div className="preview-header">
        <span className="preview-label">Status Change</span>
      </div>

      <div className="preview-content">
        <p className="status-task-title">{taskTitle}</p>

        <div className="status-change-flow">
          <span className={`status-badge status-${currentStatus.toLowerCase().replace(/\s+/g, '-')}`}>
            {currentStatus}
          </span>
          <span className="status-arrow">→</span>
          <span className={`status-badge status-${targetStatus.toLowerCase().replace(/\s+/g, '-')}`}>
            {targetStatus}
          </span>
        </div>
      </div>

      <div className="preview-actions">
        <button onClick={onReject} className="reject-button">
          Cancel
        </button>
        <button onClick={onConfirm} className="confirm-button">
          Update Status
        </button>
      </div>
    </div>
  );
}
