/**
 * RefreshButton component with spinning animation and tooltip.
 */

import { RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

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
    <Button
      variant="ghost"
      size="icon"
      onClick={onRefresh}
      disabled={disabled || isRefreshing}
      title="Auto-refreshes every 5 minutes"
      aria-label="Refresh board data"
      className="h-8 w-8"
    >
      <RefreshCw
        className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`}
      />
    </Button>
  );
}
