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
    <div className="ml-11 max-w-[500px] self-start overflow-hidden rounded-lg border border-border bg-background/56">
      <div className="bg-primary text-primary-foreground px-4 py-2 text-xs font-medium">
        <span>Status Change</span>
      </div>

      <div className="p-4">
        <p className="text-sm font-medium text-foreground mb-3">{taskTitle}</p>

        <div className="flex items-center gap-3">
          <span className="px-2.5 py-1 rounded-full border border-border bg-background/72 text-xs font-medium text-muted-foreground">
            {currentStatus}
          </span>
          <span className="text-muted-foreground">→</span>
          <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary border border-primary/20">
            {targetStatus}
          </span>
        </div>
      </div>

      <div className="flex gap-2 border-t border-border bg-background/42 p-3">
        <button
          onClick={onReject}
          className="flex-1 rounded-full border border-border bg-background/72 px-4 py-2 text-sm font-medium cursor-pointer text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground"
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          className="flex-1 py-2 px-4 rounded-md text-sm font-medium cursor-pointer transition-colors bg-primary text-primary-foreground border-none hover:bg-primary/90"
        >
          Update Status
        </button>
      </div>
    </div>
  );
}
