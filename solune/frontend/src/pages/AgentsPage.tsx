/**
 * AgentsPage — Agent catalog grid + column assignment map.
 * Composes AgentsPanel (catalog), useAgentConfig (assignments), and board columns.
 */

import { TriangleAlert } from '@/lib/icons';
import { Skeleton } from '@/components/ui/skeleton';
import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useAgentConfig } from '@/hooks/useAgentConfig';
import { useQuery } from '@tanstack/react-query';
import { pipelinesApi } from '@/services/api';
import { AgentsPanel } from '@/components/agents/AgentsPanel';
import { statusColorToCSS } from '@/components/board/colorUtils';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { ProjectSelectionEmptyState } from '@/components/common/ProjectSelectionEmptyState';
import { Button } from '@/components/ui/button';
import { Tooltip } from '@/components/ui/tooltip';
import { formatAgentName } from '@/utils/formatAgentName';
import { countPendingAssignedSubIssues } from '@/utils/agentCardMeta';
import type { AgentAssignment } from '@/types';

function buildAgentTooltip(agent: AgentAssignment): string {
  const modelName =
    agent.config && typeof agent.config === 'object' && typeof agent.config.model_name === 'string'
      ? agent.config.model_name
      : '';
  return modelName || agent.slug;
}

export function AgentsPage() {
  const { user } = useAuth();
  const {
    selectedProject,
    projects,
    isLoading: projectsLoading,
    selectProject,
  } = useProjects(user?.selected_project_id);
  const projectId = selectedProject?.project_id ?? null;

  const { boardData, boardLoading } = useProjectBoard({ selectedProjectId: projectId });
  const agentConfig = useAgentConfig(projectId);
  const { data: pipelineList, isError: pipelineListError } = useQuery({
    queryKey: ['pipelines', 'list', projectId ?? ''],
    queryFn: () => pipelinesApi.list(projectId!),
    enabled: !!projectId,
    staleTime: 30_000,
  });

  const { isError: pipelineAssignmentError } = useQuery({
    queryKey: ['pipelines', 'assignment', projectId ?? ''],
    queryFn: () => pipelinesApi.getAssignment(projectId!),
    enabled: !!projectId,
    staleTime: 30_000,
  });

  const columns = boardData?.columns ?? [];
  const repo = boardData?.columns.flatMap((c) => c.items).find((i) => i.repository)?.repository;
  const assignedCount = Object.values(agentConfig.localMappings).reduce(
    (sum, mapped) => sum + mapped.length,
    0
  );
  const agentUsageCounts = Object.values(agentConfig.localMappings).reduce<Record<string, number>>(
    (counts, mapped) => {
      mapped.forEach((assignment) => {
        counts[assignment.slug] = (counts[assignment.slug] ?? 0) + 1;
      });
      return counts;
    },
    {}
  );
  const pipelineConfigCounts = (pipelineList?.pipelines ?? []).reduce<Record<string, number>>(
    (counts, pipeline) => {
      const pipelineAgentSlugs = new Set(
        pipeline.stages.flatMap((stage) => {
          const fromGroups = (stage.groups ?? []).flatMap((g) => g.agents);
          const agents = fromGroups.length > 0 ? fromGroups : stage.agents;
          return agents.map((agent) => agent.agent_slug);
        })
      );
      pipelineAgentSlugs.forEach((slug) => {
        counts[slug] = (counts[slug] ?? 0) + 1;
      });
      return counts;
    },
    {}
  );
  const pendingSubIssueCounts = countPendingAssignedSubIssues(boardData);

  return (
    <div className="celestial-fade-in flex h-full flex-col gap-5 overflow-auto rounded-[1.5rem] border border-border/70 bg-background/42 p-4 backdrop-blur-sm sm:gap-6 sm:rounded-[1.75rem] sm:p-6">
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
        <ProjectSelectionEmptyState
          projects={projects}
          isLoading={projectsLoading}
          selectedProjectId={projectId}
          onSelectProject={selectProject}
          description="Choose a GitHub Project to manage its agent catalog, ownership patterns, and column assignments from one place."
        />
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
              pipelineConfigCounts={pipelineConfigCounts}
              pendingSubIssueCounts={pendingSubIssueCounts}
            />
          </div>

          {/* Agent-to-Column Assignment Map */}
          <div id="agent-assignments" className="space-y-4 scroll-mt-6">
            <div className="celestial-panel rounded-[1.35rem] border border-border/75 p-4 sm:rounded-[1.5rem] sm:p-5">
              <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">Orbital map</p>
              <h3 className="mt-2 text-xl font-display font-medium">Column assignments</h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Keep agents aligned with each delivery state so status changes feel intentional
                rather than improvised.
              </p>
            </div>
            {(pipelineListError || pipelineAssignmentError) && (
              <div className="flex items-center gap-2 rounded-[1.25rem] border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
                <TriangleAlert className="h-4 w-4 shrink-0" />
                <span>Failed to load pipeline data. Assignment details may be incomplete.</span>
              </div>
            )}
            {boardLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="celestial-panel flex items-start gap-3 rounded-[1.25rem] border border-border/75 p-3.5 sm:rounded-[1.35rem] sm:p-4">
                    <Skeleton variant="shimmer" className="mt-1 h-2.5 w-2.5 rounded-full" />
                    <div className="flex-1 space-y-2">
                      <Skeleton variant="shimmer" className="h-4 w-32" />
                      <Skeleton variant="shimmer" className="h-3 w-20" />
                    </div>
                  </div>
                ))}
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
                    <div
                      key={col.status.option_id}
                      className="celestial-panel orbit-divider flex items-start gap-3 rounded-[1.25rem] border border-border/75 p-3.5 sm:rounded-[1.35rem] sm:p-4"
                    >
                      <span
                        className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full"
                        style={{ backgroundColor: dotColor }}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center justify-between gap-2 sm:gap-3">
                          <span className="text-sm font-medium">{col.status.name}</span>
                          <span className="solar-chip-soft rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]">
                            {assigned.length} mapped
                          </span>
                        </div>
                        {assigned.length > 0 ? (
                          <div className="flex flex-wrap gap-1 mt-1.5">
                            {assigned.map((a) => {
                              return (
                                <Tooltip
                                  key={a.id}
                                  title={formatAgentName(a.slug, a.display_name)}
                                  content={buildAgentTooltip(a)}
                                  side="top"
                                >
                                  <span className="solar-chip cursor-default rounded-[0.65rem] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.12em]">
                                    {formatAgentName(a.slug, a.display_name)}
                                  </span>
                                </Tooltip>
                              );
                            })}
                          </div>
                        ) : (
                          <p className="text-xs text-muted-foreground/60 mt-0.5">
                            No agents assigned
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="celestial-panel rounded-[1.3rem] border border-border/75 p-4 sm:rounded-[1.4rem] sm:p-5">
              <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">
                Guiding note
              </p>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                Use the catalog to decide which agents deserve long-lived ownership, then keep
                assignment density low enough that each column still has a clear specialist.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
