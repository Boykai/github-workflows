/**
 * ProjectBoardPanels — Issue launch panel, pipeline stages, and board content.
 *
 * Extracted from ProjectsPage to keep the page ≤ 250 lines (FR-001).
 */

import { useQueryClient } from '@tanstack/react-query';
import { ProjectIssueLaunchPanel } from '@/components/board/ProjectIssueLaunchPanel';
import { PipelineStagesSection } from '@/components/board/PipelineStagesSection';
import { ProjectBoardContent } from '@/components/board/ProjectBoardContent';
import type { AvailableAgent, BoardItem, BoardDataResponse, PipelineConfigSummary } from '@/types';
import type { UseMutationResult } from '@tanstack/react-query';

interface ProjectBoardPanelsProps {
  projectId: string;
  projectName: string | undefined;
  pipelines: PipelineConfigSummary[];
  isLoadingPipelines: boolean;
  pipelinesError: Error | null;
  refetchPipelines: () => void;
  onRefresh: () => void;
  boardData: BoardDataResponse;
  boardControls: Parameters<typeof ProjectBoardContent>[0]['boardControls'];
  assignedPipelineId: string | undefined;
  assignPipelineMutation: UseMutationResult<unknown, Error, string, unknown>;
  onCardClick: (item: BoardItem) => void;
  availableAgents: AvailableAgent[];
  onStatusUpdate: (itemId: string, newStatus: string) => Promise<void>;
}

export function ProjectBoardPanels({
  projectId,
  projectName,
  pipelines,
  isLoadingPipelines,
  pipelinesError,
  refetchPipelines,
  onRefresh,
  boardData,
  boardControls,
  assignedPipelineId,
  assignPipelineMutation,
  onCardClick,
  availableAgents,
  onStatusUpdate,
}: ProjectBoardPanelsProps) {
  const queryClient = useQueryClient();

  return (
    <div className="flex flex-1 flex-col gap-6 overflow-visible">
      <ProjectIssueLaunchPanel
        projectId={projectId}
        projectName={projectName}
        pipelines={pipelines}
        isLoadingPipelines={isLoadingPipelines}
        pipelinesError={pipelinesError instanceof Error ? pipelinesError.message : null}
        onRetryPipelines={refetchPipelines}
        onLaunched={() => {
          onRefresh();
          void queryClient.invalidateQueries({
            queryKey: ['pipelines', 'assignment', projectId],
          });
        }}
      />

      <PipelineStagesSection
        key={projectId}
        columns={boardData.columns}
        savedPipelines={pipelines}
        assignedPipelineId={assignedPipelineId}
        assignPipelineMutation={assignPipelineMutation}
      />

      <ProjectBoardContent
        boardData={boardData}
        boardControls={boardControls}
        onCardClick={onCardClick}
        availableAgents={availableAgents}
        onStatusUpdate={onStatusUpdate}
      />
    </div>
  );
}
