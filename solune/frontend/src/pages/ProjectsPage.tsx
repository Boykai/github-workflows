/**
 * ProjectsPage — Project board with enhanced Kanban view.
 * Migrated from ProjectBoardPage with page header, toolbar, and enhanced cards.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { Inbox, Search } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRateLimitStatus } from '@/context/RateLimitContext';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useRealTimeSync } from '@/hooks/useRealTimeSync';
import { useBoardRefresh } from '@/hooks/useBoardRefresh';
import { useProjects } from '@/hooks/useProjects';
import { useAuth } from '@/hooks/useAuth';
import { ProjectBoard } from '@/components/board/ProjectBoard';
import { IssueDetailModal } from '@/components/board/IssueDetailModal';
import { BoardToolbar } from '@/components/board/BoardToolbar';
import { ProjectIssueLaunchPanel } from '@/components/board/ProjectIssueLaunchPanel';
import { PipelineStagesPanel } from '@/components/board/PipelineStagesPanel';
import { RefreshButton } from '@/components/board/RefreshButton';
import { ProjectSelectionEmptyState } from '@/components/common/ProjectSelectionEmptyState';
import { useAvailableAgents } from '@/hooks/useAgentConfig';
import { useBoardControls } from '@/hooks/useBoardControls';
import { formatTimeAgo, formatTimeUntil } from '@/utils/formatTime';
import { extractRateLimitInfo, isRateLimitApiError } from '@/utils/rateLimit';
import { cn } from '@/lib/utils';
import type { BoardItem } from '@/types';
import { pipelinesApi } from '@/services/api';
import { BoardStatusBanners } from '@/components/board/BoardStatusBanners';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { Button } from '@/components/ui/button';

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

  const {
    refresh,
    isRefreshing,
    error: refreshError,
    rateLimitInfo,
    isRateLimitLow,
    resetTimer,
  } = useBoardRefresh({ projectId: selectedProjectId, boardData });

  const { status: syncStatus, lastUpdate: syncLastUpdate } = useRealTimeSync(selectedProjectId, {
    onRefreshTriggered: resetTimer,
  });

  const [selectedItem, setSelectedItem] = useState<BoardItem | null>(null);

  const { agents: availableAgents } = useAvailableAgents(selectedProjectId);

  // Board controls: filter, sort, group-by with localStorage persistence
  const boardControls = useBoardControls(selectedProjectId, boardData ?? undefined);
  const transformedBoardData = boardControls.transformedData;

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
      setPipelineSelectorOpen(false);
      queryClient.setQueryData(['pipelines', 'assignment', selectedProjectId], assignment);
    },
  });

  const handleCardClick = useCallback((item: BoardItem) => setSelectedItem(item), []);
  const handleCloseModal = useCallback(() => setSelectedItem(null), []);
  const pipelineColumnCount = Math.max(transformedBoardData?.columns.length ?? 0, 1);
  const pipelineGridStyle = useMemo(
    () => ({ gridTemplateColumns: `repeat(${pipelineColumnCount}, minmax(min(14rem, 85vw), 1fr))` }),
    [pipelineColumnCount]
  );
  const assignedPipeline = useMemo(
    () =>
      savedPipelines?.pipelines.find(
        (pipeline) => pipeline.id === (pipelineAssignment?.pipeline_id ?? '')
      ) ?? null,
    [pipelineAssignment?.pipeline_id, savedPipelines]
  );
  const assignedStageMap = useMemo(
    () =>
      new Map((assignedPipeline?.stages ?? []).map((stage) => [stage.name.toLowerCase(), stage])),
    [assignedPipeline]
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
      { label: 'Pipeline', value: assignedPipeline?.name ?? 'None assigned' },
      { label: 'Project', value: selectedProject?.name ?? 'Unselected' },
    ],
    [transformedBoardData?.columns, assignedPipeline?.name, selectedProject?.name]
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
  useEffect(() => {
    updateRateLimit({ info: effectiveRateLimitInfo ?? null, hasError: hasActiveRateLimitError });
  }, [effectiveRateLimitInfo, hasActiveRateLimitError, updateRateLimit]);

  const handlePipelineSelection = useCallback(
    (pipelineId: string) => {
      assignPipelineMutation.mutate(pipelineId, {
        onError: () => {
          // Pipeline assignment failed — no user feedback from state needed here
          // since PipelineStagesPanel manages its own selector state
        },
      });
    },
    [assignPipelineMutation]
  );

  const rateLimitRetryAfter =
    refreshError?.retryAfter ??
    (effectiveRateLimitInfo ? new Date(effectiveRateLimitInfo.reset_at * 1000) : undefined);
  const showRateLimitBanner =
    refreshRateLimitError || boardRateLimitError || projectsRateLimitError;
  const syncStatusLabel =
    syncStatus === 'connected'
      ? 'Live sync'
      : syncStatus === 'polling'
        ? 'Polling'
        : syncStatus === 'connecting'
          ? 'Connecting'
          : 'Offline';
  const syncStatusToneClass =
    syncStatus === 'connected'
      ? 'bg-[hsl(var(--sync-connected))]'
      : syncStatus === 'polling'
        ? 'bg-[hsl(var(--sync-polling))]'
        : syncStatus === 'connecting'
          ? 'bg-[hsl(var(--sync-connecting))]'
          : 'bg-[hsl(var(--sync-disconnected))]';

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
      </div>

      {/* Rate limit / error banners */}
      <BoardStatusBanners
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
        onRetryBoard={() => selectBoardProject(selectedProjectId!)}
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
          <CelestialLoader size="md" label="Loading board…" />
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

          <PipelineStagesPanel
            columns={transformedBoardData.columns}
            pipelineGridStyle={pipelineGridStyle}
            assignedStageMap={assignedStageMap}
            savedPipelines={savedPipelines?.pipelines}
            pipelineAssignment={pipelineAssignment ?? undefined}
            assignedPipeline={assignedPipeline}
            isAssigning={assignPipelineMutation.isPending}
            onPipelineSelect={handlePipelineSelection}
          />

          <div id="board" className="flex flex-1 gap-6 scroll-mt-24">
            {transformedBoardData.columns.every((col) => col.items.length === 0) ? (
              <div className="celestial-panel flex min-h-[32rem] flex-1 flex-col items-center justify-center gap-4 rounded-[1.4rem] border border-dashed border-border/80 p-8 text-center sm:min-h-[40rem]">
                {boardControls.hasActiveControls ? (
                  <>
                    <Search className="mb-2 h-10 w-10 text-primary/80" />
                    <h3 className="text-xl font-semibold">No issues match the current view</h3>
                    <p className="text-muted-foreground">
                      Try adjusting your filter, sort, or group settings.
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={boardControls.clearAll}
                      className="mt-2"
                      type="button"
                    >
                      Clear all filters
                    </Button>
                  </>
                ) : (
                  <>
                    <Inbox className="mb-2 h-10 w-10 text-primary/70" />
                    <h3 className="text-xl font-semibold">No items yet</h3>
                    <p className="text-muted-foreground">
                      This project has no items. Add items in GitHub to see them here.
                    </p>
                  </>
                )}
              </div>
            ) : (
              <ProjectBoard
                boardData={transformedBoardData}
                onCardClick={handleCardClick}
                availableAgents={availableAgents}
                getGroups={boardControls.getGroups}
              />
            )}
          </div>
        </div>
      )}

      {selectedItem && <IssueDetailModal item={selectedItem} onClose={handleCloseModal} />}
    </div>
  );
}
