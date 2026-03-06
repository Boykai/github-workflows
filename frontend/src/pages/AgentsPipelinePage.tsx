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
    <div className="flex flex-col h-full p-6 gap-6 overflow-auto">
      {/* Page Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Agents Pipeline</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Configure how agents process items across board columns
          </p>
        </div>
        {workflowConfig && (
          <span className={`px-3 py-1 text-xs font-medium rounded-full ${
            workflowConfig.enabled ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
          }`}>
            {workflowConfig.enabled ? 'Workflow enabled' : 'Workflow disabled'}
          </span>
        )}
      </div>

      {/* No project selected */}
      {!projectId && (
        <div className="flex flex-col items-center justify-center flex-1 gap-4 text-center p-8 border-2 border-dashed border-border rounded-lg bg-muted/10">
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
                    <div className="flex flex-col items-center gap-2 p-4 rounded-lg border border-border bg-card min-w-[160px]">
                      <span className="w-3 h-3 rounded-full" style={{ backgroundColor: dotColor }} />
                      <span className="text-sm font-medium text-center">{col.status.name}</span>
                      <span className="text-xs text-muted-foreground">{col.item_count} items</span>
                      {assigned.length > 0 ? (
                        <div className="flex flex-wrap gap-1 justify-center mt-1">
                          {assigned.map((a) => (
                            <span key={a.id} className="px-2 py-0.5 text-[10px] font-medium bg-primary/10 text-primary rounded-full">
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
            <div className="rounded-lg border border-border bg-card p-4">
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
