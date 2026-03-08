/**
 * ChoresPage — Chore management with catalog, scheduling, and cleanup.
 * Composes ChoresPanel (list + add + cleanup), useProjectBoard for repo info.
 */

import { useMemo, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useChoresList } from '@/hooks/useChores';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';
import { ChoresPanel } from '@/components/chores/ChoresPanel';
import { FeaturedRitualsPanel } from '@/components/chores/FeaturedRitualsPanel';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { Button } from '@/components/ui/button';
import { useQuery } from '@tanstack/react-query';
import { workflowApi } from '@/services/api';

export function ChoresPage() {
  const { user } = useAuth();
  const { selectedProject } = useProjects(user?.selected_project_id);
  const projectId = selectedProject?.project_id ?? null;

  const { boardData } = useProjectBoard({ selectedProjectId: projectId });
  const { data: chores } = useChoresList(projectId);
  const [isAnyDirty, setIsAnyDirty] = useState(false);

  // Mirror the recent-parent-issues filter so counters only include unique parent issues.
  const parentIssueCount = useMemo(() => {
    if (!boardData?.columns) return 0;

    const subIssueNumbers = new Set<number>();
    const seenItemIds = new Set<string>();
    let count = 0;

    for (const column of boardData.columns) {
      for (const item of column.items ?? []) {
        for (const subIssue of item.sub_issues ?? []) {
          subIssueNumbers.add(subIssue.number);
        }
      }
    }

    for (const column of boardData.columns) {
      for (const item of column.items ?? []) {
        if (item.content_type !== 'issue') continue;
        if (seenItemIds.has(item.item_id)) continue;
        seenItemIds.add(item.item_id);
        if (item.number != null && subIssueNumbers.has(item.number)) continue;
        count += 1;
      }
    }

    return count;
  }, [boardData]);

  // Unsaved changes navigation guard
  const { isBlocked, blocker } = useUnsavedChanges({ isDirty: isAnyDirty });

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

      {/* Featured Rituals Panel */}
      {projectId && (
        <section className="ritual-stage rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6">
          <div className="mb-4">
            <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">Featured Rituals</p>
            <h4 className="mt-1 text-[1.15rem] font-display font-medium leading-tight">Key chore highlights</h4>
          </div>
          <FeaturedRitualsPanel
            chores={chores ?? []}
            parentIssueCount={parentIssueCount}
          />
        </section>
      )}

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
            parentIssueCount={parentIssueCount}
            onDirtyChange={setIsAnyDirty}
          />
        </div>
      )}

      {/* Unsaved changes confirmation modal */}
      {isBlocked && (
        <div className="fixed inset-0 z-[70] flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" role="presentation" />
          <div className="relative z-10 w-full max-w-sm mx-4 rounded-lg border border-border bg-background shadow-xl p-6 text-center">
            <h3 className="text-lg font-semibold text-foreground mb-2">Unsaved Changes</h3>
            <p className="text-sm text-muted-foreground mb-4">
              You have unsaved changes — are you sure you want to leave?
            </p>
            <div className="flex justify-center gap-3">
              <Button variant="outline" onClick={() => blocker.reset?.()}>
                Stay
              </Button>
              <Button variant="destructive" onClick={() => blocker.proceed?.()}>
                Discard and Leave
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
