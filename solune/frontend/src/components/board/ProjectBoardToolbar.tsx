/**
 * ProjectBoardToolbar — Sync status chip, refresh button, updated timestamp,
 * board filter/sort/group toolbar, and queue/auto-merge toggle buttons.
 *
 * Extracted from ProjectsPage to keep the page ≤ 250 lines (FR-001).
 */

import { useCallback } from 'react';
import { RefreshButton } from '@/components/board/RefreshButton';
import { BoardToolbar } from '@/components/board/BoardToolbar';
import { formatTimeAgo } from '@/utils/formatTime';
import { getSyncStatusLabel, getSyncStatusToneClass } from '@/utils/projectBoardUtils';
import { cn } from '@/lib/utils';
import { ListOrdered, GitMerge } from '@/lib/icons';
import { toast } from 'sonner';
import type { BoardDataResponse, PipelineConfigSummary } from '@/types';
import type {
  BoardFilterState,
  BoardSortState,
  BoardGroupState,
  BoardControlsState,
} from '@/hooks/useBoardControls';

interface BoardControlsProps {
  controls: BoardControlsState;
  setFilters: (filters: BoardFilterState) => void;
  setSort: (sort: BoardSortState) => void;
  setGroup: (group: BoardGroupState) => void;
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

interface ProjectBoardToolbarProps {
  selectedProjectId: string | null;
  boardData: BoardDataResponse | null | undefined;
  syncStatus: 'connected' | 'polling' | 'connecting' | 'disconnected';
  syncLastUpdate: Date | null;
  lastUpdated: Date | null;
  isRefreshing: boolean;
  isFetching: boolean;
  boardLoading: boolean;
  onRefresh: () => void;
  boardControls: BoardControlsProps;
  isQueueMode: boolean;
  isAutoMerge: boolean;
  isSettingsUpdating: boolean;
  updateSettings: (update: { queue_mode?: boolean; auto_merge?: boolean }) => Promise<unknown>;
  savedPipelines: PipelineConfigSummary[] | undefined;
}

export function ProjectBoardToolbar({
  selectedProjectId,
  boardData,
  syncStatus,
  syncLastUpdate,
  lastUpdated,
  isRefreshing,
  isFetching,
  boardLoading,
  onRefresh,
  boardControls,
  isQueueMode,
  isAutoMerge,
  isSettingsUpdating,
  updateSettings,
  savedPipelines,
}: ProjectBoardToolbarProps) {
  const syncStatusLabel = getSyncStatusLabel(syncStatus);
  const syncStatusToneClass = getSyncStatusToneClass(syncStatus);

  const handleToggleQueueMode = useCallback(async () => {
    if (!selectedProjectId) return;
    try {
      await updateSettings({ queue_mode: !isQueueMode });
      toast.success(isQueueMode ? 'Queue mode disabled' : 'Queue mode enabled');
    } catch {
      toast.error('Failed to update queue mode');
    }
  }, [selectedProjectId, isQueueMode, updateSettings]);

  const handleToggleAutoMerge = useCallback(async () => {
    if (!selectedProjectId) return;
    if (!isAutoMerge) {
      const hasPipelines = Array.isArray(savedPipelines) && savedPipelines.length > 0;
      if (hasPipelines) {
        const confirmed = window.confirm(
          `Enable auto-merge for this project? This will also apply to ${savedPipelines.length} existing pipeline(s) and may change how they are merged.`,
        );
        if (!confirmed) return;
      }
    }
    try {
      await updateSettings({ auto_merge: !isAutoMerge });
      toast.success(isAutoMerge ? 'Auto merge disabled' : 'Auto merge enabled');
    } catch {
      toast.error('Failed to update auto merge');
    }
  }, [selectedProjectId, isAutoMerge, updateSettings, savedPipelines]);

  return (
    <div className="flex shrink-0 flex-wrap items-center gap-3 text-sm text-muted-foreground">
      {selectedProjectId && (
        <span
          className="solar-chip-soft inline-flex items-center gap-2 rounded-full px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-foreground"
          aria-live="polite"
        >
          <span
            aria-hidden="true"
            className={cn(
              'h-2.5 w-2.5 rounded-full shadow-[0_0_0_3px_hsl(var(--background)/0.7)]',
              syncStatusToneClass,
            )}
          />
          {syncStatusLabel}
        </span>
      )}

      {selectedProjectId && (
        <RefreshButton
          onRefresh={onRefresh}
          isRefreshing={isRefreshing || (isFetching && !boardLoading)}
        />
      )}

      {(lastUpdated || syncLastUpdate) && (
        <span className="rounded-full border border-border/70 bg-background/45 px-3 py-2 text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
          Updated {formatTimeAgo(syncLastUpdate ?? lastUpdated!)}
        </span>
      )}

      {selectedProjectId && boardData && (
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

      {selectedProjectId && boardData && (
        <button
          onClick={handleToggleQueueMode}
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
          <ListOrdered aria-hidden="true" className="h-3.5 w-3.5" />
          Queue Mode
        </button>
      )}

      {selectedProjectId && boardData && (
        <button
          onClick={handleToggleAutoMerge}
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
          <GitMerge aria-hidden="true" className="h-3.5 w-3.5" />
          Auto Merge
        </button>
      )}
    </div>
  );
}
