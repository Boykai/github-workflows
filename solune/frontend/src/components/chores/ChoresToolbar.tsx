/**
 * ChoresToolbar — search input, status/schedule filters, sort controls.
 *
 * Extracted from ChoresPanel for single-responsibility.
 */

import { Search } from '@/lib/icons';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

type ChoreStatusFilter = 'all' | 'active' | 'paused';
type ScheduleFilter = 'all' | 'time' | 'count' | 'unscheduled';
type ChoreSortMode = 'attention' | 'updated' | 'name';

interface ChoresToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;
  statusFilter: ChoreStatusFilter;
  onStatusFilterChange: (value: ChoreStatusFilter) => void;
  scheduleFilter: ScheduleFilter;
  onScheduleFilterChange: (value: ScheduleFilter) => void;
  sortMode: ChoreSortMode;
  onSortModeChange: (value: ChoreSortMode) => void;
}

const STATUS_OPTIONS: { value: ChoreStatusFilter; label: string }[] = [
  { value: 'all', label: 'All states' },
  { value: 'active', label: 'Active' },
  { value: 'paused', label: 'Paused' },
];

export type { ChoreStatusFilter, ScheduleFilter, ChoreSortMode };

export function ChoresToolbar({
  search,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  scheduleFilter,
  onScheduleFilterChange,
  sortMode,
  onSortModeChange,
}: ChoresToolbarProps) {
  return (
    <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
      <div>
        <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">
          Catalog controls
        </p>
        <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">
          Filter active routines
        </h4>
      </div>

      <div className="flex flex-col gap-3 xl:min-w-[34rem]">
        <div className="relative">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search by name or template path"
            aria-label="Search chores by name or template path"
            className="moonwell h-12 rounded-full border-border/60 pl-10"
          />
        </div>
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by status">
            {STATUS_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => onStatusFilterChange(option.value)}
                aria-pressed={statusFilter === option.value}
                className={cn(
                  'celestial-focus rounded-full border px-3 py-1.5 text-xs font-medium uppercase tracking-[0.16em] transition-colors focus-visible:outline-none',
                  statusFilter === option.value
                    ? 'solar-chip'
                    : 'solar-chip-soft hover:bg-primary/10 hover:text-foreground'
                )}
              >
                {option.label}
              </button>
            ))}
          </div>

          <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
            <select
              className="celestial-focus moonwell h-10 w-full rounded-full border-border/60 px-4 text-sm text-foreground focus-visible:outline-none sm:w-auto"
              value={scheduleFilter}
              onChange={(event) =>
                onScheduleFilterChange(event.target.value as ScheduleFilter)
              }
              aria-label="Filter chores by schedule"
            >
              <option value="all">All schedules</option>
              <option value="time">Time-based</option>
              <option value="count">Count-based</option>
              <option value="unscheduled">Unscheduled</option>
            </select>
            <select
              className="celestial-focus moonwell h-10 w-full rounded-full border-border/60 px-4 text-sm text-foreground focus-visible:outline-none sm:w-auto"
              value={sortMode}
              onChange={(event) => onSortModeChange(event.target.value as ChoreSortMode)}
              aria-label="Sort chores"
            >
              <option value="attention">Needs attention</option>
              <option value="updated">Recently updated</option>
              <option value="name">Alphabetical</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
