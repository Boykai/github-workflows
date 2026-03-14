/**
 * ChoreScheduleConfig — inline editor for a chore's schedule.
 *
 * Dropdown for schedule type (time/count), numeric input for value,
 * save button calling the update mutation.
 */

import { useState } from 'react';
import { useUpdateChore } from '@/hooks/useChores';
import type { Chore, ScheduleType } from '@/types';

interface ChoreScheduleConfigProps {
  chore: Chore;
  projectId: string;
  onDone?: () => void;
}

export function ChoreScheduleConfig({ chore, projectId, onDone }: ChoreScheduleConfigProps) {
  const [scheduleType, setScheduleType] = useState<ScheduleType | ''>(chore.schedule_type ?? '');
  const [scheduleValue, setScheduleValue] = useState<string>(
    chore.schedule_value?.toString() ?? ''
  );
  const [error, setError] = useState<string | null>(null);

  const updateMutation = useUpdateChore(projectId);

  const handleSave = async () => {
    setError(null);

    if (!scheduleType) {
      setError('Select a schedule type');
      return;
    }

    const numValue = Number(scheduleValue);
    if (!scheduleValue || !Number.isInteger(numValue) || numValue <= 0) {
      setError('Value must be a positive integer');
      return;
    }

    try {
      await updateMutation.mutateAsync({
        choreId: chore.id,
        data: {
          schedule_type: scheduleType as ScheduleType,
          schedule_value: numValue,
        },
      });
      onDone?.();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update schedule';
      setError(message);
    }
  };

  return (
    <div className="flex flex-col gap-2 p-2 rounded-md border border-border bg-background">
      <div className="flex items-center gap-2">
        <select
          value={scheduleType}
          onChange={(e) => setScheduleType(e.target.value as ScheduleType | '')}
          className="celestial-focus h-8 rounded-md border border-input bg-background px-2 text-xs focus:outline-none"
          aria-label="Schedule type"
        >
          <option value="">Select type…</option>
          <option value="time">Time (days)</option>
          <option value="count">Count (issues)</option>
        </select>

        <input
          type="number"
          min={1}
          value={scheduleValue}
          onChange={(e) => setScheduleValue(e.target.value)}
          placeholder={scheduleType === 'time' ? 'Days' : 'Issues'}
          className="celestial-focus h-8 w-20 rounded-md border border-input bg-background px-2 text-xs focus:outline-none"
          aria-label="Schedule value"
        />

        <button
          type="button"
          onClick={handleSave}
          disabled={updateMutation.isPending}
          className="h-8 px-3 text-xs font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {updateMutation.isPending ? 'Saving…' : 'Save'}
        </button>
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
