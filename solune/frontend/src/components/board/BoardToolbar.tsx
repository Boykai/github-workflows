/**
 * BoardToolbar component — Filter, Sort, and Group By controls for the Project Board.
 * Operates on parent issues only. Each panel is mutually exclusive.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { Filter, ArrowUpDown, Columns3, Search, X } from '@/lib/icons';
import { Tooltip } from '@/components/ui/tooltip';
import { useMediaQuery } from '@/hooks/useMediaQuery';
import type { BoardFilterState, BoardSortState, BoardGroupState } from '@/hooks/useBoardControls';
import { cn } from '@/lib/utils';

type ActivePanel = 'filter' | 'sort' | 'group' | null;

interface BoardToolbarProps {
  filters: BoardFilterState;
  sort: BoardSortState;
  group: BoardGroupState;
  onFiltersChange: (f: BoardFilterState) => void;
  onSortChange: (s: BoardSortState) => void;
  onGroupChange: (g: BoardGroupState) => void;
  onClearAll: () => void;
  availableLabels: string[];
  availableAssignees: string[];
  availableMilestones: string[];
  availablePipelineConfigs?: string[];
  hasActiveFilters: boolean;
  hasActiveSort: boolean;
  hasActiveGroup: boolean;
  hasActiveControls: boolean;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
}

function ToolbarButton({
  icon: Icon,
  label,
  isActive,
  hasIndicator,
  onClick,
  iconOnly = false,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  isActive: boolean;
  hasIndicator: boolean;
  onClick: () => void;
  iconOnly?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={cn('relative flex items-center gap-1.5 rounded-full border px-4 py-2 text-xs font-medium uppercase tracking-[0.16em] transition-colors', isActive
          ? 'border-primary/50 bg-primary/10 text-primary'
          : 'border-border/70 bg-background/50 hover:bg-accent/45',
        iconOnly && 'px-2.5')}
      type="button"
      title={iconOnly ? label : undefined}
      aria-label={iconOnly ? label : undefined}
    >
      <Icon className="w-3.5 h-3.5" />
      {!iconOnly && label}
      {hasIndicator && (
        <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-primary" />
      )}
    </button>
  );
}

function CheckboxList({
  title,
  options,
  selected,
  onChange,
}: {
  title: string;
  options: string[];
  selected: string[];
  onChange: (v: string[]) => void;
}) {
  if (options.length === 0) return null;

  const toggle = (item: string) => {
    onChange(selected.includes(item) ? selected.filter((s) => s !== item) : [...selected, item]);
  };

  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </span>
      <div className="flex flex-col gap-0.5 max-h-40 overflow-y-auto">
        {options.map((opt) => (
          <label
            key={opt}
            className="flex items-center gap-2 px-2 py-1 rounded hover:bg-muted/50 cursor-pointer text-xs"
          >
            <input
              type="checkbox"
              checked={selected.includes(opt)}
              onChange={() => toggle(opt)}
              className="rounded border-border"
            />
            <span className="truncate">{opt}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

function RadioList({
  options,
  selected,
  onChange,
}: {
  options: { value: string; label: string }[];
  selected: string | null;
  onChange: (v: string | null) => void;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      {options.map((opt) => (
        <label
          key={opt.value}
          className="flex items-center gap-2 px-2 py-1 rounded hover:bg-muted/50 cursor-pointer text-xs"
        >
          <input
            type="radio"
            name="board-control-radio"
            checked={selected === opt.value}
            onChange={() => onChange(opt.value)}
            className="border-border"
          />
          <span>{opt.label}</span>
        </label>
      ))}
    </div>
  );
}

export function BoardToolbar({
  filters,
  sort,
  group,
  onFiltersChange,
  onSortChange,
  onGroupChange,
  onClearAll,
  availableLabels,
  availableAssignees,
  availableMilestones,
  availablePipelineConfigs = [],
  hasActiveFilters,
  hasActiveSort,
  hasActiveGroup,
  hasActiveControls,
  searchQuery = '',
  onSearchChange,
}: BoardToolbarProps) {
  const [activePanel, setActivePanel] = useState<ActivePanel>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const isMobile = useMediaQuery('(max-width: 767px)');

  const togglePanel = useCallback((panel: ActivePanel) => {
    setActivePanel((prev) => (prev === panel ? null : panel));
  }, []);

  // Close panel on outside click
  useEffect(() => {
    if (!activePanel) return undefined;
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setActivePanel(null);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [activePanel]);

  // Close on Escape
  useEffect(() => {
    if (!activePanel) return undefined;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setActivePanel(null);
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [activePanel]);

  return (
    <div className="relative flex items-center gap-2 shrink-0 flex-wrap" ref={panelRef}>
      {onSearchChange && (
        <div className="relative flex items-center">
          <Search className="absolute left-2.5 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search issues…"
            aria-label="Search issues"
            className="h-8 rounded-full border border-border/70 bg-background/50 pl-8 pr-3 text-xs placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-primary/40 w-40 sm:w-52"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => onSearchChange('')}
              className="absolute right-2 text-muted-foreground hover:text-foreground"
              aria-label="Clear search"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      )}
      <ToolbarButton
        icon={Filter}
        label="Filter"
        isActive={activePanel === 'filter'}
        hasIndicator={hasActiveFilters}
        onClick={() => togglePanel('filter')}
        iconOnly={isMobile}
      />
      <ToolbarButton
        icon={ArrowUpDown}
        label={sort.field ? `Sort: ${sort.field}` : 'Sort'}
        isActive={activePanel === 'sort'}
        hasIndicator={hasActiveSort}
        onClick={() => togglePanel('sort')}
        iconOnly={isMobile}
      />
      <ToolbarButton
        icon={Columns3}
        label={group.field ? `Group: ${group.field}` : 'Group by'}
        isActive={activePanel === 'group'}
        hasIndicator={hasActiveGroup}
        onClick={() => togglePanel('group')}
        iconOnly={isMobile}
      />

      {hasActiveControls && (
        <Tooltip contentKey="board.toolbar.clearAllButton">
          <button
            onClick={onClearAll}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            type="button"
          >
            <X className="w-3 h-3" />
            Clear
          </button>
        </Tooltip>
      )}

      {/* Filter Panel */}
      {activePanel === 'filter' && (
        <div className="absolute left-0 top-full mt-2 z-50 w-72 rounded-lg border border-border bg-card shadow-lg p-4 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">Filters</span>
            {hasActiveFilters && (
              <button
                onClick={() => onFiltersChange({ labels: [], assignees: [], milestones: [], priority: [], pipelineConfig: null })}
                className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                type="button"
              >
                Clear All
              </button>
            )}
          </div>
          <CheckboxList
            title="Labels"
            options={availableLabels}
            selected={filters.labels}
            onChange={(labels) => onFiltersChange({ ...filters, labels })}
          />
          <CheckboxList
            title="Assignees"
            options={availableAssignees}
            selected={filters.assignees}
            onChange={(assignees) => onFiltersChange({ ...filters, assignees })}
          />
          <CheckboxList
            title="Milestones"
            options={availableMilestones}
            selected={filters.milestones}
            onChange={(milestones) => onFiltersChange({ ...filters, milestones })}
          />
          <CheckboxList
            title="Priority"
            options={['P0', 'P1', 'P2', 'P3']}
            selected={filters.priority}
            onChange={(priority) => onFiltersChange({ ...filters, priority })}
          />
          {availablePipelineConfigs.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                Pipeline Config
              </span>
              <select
                className="rounded-md border border-border bg-background px-2 py-1 text-xs"
                value={filters.pipelineConfig ?? ''}
                onChange={(e) =>
                  onFiltersChange({
                    ...filters,
                    pipelineConfig: e.target.value || null,
                  })
                }
              >
                <option value="">All pipelines</option>
                {availablePipelineConfigs.map((cfg) => (
                  <option key={cfg} value={cfg}>
                    {cfg}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}

      {/* Sort Panel */}
      {activePanel === 'sort' && (
        <div className="absolute left-0 top-full mt-2 z-50 w-64 rounded-lg border border-border bg-card shadow-lg p-4 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">Sort</span>
            {hasActiveSort && (
              <button
                onClick={() => onSortChange({ field: null, direction: 'asc' })}
                className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                type="button"
              >
                Clear Sort
              </button>
            )}
          </div>
          <RadioList
            options={[
              { value: 'created', label: 'Created Date' },
              { value: 'updated', label: 'Updated Date' },
              { value: 'priority', label: 'Priority' },
              { value: 'title', label: 'Title' },
            ]}
            selected={sort.field}
            onChange={(field) => onSortChange({ ...sort, field: field as BoardSortState['field'] })}
          />
          <div className="flex items-center gap-2 pt-1 border-t border-border/50">
            <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              Direction
            </span>
            <button
              className={cn('px-2 py-0.5 text-xs rounded', sort.direction === 'asc' ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground hover:text-foreground')}
              onClick={() => onSortChange({ ...sort, direction: 'asc' })}
              type="button"
            >
              Asc
            </button>
            <button
              className={cn('px-2 py-0.5 text-xs rounded', sort.direction === 'desc' ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground hover:text-foreground')}
              onClick={() => onSortChange({ ...sort, direction: 'desc' })}
              type="button"
            >
              Desc
            </button>
          </div>
        </div>
      )}

      {/* Group By Panel */}
      {activePanel === 'group' && (
        <div className="absolute left-0 top-full mt-2 z-50 w-56 rounded-lg border border-border bg-card shadow-lg p-4 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">Group By</span>
            {hasActiveGroup && (
              <button
                onClick={() => onGroupChange({ field: null })}
                className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                type="button"
              >
                Remove Grouping
              </button>
            )}
          </div>
          <RadioList
            options={[
              { value: 'label', label: 'Label' },
              { value: 'assignee', label: 'Assignee' },
              { value: 'milestone', label: 'Milestone' },
            ]}
            selected={group.field}
            onChange={(field) => onGroupChange({ field: field as BoardGroupState['field'] })}
          />
        </div>
      )}
    </div>
  );
}
