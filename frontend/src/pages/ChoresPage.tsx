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

  const repo = boardData?.columns.flatMap(c => c.items).find(i => i.repository)?.repository;

  return (
    <div className="flex flex-col h-full p-6 gap-6 overflow-auto">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Chores</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Schedule automated tasks and manage project cleanup
        </p>
      </div>

      {/* No project selected */}
      {!projectId && (
        <div className="flex flex-col items-center justify-center flex-1 gap-4 text-center p-8 border-2 border-dashed border-border rounded-lg bg-muted/10">
          <div className="text-4xl mb-2">🧹</div>
          <h3 className="text-xl font-semibold">Select a project</h3>
          <p className="text-muted-foreground">Choose a project from the sidebar to manage its chores</p>
        </div>
      )}

      {projectId && (
        <div className="flex-1">
          <ChoresPanel
            projectId={projectId}
            owner={repo?.owner}
            repo={repo?.name}
          />
        </div>
      )}
    </div>
  );
}
