/**
 * AgentsPage — Agent catalog grid + column assignment map.
 * Composes AgentsPanel (catalog), useAgentConfig (assignments), and board columns.
 */

import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useAgentConfig } from '@/hooks/useAgentConfig';
import { AgentsPanel } from '@/components/agents/AgentsPanel';
import { statusColorToCSS } from '@/components/board/colorUtils';

export function AgentsPage() {
  const { user } = useAuth();
  const { selectedProject } = useProjects(user?.selected_project_id);
  const projectId = selectedProject?.project_id ?? null;

  const { boardData, boardLoading } = useProjectBoard({ selectedProjectId: projectId });
  const agentConfig = useAgentConfig(projectId);

  const columns = boardData?.columns ?? [];
  const repo = boardData?.columns.flatMap(c => c.items).find(i => i.repository)?.repository;

  return (
    <div className="flex flex-col h-full p-6 gap-6 overflow-auto">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Agents</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Manage your agent catalog and view column assignments
        </p>
      </div>

      {/* No project selected */}
      {!projectId && (
        <div className="flex flex-col items-center justify-center flex-1 gap-4 text-center p-8 border-2 border-dashed border-border rounded-lg bg-muted/10">
          <div className="text-4xl mb-2">🤖</div>
          <h3 className="text-xl font-semibold">Select a project</h3>
          <p className="text-muted-foreground">Choose a project from the sidebar to manage its agents</p>
        </div>
      )}

      {projectId && (
        <div className="flex flex-col lg:flex-row gap-6 flex-1 overflow-hidden">
          {/* Agent Catalog */}
          <div className="flex-1 min-w-0">
            <AgentsPanel
              projectId={projectId}
              owner={repo?.owner}
              repo={repo?.name}
            />
          </div>

          {/* Agent-to-Column Assignment Map */}
          <div className="lg:w-80 shrink-0">
            <h3 className="text-lg font-semibold mb-3">Column Assignments</h3>
            {boardLoading ? (
              <div className="flex items-center justify-center p-8">
                <div className="w-6 h-6 border-3 border-border border-t-primary rounded-full animate-spin" />
              </div>
            ) : columns.length === 0 ? (
              <p className="text-sm text-muted-foreground p-4 border border-dashed border-border rounded-lg text-center">
                No board columns available
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {columns.map((col) => {
                  const assigned = agentConfig.localMappings[col.status.name] ?? [];
                  const dotColor = statusColorToCSS(col.status.color);
                  return (
                    <div key={col.status.option_id} className="flex items-start gap-3 p-3 rounded-lg border border-border bg-card">
                      <span className="w-2.5 h-2.5 rounded-full mt-1 shrink-0" style={{ backgroundColor: dotColor }} />
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-medium">{col.status.name}</span>
                        {assigned.length > 0 ? (
                          <div className="flex flex-wrap gap-1 mt-1.5">
                            {assigned.map((a) => (
                              <span key={a.id} className="px-2 py-0.5 text-[10px] font-medium bg-primary/10 text-primary rounded-full">
                                {a.display_name ?? a.slug}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-muted-foreground/60 mt-0.5">No agents assigned</p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
