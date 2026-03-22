/**
 * AgentColumnCell component - renders a vertical stack of AgentTile components
 * for one status column, plus an "Add Agent" button.
 * Registers as a droppable zone for cross-column drag-and-drop.
 * Retains SortableContext for within-column ordering.
 */

import { useCallback } from 'react';
import { TriangleAlert } from '@/lib/icons';
import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { AgentAssignment, AvailableAgent } from '@/types';
import { AgentTile } from './AgentTile';
import { cn } from '@/lib/utils';

interface AgentColumnCellProps {
  status: string;
  agents: AgentAssignment[];
  isModified: boolean;
  onRemoveAgent: (status: string, agentInstanceId: string) => void;
  onCloneAgent: (status: string, agentInstanceId: string) => void;
  onReorderAgents: (status: string, newOrder: AgentAssignment[]) => void;
  renderAddButton?: React.ReactNode;
  availableAgents?: AvailableAgent[];
  variant?: 'default' | 'compact';
}

/** Sortable wrapper for AgentTile */
function SortableAgentTile({
  agent,
  onRemove,
  onClone,
  availableAgents,
  variant,
  compactIndex,
  compactCount,
}: {
  agent: AgentAssignment;
  onRemove: (id: string) => void;
  onClone: (id: string) => void;
  availableAgents?: AvailableAgent[];
  variant?: 'default' | 'compact';
  compactIndex?: number;
  compactCount?: number;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: agent.id,
    transition: { duration: 150, easing: 'ease' },
  });

  const style: React.CSSProperties = {
    transform: CSS.Translate.toString(transform),
    transition,
  };

  const isWarning = availableAgents
    ? availableAgents.length > 0 && !availableAgents.some((a) => a.slug === agent.slug)
    : false;

  return (
    <AgentTile
      agent={agent}
      onRemove={onRemove}
      onClone={onClone}
      availableAgents={availableAgents}
      isWarning={isWarning}
      variant={variant}
      compactIndex={compactIndex}
      compactCount={compactCount}
      sortableProps={{
        attributes: attributes as unknown as Record<string, unknown>,
        listeners: listeners as unknown as Record<string, unknown>,
        setNodeRef,
        style,
        isDragging,
      }}
    />
  );
}

export function AgentColumnCell({
  status,
  agents,
  isModified,
  onRemoveAgent,
  onCloneAgent,
  onReorderAgents: _onReorderAgents,
  renderAddButton,
  availableAgents,
  variant = 'default',
}: AgentColumnCellProps) {
  // Register as a droppable zone for cross-column DnD
  const { setNodeRef, isOver } = useDroppable({ id: status });

  const handleRemove = useCallback(
    (agentInstanceId: string) => {
      onRemoveAgent(status, agentInstanceId);
    },
    [status, onRemoveAgent]
  );

  const handleClone = useCallback(
    (agentInstanceId: string) => {
      onCloneAgent(status, agentInstanceId);
    },
    [onCloneAgent, status]
  );

  const agentCount = agents.length;
  const isCompact = variant === 'compact';

  // Drop zone highlighting: ring + background when item is dragged over this column
  const dropHighlight = isOver ? 'border-primary/40 bg-primary/5 ring-2 ring-primary/30' : '';

  return (
    <div
      ref={setNodeRef}
      role="group"
      aria-label={`${status} column, ${agentCount} agents`}
      className={cn('flex h-full min-w-0 flex-col transition-colors duration-150', isCompact ? 'pipeline-column-surface pipeline-stage-card gap-1.5 rounded-[1rem] border p-1.5' : 'gap-2 rounded-[1.2rem] border p-2', isModified ? 'border-primary/50 bg-primary/5' : 'border-border/60', dropHighlight)}
    >
      {isCompact && (
        <div className="flex items-center justify-between px-1 pb-0.5">
          <div className="flex min-w-0 items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-primary/70 shadow-[0_0_10px_hsl(var(--glow)/0.45)]" />
            <span
              className="truncate text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground/80"
              title={status}
            >
              {status}
            </span>
          </div>
          <span className="text-[10px] text-muted-foreground/65">{agentCount}</span>
        </div>
      )}
      <SortableContext items={agents.map((a) => a.id)} strategy={verticalListSortingStrategy}>
        <div role="list" aria-label={`Agents in ${status}`} className={cn('flex min-h-[2px] flex-col', isCompact ? 'gap-1.5' : 'gap-2')}>
          {agents.map((agent, index) => (
            <SortableAgentTile
              key={agent.id}
              agent={agent}
              onRemove={handleRemove}
              onClone={handleClone}
              availableAgents={availableAgents}
              variant={variant}
              compactIndex={index}
              compactCount={agents.length}
            />
          ))}
        </div>
      </SortableContext>

      {/* Add agent button placeholder / slot */}
      {renderAddButton}

      {/* Soft limit warning (T021) */}
      {agentCount > 10 && !isCompact && (
        <div className="mt-1 rounded-md border border-amber-400/40 bg-amber-500/12 px-2 py-1 text-center text-xs font-medium text-amber-800 dark:text-amber-300">
          <span className="inline-flex items-center gap-1">
            <TriangleAlert className="h-3.5 w-3.5" />
            {agentCount} agents assigned — consider reducing
          </span>
        </div>
      )}
    </div>
  );
}
