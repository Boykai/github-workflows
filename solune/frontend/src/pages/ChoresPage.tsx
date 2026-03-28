/**
 * ChoresPage — Chore management with catalog, scheduling, and cleanup.
 * Composes ChoresPanel (list + add + cleanup), useProjectBoard for repo info.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useChoresListPaginated, useEvaluateChoresTriggers, choreKeys } from '@/hooks/useChores';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';
import { ChoresPanel } from '@/components/chores/ChoresPanel';
import { FeaturedRitualsPanel } from '@/components/chores/FeaturedRitualsPanel';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { ProjectSelectionEmptyState } from '@/components/common/ProjectSelectionEmptyState';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { workflowApi, choresApi } from '@/services/api';
import { countParentIssues } from '@/utils/parentIssueCount';

export function ChoresPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const {
    selectedProject,
    projects,
    isLoading: projectsLoading,
    selectProject,
  } = useProjects(user?.selected_project_id);
  const projectId = selectedProject?.project_id ?? null;

  // Seed chore presets when projectId changes (idempotent per project).
  // Tracking the last-seeded ID (not a boolean) ensures presets are seeded
  // for each project even when the user switches without a full remount.
  const seededRef = useRef<string | null>(null);
  useEffect(() => {
    if (!projectId || seededRef.current === projectId) return;
    choresApi
      .seedPresets(projectId)
      .then(() => {
        seededRef.current = projectId;
        queryClient.invalidateQueries({ queryKey: choreKeys.list(projectId) });
      })
      .catch((err) => {
        console.warn('Failed to seed preset chores:', err);
      });
  }, [projectId, queryClient]);

  const { boardData } = useProjectBoard({ selectedProjectId: projectId });
  const { allItems: chores, isLoading: choresLoading } = useChoresListPaginated(projectId);
  const [isAnyDirty, setIsAnyDirty] = useState(false);

  const parentIssueCount = useMemo(() => countParentIssues(boardData), [boardData]);

  // Poll evaluate-triggers while this page is mounted so count-based chores
  // fire automatically when parentIssueCount crosses the threshold.
  useEvaluateChoresTriggers(projectId, parentIssueCount, !!boardData?.columns);

  // Unsaved changes navigation guard
  const { isBlocked, blocker } = useUnsavedChanges({ isDirty: isAnyDirty });

  // Prefer repo info from board items; fall back to the project's workflow config.
  const boardRepo = boardData?.columns
    .flatMap((c) => c.items)
    .find((i) => i.repository)?.repository;

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
    <div className="celestial-fade-in flex h-full flex-col gap-5 overflow-auto rounded-[1.5rem] border border-border/70 bg-background/42 p-4 backdrop-blur-sm sm:gap-6 sm:rounded-[1.75rem] sm:p-6">
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
            <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">
              Featured Rituals
            </p>
            <h4 className="mt-1 text-[1.15rem] font-display font-medium leading-tight">
              Key chore highlights
            </h4>
          </div>
          <FeaturedRitualsPanel chores={chores ?? []} parentIssueCount={parentIssueCount} />
        </section>
      )}

      {/* No project selected */}
      {!projectId && (
        <ProjectSelectionEmptyState
          projects={projects}
          isLoading={projectsLoading}
          selectedProjectId={projectId}
          onSelectProject={selectProject}
          description="Choose a GitHub Project to manage its recurring chores, automation cadence, and cleanup routines."
        />
      )}

      {projectId && (
        <div className="flex-1 min-w-0">
          {choresLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="celestial-panel flex items-start gap-3 rounded-[1.25rem] border border-border/75 p-4">
                  <Skeleton variant="shimmer" className="h-10 w-10 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <Skeleton variant="shimmer" className="h-4 w-40" />
                    <Skeleton variant="shimmer" className="h-3 w-56" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <ChoresPanel
              projectId={projectId}
              owner={owner}
              repo={repoName}
              parentIssueCount={parentIssueCount}
              onDirtyChange={setIsAnyDirty}
            />
          )}
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
