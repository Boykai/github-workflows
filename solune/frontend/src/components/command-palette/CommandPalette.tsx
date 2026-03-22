/**
 * CommandPalette — accessible overlay for global search and quick navigation.
 *
 * Implements the WAI-ARIA Combobox pattern with keyboard navigation,
 * categorized results, and focus management.
 */

import { useEffect, useRef, useCallback } from 'react';
import { Loader2 } from '@/lib/icons';
import { cn } from '@/lib/utils';
import {
  useCommandPalette,
  CATEGORY_META,
  type CommandPaletteItem,
  type CommandCategory,
} from '@/hooks/useCommandPalette';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string | null;
}

/** Maximum visible results before scrolling. */
const MAX_VISIBLE_RESULTS = 15;
/** Approximate height per result item (px) for max-height calculation. */
const RESULT_ITEM_HEIGHT = 44;
/** Category header height (px). */
const CATEGORY_HEADER_HEIGHT = 32;

export function CommandPalette({ isOpen, onClose, projectId }: CommandPaletteProps) {
  const {
    query,
    setQuery,
    results,
    selectedIndex,
    moveUp,
    moveDown,
    selectCurrent,
    isLoading,
  } = useCommandPalette({ projectId, isOpen });

  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Auto-focus search input when opening
  useEffect(() => {
    if (isOpen) {
      // Small delay to ensure the DOM is ready
      requestAnimationFrame(() => {
        inputRef.current?.focus();
      });
    }
  }, [isOpen]);

  // Scroll selected item into view
  useEffect(() => {
    if (!listRef.current) return;
    const selectedEl = listRef.current.querySelector('[aria-selected="true"]');
    if (selectedEl) {
      selectedEl.scrollIntoView({ block: 'nearest' });
    }
  }, [selectedIndex]);

  // Keyboard handler for the input (arrows + Enter)
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          moveDown();
          break;
        case 'ArrowUp':
          e.preventDefault();
          moveUp();
          break;
        case 'Enter':
          e.preventDefault();
          selectCurrent();
          onClose();
          break;
      }
    },
    [moveDown, moveUp, selectCurrent, onClose],
  );

  // Handle Ctrl+K when palette is already open — select all text
  useEffect(() => {
    if (!isOpen) return;
    const handleGlobalKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.select();
      }
    };
    document.addEventListener('keydown', handleGlobalKey);
    return () => document.removeEventListener('keydown', handleGlobalKey);
  }, [isOpen]);

  // Document-level Escape handling and focus trapping
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Escape — close palette regardless of which inner element has focus
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
        return;
      }

      // Tab — trap focus within the dialog
      if (e.key === 'Tab' && dialogRef.current) {
        const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [tabindex]:not([tabindex="-1"]), a[href], input, select, textarea',
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Group results by category
  const groupedResults = groupByCategory(results);

  // Compute max-height for results area
  const maxItems = MAX_VISIBLE_RESULTS;
  const maxResultsHeight =
    maxItems * RESULT_ITEM_HEIGHT + groupedResults.length * CATEGORY_HEADER_HEIGHT;

  // Build a flat index map for aria-selected
  let flatIndex = 0;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-[9998] bg-black/50 backdrop-blur-sm celestial-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Dialog */}
      <div
        ref={dialogRef}
        className="fixed inset-0 z-[9999] flex items-start justify-center p-4 pt-[15vh]"
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
      >
        <div className="celestial-panel celestial-fade-in w-full max-w-lg rounded-2xl border border-border/80 bg-card shadow-xl">
          {/* Search input */}
          <div className="flex items-center gap-3 border-b border-border/70 px-4 py-3">
            <svg
              className="h-5 w-5 shrink-0 text-muted-foreground"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search commands, pages, agents..."
              className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none"
              aria-label="Search commands"
              aria-expanded={results.length > 0}
              aria-controls="palette-results"
              aria-activedescendant={
                results.length > 0 ? `palette-item-${selectedIndex}` : undefined
              }
              role="combobox"
              aria-autocomplete="list"
            />
            <kbd className="hidden sm:inline-flex min-w-[1.75rem] items-center justify-center rounded-md border border-border bg-muted px-1.5 py-0.5 text-xs font-medium text-muted-foreground">
              Esc
            </kbd>
          </div>

          {/* Results area */}
          <div
            ref={listRef}
            id="palette-results"
            role="listbox"
            aria-label="Search results"
            className="overflow-y-auto overscroll-contain"
            style={{ maxHeight: `${maxResultsHeight}px` }}
          >
            {/* Loading state */}
            {isLoading && query.trim() && results.length === 0 && (
              <div className="flex items-center justify-center gap-2 px-4 py-8 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Loading...</span>
              </div>
            )}

            {/* No results */}
            {!isLoading && query.trim() && results.length === 0 && (
              <div className="px-4 py-8 text-center text-sm text-muted-foreground">
                No results found for &ldquo;{query}&rdquo;
              </div>
            )}

            {/* Empty state (no query) */}
            {!query.trim() && (
              <div className="px-4 py-6 text-center text-sm text-muted-foreground">
                Start typing to search...
              </div>
            )}

            {/* Grouped results */}
            {groupedResults.map(([category, items]) => {
              const meta = CATEGORY_META[category];
              const CategoryIcon = meta.icon;
              return (
                <div key={category}>
                  {/* Category header */}
                  <div
                    className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5"
                    role="presentation"
                  >
                    <CategoryIcon className="h-3.5 w-3.5" />
                    {meta.label}
                  </div>
                  {/* Items */}
                  {items.map((item) => {
                    const itemIndex = flatIndex++;
                    const isSelected = itemIndex === selectedIndex;
                    return (
                      <ResultItem
                        key={item.id}
                        item={item}
                        index={itemIndex}
                        isSelected={isSelected}
                        onClick={() => {
                          item.action();
                          onClose();
                        }}
                      />
                    );
                  })}
                </div>
              );
            })}
          </div>

          {/* Footer hint */}
          {results.length > 0 && (
            <div className="border-t border-border/70 px-4 py-2 text-xs text-muted-foreground flex items-center gap-3">
              <span className="flex items-center gap-1">
                <kbd className="inline-flex min-w-[1.25rem] items-center justify-center rounded border border-border bg-muted px-1 py-0.5 text-[10px] font-medium">
                  ↑
                </kbd>
                <kbd className="inline-flex min-w-[1.25rem] items-center justify-center rounded border border-border bg-muted px-1 py-0.5 text-[10px] font-medium">
                  ↓
                </kbd>
                navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="inline-flex min-w-[1.25rem] items-center justify-center rounded border border-border bg-muted px-1 py-0.5 text-[10px] font-medium">
                  ↵
                </kbd>
                select
              </span>
              <span className="flex items-center gap-1">
                <kbd className="inline-flex min-w-[1.25rem] items-center justify-center rounded border border-border bg-muted px-1 py-0.5 text-[10px] font-medium">
                  esc
                </kbd>
                close
              </span>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

// ============ Internal Components ============

interface ResultItemProps {
  item: CommandPaletteItem;
  index: number;
  isSelected: boolean;
  onClick: () => void;
}

function ResultItem({ item, index, isSelected, onClick }: ResultItemProps) {
  const Icon = item.icon;
  return (
    <div
      id={`palette-item-${index}`}
      role="option"
      aria-selected={isSelected}
      tabIndex={-1}
      className={cn(
        'flex w-full cursor-pointer items-center gap-3 px-4 py-2.5 text-sm transition-colors text-left',
        isSelected
          ? 'bg-primary/10 text-foreground ring-1 ring-inset ring-primary/30'
          : 'text-foreground/80 hover:bg-muted/50',
      )}
      onMouseDown={(e) => {
        e.preventDefault();
        onClick();
      }}
    >
      <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
      <div className="flex-1 min-w-0">
        <span className="truncate">{item.label}</span>
        {item.description && (
          <span className="ml-2 text-xs text-muted-foreground">{item.description}</span>
        )}
      </div>
    </div>
  );
}

// ============ Helpers ============

function groupByCategory(
  items: CommandPaletteItem[],
): [CommandCategory, CommandPaletteItem[]][] {
  const groups = new Map<CommandCategory, CommandPaletteItem[]>();

  for (const item of items) {
    const group = groups.get(item.category);
    if (group) {
      group.push(item);
    } else {
      groups.set(item.category, [item]);
    }
  }

  // Return in canonical category order
  const ordered: [CommandCategory, CommandPaletteItem[]][] = [];
  const categoryOrder: CommandCategory[] = [
    'pages',
    'agents',
    'pipelines',
    'tools',
    'chores',
    'apps',
    'actions',
  ];
  for (const cat of categoryOrder) {
    const group = groups.get(cat);
    if (group && group.length > 0) {
      ordered.push([cat, group]);
    }
  }
  return ordered;
}
