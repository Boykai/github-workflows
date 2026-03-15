/**
 * ProjectsPage — Project board with enhanced Kanban view.
 * Migrated from ProjectBoardPage with page header, toolbar, and enhanced cards.
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Link } from 'react-router-dom';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { ChevronDown, Inbox, Search, TriangleAlert } from 'lucide-react';
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
import { RefreshButton } from '@/components/board/RefreshButton';
import { statusColorToCSS } from '@/components/board/colorUtils';
import { ProjectSelectionEmptyState } from '@/components/common/ProjectSelectionEmptyState';
import { useAvailableAgents } from '@/hooks/useAgentConfig';
import { useBoardControls } from '@/hooks/useBoardControls';
import { formatTimeAgo, formatTimeUntil } from '@/utils/formatTime';
import { extractRateLimitInfo, isRateLimitApiError } from '@/utils/rateLimit';
import { formatAgentName } from '@/utils/formatAgentName';
import { cn } from '@/lib/utils';
import type { BoardItem } from '@/types';
import { ApiError, pipelinesApi } from '@/services/api';
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
  const [pipelineSelectorOpen, setPipelineSelectorOpen] = useState(false);
  const pipelineSelectorRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    if (!pipelineSelectorOpen) return;

    function handlePointerDown(event: MouseEvent) {
      if (
        pipelineSelectorRef.current &&
        !pipelineSelectorRef.current.contains(event.target as Node)
      ) {
        setPipelineSelectorOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setPipelineSelectorOpen(false);
      }
    }

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [pipelineSelectorOpen]);

  useEffect(() => {
    setPipelineSelectorOpen(false);
  }, [selectedProjectId]);

  const handlePipelineSelection = useCallback(
    (pipelineId: string) => {
      setPipelineSelectorOpen(false);
      assignPipelineMutation.mutate(pipelineId);
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
    <div className="projects-page-shell celestial-fade-in flex min-h-full flex-col gap-5 overflow-visible rounded-[1.75rem] border border-border/70 bg-background/35 p-4 backdrop-blur-sm sm:p-6">
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
      <div className="flex shrink-0 flex-col gap-3">
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
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
        </div>

        {selectedProjectId && boardData && (
          <div className="flex flex-wrap items-start gap-2">
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
          </div>
        )}
      </div>

      {/* Rate limit / error banners */}
      {showRateLimitBanner && (
        <div
          className="flex items-start gap-3 rounded-[1.1rem] border border-accent/30 bg-accent/12 p-4 text-accent-foreground"
          role="alert"
        >
          <span className="text-lg">⏳</span>
          <div className="flex flex-col gap-1">
            <strong>Rate limit reached</strong>
            <p>
              {rateLimitRetryAfter
                ? `Resets ${formatTimeUntil(rateLimitRetryAfter)}.`
                : 'GitHub API rate limit reached. Retry after the quota window resets.'}
            </p>
          </div>
        </div>
      )}

      {isRateLimitLow && !showRateLimitBanner && rateLimitInfo && (
        <div
          className="flex items-start gap-3 rounded-[1.1rem] border border-accent/30 bg-accent/12 p-4 text-accent-foreground"
          role="alert"
        >
          <TriangleAlert className="h-5 w-5 shrink-0" />
          <div className="flex flex-col gap-1">
            <strong>Rate limit low</strong>
            <p>Only {rateLimitInfo.remaining} API requests remaining.</p>
          </div>
        </div>
      )}

      {refreshError && refreshError.type !== 'rate_limit' && (
        <div
          className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive"
          role="alert"
        >
          <TriangleAlert className="h-5 w-5 shrink-0" />
          <div className="flex flex-col gap-1">
            <strong>Refresh failed</strong>
            <p>{refreshError.message}</p>
          </div>
        </div>
      )}

      {projectsError && !projectsRateLimitError && (
        <div
          className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive"
          role="alert"
        >
          <TriangleAlert className="h-5 w-5 shrink-0" />
          <div className="flex flex-col gap-1">
            <strong>Failed to load projects</strong>
            <p>{projectsError.message}</p>
            {(() => {
              if (!(projectsError instanceof ApiError)) return null;
              const reason = projectsError.error.details?.reason;
              return typeof reason === 'string' ? (
                <p className="text-sm opacity-75">{reason}</p>
              ) : null;
            })()}
          </div>
        </div>
      )}

      {boardError && !boardLoading && !boardRateLimitError && (
        <div
          className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive"
          role="alert"
        >
          <TriangleAlert className="h-5 w-5 shrink-0" />
          <div className="flex flex-col gap-1">
            <strong>Failed to load board data</strong>
            <p>{boardError.message}</p>
          </div>
          <Button
            variant="destructive"
            size="sm"
            className="ml-auto self-start"
            onClick={() => selectBoardProject(selectedProjectId!)}
          >
            Retry loading board data
          </Button>
        </div>
      )}

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
        <div className="flex flex-col gap-6 overflow-visible">
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

          <section id="pipeline-stages" className="space-y-4 scroll-mt-24">
            <div>
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                <h3 id="pipeline-stages-heading" className="text-lg font-semibold">
                  Pipeline Stages
                </h3>
                {(savedPipelines?.pipelines.length ?? 0) > 0 ? (
                  <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                      <span>Agent Pipeline</span>
                      <div ref={pipelineSelectorRef} className="relative">
                        <button
                          type="button"
                          onClick={() => setPipelineSelectorOpen((current) => !current)}
                          disabled={assignPipelineMutation.isPending}
                          className={cn(
                            'project-pipeline-select project-pipeline-trigger flex h-9 min-w-[12rem] items-center justify-between gap-3 rounded-full px-4 text-xs font-medium text-foreground',
                            pipelineAssignment?.pipeline_id && 'project-pipeline-select-active',
                            pipelineSelectorOpen && 'project-pipeline-select-open'
                          )}
                          aria-haspopup="listbox"
                          aria-expanded={pipelineSelectorOpen}
                          aria-label="Agent Pipeline"
                        >
                          <span className="truncate">
                            {assignedPipeline?.name ?? 'No pipeline selected'}
                          </span>
                          <ChevronDown
                            className={cn(
                              'h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform',
                              pipelineSelectorOpen && 'rotate-180'
                            )}
                          />
                        </button>

                        {pipelineSelectorOpen && (
                          <div className="project-pipeline-menu absolute right-0 top-full z-30 mt-2 w-[min(20rem,calc(100vw-3rem))] overflow-hidden rounded-[1.1rem] border border-border/80">
                            <div className="border-b border-border/65 px-3 py-2.5 text-[10px] font-semibold uppercase tracking-[0.22em] text-muted-foreground/90">
                              Select pipeline
                            </div>
                            <div
                              className="max-h-72 overflow-y-auto p-1.5"
                              role="listbox"
                              aria-label="Agent Pipeline options"
                            >
                              <button
                                type="button"
                                role="option"
                                aria-selected={!pipelineAssignment?.pipeline_id}
                                onClick={() => handlePipelineSelection('')}
                                disabled={assignPipelineMutation.isPending}
                                className={cn(
                                  'project-pipeline-option flex w-full items-center justify-between gap-3 rounded-[0.9rem] px-3 py-2.5 text-left text-sm disabled:cursor-not-allowed disabled:opacity-60',
                                  !pipelineAssignment?.pipeline_id &&
                                    'project-pipeline-option-active'
                                )}
                              >
                                <span className="truncate">No pipeline selected</span>
                                {!pipelineAssignment?.pipeline_id && (
                                  <span className="text-[10px] font-semibold uppercase tracking-[0.18em]">
                                    Current
                                  </span>
                                )}
                              </button>
                              {savedPipelines?.pipelines.map((pipeline) => {
                                const isSelected =
                                  pipeline.id === (pipelineAssignment?.pipeline_id ?? '');

                                return (
                                  <button
                                    key={pipeline.id}
                                    type="button"
                                    role="option"
                                    aria-selected={isSelected}
                                    onClick={() => handlePipelineSelection(pipeline.id)}
                                    disabled={assignPipelineMutation.isPending}
                                    className={cn(
                                      'project-pipeline-option flex w-full items-center justify-between gap-3 rounded-[0.9rem] px-3 py-2.5 text-left text-sm disabled:cursor-not-allowed disabled:opacity-60',
                                      isSelected && 'project-pipeline-option-active'
                                    )}
                                  >
                                    <span className="truncate">{pipeline.name}</span>
                                    {isSelected && (
                                      <span className="text-[10px] font-semibold uppercase tracking-[0.18em]">
                                        Current
                                      </span>
                                    )}
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <Link
                    to="/pipeline"
                    className="solar-chip-soft inline-flex items-center rounded-full px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] transition-colors hover:bg-primary/10 hover:text-foreground"
                  >
                    Create new pipeline
                  </Link>
                )}
              </div>
              <div className="overflow-x-auto pb-2">
                <div
                  className="grid min-w-full items-stretch gap-3"
                  style={pipelineGridStyle}
                  role="region"
                  aria-labelledby="pipeline-stages-heading"
                >
                  {transformedBoardData.columns.map((col) => {
                    const assigned =
                      assignedStageMap.get(col.status.name.toLowerCase())?.agents ?? [];
                    const dotColor = statusColorToCSS(col.status.color);

                    return (
                      <div
                        key={col.status.option_id}
                        className="celestial-panel pipeline-stage-card flex h-full min-w-0 flex-col items-center gap-2 rounded-[1.2rem] border border-border/75 bg-background/28 p-4 text-center shadow-sm sm:rounded-[1.35rem]"
                      >
                        <span
                          className="h-3 w-3 rounded-full"
                          style={{ backgroundColor: dotColor }}
                        />
                        <span className="text-sm font-medium">{col.status.name}</span>
                        <span className="text-xs text-muted-foreground">
                          {col.item_count} items
                        </span>
                        {assigned.length > 0 ? (
                          <div className="mt-1 flex flex-wrap justify-center gap-1">
                            {assigned.map((assignment) => (
                              <span
                                key={assignment.id}
                                className="solar-chip rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]"
                              >
                                {formatAgentName(
                                  assignment.agent_slug,
                                  assignment.agent_display_name
                                )}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="mt-1 text-[10px] text-muted-foreground/60">
                            No agents
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </section>

          <div id="board" className="flex min-h-[42rem] gap-6 scroll-mt-24 sm:min-h-[56rem]">
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
