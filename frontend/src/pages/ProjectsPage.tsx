/**
 * ProjectsPage — Project board with enhanced Kanban view.
 * Migrated from ProjectBoardPage with page header, toolbar, and enhanced cards.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Lock } from 'lucide-react';
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
import { useAvailableAgents } from '@/hooks/useAgentConfig';
import { useBoardControls } from '@/hooks/useBoardControls';
import { useBlockingQueue } from '@/hooks/useBlockingQueue';
import { formatTimeAgo, formatTimeUntil } from '@/utils/formatTime';
import { extractRateLimitInfo, isRateLimitApiError } from '@/utils/rateLimit';
import { formatAgentName } from '@/utils/formatAgentName';
import type { BoardItem } from '@/types';
import { ApiError, pipelinesApi } from '@/services/api';

export function ProjectsPage() {
  const { updateRateLimit } = useRateLimitStatus();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const {
    selectedProject,
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
  } = useProjectBoard({ selectedProjectId: selectedProject?.project_id, onProjectSelect: selectProject });

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

  // Blocking queue state for the blocking chain panel
  const { data: blockingQueueEntries } = useBlockingQueue(selectedProjectId ?? undefined);
  const blockingIssueNumbers = useMemo(
    () => new Set((blockingQueueEntries ?? []).map((entry) => entry.issue_number)),
    [blockingQueueEntries],
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
  const pipelineGridStyle = { gridTemplateColumns: `repeat(${pipelineColumnCount}, minmax(14rem, 1fr))` };
  const assignedPipeline = useMemo(
    () => savedPipelines?.pipelines.find((pipeline) => pipeline.id === (pipelineAssignment?.pipeline_id ?? '')) ?? null,
    [pipelineAssignment?.pipeline_id, savedPipelines],
  );
  const assignedStageMap = useMemo(
    () => new Map((assignedPipeline?.stages ?? []).map((stage) => [stage.name.toLowerCase(), stage])),
    [assignedPipeline],
  );

  // Effective blocking = project override (if set) otherwise pipeline default
  const effectiveBlocking = pipelineAssignment?.blocking_override ?? assignedPipeline?.blocking ?? false;
  const hasBlockingOverride = pipelineAssignment?.blocking_override != null;

  const projectsRateLimitError = isRateLimitApiError(projectsError);
  const boardRateLimitError = isRateLimitApiError(boardError);
  const refreshRateLimitError = refreshError?.type === 'rate_limit';
  const projectsRateLimitDetails = extractRateLimitInfo(projectsError);
  const boardRateLimitDetails = extractRateLimitInfo(boardError);
  const effectiveRateLimitInfo = rateLimitInfo
    ?? projectsRateLimitInfo
    ?? refreshError?.rateLimitInfo
    ?? boardRateLimitDetails
    ?? projectsRateLimitDetails;
  const hasActiveRateLimitError = refreshRateLimitError || boardRateLimitError || projectsRateLimitError;

  // Publish rate limit state to global context so TopBar can display it on any page.
  useEffect(() => {
    updateRateLimit({ info: effectiveRateLimitInfo ?? null, hasError: hasActiveRateLimitError });
  }, [effectiveRateLimitInfo, hasActiveRateLimitError, updateRateLimit]);

  const rateLimitRetryAfter = refreshError?.retryAfter
    ?? (effectiveRateLimitInfo ? new Date(effectiveRateLimitInfo.reset_at * 1000) : undefined);
  const showRateLimitBanner = refreshRateLimitError || boardRateLimitError || projectsRateLimitError;

  return (
    <div className="flex h-full flex-col gap-5 rounded-[1.75rem] border border-border/70 bg-background/35 p-6 backdrop-blur-sm overflow-hidden">
      {/* Page Header */}
      <div className="flex items-center justify-end shrink-0">
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          {selectedProjectId && (
            <span className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${
                syncStatus === 'connected' ? 'bg-green-500' :
                syncStatus === 'polling' ? 'bg-yellow-500' :
                syncStatus === 'connecting' ? 'bg-blue-500' :
                'bg-red-500'
              }`} />
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
            <span className="text-xs">
              Updated {formatTimeAgo(syncLastUpdate ?? lastUpdated!)}
            </span>
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
          <span className="text-lg">⚠️</span>
          <div className="flex flex-col gap-1">
            <strong>Rate limit low</strong>
            <p>Only {rateLimitInfo.remaining} API requests remaining.</p>
          </div>
        </div>
      )}

      {refreshError && refreshError.type !== 'rate_limit' && (
        <div className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive">
          <span className="text-lg">⚠️</span>
          <div className="flex flex-col gap-1">
            <strong>Refresh failed</strong>
            <p>{refreshError.message}</p>
          </div>
        </div>
      )}

      {projectsError && !projectsRateLimitError && (
        <div className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive">
          <span className="text-lg">⚠️</span>
          <div className="flex flex-col gap-1">
            <strong>Failed to load projects</strong>
            <p>{projectsError.message}</p>
            {(() => {
              if (!(projectsError instanceof ApiError)) return null;
              const reason = projectsError.error.details?.reason;
              return typeof reason === 'string' ? <p className="text-sm opacity-75">{reason}</p> : null;
            })()}
          </div>
        </div>
      )}

      {boardError && !boardLoading && !boardRateLimitError && (
        <div className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive">
          <span className="text-lg">⚠️</span>
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
        <div className="celestial-panel flex flex-1 flex-col items-center justify-center gap-4 rounded-[1.4rem] border border-dashed border-border/80 bg-background/26 p-8 text-center">
          <div className="text-4xl mb-2">📋</div>
          <h3 className="text-xl font-semibold">Select a project</h3>
          <p className="text-muted-foreground">Choose a project from the dropdown above to view its board</p>
        </div>
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
                    <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                      <span>Agent Pipeline</span>
                      <select
                        value={pipelineAssignment?.pipeline_id ?? ''}
                        onChange={(event) => assignPipelineMutation.mutate(event.target.value)}
                        disabled={assignPipelineMutation.isPending}
                        className="moonwell h-9 min-w-[12rem] rounded-full border-border/60 px-4 text-xs font-medium text-foreground"
                        aria-label="Agent Pipeline"
                      >
                        <option value="">No pipeline selected</option>
                        {savedPipelines?.pipelines.map((pipeline) => (
                          <option key={pipeline.id} value={pipeline.id}>
                            {pipeline.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    {pipelineAssignment !== undefined && (
                      <label className="flex cursor-pointer items-center gap-2">
                        <button
                          type="button"
                          role="switch"
                          aria-checked={effectiveBlocking}
                          disabled={setBlockingOverrideMutation.isPending}
                          onClick={() =>
                            setBlockingOverrideMutation.mutate(effectiveBlocking ? null : true)
                          }
                          title={
                            hasBlockingOverride
                              ? 'Blocking override set on this project — click to clear'
                              : 'Using pipeline default — click to force blocking on'
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
                        <span className={`flex items-center gap-1 text-xs font-semibold uppercase tracking-[0.16em] ${effectiveBlocking ? 'text-amber-500' : 'text-muted-foreground'}`}>
                          <Lock className="h-3 w-3" />
                          Blocking{hasBlockingOverride ? '' : ' (default)'}
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
                    const assigned = assignedStageMap.get(col.status.name.toLowerCase())?.agents ?? [];
                    const dotColor = statusColorToCSS(col.status.color);

                    return (
                      <div key={col.status.option_id} className="celestial-panel flex h-full min-w-0 flex-col items-center gap-2 rounded-[1.2rem] border border-border/75 bg-background/28 p-4 text-center shadow-sm">
                        <span className="h-3 w-3 rounded-full" style={{ backgroundColor: dotColor }} />
                        <span className="text-sm font-medium">{col.status.name}</span>
                        <span className="text-xs text-muted-foreground">{col.item_count} items</span>
                        {assigned.length > 0 ? (
                          <div className="mt-1 flex flex-wrap justify-center gap-1">
                            {assigned.map((assignment) => (
                              <span key={assignment.id} className="solar-chip rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]">
                                {formatAgentName(assignment.agent_slug, assignment.agent_display_name)}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="mt-1 text-[10px] text-muted-foreground/60">No agents</span>
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
                    <div className="text-4xl mb-2">🔍</div>
                    <h3 className="text-xl font-semibold">No issues match the current view</h3>
                    <p className="text-muted-foreground">Try adjusting your filter, sort, or group settings.</p>
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
                    <div className="text-4xl mb-2">📭</div>
                    <h3 className="text-xl font-semibold">No items yet</h3>
                    <p className="text-muted-foreground">This project has no items. Add items in GitHub to see them here.</p>
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

      {selectedItem && (
        <IssueDetailModal item={selectedItem} onClose={handleCloseModal} />
      )}
    </div>
  );
}
