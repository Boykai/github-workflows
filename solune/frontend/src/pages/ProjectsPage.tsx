import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRateLimitStatus } from '@/context/RateLimitContext';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useRealTimeSync } from '@/hooks/useRealTimeSync';
import { useBoardRefresh } from '@/hooks/useBoardRefresh';
import { useProjects } from '@/hooks/useProjects';
import { useAuth } from '@/hooks/useAuth';
import { useProjectSettings } from '@/hooks/useSettings';
import { useConfirmation } from '@/hooks/useConfirmation';
import { useBoardStatusUpdate } from '@/hooks/useBoardStatusUpdate';
import { IssueDetailModal } from '@/components/board/IssueDetailModal';
import { ProjectIssueLaunchPanel } from '@/components/board/ProjectIssueLaunchPanel';
import { PipelineStagesSection } from '@/components/board/PipelineStagesSection';
import { ProjectBoardErrorBanners } from '@/components/board/ProjectBoardErrorBanners';
import { ProjectBoardContent } from '@/components/board/ProjectBoardContent';
import { ProjectsBoardToolbar } from '@/components/board/ProjectsBoardToolbar';
import { ProjectSelectionEmptyState } from '@/components/common/ProjectSelectionEmptyState';
import { useAvailableAgents } from '@/hooks/useAgentConfig';
import { useBoardControls } from '@/hooks/useBoardControls';
import { extractRateLimitInfo, isRateLimitApiError } from '@/utils/rateLimit';
import type { BoardItem } from '@/types';
import { pipelinesApi } from '@/services/api';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

export function ProjectsPage() {
  const { updateRateLimit } = useRateLimitStatus();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { confirm } = useConfirmation();
  const {
    selectedProject, projects, isLoading: projectsListLoading, selectProject,
  } = useProjects(user?.selected_project_id);

  const {
    projectsRateLimitInfo, projectsLoading, projectsError, selectedProjectId,
    boardData, boardLoading, isFetching, boardError, lastUpdated,
    selectProject: selectBoardProject,
  } = useProjectBoard({
    selectedProjectId: selectedProject?.project_id,
    onProjectSelect: selectProject,
  });

  // Stable ref so useRealTimeSync can call the latest resetTimer.
  const resetTimerRef = useRef<() => void>(() => {});
  const stableResetTimer = useCallback(() => resetTimerRef.current(), []);
  const { status: syncStatus, lastUpdate: syncLastUpdate } = useRealTimeSync(selectedProjectId, {
    onRefreshTriggered: stableResetTimer,
  });
  const isWebSocketConnected = syncStatus === 'connected';
  const {
    refresh, isRefreshing, error: refreshError, rateLimitInfo, isRateLimitLow, resetTimer,
  } = useBoardRefresh({ projectId: selectedProjectId, boardData, isWebSocketConnected });
  useEffect(() => { resetTimerRef.current = resetTimer; }, [resetTimer]);

  const [selectedItem, setSelectedItem] = useState<BoardItem | null>(null);
  const { agents: availableAgents } = useAvailableAgents(selectedProjectId);
  const boardControls = useBoardControls(selectedProjectId, boardData ?? undefined);
  const transformedBoardData = boardControls.transformedData;
  const { settings: projectSettings, updateSettings, isUpdating: isSettingsUpdating } =
    useProjectSettings(selectedProjectId ?? undefined);
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
    data: savedPipelines, isLoading: savedPipelinesLoading,
    error: savedPipelinesError, refetch: refetchSavedPipelines,
  } = useQuery({
    queryKey: ['pipelines', selectedProjectId],
    queryFn: () => pipelinesApi.list(selectedProjectId!),
    enabled: !!selectedProjectId,
    staleTime: 60_000,
  });

  const handleToggleAutoMerge = useCallback(async () => {
    if (!selectedProjectId) return;
    if (!isAutoMerge) {
      const hasPipelines = Array.isArray(savedPipelines) && savedPipelines.length > 0;
      if (hasPipelines) {
        const confirmed = await confirm({
          title: 'Enable Auto Merge',
          description: `Enable auto-merge for this project? This will also apply to ${savedPipelines.length} existing pipeline(s) and may change how they are merged.`,
          variant: 'warning',
          confirmLabel: 'Enable Auto Merge',
        });
        if (!confirmed) return;
      }
    }
    try {
      await updateSettings({ auto_merge: !isAutoMerge });
      toast.success(isAutoMerge ? 'Auto merge disabled' : 'Auto merge enabled');
    } catch {
      toast.error('Failed to update auto merge');
    }
  }, [selectedProjectId, isAutoMerge, updateSettings, savedPipelines, confirm]);

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
  const handleStatusUpdate = useBoardStatusUpdate(selectedProjectId);
  const assignedPipelineName = useMemo(
    () => savedPipelines?.pipelines.find(
      (p) => p.id === (pipelineAssignment?.pipeline_id ?? ''),
    )?.name ?? 'None assigned',
    [pipelineAssignment?.pipeline_id, savedPipelines],
  );
  const heroStats = useMemo(() => [
    { label: 'Board columns', value: String(transformedBoardData?.columns.length ?? 0) },
    { label: 'Total items', value: String(transformedBoardData?.columns.reduce((sum, c) => sum + c.items.length, 0) ?? 0) },
    { label: 'Pipeline', value: assignedPipelineName },
    { label: 'Project', value: selectedProject?.name ?? 'Unselected' },
  ], [transformedBoardData?.columns, assignedPipelineName, selectedProject?.name]);

  // ── Rate limit derivations ──
  const projectsRateLimitError = isRateLimitApiError(projectsError);
  const boardRateLimitError = isRateLimitApiError(boardError);
  const refreshRateLimitError = refreshError?.type === 'rate_limit';
  const effectiveRateLimitInfo =
    rateLimitInfo ?? projectsRateLimitInfo ?? refreshError?.rateLimitInfo ??
    extractRateLimitInfo(boardError) ?? extractRateLimitInfo(projectsError);
  const hasActiveRateLimitError = refreshRateLimitError || boardRateLimitError || projectsRateLimitError;
  const rateLimitState = useMemo(
    () => ({ info: effectiveRateLimitInfo ?? null, hasError: hasActiveRateLimitError }),
    [effectiveRateLimitInfo, hasActiveRateLimitError],
  );
  useEffect(() => { updateRateLimit(rateLimitState); }, [rateLimitState, updateRateLimit]);

  const rateLimitRetryAfter = refreshError?.retryAfter ??
    (effectiveRateLimitInfo ? new Date(effectiveRateLimitInfo.reset_at * 1000) : undefined);
  const showRateLimitBanner = refreshRateLimitError || boardRateLimitError || projectsRateLimitError;

  return (
    <div className="projects-page-shell celestial-fade-in flex h-full flex-col gap-5 overflow-visible rounded-[1.75rem] border border-border/70 bg-background/35 p-4 backdrop-blur-sm sm:p-6">
      <CelestialCatalogHero
        className="projects-catalog-hero"
        eyebrow="Mission Control"
        title="Every project, mapped and moving."
        description="Live Kanban view of your GitHub Project. Filter, sort, and group issues across pipeline stages, then trigger agents directly from the board."
        badge={selectedProject ? `${selectedProject.owner_login}/${selectedProject.name}` : 'Awaiting project'}
        note="Use the board to triage work and queue items for the active agent pipeline — all without leaving the project view."
        stats={heroStats}
        actions={<>
          <Button variant="default" size="lg" asChild><a href="#board">View board</a></Button>
          <Button variant="outline" size="lg" asChild><a href="#pipeline-stages">Pipeline stages</a></Button>
        </>}
      />
      <ProjectsBoardToolbar
        selectedProjectId={selectedProjectId}
        syncStatus={syncStatus}
        onRefresh={refresh}
        isRefreshing={isRefreshing || (isFetching && !boardLoading)}
        lastUpdated={lastUpdated}
        syncLastUpdate={syncLastUpdate}
        hasBoardData={!!boardData}
        boardControls={boardControls}
        isQueueMode={isQueueMode}
        isAutoMerge={isAutoMerge}
        isSettingsUpdating={isSettingsUpdating}
        onToggleQueueMode={handleToggleQueueMode}
        onToggleAutoMerge={handleToggleAutoMerge}
      />
      <ProjectBoardErrorBanners
        showRateLimitBanner={showRateLimitBanner} rateLimitRetryAfter={rateLimitRetryAfter}
        isRateLimitLow={isRateLimitLow} rateLimitInfo={rateLimitInfo}
        refreshError={refreshError} projectsError={projectsError}
        projectsRateLimitError={projectsRateLimitError} boardError={boardError}
        boardLoading={boardLoading} boardRateLimitError={boardRateLimitError}
        selectedProjectId={selectedProjectId} onRetryBoard={selectBoardProject}
      />
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
            pipelinesError={savedPipelinesError instanceof Error ? savedPipelinesError.message : null}
            onRetryPipelines={() => { void refetchSavedPipelines(); }}
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
