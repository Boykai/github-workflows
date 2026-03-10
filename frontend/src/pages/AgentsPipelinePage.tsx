/**
 * AgentsPipelinePage — Pipeline visualization + pipeline CRUD + agent config + activity feed.
 * Composes useProjectBoard columns with agent configuration, pipeline board, and saved workflows.
 */

import { useState, useEffect, useCallback, useMemo, useRef, type CSSProperties } from 'react';
import { useBlocker } from 'react-router-dom';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useAgentConfig, useAvailableAgents } from '@/hooks/useAgentConfig';
import { useWorkflow } from '@/hooks/useWorkflow';
import { usePipelineConfig, pipelineKeys } from '@/hooks/usePipelineConfig';
import { useModels } from '@/hooks/useModels';
import { useConfirmation } from '@/hooks/useConfirmation';
import { pipelinesApi } from '@/services/api';
import { AgentConfigRow } from '@/components/board/AgentConfigRow';
import { AddAgentPopover } from '@/components/board/AddAgentPopover';
import { statusColorToCSS } from '@/components/board/colorUtils';
import { PipelineBoard } from '@/components/pipeline/PipelineBoard';
import { PipelineToolbar } from '@/components/pipeline/PipelineToolbar';
import { SavedWorkflowsList } from '@/components/pipeline/SavedWorkflowsList';
import { UnsavedChangesDialog } from '@/components/pipeline/UnsavedChangesDialog';
import { PipelineFlowGraph } from '@/components/pipeline/PipelineFlowGraph';
import { ProjectSelectionEmptyState } from '@/components/common/ProjectSelectionEmptyState';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { Button } from '@/components/ui/button';
import { Tooltip } from '@/components/ui/tooltip';
import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';
import { formatAgentName } from '@/utils/formatAgentName';

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
  const { config: workflowConfig } = useWorkflow();
  const pipelineConfig = usePipelineConfig(projectId);
  const { models: availableModels } = useModels();
  const { confirm } = useConfirmation();

  const columns = useMemo(() => boardData?.columns ?? [], [boardData?.columns]);
  const alignedColumnCount = Math.max(
    columns.length,
    pipelineConfig.pipeline?.stages.length ?? 0,
    1
  );
  const alignedGridStyle: CSSProperties = {
    gridTemplateColumns: `repeat(${alignedColumnCount}, minmax(14rem, 1fr))`,
  };
  const pipelineEditorRef = useRef<HTMLDivElement | null>(null);

  const focusPipelineEditor = useCallback(() => {
    requestAnimationFrame(() => {
      pipelineEditorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }, []);

  // Seed presets on mount
  const seededRef = useRef(false);
  useEffect(() => {
    if (!projectId || seededRef.current) return;
    seededRef.current = true;
    pipelinesApi
      .seedPresets(projectId)
      .then(() => {
        queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
      })
      .catch((err) => {
        console.warn('Failed to seed preset pipelines:', err);
      });
  }, [projectId, queryClient]);

  // Block in-app SPA navigation when there are unsaved changes
  useBlocker(pipelineConfig.isDirty);

  // Unsaved changes dialog state
  const [unsavedDialog, setUnsavedDialog] = useState<{
    isOpen: boolean;
    pendingAction: (() => void) | null;
    description: string;
  }>({ isOpen: false, pendingAction: null, description: '' });

  // Browser navigation guard
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (pipelineConfig.isDirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [pipelineConfig.isDirty]);

  // Handle selecting a saved workflow with unsaved changes check
  const handleWorkflowSelect = useCallback(
    (pipelineId: string) => {
      if (pipelineConfig.isDirty) {
        setUnsavedDialog({
          isOpen: true,
          pendingAction: async () => {
            await pipelineConfig.loadPipeline(pipelineId);
            focusPipelineEditor();
          },
          description: 'Loading a different workflow will discard your changes',
        });
      } else {
        pipelineConfig.loadPipeline(pipelineId).then(() => {
          focusPipelineEditor();
        });
      }
    },
    [focusPipelineEditor, pipelineConfig]
  );

  // Handle new pipeline with unsaved changes check
  const handleNewPipeline = useCallback(() => {
    const initialStageNames = columns.map((column) => column.status.name);

    if (pipelineConfig.isDirty) {
      setUnsavedDialog({
        isOpen: true,
        pendingAction: () => pipelineConfig.newPipeline(initialStageNames),
        description: 'Creating a new pipeline will discard your changes',
      });
    } else {
      pipelineConfig.newPipeline(initialStageNames);
    }
  }, [columns, pipelineConfig]);

  // Handle delete with confirmation
  const handleDelete = useCallback(async () => {
    const confirmed = await confirm({
      title: 'Delete Pipeline',
      description: 'Are you sure you want to delete this pipeline? This action cannot be undone.',
      variant: 'danger',
      confirmLabel: 'Delete Pipeline',
    });
    if (confirmed) {
      pipelineConfig.deletePipeline();
    }
  }, [pipelineConfig, confirm]);

  // Unsaved dialog handlers
  const handleUnsavedSave = useCallback(async () => {
    const saved = await pipelineConfig.savePipeline();
    const action = unsavedDialog.pendingAction;
    setUnsavedDialog({ isOpen: false, pendingAction: null, description: '' });
    if (saved) {
      action?.();
    }
  }, [pipelineConfig, unsavedDialog.pendingAction]);

  const handleUnsavedDiscard = useCallback(() => {
    pipelineConfig.discardChanges();
    const action = unsavedDialog.pendingAction;
    setUnsavedDialog({ isOpen: false, pendingAction: null, description: '' });
    action?.();
  }, [pipelineConfig, unsavedDialog.pendingAction]);

  const handleUnsavedCancel = useCallback(() => {
    setUnsavedDialog({ isOpen: false, pendingAction: null, description: '' });
  }, []);

  return (
    <div className="celestial-fade-in flex h-full flex-col gap-6 rounded-[1.75rem] border border-border/70 bg-background/42 p-6 backdrop-blur-sm overflow-auto">
      {/* Page Header */}
      <CelestialCatalogHero
        eyebrow="Constellation Flow"
        title="Orchestrate agents across every stage."
        description="Build custom pipelines that route issues through agents as they move across board columns. Create stages, assign agents, pick models, and save reusable workflows."
        badge={
          selectedProject
            ? `${selectedProject.owner_login}/${selectedProject.name}`
            : 'Awaiting project'
        }
        note="Design once, assign to a project, and let the pipeline run automatically whenever items transition between board columns."
        stats={[
          {
            label: 'Saved pipelines',
            value: String(pipelineConfig.pipelines?.pipelines.length ?? 0),
          },
          { label: 'Active stages', value: String(pipelineConfig.pipeline?.stages.length ?? 0) },
          {
            label: 'Assigned pipeline',
            value:
              pipelineConfig.pipelines?.pipelines.find(
                (p) => p.id === pipelineConfig.assignedPipelineId
              )?.name ?? 'None',
          },
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
                onAddAgent={(stageId, slug) => {
                  const agent = availableAgents.find((a) => a.slug === slug);
                  if (agent) pipelineConfig.addAgentToStage(stageId, agent);
                }}
                onRemoveAgent={pipelineConfig.removeAgentFromStage}
                onUpdateAgent={pipelineConfig.updateAgentInStage}
                onUpdateStage={(stageId, updates) => pipelineConfig.updateStage(stageId, updates)}
                onCloneAgent={(stageId, agentNodeId) =>
                  pipelineConfig.cloneAgentInStage(stageId, agentNodeId)
                }
                onReorderAgents={pipelineConfig.reorderAgentsInStage}
                pipelineBlocking={pipelineConfig.pipeline?.blocking ?? false}
                onBlockingChange={pipelineConfig.setPipelineBlocking}
              />
            )}

            {/* Empty board state */}
            {pipelineConfig.boardState === 'empty' && (
              <div className="celestial-panel flex flex-col items-center justify-center gap-3 rounded-[1.2rem] border border-dashed border-border/60 bg-background/24 p-8 text-center">
                <Tooltip contentKey="pipeline.board.createButton">
                  <button
                    type="button"
                    onClick={handleNewPipeline}
                    className="group relative mb-2 flex h-24 w-24 items-center justify-center rounded-full transition-transform duration-200 hover:scale-[1.03] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                    aria-label="Create new pipeline"
                  >
                    <div className="absolute inset-0 rounded-full border border-border/40 bg-[radial-gradient(circle_at_center,hsl(var(--glow)/0.22)_0%,transparent_62%)] transition-colors duration-200 group-hover:border-primary/30 group-hover:bg-[radial-gradient(circle_at_center,hsl(var(--glow)/0.32)_0%,transparent_62%)]" />
                    <div className="absolute inset-[10px] rounded-full border border-primary/18 transition-colors duration-200 group-hover:border-primary/35" />
                    <span className="absolute left-1/2 top-1.5 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-[hsl(var(--glow))] shadow-[0_0_12px_hsl(var(--glow)/0.8)]" />
                    <span className="absolute bottom-4 right-2 h-2.5 w-2.5 rounded-full bg-[hsl(var(--gold))] shadow-[0_0_18px_hsl(var(--gold)/0.45)]" />
                    <span className="absolute left-2 top-1/2 h-2 w-2 -translate-y-1/2 rounded-full bg-[hsl(var(--gold)/0.55)]" />
                    <ThemedAgentIcon
                      name="Pipeline constellation"
                      iconName="constellation"
                      size="lg"
                      className="h-14 w-14 border-primary/30 shadow-[0_12px_30px_hsl(var(--night)/0.3)] transition-transform duration-200 group-hover:scale-105"
                    />
                  </button>
                </Tooltip>
                <h3 className="text-sm font-semibold text-foreground">Create new agent pipeline</h3>
                <p className="text-xs text-muted-foreground max-w-md">
                  Build custom agent workflows by creating a pipeline with stages and agents. Click
                  the constellation to get started.
                </p>
              </div>
            )}
          </div>

          {/* Save error display */}
          {pipelineConfig.saveError && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-2 text-sm text-destructive">
              {pipelineConfig.saveError}
            </div>
          )}

          {/* Agent Config Row — drag-and-drop assignment */}
          <AgentConfigRow
            columnCount={alignedColumnCount}
            columns={columns}
            agentConfig={agentConfig}
            availableAgents={availableAgents}
            variant="compact"
            title="Current Pipeline"
            workflowEnabled={workflowConfig?.enabled ?? null}
            renderAddButton={(status: string) => (
              <AddAgentPopover
                status={status}
                availableAgents={availableAgents}
                assignedAgents={agentConfig.localMappings[status] ?? []}
                isLoading={agentsLoading}
                error={agentsError}
                onRetry={refetchAgents}
                onAddAgent={agentConfig.addAgent}
                compact={true}
              />
            )}
          />

          {/* Pipeline Stages Visualization */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Pipeline Stages</h3>
            <div className="overflow-x-auto pb-2">
              <div className="grid min-w-full items-stretch gap-3" style={alignedGridStyle}>
                {columns.map((col) => {
                  const assigned = agentConfig.localMappings[col.status.name] ?? [];
                  const dotColor = statusColorToCSS(col.status.color);
                  return (
                    <div
                      key={col.status.option_id}
                      className="celestial-panel flex h-full min-w-0 flex-col items-center gap-2 rounded-[1.2rem] border border-border/75 bg-background/28 p-4 text-center shadow-sm"
                    >
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: dotColor }}
                      />
                      <span className="text-sm font-medium">{col.status.name}</span>
                      <span className="text-xs text-muted-foreground">{col.item_count} items</span>
                      {assigned.length > 0 ? (
                        <div className="flex flex-wrap gap-1 justify-center mt-1">
                          {assigned.map((a) => (
                            <span
                              key={a.id}
                              className="solar-chip rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]"
                            >
                              {formatAgentName(a.slug, a.display_name)}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-[10px] text-muted-foreground/60 mt-1">No agents</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Saved Workflows List */}
          <SavedWorkflowsList
            pipelines={pipelineConfig.pipelines?.pipelines ?? []}
            activePipelineId={pipelineConfig.editingPipelineId}
            assignedPipelineId={pipelineConfig.assignedPipelineId}
            isLoading={pipelineConfig.pipelinesLoading}
            onSelect={handleWorkflowSelect}
            onAssign={pipelineConfig.assignPipeline}
          />

          {/* Activity Feed with flow graph for recent pipelines */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Recent Activity</h3>
            <div className="celestial-panel rounded-[1.2rem] border border-border/75 p-4">
              {(pipelineConfig.pipelines?.pipelines ?? []).length > 0 ? (
                <div className="overflow-x-auto pb-2">
                  <div className="flex min-w-full flex-col gap-3">
                    {(pipelineConfig.pipelines?.pipelines ?? []).slice(0, 3).map((p) => (
                      <div key={p.id} className="grid min-w-full gap-3" style={alignedGridStyle}>
                        <div className="col-[1/-1] rounded-[1rem] border border-border/40 bg-background/12 p-3">
                          <PipelineFlowGraph
                            stages={p.stages ?? []}
                            width={220}
                            height={84}
                            responsive={true}
                            className="w-full"
                          />
                          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                            <div className="min-w-0">
                              <Tooltip content={p.name}>
                                <p className="truncate text-xs font-medium text-foreground">
                                  {p.name}
                                </p>
                              </Tooltip>
                              <p className="text-[10px] text-muted-foreground">
                                {p.stage_count} stages · {p.agent_count} agents
                              </p>
                            </div>
                            <span className="solar-chip-soft rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em]">
                              Recent pipeline
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  {(pipelineConfig.pipelines?.pipelines ?? []).length > 3 && (
                    <p className="mt-2 text-center text-xs text-muted-foreground">
                      Showing 3 of {(pipelineConfig.pipelines?.pipelines ?? []).length} —{' '}
                      <a href="#saved-pipelines" className="text-primary/70 hover:text-primary underline-offset-2 hover:underline">
                        see all in Saved Pipelines
                      </a>
                    </p>
                  )}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">
                  Agent workflow events will appear here as agents process items
                </p>
              )}
            </div>
          </div>
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
    </div>
  );
}
