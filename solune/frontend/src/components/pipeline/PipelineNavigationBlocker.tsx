/**
 * PipelineNavigationBlocker — SPA navigation blocker modal.
 * Shown when react-router navigation is blocked due to unsaved pipeline changes.
 */

import { Button } from '@/components/ui/button';

interface PipelineNavigationBlockerProps {
  isBlocked: boolean;
  onStay: () => void;
  onLeave: () => void;
}

export function PipelineNavigationBlocker({
  isBlocked,
  onStay,
  onLeave,
}: PipelineNavigationBlockerProps) {
  if (!isBlocked) return null;

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" role="presentation" />
      <div className="relative z-10 mx-4 w-full max-w-sm rounded-lg border border-border bg-background p-6 text-center shadow-xl">
        <h3 className="mb-2 text-lg font-semibold text-foreground">Unsaved Changes</h3>
        <p className="mb-4 text-sm text-muted-foreground">
          You have unsaved changes — are you sure you want to leave?
        </p>
        <div className="flex justify-center gap-3">
          <Button variant="outline" onClick={onStay}>
            Stay
          </Button>
          <Button variant="destructive" onClick={onLeave}>
            Discard and Leave
          </Button>
        </div>
      </div>
    </div>
  );
}
