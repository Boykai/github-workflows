/**
 * Drag-and-drop overlay component.
 * Shows dashed border overlay with "Drop files here" text during drag.
 */

interface DragDropOverlayProps {
  isDragging: boolean;
}

export function DragDropOverlay({ isDragging }: DragDropOverlayProps) {
  if (!isDragging) return null;

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-primary/5 border-2 border-dashed border-primary rounded-lg pointer-events-none">
      <div className="flex flex-col items-center gap-2 text-primary">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="32" height="32">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <span className="text-sm font-medium">Drop files here</span>
      </div>
    </div>
  );
}
