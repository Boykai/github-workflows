/**
 * AgentsPipelinePage — Pipeline visualization + agent config + activity feed.
 * Composes useProjectBoard columns with agent configuration and workflow events.
 */

import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useAgentConfig, useAvailableAgents } from '@/hooks/useAgentConfig';
import { useWorkflow } from '@/hooks/useWorkflow';
import { AgentConfigRow } from '@/components/board/AgentConfigRow';
import { AddAgentPopover } from '@/components/board/AddAgentPopover';
import { AgentPresetSelector } from '@/components/board/AgentPresetSelector';
import { statusColorToCSS } from '@/components/board/colorUtils';

export function AgentsPipelinePage() {
  const { user } = useAuth();
  const { selectedProject } = useProjects(user?.selected_project_id);
  const projectId = selectedProject?.project_id ?? null;

  const { boardData, boardLoading } = useProjectBoard({ selectedProjectId: projectId });
  const agentConfig = useAgentConfig(projectId);
  const { agents: availableAgents, isLoading: agentsLoading, error: agentsError, refetch: refetchAgents } = useAvailableAgents(projectId);
  const { config: workflowConfig } = useWorkflow();

  const columns = boardData?.columns ?? [];

  return (
    <div className="flex h-full flex-col gap-6 rounded-[1.75rem] border border-border/70 bg-background/35 p-6 backdrop-blur-sm overflow-auto">
      {/* Page Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <p className="mb-1 text-xs uppercase tracking-[0.24em] text-primary/80">Constellation Flow</p>
          <h2 className="text-3xl font-display font-medium tracking-[0.04em]">Agents Pipeline</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Configure how agents process items across board columns
          </p>
        </div>
        {workflowConfig && (
          <span className={`rounded-full px-4 py-1.5 text-xs font-medium uppercase tracking-[0.16em] ${
            workflowConfig.enabled ? 'bg-emerald-100/90 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300' : 'bg-amber-100/90 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300'
          }`}>
            {workflowConfig.enabled ? 'Workflow enabled' : 'Workflow disabled'}
          </span>
        )}
      </div>

      {/* No project selected */}
      {!projectId && (
        <div className="celestial-panel flex flex-1 flex-col items-center justify-center gap-4 rounded-[1.4rem] border border-dashed border-border/80 p-8 text-center">
          <div className="text-4xl mb-2">🔗</div>
          <h3 className="text-xl font-semibold">Select a project</h3>
          <p className="text-muted-foreground">Choose a project from the sidebar to configure its agent pipeline</p>
        </div>
      )}

      {projectId && boardLoading && (
        <div className="flex flex-col items-center justify-center flex-1 gap-4">
          <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
          <p className="text-muted-foreground">Loading pipeline...</p>
        </div>
      )}

      {projectId && !boardLoading && boardData && (
        <>
          {/* Agent Config Row — drag-and-drop assignment */}
          <AgentConfigRow
            columns={columns}
            agentConfig={agentConfig}
            availableAgents={availableAgents}
            renderPresetSelector={
              <AgentPresetSelector
                columnNames={columns.map((c) => c.status.name)}
                currentMappings={agentConfig.localMappings}
                onApplyPreset={agentConfig.applyPreset}
              />
            }
            renderAddButton={(status: string) => (
              <AddAgentPopover
                status={status}
                availableAgents={availableAgents}
                assignedAgents={agentConfig.localMappings[status] ?? []}
                isLoading={agentsLoading}
                error={agentsError}
                onRetry={refetchAgents}
                onAddAgent={agentConfig.addAgent}
              />
            )}
          />

          {/* Pipeline Stages Visualization */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Pipeline Stages</h3>
            <div className="flex gap-3 overflow-x-auto pb-2">
              {columns.map((col, idx) => {
                const assigned = agentConfig.localMappings[col.status.name] ?? [];
                const dotColor = statusColorToCSS(col.status.color);
                return (
                  <div key={col.status.option_id} className="flex items-center gap-3 shrink-0">
                    <div className="celestial-panel flex min-w-[160px] flex-col items-center gap-2 rounded-[1.2rem] border border-border/75 p-4">
                      <span className="w-3 h-3 rounded-full" style={{ backgroundColor: dotColor }} />
                      <span className="text-sm font-medium text-center">{col.status.name}</span>
                      <span className="text-xs text-muted-foreground">{col.item_count} items</span>
                      {assigned.length > 0 ? (
                        <div className="flex flex-wrap gap-1 justify-center mt-1">
                          {assigned.map((a) => (
                            <span key={a.id} className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.12em] text-primary">
                              {a.display_name ?? a.slug}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-[10px] text-muted-foreground/60 mt-1">No agents</span>
                      )}
                    </div>
                    {idx < columns.length - 1 && (
                      <span className="text-muted-foreground/40 text-lg">→</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Activity Feed placeholder */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Recent Activity</h3>
            <div className="celestial-panel rounded-[1.2rem] border border-border/75 p-4">
              <p className="text-sm text-muted-foreground text-center py-4">
                Agent workflow events will appear here as agents process items
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
