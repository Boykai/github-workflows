/**
 * RunNowButton — manual trigger button with cooldown confirmation.
 */

import { useState } from 'react';
import { useRunTask } from '@/hooks/useHousekeeping';
import { ApiError } from '@/services/api';

interface RunNowButtonProps {
  taskId: string;
  taskName: string;
  disabled?: boolean;
}

export function RunNowButton({ taskId, taskName, disabled }: RunNowButtonProps) {
  const runTask = useRunTask();
  const [showCooldownDialog, setShowCooldownDialog] = useState(false);
  const [cooldownInfo, setCooldownInfo] = useState<{
    last_triggered_at: string;
    cooldown_remaining_seconds: number;
  } | null>(null);

  const handleRun = async (force = false) => {
    setShowCooldownDialog(false);
    try {
      await runTask.mutateAsync({ id: taskId, force });
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        // Cooldown conflict — extract cooldown info from error details
        const details = err.error?.details as Record<string, unknown> | undefined;
        const lastTriggered = details?.last_triggered_at;
        const remaining = details?.cooldown_remaining_seconds;
        if (lastTriggered !== undefined) {
          setCooldownInfo({
            last_triggered_at: String(lastTriggered),
            cooldown_remaining_seconds: Number(remaining ?? 0),
          });
          setShowCooldownDialog(true);
        }
      }
    }
  };

  return (
    <div className="relative inline-block">
      <button
        onClick={() => handleRun(false)}
        disabled={disabled || runTask.isPending}
        className="px-3 py-1.5 bg-primary text-primary-foreground rounded text-sm hover:bg-primary/90 disabled:opacity-50"
      >
        {runTask.isPending ? 'Running...' : `🚀 Run Now`}
      </button>

      {showCooldownDialog && cooldownInfo && (
        <div className="absolute top-full mt-2 right-0 z-50 w-72 border rounded-lg p-4 bg-card shadow-lg">
          <h4 className="font-medium text-sm mb-2">⚠️ Cooldown Active</h4>
          <p className="text-xs text-muted-foreground mb-1">
            &quot;{taskName}&quot; was triggered recently.
          </p>
          <p className="text-xs text-muted-foreground mb-3">
            Last run: {new Date(cooldownInfo.last_triggered_at).toLocaleString()}
            <br />
            Cooldown remaining: {Math.ceil(cooldownInfo.cooldown_remaining_seconds / 60)} min
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => handleRun(true)}
              className="px-3 py-1 bg-destructive text-destructive-foreground rounded text-xs"
            >
              Force Run
            </button>
            <button
              onClick={() => setShowCooldownDialog(false)}
              className="px-3 py-1 border rounded text-xs"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
