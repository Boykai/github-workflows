/**
 * CommandAutocomplete component — overlay above chat input showing matching commands.
 * Supports keyboard navigation (ArrowUp/Down, Enter, Escape, Tab) and mouse click.
 */

import { useEffect, useRef } from 'react';
import type { CommandDefinition } from '@/lib/commands/types';
import { cn } from '@/lib/utils';

interface CommandAutocompleteProps {
  commands: CommandDefinition[];
  highlightedIndex: number;
  onSelect: (command: CommandDefinition) => void;
  onDismiss: () => void;
  onHighlightChange: (index: number) => void;
}

export function CommandAutocomplete({
  commands,
  highlightedIndex,
  onSelect,
  // onDismiss is handled by the parent component
  onHighlightChange,
}: CommandAutocompleteProps) {
  const listRef = useRef<HTMLUListElement>(null);

  // Scroll highlighted item into view
  useEffect(() => {
    if (listRef.current && highlightedIndex >= 0) {
      const items = listRef.current.querySelectorAll('[role="option"]');
      items[highlightedIndex]?.scrollIntoView({ block: 'nearest' });
    }
  }, [highlightedIndex]);

  if (commands.length === 0) return null;

  const activeId = highlightedIndex >= 0 ? `cmd-option-${highlightedIndex}` : undefined;

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
        {commands.map((cmd, index) => (
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
        ))}
      </ul>
    </div>
  );
}
