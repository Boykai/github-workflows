/**
 * ProjectsPage — Project board with enhanced Kanban view.
 * Migrated from ProjectBoardPage with page header, toolbar, and enhanced cards.
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { useRateLimitStatus } from '@/context/RateLimitContext';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useRealTimeSync } from '@/hooks/useRealTimeSync';
import { useBoardRefresh } from '@/hooks/useBoardRefresh';
import { useProjects } from '@/hooks/useProjects';
import { useAuth } from '@/hooks/useAuth';
import { useProjectSettings } from '@/hooks/useSettings';
import { IssueDetailModal } from '@/components/board/IssueDetailModal';
import { ProjectBoardErrorBanners } from '@/components/board/ProjectBoardErrorBanners';
import { ProjectBoardToolbar } from '@/components/board/ProjectBoardToolbar';
import { ProjectBoardPanels } from '@/components/board/ProjectBoardPanels';
import { ProjectSelectionEmptyState } from '@/components/common/ProjectSelectionEmptyState';
import { useAvailableAgents } from '@/hooks/useAgentConfig';
import { useBoardControls } from '@/hooks/useBoardControls';
import { useBoardStatusMutation } from '@/hooks/useBoardStatusMutation';
import { useProjectPipelines } from '@/hooks/useProjectPipelines';
import { extractRateLimitInfo, isRateLimitApiError } from '@/utils/rateLimit';
import { computeRateLimitState } from '@/utils/projectBoardUtils';
import type { BoardItem } from '@/types';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { Button } from '@/components/ui/button';

export function ProjectsPage() {
  const { updateRateLimit } = useRateLimitStatus();
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

  const { agents: availableAgents } = useAvailableAgents(selectedProjectId);

  // Board controls: filter, sort, group-by with localStorage persistence
  const boardControls = useBoardControls(selectedProjectId, boardData ?? undefined);
  const transformedBoardData = boardControls.transformedData;

  // Project settings for queue mode / auto-merge toggles
  const { settings: projectSettings, updateSettings, isUpdating: isSettingsUpdating } = useProjectSettings(selectedProjectId ?? undefined);
  const isQueueMode = projectSettings?.project?.board_display_config?.queue_mode ?? false;
  const isAutoMerge = projectSettings?.project?.board_display_config?.auto_merge ?? false;

  const {
    savedPipelines,
    savedPipelinesLoading,
    savedPipelinesError,
    refetchSavedPipelines,
    pipelineAssignment,
    assignPipelineMutation,
  } = useProjectPipelines(selectedProjectId);

  const handleCardClick = useCallback((item: BoardItem) => setSelectedItem(item), []);
  const handleCloseModal = useCallback(() => setSelectedItem(null), []);
  const handleStatusUpdate = useBoardStatusMutation(selectedProjectId);

  const assignedPipelineName = useMemo(
    () =>
      savedPipelines?.pipelines.find(
        (pipeline) => pipeline.id === (pipelineAssignment?.pipeline_id ?? ''),
      )?.name ?? 'None assigned',
    [pipelineAssignment?.pipeline_id, savedPipelines],
  );

  const heroStats = useMemo(() => {
    const totalItems = transformedBoardData?.columns.reduce((s, c) => s + c.items.length, 0) ?? 0;
    return [
      { label: 'Board columns', value: String(transformedBoardData?.columns.length ?? 0) },
      { label: 'Total items', value: String(totalItems) },
      { label: 'Pipeline', value: assignedPipelineName },
      { label: 'Project', value: selectedProject?.name ?? 'Unselected' },
    ];
  }, [transformedBoardData?.columns, assignedPipelineName, selectedProject?.name]);

  // Rate limit state (extracted to utility for FR-001)
  const rlState = useMemo(
    () =>
      computeRateLimitState({
        projectsError,
        boardError,
        refreshError,
        rateLimitInfo,
        projectsRateLimitInfo,
        isRateLimitApiError,
        extractRateLimitInfo,
      }),
    [projectsError, boardError, refreshError, rateLimitInfo, projectsRateLimitInfo],
  );

  // Publish rate limit state to global context (T025).
  const rateLimitState = useMemo(
    () => ({ info: rlState.effectiveRateLimitInfo, hasError: rlState.hasActiveRateLimitError }),
    [rlState.effectiveRateLimitInfo, rlState.hasActiveRateLimitError],
  );
  useEffect(() => {
    updateRateLimit(rateLimitState);
  }, [rateLimitState, updateRateLimit]);

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
      <ProjectBoardToolbar
        selectedProjectId={selectedProjectId}
        boardData={boardData}
        syncStatus={syncStatus}
        syncLastUpdate={syncLastUpdate}
        lastUpdated={lastUpdated}
        isRefreshing={isRefreshing}
        isFetching={isFetching}
        boardLoading={boardLoading}
        onRefresh={refresh}
        boardControls={boardControls}
        isQueueMode={isQueueMode}
        isAutoMerge={isAutoMerge}
        isSettingsUpdating={isSettingsUpdating}
        updateSettings={updateSettings}
        savedPipelines={savedPipelines?.pipelines}
      />

      {/* Rate limit / error banners */}
      <ProjectBoardErrorBanners
        showRateLimitBanner={rlState.showRateLimitBanner}
        rateLimitRetryAfter={rlState.rateLimitRetryAfter}
        isRateLimitLow={isRateLimitLow}
        rateLimitInfo={rateLimitInfo}
        refreshError={refreshError}
        projectsError={projectsError}
        projectsRateLimitError={isRateLimitApiError(projectsError)}
        boardError={boardError}
        boardLoading={boardLoading}
        boardRateLimitError={isRateLimitApiError(boardError)}
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
          <CelestialLoader size="md" label="Loading board…" />
        </div>
      )}

      {selectedProjectId && !boardLoading && transformedBoardData && (
        <ProjectBoardPanels
          projectId={selectedProjectId}
          projectName={selectedProject?.name}
          pipelines={savedPipelines?.pipelines ?? []}
          isLoadingPipelines={savedPipelinesLoading}
          pipelinesError={savedPipelinesError}
          refetchPipelines={() => { void refetchSavedPipelines(); }}
          onRefresh={refresh}
          boardData={transformedBoardData}
          boardControls={boardControls}
          assignedPipelineId={pipelineAssignment?.pipeline_id}
          assignPipelineMutation={assignPipelineMutation}
          onCardClick={handleCardClick}
          availableAgents={availableAgents}
          onStatusUpdate={handleStatusUpdate}
        />
      )}

      {selectedItem && <IssueDetailModal item={selectedItem} onClose={handleCloseModal} />}
    </div>
  );
}
