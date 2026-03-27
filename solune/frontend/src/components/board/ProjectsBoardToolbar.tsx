/**
 * ProjectsBoardToolbar — Toolbar strip with sync status chip, refresh
 * button, last-updated chip, board filter/sort/group controls, and
 * queue-mode / auto-merge toggle buttons.
 *
 * Extracted from ProjectsPage to keep the page under 250 lines.
 */

import { useMemo } from 'react';
import { BoardToolbar } from '@/components/board/BoardToolbar';
import { RefreshButton } from '@/components/board/RefreshButton';
import { formatTimeAgo } from '@/utils/formatTime';
import { cn } from '@/lib/utils';
import { ListOrdered, GitMerge } from '@/lib/icons';
import type {
  BoardFilterState,
  BoardSortState,
  BoardGroupState,
} from '@/hooks/useBoardControls';

// ── Types ───────────────────────────────────────────────────────────────────────

type SyncStatus = 'connected' | 'polling' | 'connecting' | 'disconnected';

/** Subset of the useBoardControls return value consumed by the toolbar. */
interface BoardControlsSlice {
  controls: {
    filters: BoardFilterState;
    sort: BoardSortState;
    group: BoardGroupState;
  };
  setFilters: (f: BoardFilterState) => void;
  setSort: (s: BoardSortState) => void;
  setGroup: (g: BoardGroupState) => void;
  clearAll: () => void;
  availableLabels: string[];
  availableAssignees: string[];
  availableMilestones: string[];
  availablePipelineConfigs: string[];
  hasActiveFilters: boolean;
  hasActiveSort: boolean;
  hasActiveGroup: boolean;
  hasActiveControls: boolean;
}

export interface ProjectsBoardToolbarProps {
  selectedProjectId: string | null;
  syncStatus: SyncStatus;
  onRefresh: () => void;
  isRefreshing: boolean;
  lastUpdated: Date | null;
  syncLastUpdate: Date | null;
  hasBoardData: boolean;
  boardControls: BoardControlsSlice;
  isQueueMode: boolean;
  isAutoMerge: boolean;
  isSettingsUpdating: boolean;
  onToggleQueueMode: () => void;
  onToggleAutoMerge: () => void;
}

// ── Lookup maps ─────────────────────────────────────────────────────────────────

const SYNC_LABELS: Record<SyncStatus, string> = {
  connected: 'Live sync',
  polling: 'Polling',
  connecting: 'Connecting',
  disconnected: 'Offline',
};

const SYNC_TONE: Record<SyncStatus, string> = {
  connected: 'bg-[hsl(var(--sync-connected))]',
  polling: 'bg-[hsl(var(--sync-polling))]',
  connecting: 'bg-[hsl(var(--sync-connecting))]',
  disconnected: 'bg-[hsl(var(--sync-disconnected))]',
};

// ── Component ───────────────────────────────────────────────────────────────────

export function ProjectsBoardToolbar({
  selectedProjectId,
  syncStatus,
  onRefresh,
  isRefreshing,
  lastUpdated,
  syncLastUpdate,
  hasBoardData,
  boardControls,
  isQueueMode,
  isAutoMerge,
  isSettingsUpdating,
  onToggleQueueMode,
  onToggleAutoMerge,
}: ProjectsBoardToolbarProps) {
  const label = SYNC_LABELS[syncStatus];
  const toneClass = SYNC_TONE[syncStatus];

  const updatedAgo = useMemo(
    () => {
      const ts = syncLastUpdate ?? lastUpdated;
      return ts ? formatTimeAgo(ts) : null;
    },
    [syncLastUpdate, lastUpdated],
  );

  return (
    <div className="flex shrink-0 flex-wrap items-center gap-3 text-sm text-muted-foreground">
      {selectedProjectId && (
        <span
          className="solar-chip-soft inline-flex items-center gap-2 rounded-full px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-foreground"
          aria-live="polite"
        >
          <span
            className={cn(
              'h-2.5 w-2.5 rounded-full shadow-[0_0_0_3px_hsl(var(--background)/0.7)]',
              toneClass,
            )}
          />
          {label}
        </span>
      )}

      {selectedProjectId && (
        <RefreshButton onRefresh={onRefresh} isRefreshing={isRefreshing} />
      )}

      {updatedAgo && (
        <span className="rounded-full border border-border/70 bg-background/45 px-3 py-2 text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
          Updated {updatedAgo}
        </span>
      )}

      {selectedProjectId && hasBoardData && (
        <BoardToolbar
          filters={boardControls.controls.filters}
          sort={boardControls.controls.sort}
          group={boardControls.controls.group}
          onFiltersChange={boardControls.setFilters}
          onSortChange={boardControls.setSort}
          onGroupChange={boardControls.setGroup}
          onClearAll={boardControls.clearAll}
          availableLabels={boardControls.availableLabels}
          availableAssignees={boardControls.availableAssignees}
          availableMilestones={boardControls.availableMilestones}
          availablePipelineConfigs={boardControls.availablePipelineConfigs}
          hasActiveFilters={boardControls.hasActiveFilters}
          hasActiveSort={boardControls.hasActiveSort}
          hasActiveGroup={boardControls.hasActiveGroup}
          hasActiveControls={boardControls.hasActiveControls}
        />
      )}

      {selectedProjectId && hasBoardData && (
        <button
          onClick={onToggleQueueMode}
          disabled={isSettingsUpdating}
          className={cn(
            'relative flex items-center gap-1.5 rounded-full border px-4 py-2 text-xs font-medium uppercase tracking-[0.16em] transition-colors',
            isQueueMode
              ? 'border-primary/50 bg-primary/10 text-primary'
              : 'border-border/70 bg-background/50 hover:bg-accent/45',
          )}
          type="button"
          title="Only one pipeline runs at a time — next starts when active reaches In Review or Done"
          aria-label="Toggle queue mode"
          aria-pressed={isQueueMode}
        >
          <ListOrdered className="h-3.5 w-3.5" />
          Queue Mode
        </button>
      )}

      {selectedProjectId && hasBoardData && (
        <button
          onClick={onToggleAutoMerge}
          disabled={isSettingsUpdating}
          className={cn(
            'relative flex items-center gap-1.5 rounded-full border px-4 py-2 text-xs font-medium uppercase tracking-[0.16em] transition-colors',
            isAutoMerge
              ? 'border-primary/50 bg-primary/10 text-primary'
              : 'border-border/70 bg-background/50 hover:bg-accent/45',
          )}
          type="button"
          title="Automatically squash-merge parent PRs when pipelines complete successfully"
          aria-label="Toggle auto merge"
          aria-pressed={isAutoMerge}
        >
          <GitMerge className="h-3.5 w-3.5" />
          Auto Merge
        </button>
      )}
    </div>
  );
}
