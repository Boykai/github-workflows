/**
 * BoardEmptyState — Empty state display for the project board.
 * Shows different messages based on whether filters are active.
 */

import { Inbox, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface BoardEmptyStateProps {
  hasActiveControls: boolean;
  onClearAll: () => void;
}

export function BoardEmptyState({ hasActiveControls, onClearAll }: BoardEmptyStateProps) {
  return (
    <div className="celestial-panel flex min-h-[32rem] flex-1 flex-col items-center justify-center gap-4 rounded-[1.4rem] border border-dashed border-border/80 p-8 text-center sm:min-h-[40rem]">
      {hasActiveControls ? (
        <>
          <Search aria-hidden="true" className="mb-2 h-10 w-10 text-primary/80" />
          <h3 className="text-xl font-semibold">No issues match the current view</h3>
          <p className="text-muted-foreground">
            Try adjusting your filter, sort, or group settings.
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={onClearAll}
            className="mt-2"
            type="button"
          >
            Clear all filters
          </Button>
        </>
      ) : (
        <>
          <Inbox aria-hidden="true" className="mb-2 h-10 w-10 text-primary/70" />
          <h3 className="text-xl font-semibold">No items yet</h3>
          <p className="text-muted-foreground">
            This project has no items. Add items in GitHub to see them here.
          </p>
        </>
      )}
    </div>
  );
}
