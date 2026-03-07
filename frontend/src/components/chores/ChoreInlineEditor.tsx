/**
 * ChoreInlineEditor — inline editable fields for a Chore definition.
 *
 * Renders editable input for name, textarea for template_content,
 * and reuses ChoreScheduleConfig for schedule fields.
 */

import type { ChoreInlineUpdate } from '@/types';

interface ChoreInlineEditorProps {
  name: string;
  templateContent: string;
  disabled?: boolean;
  onChange: (updates: Partial<ChoreInlineUpdate>) => void;
}

export function ChoreInlineEditor({
  name,
  templateContent,
  disabled = false,
  onChange,
}: ChoreInlineEditorProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-1.5">
        <label htmlFor={`chore-name-${name}`} className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          Name
        </label>
        <input
          id={`chore-name-${name}`}
          type="text"
          value={name}
          onChange={(e) => onChange({ name: e.target.value })}
          disabled={disabled}
          maxLength={200}
          className="flex h-8 w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <label htmlFor={`chore-content-${name}`} className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          Template Content
        </label>
        <textarea
          id={`chore-content-${name}`}
          value={templateContent}
          onChange={(e) => onChange({ template_content: e.target.value })}
          disabled={disabled}
          rows={6}
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-xs font-mono shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring resize-y min-h-[80px] disabled:opacity-50"
        />
      </div>
    </div>
  );
}
