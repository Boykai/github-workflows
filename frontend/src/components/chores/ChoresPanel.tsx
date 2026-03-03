/**
 * ChoresPanel — container for the Chores feature on the project board.
 *
 * Renders list of ChoreCards, empty state with "Add Chore" button,
 * and loading / error states.
 */

import { useState } from 'react';
import { useChoresList } from '@/hooks/useChores';
import { ChoreCard } from './ChoreCard';
import { AddChoreModal } from './AddChoreModal';

interface ChoresPanelProps {
  projectId: string;
}

export function ChoresPanel({ projectId }: ChoresPanelProps) {
  const { data: chores, isLoading, error } = useChoresList(projectId);
  const [showAddModal, setShowAddModal] = useState(false);

  return (
    <div className="flex flex-col gap-3 w-72 shrink-0">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
          🔄 Chores
        </h3>
        {/* Add Chore button */}
        <button
          className="px-2 py-1 text-xs font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          onClick={() => setShowAddModal(true)}
        >
          + Add Chore
        </button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex flex-col gap-2">
          {[1, 2].map((i) => (
            <div
              key={i}
              className="h-24 rounded-md border border-border bg-muted/30 animate-pulse"
            />
          ))}
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="flex flex-col items-center gap-2 p-4 rounded-md border border-destructive/30 bg-destructive/5 text-center">
          <span className="text-sm text-destructive">Failed to load chores</span>
          <p className="text-xs text-muted-foreground">{error.message}</p>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && chores && chores.length === 0 && (
        <div className="flex flex-col items-center gap-2 p-6 rounded-md border-2 border-dashed border-border bg-muted/10 text-center">
          <span className="text-2xl">📋</span>
          <p className="text-sm text-muted-foreground">No chores yet</p>
          <p className="text-xs text-muted-foreground">
            Add a chore to set up recurring maintenance tasks
          </p>
        </div>
      )}

      {/* Chore list */}
      {!isLoading && !error && chores && chores.length > 0 && (
        <div className="flex flex-col gap-2 overflow-y-auto max-h-[calc(100vh-280px)]">
          {chores.map((chore) => (
            <ChoreCard key={chore.id} chore={chore} projectId={projectId} />
          ))}
        </div>
      )}

      {/* Add Chore Modal */}
      <AddChoreModal
        projectId={projectId}
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
      />
    </div>
  );
}
