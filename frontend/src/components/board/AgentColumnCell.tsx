/**
 * AgentColumnCell component - renders a vertical stack of AgentTile components
 * for one status column, plus an "Add Agent" button.
 * Supports drag-and-drop reordering via @dnd-kit (T022).
 */

import { useCallback } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensors,
  useSensor,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
  arrayMove,
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable';
import { restrictToVerticalAxis } from '@dnd-kit/modifiers';
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
    transform: CSS.Transform.toString(transform),
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
  onReorderAgents,
  renderAddButton,
  availableAgents,
}: AgentColumnCellProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id) return;

      const oldIndex = agents.findIndex((a) => a.id === active.id);
      const newIndex = agents.findIndex((a) => a.id === over.id);
      if (oldIndex === -1 || newIndex === -1) return;

      const newOrder = arrayMove(agents, oldIndex, newIndex);
      onReorderAgents(status, newOrder);
    },
    [agents, status, onReorderAgents]
  );

  const handleRemove = useCallback(
    (agentInstanceId: string) => {
      onRemoveAgent(status, agentInstanceId);
    },
    [status, onRemoveAgent]
  );

  const agentCount = agents.length;

  return (
    <div className={`agent-column-cell${isModified ? ' agent-column-cell--modified' : ''}`}>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
        modifiers={[restrictToVerticalAxis]}
      >
        <SortableContext items={agents.map((a) => a.id)} strategy={verticalListSortingStrategy}>
          <div className="agent-column-cell-stack">
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
      </DndContext>

      {/* Add agent button placeholder / slot */}
      {renderAddButton}

      {/* Soft limit warning (T021) */}
      {agentCount > 10 && (
        <div className="agent-column-cell-warning">
          ⚠ {agentCount} agents assigned — consider reducing
        </div>
      )}
    </div>
  );
}
