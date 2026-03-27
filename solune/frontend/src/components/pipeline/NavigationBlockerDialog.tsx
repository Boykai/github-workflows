/**
 * NavigationBlockerDialog — Modal shown when SPA navigation is blocked
 * due to unsaved pipeline changes.
 *
 * Extracted from AgentsPipelinePage to keep the page ≤ 250 lines (FR-001).
 */

import { Button } from '@/components/ui/button';

interface NavigationBlockerDialogProps {
  onStay: () => void;
  onDiscard: () => void;
}

export function NavigationBlockerDialog({ onStay, onDiscard }: NavigationBlockerDialogProps) {
  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center" role="alertdialog" aria-labelledby="blocker-title" aria-describedby="blocker-desc">
      <div className="absolute inset-0 bg-black/50" aria-hidden="true" />
      <div className="relative z-10 mx-4 w-full max-w-sm rounded-lg border border-border bg-background p-6 text-center shadow-xl">
        <h3 id="blocker-title" className="mb-2 text-lg font-semibold text-foreground">Unsaved Changes</h3>
        <p id="blocker-desc" className="mb-4 text-sm text-muted-foreground">
          You have unsaved changes — are you sure you want to leave?
        </p>
        <div className="flex justify-center gap-3">
          <Button variant="outline" onClick={onStay}>
            Stay
          </Button>
          <Button variant="destructive" onClick={onDiscard}>
            Discard and Leave
          </Button>
        </div>
      </div>
    </div>
  );
}
