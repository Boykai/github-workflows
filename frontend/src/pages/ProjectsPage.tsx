/**
 * ProjectsPage — Project board with enhanced Kanban view.
 * Migrated from ProjectBoardPage with page header, toolbar, and enhanced cards.
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown, Inbox, Lock, Search, TriangleAlert } from 'lucide-react';
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
import { BlockingChainPanel } from '@/components/board/BlockingChainPanel';
import { RefreshButton } from '@/components/board/RefreshButton';
import { statusColorToCSS } from '@/components/board/colorUtils';
import { ProjectSelectionEmptyState } from '@/components/common/ProjectSelectionEmptyState';
import { ProjectSelector } from '@/layout/ProjectSelector';
import { useAvailableAgents } from '@/hooks/useAgentConfig';
import { useBoardControls } from '@/hooks/useBoardControls';
import { useBlockingQueue } from '@/hooks/useBlockingQueue';
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
  const [projectSelectorOpen, setProjectSelectorOpen] = useState(false);
  const [pipelineSelectorOpen, setPipelineSelectorOpen] = useState(false);
  const pipelineSelectorRef = useRef<HTMLDivElement>(null);

  const { agents: availableAgents } = useAvailableAgents(selectedProjectId);

  // Board controls: filter, sort, group-by with localStorage persistence
  const boardControls = useBoardControls(selectedProjectId, boardData ?? undefined);
  const transformedBoardData = boardControls.transformedData;

  // Blocking queue state for the blocking chain panel
  const { data: blockingQueueEntries } = useBlockingQueue(selectedProjectId ?? undefined);
  const blockingIssueNumbers = useMemo(
    () => new Set((blockingQueueEntries ?? []).map((entry) => entry.issue_number)),
    [blockingQueueEntries]
  );

  const { data: savedPipelines } = useQuery({
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

  const setBlockingOverrideMutation = useMutation({
    mutationFn: (blockingOverride: boolean | null) =>
      pipelinesApi.setBlockingOverride(selectedProjectId!, blockingOverride),
    onSuccess: (assignment) => {
      if (!selectedProjectId) return;
      queryClient.setQueryData(['pipelines', 'assignment', selectedProjectId], assignment);
    },
  });

  const handleCardClick = useCallback((item: BoardItem) => setSelectedItem(item), []);
  const handleCloseModal = useCallback(() => setSelectedItem(null), []);
  const pipelineColumnCount = Math.max(transformedBoardData?.columns.length ?? 0, 1);
  const pipelineGridStyle = {
    gridTemplateColumns: `repeat(${pipelineColumnCount}, minmax(14rem, 1fr))`,
  };
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

  // Effective blocking = project override (if set) otherwise pipeline default
  const effectiveBlocking =
    pipelineAssignment?.blocking_override ?? assignedPipeline?.blocking ?? false;
  const hasBlockingOverride = pipelineAssignment?.blocking_override != null;

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

  return (
    <div className="flex h-full flex-col gap-4 rounded-[1.75rem] border border-border/70 bg-background/35 p-3 backdrop-blur-sm overflow-hidden sm:gap-5 sm:p-4 md:p-6">
      <CelestialCatalogHero
        eyebrow="Mission Control"
        title="Every project, mapped and moving."
        description="Live Kanban view of your GitHub Project. Filter, sort, and group issues across pipeline stages, then trigger agents directly from the board."
        badge={
          selectedProject
            ? `${selectedProject.owner_login}/${selectedProject.name}`
            : 'Awaiting project'
        }
        note="Use the board to triage work, assign blocking chains, and queue items for the active agent pipeline — all without leaving the project view."
        stats={[
          { label: 'Board columns', value: String(transformedBoardData?.columns.length ?? 0) },
          {
            label: 'Total items',
            value: String(
              transformedBoardData?.columns.reduce((sum, c) => sum + c.items.length, 0) ?? 0
            ),
          },
          { label: 'Pipeline', value: assignedPipeline?.name ?? 'None assigned' },
          { label: 'Project', value: selectedProject?.name ?? 'Unselected' },
        ]}
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
      {/* Page Header */}
      <div className="flex items-start justify-between gap-4 shrink-0">
        <div className="relative">
          <button
            type="button"
            onClick={() => setProjectSelectorOpen((current) => !current)}
            className="moonwell flex min-w-[12rem] items-center gap-3 rounded-[1.05rem] border border-border/70 px-4 py-3 text-left shadow-sm transition-colors hover:border-primary/35 hover:bg-background/60"
            aria-haspopup="listbox"
            aria-expanded={projectSelectorOpen}
            aria-label="Select project"
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/12 text-sm font-semibold text-primary shadow-[inset_0_1px_0_hsl(var(--glow)/0.18)]">
              {selectedProject?.name?.charAt(0).toUpperCase() ?? '?'}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-semibold text-foreground">
                {selectedProject?.name ?? 'Select project'}
              </span>
              <span className="block truncate text-[10px] uppercase tracking-[0.22em] text-muted-foreground/80">
                {selectedProject?.owner_login ?? 'GitHub Projects'}
              </span>
            </span>
            <ChevronDown
              className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform ${projectSelectorOpen ? 'rotate-180' : ''}`}
            />
          </button>

          <ProjectSelector
            isOpen={projectSelectorOpen}
            onClose={() => setProjectSelectorOpen(false)}
            projects={projects}
            selectedProjectId={selectedProjectId}
            isLoading={projectsListLoading}
            onSelectProject={(projectId) => {
              void selectProject(projectId);
            }}
            className="top-full bottom-auto left-0 right-auto mt-2 mb-0 min-w-[20rem]"
          />
        </div>

        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          {selectedProjectId && (
            <span className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  syncStatus === 'connected'
                    ? 'bg-green-500'
                    : syncStatus === 'polling'
                      ? 'bg-yellow-500'
                      : syncStatus === 'connecting'
                        ? 'bg-blue-500'
                        : 'bg-red-500'
                }`}
              />
              {syncStatus === 'connected' && 'Live'}
              {syncStatus === 'polling' && 'Polling'}
              {syncStatus === 'connecting' && 'Connecting...'}
              {syncStatus === 'disconnected' && 'Offline'}
            </span>
          )}

          {selectedProjectId && (
            <RefreshButton
              onRefresh={refresh}
              isRefreshing={isRefreshing || (isFetching && !boardLoading)}
            />
          )}

          {(lastUpdated || syncLastUpdate) && (
            <span className="text-xs">Updated {formatTimeAgo(syncLastUpdate ?? lastUpdated!)}</span>
          )}
        </div>
      </div>

      {/* Toolbar */}
      {selectedProjectId && boardData && (
        <div className="flex items-center gap-2">
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
            hasActiveFilters={boardControls.hasActiveFilters}
            hasActiveSort={boardControls.hasActiveSort}
            hasActiveGroup={boardControls.hasActiveGroup}
            hasActiveControls={boardControls.hasActiveControls}
          />
          {blockingQueueEntries && blockingQueueEntries.length > 0 && (
            <BlockingChainPanel entries={blockingQueueEntries} />
          )}
        </div>
      )}

      {/* Rate limit / error banners */}
      {showRateLimitBanner && (
        <div className="flex items-start gap-3 rounded-[1.1rem] border border-accent/30 bg-accent/12 p-4 text-accent-foreground">
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
        <div className="flex items-start gap-3 rounded-[1.1rem] border border-accent/30 bg-accent/12 p-4 text-accent-foreground">
          <TriangleAlert className="h-5 w-5 shrink-0" />
          <div className="flex flex-col gap-1">
            <strong>Rate limit low</strong>
            <p>Only {rateLimitInfo.remaining} API requests remaining.</p>
          </div>
        </div>
      )}

      {refreshError && refreshError.type !== 'rate_limit' && (
        <div className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive">
          <TriangleAlert className="h-5 w-5 shrink-0" />
          <div className="flex flex-col gap-1">
            <strong>Refresh failed</strong>
            <p>{refreshError.message}</p>
          </div>
        </div>
      )}

      {projectsError && !projectsRateLimitError && (
        <div className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive">
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
        <div className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive">
          <TriangleAlert className="h-5 w-5 shrink-0" />
          <div className="flex flex-col gap-1">
            <strong>Failed to load board data</strong>
            <p>{boardError.message}</p>
          </div>
          <button
            className="px-3 py-1.5 text-sm font-medium bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 transition-colors ml-auto"
            onClick={() => selectBoardProject(selectedProjectId!)}
          >
            Retry
          </button>
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
        <div className="flex flex-col items-center justify-center flex-1 gap-4">
          <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
          <p className="text-muted-foreground">Loading board...</p>
        </div>
      )}

      {selectedProjectId && !boardLoading && transformedBoardData && (
        <div className="flex flex-col flex-1 gap-6 overflow-hidden">
          <section className="space-y-4">
            <div>
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                <h3 className="text-lg font-semibold">Pipeline Stages</h3>
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
                    {pipelineAssignment !== undefined && (
                      <label className="flex cursor-pointer items-center gap-2">
                        <button
                          type="button"
                          role="switch"
                          aria-checked={effectiveBlocking}
                          disabled={setBlockingOverrideMutation.isPending}
                          onClick={() =>
                            setBlockingOverrideMutation.mutate(
                              hasBlockingOverride ? null : !effectiveBlocking
                            )
                          }
                          title={
                            hasBlockingOverride
                              ? `Project override is forcing blocking ${effectiveBlocking ? 'on' : 'off'} — click to return to the pipeline default`
                              : effectiveBlocking
                                ? 'Blocking is currently on from the assigned pipeline — click to force this project off'
                                : 'Blocking is currently off from the assigned pipeline — click to force this project on'
                          }
                          className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 disabled:cursor-not-allowed disabled:opacity-50 ${
                            effectiveBlocking ? 'bg-amber-500' : 'bg-muted'
                          }`}
                        >
                          <span
                            className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition-transform ${
                              effectiveBlocking ? 'translate-x-4' : 'translate-x-0'
                            }`}
                          />
                        </button>
                        <span
                          className={`flex items-center gap-1 text-xs font-semibold uppercase tracking-[0.16em] ${effectiveBlocking ? 'text-amber-500' : 'text-muted-foreground'}`}
                        >
                          <Lock className="h-3 w-3" />
                          {effectiveBlocking ? 'BLOCKING(ON)' : 'BLOCKING(OFF)'}
                        </span>
                      </label>
                    )}
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
                <div className="grid min-w-full items-stretch gap-3" style={pipelineGridStyle}>
                  {transformedBoardData.columns.map((col) => {
                    const assigned =
                      assignedStageMap.get(col.status.name.toLowerCase())?.agents ?? [];
                    const dotColor = statusColorToCSS(col.status.color);

                    return (
                      <div
                        key={col.status.option_id}
                        className="celestial-panel flex h-full min-w-0 flex-col items-center gap-2 rounded-[1.2rem] border border-border/75 bg-background/28 p-4 text-center shadow-sm"
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

          <div className="flex flex-1 gap-6 overflow-hidden">
            {transformedBoardData.columns.every((col) => col.items.length === 0) ? (
              <div className="celestial-panel flex flex-1 flex-col items-center justify-center gap-4 rounded-[1.4rem] border border-dashed border-border/80 p-8 text-center">
                {boardControls.hasActiveControls ? (
                  <>
                    <Search className="mb-2 h-10 w-10 text-primary/80" />
                    <h3 className="text-xl font-semibold">No issues match the current view</h3>
                    <p className="text-muted-foreground">
                      Try adjusting your filter, sort, or group settings.
                    </p>
                    <button
                      onClick={boardControls.clearAll}
                      className="mt-2 px-4 py-2 text-sm font-medium rounded-md border border-border bg-background text-foreground hover:bg-muted transition-colors"
                      type="button"
                    >
                      Clear All
                    </button>
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
                blockingIssueNumbers={blockingIssueNumbers}
              />
            )}
          </div>
        </div>
      )}

      {selectedItem && <IssueDetailModal item={selectedItem} onClose={handleCloseModal} />}
    </div>
  );
}
