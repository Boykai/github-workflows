/**
 * ChoreInlineEditor — inline editable fields for a Chore definition.
 *
 * Renders editable input for name, textarea for template_content,
 * and reuses ChoreScheduleConfig for schedule fields.
 */

import type { ChoreInlineUpdate } from '@/types';
import { Lock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChoreInlineEditorProps {
  choreId: string;
  name: string;
  templateContent: string;
  scheduleType: ChoreInlineUpdate['schedule_type'];
  scheduleValue: number | null | undefined;
  blocking: boolean;
  disabled?: boolean;
  onChange: (updates: Partial<ChoreInlineUpdate>) => void;
}

export function ChoreInlineEditor({
  choreId,
  name,
  templateContent,
  scheduleType,
  scheduleValue,
  blocking,
  disabled = false,
  onChange,
}: ChoreInlineEditorProps) {
  const nameId = `chore-name-${choreId}`;
  const contentId = `chore-content-${choreId}`;
  const scheduleTypeId = `chore-schedule-type-${choreId}`;
  const scheduleValueId = `chore-schedule-value-${choreId}`;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor={nameId}
          className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground"
        >
          Name
        </label>
        <input
          id={nameId}
          type="text"
          value={name}
          onChange={(e) => onChange({ name: e.target.value })}
          disabled={disabled}
          maxLength={200}
          className="celestial-focus flex h-8 w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor={contentId}
          className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground"
        >
          Template Content
        </label>
        <textarea
          id={contentId}
          value={templateContent}
          onChange={(e) => onChange({ template_content: e.target.value })}
          disabled={disabled}
          rows={6}
          className="celestial-focus flex w-full rounded-md border border-input bg-background px-3 py-2 text-xs font-mono shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring resize-y min-h-[80px] disabled:opacity-50"
        />
      </div>
      <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_9rem]">
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor={scheduleTypeId}
            className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground"
          >
            Schedule Type
          </label>
          <select
            id={scheduleTypeId}
            value={scheduleType ?? ''}
            onChange={(e) =>
              onChange({
                schedule_type: (e.target.value || null) as ChoreInlineUpdate['schedule_type'],
              })
            }
            disabled={disabled}
            className="celestial-focus flex h-8 w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
          >
            <option value="">No schedule</option>
            <option value="time">Time (days)</option>
            <option value="count">Count (issues)</option>
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor={scheduleValueId}
            className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground"
          >
            Schedule Value
          </label>
          <input
            id={scheduleValueId}
            type="number"
            min={1}
            value={scheduleValue ?? ''}
            onChange={(e) =>
              onChange({ schedule_value: e.target.value === '' ? null : Number(e.target.value) })
            }
            disabled={disabled || !scheduleType}
            className="celestial-focus flex h-8 w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
          />
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          Execution Mode
        </span>
        <button
          type="button"
          onClick={() => onChange({ blocking: !blocking })}
          disabled={disabled}
          className={cn(
            'flex w-fit items-center gap-1 rounded-full border px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.14em] transition-colors disabled:opacity-50',
            blocking
              ? 'border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400'
              : 'border-border/60 bg-muted/40 text-muted-foreground'
          )}
          aria-label={blocking ? 'Blocking' : 'Non-blocking'}
          title={`Blocking: ${blocking ? 'ON — issues serialize activation' : 'OFF'}`}
        >
          <Lock className="h-3 w-3" />
          {blocking ? 'Blocking' : 'Non-blocking'}
        </button>
      </div>
    </div>
  );
}
