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
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { Button } from '@/components/ui/button';

export function AgentsPage() {
  const { user } = useAuth();
  const { selectedProject } = useProjects(user?.selected_project_id);
  const projectId = selectedProject?.project_id ?? null;

  const { boardData, boardLoading } = useProjectBoard({ selectedProjectId: projectId });
  const agentConfig = useAgentConfig(projectId);

  const columns = boardData?.columns ?? [];
  const repo = boardData?.columns.flatMap(c => c.items).find(i => i.repository)?.repository;
  const assignedCount = Object.values(agentConfig.localMappings).reduce((sum, mapped) => sum + mapped.length, 0);
  const agentUsageCounts = Object.values(agentConfig.localMappings).reduce<Record<string, number>>((counts, mapped) => {
    mapped.forEach((assignment) => {
      counts[assignment.slug] = (counts[assignment.slug] ?? 0) + 1;
    });
    return counts;
  }, {});

  return (
    <div className="flex h-full flex-col gap-5 overflow-auto rounded-[1.5rem] border border-border/70 bg-background/35 p-4 backdrop-blur-sm sm:gap-6 sm:rounded-[1.75rem] sm:p-6">
      <CelestialCatalogHero
        eyebrow="Celestial Catalog"
        title="Shape your agent constellation."
        description="Browse repository agents in a broader catalog, spotlight the most active rituals, and keep every board column tied to the right assistant." 
        badge={repo ? `${repo.owner}/${repo.name}` : 'Awaiting repository'}
        note="Give active agents more surface area, keep pending work visible, and let assignments read like a calm operations map instead of a stacked sidebar."
        stats={[
          { label: 'Board columns', value: String(columns.length) },
          { label: 'Assignments', value: String(assignedCount) },
          { label: 'Mapped states', value: String(Object.keys(agentConfig.localMappings).length) },
          { label: 'Project', value: selectedProject?.name ?? 'Unselected' },
        ]}
        actions={
          <>
            <Button variant="default" size="lg" asChild>
              <a href="#agents-catalog">Curate agent rituals</a>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <a href="#agent-assignments">Review assignments</a>
            </Button>
          </>
        }
      />

      {/* No project selected */}
      {!projectId && (
        <div className="celestial-panel flex flex-1 flex-col items-center justify-center gap-4 rounded-[1.4rem] border border-dashed border-border/80 p-8 text-center">
          <div className="text-4xl mb-2">🤖</div>
          <h3 className="text-xl font-semibold">Select a project</h3>
          <p className="text-muted-foreground">Choose a project from the sidebar to manage its agents</p>
        </div>
      )}

      {projectId && (
        <div className="grid flex-1 gap-5 xl:grid-cols-[minmax(0,1fr)_22rem] xl:gap-6">
          {/* Agent Catalog */}
          <div className="min-w-0">
            <AgentsPanel
              projectId={projectId}
              owner={repo?.owner}
              repo={repo?.name}
              agentUsageCounts={agentUsageCounts}
            />
          </div>

          {/* Agent-to-Column Assignment Map */}
          <div id="agent-assignments" className="space-y-4 scroll-mt-6">
            <div className="celestial-panel rounded-[1.35rem] border border-border/75 p-4 sm:rounded-[1.5rem] sm:p-5">
              <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">Orbital map</p>
              <h3 className="mt-2 text-xl font-display font-medium">Column assignments</h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Keep agents aligned with each delivery state so status changes feel intentional rather than improvised.
              </p>
            </div>
            {boardLoading ? (
              <div className="celestial-panel flex items-center justify-center rounded-[1.3rem] border border-border/70 p-6 sm:rounded-[1.4rem] sm:p-8">
                <div className="w-6 h-6 border-3 border-border border-t-primary rounded-full animate-spin" />
              </div>
            ) : columns.length === 0 ? (
              <p className="celestial-panel rounded-[1.3rem] border border-dashed border-border/80 p-4 text-center text-sm text-muted-foreground sm:rounded-[1.4rem] sm:p-5">
                No board columns available
              </p>
            ) : (
              <div className="space-y-3">
                {columns.map((col) => {
                  const assigned = agentConfig.localMappings[col.status.name] ?? [];
                  const dotColor = statusColorToCSS(col.status.color);
                  return (
                    <div key={col.status.option_id} className="celestial-panel orbit-divider flex items-start gap-3 rounded-[1.25rem] border border-border/75 p-3.5 sm:rounded-[1.35rem] sm:p-4">
                      <span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: dotColor }} />
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center justify-between gap-2 sm:gap-3">
                          <span className="text-sm font-medium">{col.status.name}</span>
                          <span className="rounded-full bg-background/60 px-2 py-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                            {assigned.length} mapped
                          </span>
                        </div>
                        {assigned.length > 0 ? (
                          <div className="flex flex-wrap gap-1 mt-1.5">
                            {assigned.map((a) => (
                              <span key={a.id} className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.12em] text-primary">
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

            <div className="celestial-panel rounded-[1.3rem] border border-border/75 p-4 sm:rounded-[1.4rem] sm:p-5">
              <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">Guiding note</p>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                Use the catalog to decide which agents deserve long-lived ownership, then keep assignment density low enough that each column still has a clear specialist.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
