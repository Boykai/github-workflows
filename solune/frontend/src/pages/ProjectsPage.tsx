/**
 * ProjectsPage — Project board with enhanced Kanban view.
 * Migrated from ProjectBoardPage with page header, toolbar, and enhanced cards.
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { CelestialLoadingProgress } from '@/components/common/CelestialLoadingProgress';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRateLimitStatus } from '@/context/RateLimitContext';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useRealTimeSync } from '@/hooks/useRealTimeSync';
import { useBoardRefresh } from '@/hooks/useBoardRefresh';
import { useProjects } from '@/hooks/useProjects';
import { useAuth } from '@/hooks/useAuth';
import { useProjectSettings } from '@/hooks/useSettings';
import { IssueDetailModal } from '@/components/board/IssueDetailModal';
import { BoardToolbar } from '@/components/board/BoardToolbar';
import { ProjectIssueLaunchPanel } from '@/components/board/ProjectIssueLaunchPanel';
import { RefreshButton } from '@/components/board/RefreshButton';
import { PipelineStagesSection } from '@/components/board/PipelineStagesSection';
import { ProjectBoardErrorBanners } from '@/components/board/ProjectBoardErrorBanners';
import { ProjectBoardContent } from '@/components/board/ProjectBoardContent';
import { ProjectSelectionEmptyState } from '@/components/common/ProjectSelectionEmptyState';
import { useAvailableAgents } from '@/hooks/useAgentConfig';
import { useBoardControls } from '@/hooks/useBoardControls';
import { formatTimeAgo } from '@/utils/formatTime';
import { extractRateLimitInfo, isRateLimitApiError } from '@/utils/rateLimit';
import { cn } from '@/lib/utils';
import type { BoardItem, BoardDataResponse } from '@/types';
import { boardApi, pipelinesApi } from '@/services/api';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { Button } from '@/components/ui/button';
import { ListOrdered, GitMerge } from '@/lib/icons';
import { toast } from 'sonner';

export function ProjectsPage() {
  const { updateRateLimit } = useRateLimitStatus();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const {
    selectedProject,
    projects,
    isLoading: projectsListLoading,
    selectProject,
  } = useProjects(user?.selected_project_id);

  const {
    projectsRateLimitInfo,
    projectsLoading,
    projectsError,
    selectedProjectId,
    boardData,
    boardLoading,
    isFetching,
    boardError,
    lastUpdated,
    selectProject: selectBoardProject,
  } = useProjectBoard({
    selectedProjectId: selectedProject?.project_id,
    onProjectSelect: selectProject,
  });

  // Stable ref for the board-refresh resetTimer callback so that
  // useRealTimeSync can be called before useBoardRefresh without a stale
  // closure.  The ref is updated after useBoardRefresh returns.
  const resetTimerRef = useRef<() => void>(() => {});
  const stableResetTimer = useCallback(() => resetTimerRef.current(), []);

  const { status: syncStatus, lastUpdate: syncLastUpdate } = useRealTimeSync(selectedProjectId, {
    onRefreshTriggered: stableResetTimer,
  });

  const isWebSocketConnected = syncStatus === 'connected';

  const {
    refresh,
    isRefreshing,
    error: refreshError,
    rateLimitInfo,
    isRateLimitLow,
    resetTimer,
  } = useBoardRefresh({ projectId: selectedProjectId, boardData, isWebSocketConnected });

  // Keep the ref in sync so stableResetTimer always calls the latest resetTimer.
  useEffect(() => {
    resetTimerRef.current = resetTimer;
  }, [resetTimer]);

  const [selectedItem, setSelectedItem] = useState<BoardItem | null>(null);

  const { agents: availableAgents, isLoading: agentsLoading } = useAvailableAgents(selectedProjectId);

  // Board controls: filter, sort, group-by with localStorage persistence
  const boardControls = useBoardControls(selectedProjectId, boardData ?? undefined);
  const transformedBoardData = boardControls.transformedData;

  // Project settings for queue mode toggle
  const { settings: projectSettings, updateSettings, isUpdating: isSettingsUpdating } = useProjectSettings(selectedProjectId ?? undefined);
  const isQueueMode = projectSettings?.project?.board_display_config?.queue_mode ?? false;
  const isAutoMerge = projectSettings?.project?.board_display_config?.auto_merge ?? false;

  const handleToggleQueueMode = useCallback(async () => {
    if (!selectedProjectId) return;
    try {
      await updateSettings({ queue_mode: !isQueueMode });
      toast.success(isQueueMode ? 'Queue mode disabled' : 'Queue mode enabled');
    } catch {
      toast.error('Failed to update queue mode');
    }
  }, [selectedProjectId, isQueueMode, updateSettings]);

  const {
    data: savedPipelines,
    isLoading: savedPipelinesLoading,
    error: savedPipelinesError,
    refetch: refetchSavedPipelines,
  } = useQuery({
    queryKey: ['pipelines', selectedProjectId],
    queryFn: () => pipelinesApi.list(selectedProjectId!),
    enabled: !!selectedProjectId,
    staleTime: 60_000,
  });

  const handleToggleAutoMerge = useCallback(async () => {
    if (!selectedProjectId) return;

    // When enabling auto-merge on a project with active pipelines,
    // require explicit user confirmation (retroactive impact).
    if (!isAutoMerge) {
      const hasPipelines = Array.isArray(savedPipelines) && savedPipelines.length > 0;
      if (hasPipelines) {
        const confirmed = window.confirm(
          `Enable auto-merge for this project? This will also apply to ${savedPipelines.length} existing pipeline(s) and may change how they are merged.`
        );
        if (!confirmed) {
          return;
        }
      }
    }

    try {
      await updateSettings({ auto_merge: !isAutoMerge });
      toast.success(isAutoMerge ? 'Auto merge disabled' : 'Auto merge enabled');
    } catch {
      toast.error('Failed to update auto merge');
    }
  }, [selectedProjectId, isAutoMerge, updateSettings, savedPipelines]);

  const { data: pipelineAssignment } = useQuery({
    queryKey: ['pipelines', 'assignment', selectedProjectId],
    queryFn: () => pipelinesApi.getAssignment(selectedProjectId!),
    enabled: !!selectedProjectId,
    staleTime: 60_000,
  });

  const assignPipelineMutation = useMutation({
    mutationFn: (pipelineId: string) => pipelinesApi.setAssignment(selectedProjectId!, pipelineId),
    onSuccess: (assignment) => {
      if (!selectedProjectId) return;
      queryClient.setQueryData(['pipelines', 'assignment', selectedProjectId], assignment);
    },
  });

  const handleCardClick = useCallback((item: BoardItem) => setSelectedItem(item), []);
  const handleCloseModal = useCallback(() => setSelectedItem(null), []);

  // ── Board status update mutation with optimistic UI ──
  const boardStatusMutation = useMutation({
    mutationFn: ({ itemId, newStatus }: { itemId: string; newStatus: string }) =>
      boardApi.updateItemStatus(selectedProjectId!, itemId, newStatus),
    onMutate: async ({ itemId, newStatus }) => {
      if (!selectedProjectId) return;
      const queryKey = ['board', 'data', selectedProjectId];
      await queryClient.cancelQueries({ queryKey });
      const snapshot = queryClient.getQueryData<BoardDataResponse>(queryKey);
      if (!snapshot) return;

      queryClient.setQueryData<BoardDataResponse>(queryKey, (old) => {
        if (!old) return old;
        let movedItem: BoardItem | undefined;
        const columns = old.columns.map((col) => {
          const found = col.items.find((item) => item.item_id === itemId);
          if (found) {
            movedItem = { ...found, status: newStatus };
            return {
              ...col,
              items: col.items.filter((item) => item.item_id !== itemId),
              item_count: col.item_count - 1,
            };
          }
          return col;
        });

        if (!movedItem) return old;

        return {
          ...old,
          columns: columns.map((col) => {
            if (col.status.name === newStatus) {
              const updatedItem = { ...movedItem!, status_option_id: col.status.option_id };
              return {
                ...col,
                items: [...col.items, updatedItem],
                item_count: col.item_count + 1,
              };
            }
            return col;
          }),
        };
      });

      return { snapshot, queryKey };
    },
    onError: (_error, _variables, context) => {
      if (context?.snapshot && context.queryKey) {
        queryClient.setQueryData(context.queryKey, context.snapshot);
      }
    },
    onSettled: (_data, _error, _variables, context) => {
      if (context?.queryKey) {
        queryClient.invalidateQueries({ queryKey: context.queryKey });
      }
    },
  });

  const handleStatusUpdate = useCallback(
    async (itemId: string, newStatus: string) => {
      await boardStatusMutation.mutateAsync({ itemId, newStatus });
    },
    [boardStatusMutation],
  );

  const assignedPipelineName = useMemo(
    () =>
      savedPipelines?.pipelines.find(
        (pipeline) => pipeline.id === (pipelineAssignment?.pipeline_id ?? '')
      )?.name ?? 'None assigned',
    [pipelineAssignment?.pipeline_id, savedPipelines],
  );

  const heroStats = useMemo(
    () => [
      { label: 'Board columns', value: String(transformedBoardData?.columns.length ?? 0) },
      {
        label: 'Total items',
        value: String(
          transformedBoardData?.columns.reduce((sum, c) => sum + c.items.length, 0) ?? 0
        ),
      },
      { label: 'Pipeline', value: assignedPipelineName },
      { label: 'Project', value: selectedProject?.name ?? 'Unselected' },
    ],
    [transformedBoardData?.columns, assignedPipelineName, selectedProject?.name]
  );

  const projectsRateLimitError = isRateLimitApiError(projectsError);
  const boardRateLimitError = isRateLimitApiError(boardError);
  const refreshRateLimitError = refreshError?.type === 'rate_limit';
  const projectsRateLimitDetails = extractRateLimitInfo(projectsError);
  const boardRateLimitDetails = extractRateLimitInfo(boardError);
  const effectiveRateLimitInfo =
    rateLimitInfo ??
    projectsRateLimitInfo ??
    refreshError?.rateLimitInfo ??
    boardRateLimitDetails ??
    projectsRateLimitDetails;
  const hasActiveRateLimitError =
    refreshRateLimitError || boardRateLimitError || projectsRateLimitError;

  // Publish rate limit state to global context so TopBar can display it on any page.
  // Memoize the state object to avoid triggering consumer rerenders when values
  // have not actually changed (T025).
  const rateLimitState = useMemo(
    () => ({ info: effectiveRateLimitInfo ?? null, hasError: hasActiveRateLimitError }),
    [effectiveRateLimitInfo, hasActiveRateLimitError],
  );
  useEffect(() => {
    updateRateLimit(rateLimitState);
  }, [rateLimitState, updateRateLimit]);

  const rateLimitRetryAfter =
    refreshError?.retryAfter ??
    (effectiveRateLimitInfo ? new Date(effectiveRateLimitInfo.reset_at * 1000) : undefined);
  const showRateLimitBanner =
    refreshRateLimitError || boardRateLimitError || projectsRateLimitError;

  // Memoize sync status labels to prevent re-computation on unrelated
  // state changes (T025).
  const syncStatusLabel = useMemo(
    () =>
      syncStatus === 'connected'
        ? 'Live sync'
        : syncStatus === 'polling'
          ? 'Polling'
          : syncStatus === 'connecting'
            ? 'Connecting'
            : 'Offline',
    [syncStatus],
  );
  const syncStatusToneClass = useMemo(
    () =>
      syncStatus === 'connected'
        ? 'bg-[hsl(var(--sync-connected))]'
        : syncStatus === 'polling'
          ? 'bg-[hsl(var(--sync-polling))]'
          : syncStatus === 'connecting'
            ? 'bg-[hsl(var(--sync-connecting))]'
            : 'bg-[hsl(var(--sync-disconnected))]',
    [syncStatus],
  );

  return (
    <div className="projects-page-shell celestial-fade-in flex h-full flex-col gap-5 overflow-visible rounded-[1.75rem] border border-border/70 bg-background/35 p-4 backdrop-blur-sm sm:p-6">
      <CelestialCatalogHero
        className="projects-catalog-hero"
        eyebrow="Mission Control"
        title="Every project, mapped and moving."
        description="Live Kanban view of your GitHub Project. Filter, sort, and group issues across pipeline stages, then trigger agents directly from the board."
        badge={
          selectedProject
            ? `${selectedProject.owner_login}/${selectedProject.name}`
            : 'Awaiting project'
        }
        note="Use the board to triage work and queue items for the active agent pipeline — all without leaving the project view."
        stats={heroStats}
        actions={
          <>
            <Button variant="default" size="lg" asChild>
              <a href="#board">View board</a>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <a href="#pipeline-stages">Pipeline stages</a>
            </Button>
          </>
        }
      />
      {/* Page Header + Toolbar */}
      <div className="flex shrink-0 flex-wrap items-center gap-3 text-sm text-muted-foreground">
          {selectedProjectId && (
            <span
              className="solar-chip-soft inline-flex items-center gap-2 rounded-full px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-foreground"
              aria-live="polite"
            >
              <span
                className={cn(
                  'h-2.5 w-2.5 rounded-full shadow-[0_0_0_3px_hsl(var(--background)/0.7)]',
                  syncStatusToneClass
                )}
              />
              {syncStatusLabel}
            </span>
          )}

          {selectedProjectId && (
            <RefreshButton
              onRefresh={refresh}
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
                : 'border-border/70 bg-background/50 hover:bg-accent/45'
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

        {selectedProjectId && boardData && (
          <button
            onClick={handleToggleAutoMerge}
            disabled={isSettingsUpdating}
            className={cn(
              'relative flex items-center gap-1.5 rounded-full border px-4 py-2 text-xs font-medium uppercase tracking-[0.16em] transition-colors',
              isAutoMerge
                ? 'border-primary/50 bg-primary/10 text-primary'
                : 'border-border/70 bg-background/50 hover:bg-accent/45'
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

      {/* Rate limit / error banners */}
      <ProjectBoardErrorBanners
        showRateLimitBanner={showRateLimitBanner}
        rateLimitRetryAfter={rateLimitRetryAfter}
        isRateLimitLow={isRateLimitLow}
        rateLimitInfo={rateLimitInfo}
        refreshError={refreshError}
        projectsError={projectsError}
        projectsRateLimitError={projectsRateLimitError}
        boardError={boardError}
        boardLoading={boardLoading}
        boardRateLimitError={boardRateLimitError}
        selectedProjectId={selectedProjectId}
        onRetryBoard={selectBoardProject}
      />

      {/* Content area */}
      {!selectedProjectId && !projectsLoading && (
        <ProjectSelectionEmptyState
          projects={projects}
          isLoading={projectsListLoading}
          selectedProjectId={selectedProjectId}
          onSelectProject={selectProject}
          description="Open one of your GitHub Projects to review its board, column flow, and current delivery state."
        />
      )}

      {selectedProjectId && boardLoading && (
        <div className="flex flex-1 flex-col items-center justify-center gap-4">
          <CelestialLoadingProgress
            phases={[
              { label: 'Connecting to GitHub…', complete: !projectsLoading },
              { label: 'Loading project board…', complete: !boardLoading },
              { label: 'Loading pipelines…', complete: !savedPipelinesLoading },
              { label: 'Loading agents…', complete: !agentsLoading },
            ]}
          />
        </div>
      )}

      {selectedProjectId && !boardLoading && transformedBoardData && (
        <div className="flex flex-1 flex-col gap-6 overflow-visible">
          <ProjectIssueLaunchPanel
            projectId={selectedProjectId}
            projectName={selectedProject?.name}
            pipelines={savedPipelines?.pipelines ?? []}
            isLoadingPipelines={savedPipelinesLoading}
            pipelinesError={
              savedPipelinesError instanceof Error ? savedPipelinesError.message : null
            }
            onRetryPipelines={() => {
              void refetchSavedPipelines();
            }}
            onLaunched={() => {
              refresh();
              void queryClient.invalidateQueries({
                queryKey: ['pipelines', 'assignment', selectedProjectId],
              });
            }}
          />

          <PipelineStagesSection
            key={selectedProjectId}
            columns={transformedBoardData.columns}
            savedPipelines={savedPipelines?.pipelines ?? []}
            assignedPipelineId={pipelineAssignment?.pipeline_id}
            assignPipelineMutation={assignPipelineMutation}
          />

          <ProjectBoardContent
            boardData={transformedBoardData}
            boardControls={boardControls}
            onCardClick={handleCardClick}
            availableAgents={availableAgents}
            onStatusUpdate={handleStatusUpdate}
          />
        </div>
      )}

      {selectedItem && <IssueDetailModal item={selectedItem} onClose={handleCloseModal} />}
    </div>
  );
}
