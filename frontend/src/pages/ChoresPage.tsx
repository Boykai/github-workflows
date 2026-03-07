/**
 * ChoresPage — Chore management with catalog, scheduling, and cleanup.
 * Composes ChoresPanel (list + add + cleanup), useProjectBoard for repo info.
 */

import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { ChoresPanel } from '@/components/chores/ChoresPanel';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { Button } from '@/components/ui/button';
import { useQuery } from '@tanstack/react-query';
import { workflowApi } from '@/services/api';

export function ChoresPage() {
  const { user } = useAuth();
  const { selectedProject } = useProjects(user?.selected_project_id);
  const projectId = selectedProject?.project_id ?? null;

  const { boardData } = useProjectBoard({ selectedProjectId: projectId });

  // Prefer repo info from board items; fall back to the project's workflow config.
  const boardRepo = boardData?.columns.flatMap(c => c.items).find(i => i.repository)?.repository;

  const { data: workflowConfig } = useQuery({
    queryKey: ['workflow', 'config', projectId],
    queryFn: () => workflowApi.getConfig(),
    enabled: !!projectId && !boardRepo,
    staleTime: 60_000,
  });

  const owner = boardRepo?.owner ?? workflowConfig?.repository_owner;
  const repoName = boardRepo?.name ?? workflowConfig?.repository_name;

  // Synthesise a repo-like object for the hero badge/stats (same shape as BoardRepository)
  const repo = owner && repoName ? { owner, name: repoName } : undefined;

  return (
    <div className="flex h-full flex-col gap-5 overflow-auto rounded-[1.5rem] border border-border/70 bg-background/42 p-4 backdrop-blur-sm sm:gap-6 sm:rounded-[1.75rem] sm:p-6">
      <CelestialCatalogHero
        eyebrow="Ritual Maintenance"
        title="Turn upkeep into a visible rhythm."
        description="Organize recurring repository chores in the same spacious catalog pattern as agents, with room for templates, automation health, and fast manual interventions."
        badge={repo ? `${repo.owner}/${repo.name}` : 'Awaiting repository'}
        note="A chore page should feel like a seasonal calendar: templates at the top, active routines in the center, and manual cleanup available without cluttering the rest of the page."
        stats={[
          { label: 'Board columns', value: String(boardData?.columns.length ?? 0) },
          { label: 'Project', value: selectedProject?.name ?? 'Unselected' },
          { label: 'Repository', value: repo ? repo.name : 'Unlinked' },
          { label: 'Automation mode', value: projectId ? 'Live' : 'Idle' },
        ]}
        actions={
          <>
            <Button variant="default" size="lg" asChild>
              <a href="#chores-catalog">Plan recurring work</a>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <a href="#chore-templates">Review upkeep cadence</a>
            </Button>
          </>
        }
      />

      {/* No project selected */}
      {!projectId && (
        <div className="celestial-panel flex flex-1 flex-col items-center justify-center gap-4 rounded-[1.4rem] border border-dashed border-border/80 bg-background/26 p-8 text-center">
          <div className="text-4xl mb-2">🧹</div>
          <h3 className="text-xl font-semibold">Select a project</h3>
          <p className="text-muted-foreground">Choose a project from the sidebar to manage its chores</p>
        </div>
      )}

      {projectId && (
        <div className="flex-1 min-w-0">
          <ChoresPanel
            projectId={projectId}
            owner={owner}
            repo={repoName}
          />
        </div>
      )}
    </div>
  );
}
