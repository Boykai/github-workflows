/**
 * CommandAutocomplete component — overlay above chat input showing matching commands.
 * Supports keyboard navigation (ArrowUp/Down, Enter, Escape, Tab) and mouse click.
 * Commands are grouped by category ('Solune' and 'GitHub Copilot') with section headers.
 */

import { useEffect, useMemo, useRef } from 'react';
import type { CommandDefinition } from '@/lib/commands/types';
import { cn } from '@/lib/utils';

interface CommandAutocompleteProps {
  commands: CommandDefinition[];
  highlightedIndex: number;
  onSelect: (command: CommandDefinition) => void;
  onDismiss: () => void;
  onHighlightChange: (index: number) => void;
}

/** Category display labels. */
const CATEGORY_LABELS: Record<string, string> = {
  solune: 'Solune',
  copilot: 'GitHub Copilot',
};

/** Order in which categories appear. */
const CATEGORY_ORDER = ['solune', 'copilot'] as const;

export function CommandAutocomplete({
  commands,
  highlightedIndex,
  onSelect,
  // onDismiss is handled by the parent component
  onHighlightChange,
}: CommandAutocompleteProps) {
  const listRef = useRef<HTMLUListElement>(null);

  // Group commands by category
  const grouped = useMemo(() => {
    const groups: { category: string; label: string; commands: CommandDefinition[] }[] = [];
    for (const cat of CATEGORY_ORDER) {
      const cmds = commands.filter((c) => (c.category ?? 'solune') === cat);
      if (cmds.length > 0) {
        groups.push({ category: cat, label: CATEGORY_LABELS[cat] ?? cat, commands: cmds });
      }
    }
    return groups;
  }, [commands]);

  const hasMultipleCategories = grouped.length > 1;

  // Scroll highlighted item into view
  useEffect(() => {
    if (listRef.current && highlightedIndex >= 0) {
      const items = listRef.current.querySelectorAll('[role="option"]');
      items[highlightedIndex]?.scrollIntoView({ block: 'nearest' });
    }
  }, [highlightedIndex]);

  if (commands.length === 0) return null;

  const activeId = highlightedIndex >= 0 ? `cmd-option-${highlightedIndex}` : undefined;

  // Build a flat index to map grouped rendering back to the overall command index
  let flatIndex = 0;

  return (
    <div className="absolute bottom-full left-0 right-0 mb-1 z-50" role="presentation">
      <ul
        ref={listRef}
        role="listbox"
        aria-label="Command suggestions"
        aria-activedescendant={activeId}
        tabIndex={-1}
        className="max-h-60 overflow-y-auto rounded-lg border border-border bg-popover py-1 shadow-lg backdrop-blur-sm"
      >
        {grouped.map((group) => {
          const items = group.commands.map((cmd) => {
            const index = flatIndex++;
            return (
              <li
                key={cmd.name}
                id={`cmd-option-${index}`}
                role="option"
                aria-selected={index === highlightedIndex}
                className={cn('px-3 py-2 cursor-pointer flex items-center gap-2 text-sm transition-colors', index === highlightedIndex
                    ? 'bg-primary/10 text-foreground'
                    : 'text-foreground hover:bg-primary/10')}
                onMouseDown={(e) => {
                  e.preventDefault();
                  onSelect(cmd);
                }}
                onMouseEnter={() => onHighlightChange(index)}
              >
                <span className="font-mono font-medium text-primary">/{cmd.name}</span>
                <span className="text-muted-foreground truncate">{cmd.description}</span>
              </li>
            );
          });

          return (
            <li key={group.category} role="presentation">
              {hasMultipleCategories && (
                <div className="px-3 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider select-none">
                  {group.label}
                </div>
              )}
              <ul role="group" aria-label={group.label}>
                {items}
              </ul>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
