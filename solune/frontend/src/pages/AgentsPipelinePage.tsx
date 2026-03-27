/** AgentsPipelinePage — pipeline visualization, CRUD, agent config & activity feed. */

import { useEffect, useCallback, useMemo, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useAgentConfig, useAvailableAgents } from '@/hooks/useAgentConfig';
import { usePipelineConfig, pipelineKeys } from '@/hooks/usePipelineConfig';
import { useModels } from '@/hooks/useModels';
import { useConfirmation } from '@/hooks/useConfirmation';
import { useUnsavedPipelineGuard } from '@/hooks/useUnsavedPipelineGuard';
import { pipelinesApi } from '@/services/api';
import { PipelineBoard } from '@/components/pipeline/PipelineBoard';
import { PipelineToolbar } from '@/components/pipeline/PipelineToolbar';
import { SavedWorkflowsList } from '@/components/pipeline/SavedWorkflowsList';
import { UnsavedChangesDialog } from '@/components/pipeline/UnsavedChangesDialog';
import { PipelineAnalytics } from '@/components/pipeline/PipelineAnalytics';
import { PipelineRunHistory } from '@/components/pipeline/PipelineRunHistory';
import { PipelineStagesOverview } from '@/components/pipeline/PipelineStagesOverview';
import { PipelineEmptyBoard } from '@/components/pipeline/PipelineEmptyBoard';
import { PipelineNavigationBlocker } from '@/components/pipeline/PipelineNavigationBlocker';
import { ProjectSelectionEmptyState } from '@/components/common/ProjectSelectionEmptyState';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { Button } from '@/components/ui/button';

export function AgentsPipelinePage() {
  const { user } = useAuth();
  const {
    selectedProject,
    projects,
    isLoading: projectsLoading,
    selectProject,
  } = useProjects(user?.selected_project_id);
  const projectId = selectedProject?.project_id ?? null;
  const queryClient = useQueryClient();

  const { boardData, boardLoading } = useProjectBoard({ selectedProjectId: projectId });
  const agentConfig = useAgentConfig(projectId);
  const {
    agents: availableAgents,
    isLoading: agentsLoading,
    error: agentsError,
    refetch: refetchAgents,
  } = useAvailableAgents(projectId);
  const pipelineConfig = usePipelineConfig(projectId);
  const { models: availableModels } = useModels();
  const { confirm } = useConfirmation();

  const columns = useMemo(() => boardData?.columns ?? [], [boardData?.columns]);
  const alignedColumnCount = Math.max(columns.length, pipelineConfig.pipeline?.stages.length ?? 0, 1);
  const pipelineEditorRef = useRef<HTMLDivElement | null>(null);

  const focusPipelineEditor = useCallback(() => {
    requestAnimationFrame(() => {
      pipelineEditorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }, []);

  const seededRef = useRef(false);
  useEffect(() => {
    if (!projectId || seededRef.current) return;
    seededRef.current = true;
    pipelinesApi
      .seedPresets(projectId)
      .then(() => queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) }))
      .catch(() => { /* best-effort */ });
  }, [projectId, queryClient]);

  // Unsaved changes guard
  const {
    unsavedDialog, blocker, isBlocked,
    handleWorkflowSelect, handleWorkflowCopy, handleNewPipeline,
    handleDelete, handleUnsavedSave, handleUnsavedDiscard, handleUnsavedCancel,
  } = useUnsavedPipelineGuard({
    pipelineConfig, projectId, confirm, focusPipelineEditor, columns,
  });

  return (
    <div className="celestial-fade-in flex h-full flex-col gap-6 overflow-auto rounded-[1.75rem] border border-border/70 bg-background/42 p-6 backdrop-blur-sm dark:border-border/85 dark:bg-[linear-gradient(180deg,hsl(var(--night)/0.96)_0%,hsl(var(--panel)/0.9)_100%)]">
      {/* Page Header */}
      <CelestialCatalogHero
        eyebrow="Constellation Flow"
        title="Orchestrate agents across every stage."
        description="Build custom pipelines that route issues through agents as they move across board columns. Create stages, assign agents, pick models, and save reusable workflows."
        badge={
          selectedProject ? `${selectedProject.owner_login}/${selectedProject.name}` : 'Awaiting project'
        }
        note="Design once, assign to a project, and let the pipeline run automatically whenever items transition between board columns."
        stats={[
          { label: 'Saved pipelines', value: String(pipelineConfig.pipelines?.pipelines.length ?? 0) },
          { label: 'Active stages', value: String(pipelineConfig.pipeline?.stages.length ?? 0) },
          { label: 'Assigned pipeline', value: pipelineConfig.pipelines?.pipelines.find((p) => p.id === pipelineConfig.assignedPipelineId)?.name ?? 'None' },
          { label: 'Project', value: selectedProject?.name ?? 'Unselected' },
        ]}
        actions={
          <>
            <Button variant="default" size="lg" onClick={handleNewPipeline}>
              New pipeline
            </Button>
            <Button variant="outline" size="lg" asChild>
              <a href="#saved-pipelines">Saved workflows</a>
            </Button>
          </>
        }
      />

      {/* No project selected */}
      {!projectId && (
        <ProjectSelectionEmptyState
          projects={projects}
          isLoading={projectsLoading}
          selectedProjectId={projectId}
          onSelectProject={selectProject}
          description="Choose a GitHub Project to configure its agent pipeline stages, saved workflows, and stage-to-agent routing."
        />
      )}

      {projectId && boardLoading && (
        <div className="flex flex-col items-center justify-center flex-1 gap-4">
          <CelestialLoader size="md" label="Loading pipelines…" />
        </div>
      )}

      {projectId && !boardLoading && boardData && (
        <>
          <div ref={pipelineEditorRef} className="flex flex-col gap-4 scroll-mt-6">
            {/* Pipeline Toolbar */}
            <PipelineToolbar
              boardState={pipelineConfig.boardState}
              isDirty={pipelineConfig.isDirty}
              isSaving={pipelineConfig.isSaving}
              isPreset={pipelineConfig.isPreset}
              pipelineName={pipelineConfig.pipeline?.name}
              validationErrors={pipelineConfig.validationErrors}
              onSave={pipelineConfig.savePipeline}
              onSaveAsCopy={(newName) => pipelineConfig.saveAsCopy(newName)}
              onDelete={handleDelete}
              onDiscard={pipelineConfig.discardChanges}
            />

            {/* Pipeline Board */}
            {pipelineConfig.boardState !== 'empty' && pipelineConfig.pipeline && (
              <PipelineBoard
                columnCount={alignedColumnCount}
                stages={pipelineConfig.pipeline.stages}
                availableAgents={availableAgents}
                agentsLoading={agentsLoading}
                agentsError={agentsError}
                onRetryAgents={refetchAgents}
                availableModels={availableModels}
                isEditMode={pipelineConfig.boardState === 'editing'}
                pipelineName={pipelineConfig.pipeline.name}
                projectId={projectId}
                modelOverride={pipelineConfig.modelOverride}
                validationErrors={pipelineConfig.validationErrors}
                onNameChange={pipelineConfig.setPipelineName}
                onModelOverrideChange={pipelineConfig.setModelOverride}
                onClearValidationError={pipelineConfig.clearValidationError}
                onRemoveStage={pipelineConfig.removeStage}
                onAddAgent={(stageId, slug, groupId) => {
                  const agent = availableAgents.find((a) => a.slug === slug);
                  if (agent) pipelineConfig.addAgentToStage(stageId, agent, groupId);
                }}
                onRemoveAgent={pipelineConfig.removeAgentFromStage}
                onUpdateAgent={pipelineConfig.updateAgentInStage}
                onUpdateStage={(stageId, updates) => pipelineConfig.updateStage(stageId, updates)}
                onCloneAgent={(stageId, agentNodeId) =>
                  pipelineConfig.cloneAgentInStage(stageId, agentNodeId)
                }
                onReorderAgents={pipelineConfig.reorderAgentsInStage}
                onAddGroup={pipelineConfig.addGroupToStage}
                onRemoveGroup={pipelineConfig.removeGroupFromStage}
                onToggleGroupMode={pipelineConfig.updateGroupExecutionMode}
                onReorderAgentsInGroup={pipelineConfig.reorderAgentsInGroup}
              />
            )}

            {/* Empty board state */}
            {pipelineConfig.boardState === 'empty' && (
              <PipelineEmptyBoard onCreatePipeline={handleNewPipeline} />
            )}
          </div>

          {/* Save error display */}
          {pipelineConfig.saveError && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-2 text-sm text-destructive">
              {pipelineConfig.saveError}
            </div>
          )}

          {/* Pipeline Stages Visualization */}
          <PipelineStagesOverview
            columns={columns}
            localMappings={agentConfig.localMappings}
            alignedColumnCount={alignedColumnCount}
          />

          {/* Saved Workflows List */}
          <SavedWorkflowsList
            pipelines={pipelineConfig.pipelines?.pipelines ?? []}
            activePipelineId={pipelineConfig.editingPipelineId}
            assignedPipelineId={pipelineConfig.assignedPipelineId}
            isLoading={pipelineConfig.pipelinesLoading}
            onSelect={handleWorkflowSelect}
            onCopy={handleWorkflowCopy}
            onAssign={pipelineConfig.assignPipeline}
          />

          {/* Pipeline Analytics Dashboard */}
          <PipelineAnalytics pipelines={pipelineConfig.pipelines?.pipelines ?? []} />

          {/* Pipeline Run History */}
          {pipelineConfig.editingPipelineId && (
            <PipelineRunHistory pipelineId={pipelineConfig.editingPipelineId} />
          )}
        </>
      )}

      {/* Unsaved Changes Dialog */}
      <UnsavedChangesDialog
        isOpen={unsavedDialog.isOpen}
        onSave={handleUnsavedSave}
        onDiscard={handleUnsavedDiscard}
        onCancel={handleUnsavedCancel}
        actionDescription={unsavedDialog.description}
      />

      {/* SPA navigation blocker — shown when react-router navigation is blocked */}
      <PipelineNavigationBlocker
        isBlocked={isBlocked}
        onStay={() => blocker.reset?.()}
        onLeave={() => blocker.proceed?.()}
      />
    </div>
  );
}
