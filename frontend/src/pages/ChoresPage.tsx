/**
 * ChoresPage — Chore management with catalog, scheduling, and cleanup.
 * Composes ChoresPanel (list + add + cleanup), useProjectBoard for repo info.
 */

import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { ChoresPanel } from '@/components/chores/ChoresPanel';

export function ChoresPage() {
  const { user } = useAuth();
  const { selectedProject } = useProjects(user?.selected_project_id);
  const projectId = selectedProject?.project_id ?? null;

  const { boardData } = useProjectBoard({ selectedProjectId: projectId });

  const repo = boardData?.columns.flatMap((c) => c.items).find((i) => i.repository)?.repository;

  return (
    <div className="flex h-full flex-col gap-6 rounded-[1.75rem] border border-border/70 bg-background/35 p-6 backdrop-blur-sm overflow-auto">
      {/* Page Header */}
      <div>
        <p className="mb-1 text-xs uppercase tracking-[0.24em] text-primary/80">
          Ritual Maintenance
        </p>
        <h2 className="text-3xl font-display font-medium tracking-[0.04em]">Chores</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Schedule automated tasks and manage project cleanup
        </p>
      </div>

      {/* No project selected */}
      {!projectId && (
        <div className="celestial-panel flex flex-1 flex-col items-center justify-center gap-4 rounded-[1.4rem] border border-dashed border-border/80 p-8 text-center">
          <div className="text-4xl mb-2">🧹</div>
          <h3 className="text-xl font-semibold">Select a project</h3>
          <p className="text-muted-foreground">
            Choose a project from the sidebar to manage its chores
          </p>
        </div>
      )}

      {projectId && (
        <div className="flex-1">
          <ChoresPanel projectId={projectId} owner={repo?.owner} repo={repo?.name} />
        </div>
      )}
    </div>
  );
}
