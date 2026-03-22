/**
 * ToolChips — renders selected MCP tools as removable chips on the agent form.
 */

import { X, Wrench } from '@/lib/icons';
import type { ToolChip as ToolChipType } from '@/types';

interface ToolChipsProps {
  tools: ToolChipType[];
  onRemove: (toolId: string) => void;
  onAddClick: () => void;
}

export function ToolChips({ tools, onRemove, onAddClick }: ToolChipsProps) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {tools.map((tool) => (
        <span
          key={tool.id}
          className="solar-chip inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold"
          title={tool.description}
        >
          <Wrench className="h-3 w-3" />
          {tool.name}
          <button
            type="button"
            onClick={() => onRemove(tool.id)}
            className="ml-0.5 rounded-full p-0.5 hover:bg-primary/20"
            aria-label={`Remove ${tool.name}`}
          >
            <X className="h-3 w-3" />
          </button>
        </span>
      ))}
      <button
        type="button"
        onClick={onAddClick}
        className="inline-flex items-center gap-1 rounded-full border border-dashed border-border bg-background/72 px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:border-primary hover:bg-primary/10 hover:text-primary"
      >
        <Wrench className="h-3 w-3" />
        {tools.length === 0 ? 'Add Tools' : '+ Add more'}
      </button>
    </div>
  );
}
