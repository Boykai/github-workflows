/**
 * AgentColumnCell component - renders a vertical stack of AgentTile components
 * for one status column, plus an "Add Agent" button.
 * Registers as a droppable zone for cross-column drag-and-drop.
 * Retains SortableContext for within-column ordering.
 */

import { useCallback } from 'react';
import { useDroppable } from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { AgentAssignment, AvailableAgent } from '@/types';
import { AgentTile } from './AgentTile';

interface AgentColumnCellProps {
  status: string;
  agents: AgentAssignment[];
  isModified: boolean;
  onRemoveAgent: (status: string, agentInstanceId: string) => void;
  onReorderAgents: (status: string, newOrder: AgentAssignment[]) => void;
  renderAddButton?: React.ReactNode;
  availableAgents?: AvailableAgent[];
}

/** Sortable wrapper for AgentTile */
function SortableAgentTile({
  agent,
  onRemove,
  availableAgents,
}: {
  agent: AgentAssignment;
  onRemove: (id: string) => void;
  availableAgents?: AvailableAgent[];
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
      availableAgents={availableAgents}
      isWarning={isWarning}
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
  onReorderAgents: _onReorderAgents,
  renderAddButton,
  availableAgents,
}: AgentColumnCellProps) {
  // Register as a droppable zone for cross-column DnD
  const { setNodeRef, isOver } = useDroppable({ id: status });

  const handleRemove = useCallback(
    (agentInstanceId: string) => {
      onRemoveAgent(status, agentInstanceId);
    },
    [status, onRemoveAgent]
  );

  const agentCount = agents.length;

  // Drop zone highlighting: ring + background when item is dragged over this column
  const dropHighlight = isOver ? 'border-primary/40 bg-primary/5 ring-2 ring-primary/30' : '';

  return (
    <div
      ref={setNodeRef}
      role="group"
      aria-label={`${status} column, ${agentCount} agents`}
      className={`flex h-full min-w-0 flex-col gap-2 rounded-[1.2rem] border p-2 transition-colors duration-150 ${isModified ? 'border-primary/50 bg-primary/5' : 'border-border/60'} ${dropHighlight}`}
    >
      <SortableContext items={agents.map((a) => a.id)} strategy={verticalListSortingStrategy}>
        <div className="flex flex-col gap-2 min-h-[2px]">
          {agents.map((agent) => (
            <SortableAgentTile
              key={agent.id}
              agent={agent}
              onRemove={handleRemove}
              availableAgents={availableAgents}
            />
          ))}
        </div>
      </SortableContext>

      {/* Add agent button placeholder / slot */}
      {renderAddButton}

      {/* Soft limit warning (T021) */}
      {agentCount > 10 && (
        <div className="text-xs text-accent-foreground bg-accent/10 px-2 py-1 rounded-md text-center mt-1">
          ⚠ {agentCount} agents assigned — consider reducing
        </div>
      )}
    </div>
  );
}
