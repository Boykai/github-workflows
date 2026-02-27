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
    <div className="bg-muted/50 border border-border rounded-lg overflow-hidden max-w-[500px] self-start ml-11">
      <div className="bg-primary text-primary-foreground px-4 py-2 text-xs font-medium">
        <span>Status Change</span>
      </div>

      <div className="p-4">
        <p className="text-sm font-medium text-foreground mb-3">{taskTitle}</p>

        <div className="flex items-center gap-3">
          <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground border border-border">
            {currentStatus}
          </span>
          <span className="text-muted-foreground">→</span>
          <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary border border-primary/20">
            {targetStatus}
          </span>
        </div>
      </div>

      <div className="flex gap-2 p-3 bg-background border-t border-border">
        <button onClick={onReject} className="flex-1 py-2 px-4 rounded-md text-sm font-medium cursor-pointer transition-colors bg-muted text-muted-foreground border border-border hover:bg-border">
          Cancel
        </button>
        <button onClick={onConfirm} className="flex-1 py-2 px-4 rounded-md text-sm font-medium cursor-pointer transition-colors bg-green-500 text-white border-none hover:bg-green-600">
          Update Status
        </button>
      </div>
    </div>
  );
}
