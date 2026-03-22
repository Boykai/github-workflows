/**
 * RefreshButton component with spinning animation and tooltip.
 */

import { RefreshCw } from '@/lib/icons';
import { Button } from '@/components/ui/button';
import { Tooltip } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface RefreshButtonProps {
  /** Callback to trigger manual refresh */
  onRefresh: () => void;
  /** Whether a refresh is currently in progress */
  isRefreshing: boolean;
  /** Whether the button should be disabled */
  disabled?: boolean;
}

export function RefreshButton({ onRefresh, isRefreshing, disabled }: RefreshButtonProps) {
  return (
    <Tooltip contentKey="board.toolbar.refreshButton">
      <Button
        variant="ghost"
        size="icon"
        onClick={onRefresh}
        disabled={disabled || isRefreshing}
        aria-label="Refresh board data"
        className="h-8 w-8"
      >
        <RefreshCw className={cn('h-4 w-4', isRefreshing ? 'animate-spin' : '')} />
      </Button>
    </Tooltip>
  );
}
