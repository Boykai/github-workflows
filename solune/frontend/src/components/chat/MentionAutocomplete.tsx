/**
 * MentionAutocomplete component — floating dropdown for @mention pipeline selection.
 * Follows the CommandAutocomplete ARIA pattern with keyboard and mouse support.
 */

import { useEffect, useRef } from 'react';
import type { MentionFilterResult, PipelineConfigSummary } from '@/types';
import { cn } from '@/lib/utils';

interface MentionAutocompleteProps {
  pipelines: MentionFilterResult[];
  highlightedIndex: number;
  isLoading: boolean;
  isVisible: boolean;
  error?: string | null;
  onSelect: (pipeline: PipelineConfigSummary) => void;
  onDismiss: () => void;
  onHighlightChange: (index: number) => void;
}

export function MentionAutocomplete({
  pipelines,
  highlightedIndex,
  isLoading,
  isVisible,
  error,
  onSelect,
  // onDismiss is handled by the parent component
  onHighlightChange,
}: MentionAutocompleteProps) {
  const listRef = useRef<HTMLUListElement>(null);

  // Scroll highlighted item into view
  useEffect(() => {
    if (listRef.current && highlightedIndex >= 0) {
      const items = listRef.current.querySelectorAll('[role="option"]');
      items[highlightedIndex]?.scrollIntoView({ block: 'nearest' });
    }
  }, [highlightedIndex]);

  if (!isVisible) return null;

  const activeId = highlightedIndex >= 0 ? `mention-option-${highlightedIndex}` : undefined;

  return (
    <div className="absolute bottom-full left-0 right-0 mb-1 z-50" role="presentation">
      <ul
        ref={listRef}
        role="listbox"
        aria-label="Pipeline suggestions"
        aria-activedescendant={activeId}
        tabIndex={-1}
        className="max-h-60 overflow-y-auto rounded-lg border border-border bg-popover py-1 shadow-lg backdrop-blur-sm"
      >
        {isLoading && (
          <li className="px-3 py-2 text-sm text-muted-foreground animate-pulse">
            Loading pipelines…
          </li>
        )}

        {error && !isLoading && (
          <li className="px-3 py-2 text-sm text-destructive">Unable to load pipelines</li>
        )}

        {!isLoading && !error && pipelines.length === 0 && (
          <li className="px-3 py-2 text-sm text-muted-foreground">No pipelines found</li>
        )}

        {!isLoading &&
          !error &&
          pipelines.map(({ pipeline }, index) => (
            <li
              key={pipeline.id}
              id={`mention-option-${index}`}
              role="option"
              aria-selected={index === highlightedIndex}
              className={cn('px-3 py-2 cursor-pointer flex flex-col gap-0.5 text-sm transition-colors', index === highlightedIndex
                  ? 'bg-primary/10 text-foreground'
                  : 'text-foreground hover:bg-primary/10')}
              onMouseDown={(e) => {
                e.preventDefault();
                onSelect(pipeline);
              }}
              onMouseEnter={() => onHighlightChange(index)}
            >
              <span className="font-medium">@{pipeline.name}</span>
              {pipeline.description && (
                <span className="text-muted-foreground text-xs truncate">
                  {pipeline.description}
                </span>
              )}
            </li>
          ))}
      </ul>
    </div>
  );
}
