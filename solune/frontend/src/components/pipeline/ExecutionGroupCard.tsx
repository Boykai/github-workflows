/**
 * ExecutionGroupCard — renders a single execution group within a pipeline stage.
 *
 * Each group contains agent nodes and a per-group execution mode toggle
 * (sequential / parallel). Groups support drag-and-drop reordering of agents.
 */

import { useState } from 'react';
import { GitBranch, Trash2, ArrowDownUp, Plus } from '@/lib/icons';
import {
  DndContext,
  closestCenter,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
import {
  SortableContext,
  rectSortingStrategy,
  verticalListSortingStrategy,
  sortableKeyboardCoordinates,
  arrayMove,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { AgentNode } from './AgentNode';
import { Tooltip } from '@/components/ui/tooltip';
import type { PipelineAgentNode, ExecutionGroup } from '@/types';
import { cn } from '@/lib/utils';

/** Sortable wrapper for agent nodes within a group. */
function SortableAgentNode({
  agent,
  onModelSelect,
  onRemove,
  onToolsClick,
  onClone,
  isParallel,
}: {
  agent: PipelineAgentNode;
  onModelSelect: (modelId: string, modelName: string) => void;
  onRemove: () => void;
  onToolsClick?: () => void;
  onClone?: () => void;
  isParallel?: boolean;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: agent.id,
  });

  return (
    <AgentNode
      agentNode={agent}
      onModelSelect={onModelSelect}
      onRemove={onRemove}
      onToolsClick={onToolsClick}
      onClone={onClone}
      isParallel={isParallel}
      setNodeRef={setNodeRef}
      dragHandleListeners={listeners}
      dragHandleAttributes={attributes}
      dragStyle={{ transform: CSS.Transform.toString(transform), transition }}
      isDragging={isDragging}
    />
  );
}

interface ExecutionGroupCardProps {
  group: ExecutionGroup;
  stageId: string;
  canDelete: boolean;
  onRemoveGroup: () => void;
  onToggleMode: (mode: 'sequential' | 'parallel') => void;
  onRemoveAgent: (agentNodeId: string) => void;
  onUpdateAgent: (agentNodeId: string, updates: Partial<PipelineAgentNode>) => void;
  onCloneAgent?: (agentNodeId: string) => void;
  onReorderAgents: (newOrder: PipelineAgentNode[]) => void;
  onToolsClick: (agentNodeId: string) => void;
  onAddAgent?: () => void;
}

export function ExecutionGroupCard({
  group,
  canDelete,
  onRemoveGroup,
  onToggleMode,
  onRemoveAgent,
  onUpdateAgent,
  onCloneAgent,
  onReorderAgents,
  onToolsClick,
  onAddAgent,
}: ExecutionGroupCardProps) {
  const isParallel = group.execution_mode === 'parallel';
  const hasAgents = group.agents.length > 0;
  const [isHovering, setIsHovering] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = group.agents.findIndex((a) => a.id === active.id);
    const newIndex = group.agents.findIndex((a) => a.id === over.id);
    if (oldIndex === -1 || newIndex === -1) return;
    onReorderAgents(arrayMove(group.agents, oldIndex, newIndex));
  };

  return (
    <div
      data-testid={`execution-group-${group.id}`}
      className={cn(
        'rounded-xl border p-2 transition-colors',
        isParallel
          ? 'border-primary/25 bg-primary/[0.07] dark:border-primary/45 dark:bg-[linear-gradient(180deg,hsl(var(--primary)/0.18)_0%,hsl(var(--night)/0.62)_100%)]'
          : 'border-border/50 bg-background/18 dark:border-border/80 dark:bg-[linear-gradient(180deg,hsl(var(--night)/0.84)_0%,hsl(var(--panel)/0.76)_100%)]',
      )}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      {/* Group header */}
      <div className="mb-1.5 flex items-center justify-between gap-1">
        <div className="flex items-center gap-1.5">
          {/* Mode toggle */}
          <Tooltip contentKey={isParallel ? 'pipeline.group.parallel' : 'pipeline.group.sequential'}>
            <button
              type="button"
              aria-label={`Switch to ${isParallel ? 'sequential' : 'parallel'} mode`}
              onClick={() => onToggleMode(isParallel ? 'sequential' : 'parallel')}
              className={cn(
                'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.16em] transition-colors',
                isParallel
                  ? 'border-primary/30 bg-primary/10 text-primary hover:bg-primary/20 dark:border-primary/45 dark:bg-primary/18'
                  : 'border-border/60 bg-background/40 text-muted-foreground hover:bg-background/60 dark:border-border/80 dark:bg-background/70 dark:text-muted-foreground/90',
              )}
            >
              {isParallel ? (
                <>
                  <GitBranch className="h-3 w-3" />
                  Parallel
                </>
              ) : (
                <>
                  <ArrowDownUp className="h-3 w-3" />
                  Sequential
                </>
              )}
            </button>
          </Tooltip>
          <span className="text-[10px] text-muted-foreground">
            {hasAgents ? `${group.agents.length} agent${group.agents.length === 1 ? '' : 's'}` : ''}
          </span>
        </div>
        {/* Delete group button — only visible on hover and if not the only group */}
        {canDelete && isHovering && (
          <Tooltip contentKey="pipeline.group.deleteButton">
            <button
              type="button"
              onClick={onRemoveGroup}
              aria-label="Remove group"
              className="shrink-0 rounded-md p-0.5 text-muted-foreground/50 transition-colors hover:bg-destructive/10 hover:text-destructive"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          </Tooltip>
        )}
      </div>

      {/* Agent nodes */}
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext
          items={group.agents.map((a) => a.id)}
          strategy={isParallel ? rectSortingStrategy : verticalListSortingStrategy}
        >
          {hasAgents ? (
            <div
              className={cn(
                isParallel
                  ? 'grid grid-cols-[repeat(auto-fit,minmax(14rem,1fr))] gap-2'
                  : 'flex flex-col gap-1.5',
              )}
            >
              {group.agents.map((agent) => (
                <SortableAgentNode
                  key={agent.id}
                  agent={agent}
                  isParallel={isParallel}
                  onModelSelect={(modelId, modelName) =>
                    onUpdateAgent(agent.id, { model_id: modelId, model_name: modelName })
                  }
                  onRemove={() => onRemoveAgent(agent.id)}
                  onToolsClick={() => onToolsClick(agent.id)}
                  onClone={onCloneAgent ? () => onCloneAgent(agent.id) : undefined}
                />
              ))}
            </div>
          ) : (
            <p className="rounded-lg border border-dashed border-border/60 bg-background/20 px-3 py-2 text-[11px] text-muted-foreground dark:border-border/80 dark:bg-background/50 dark:text-muted-foreground/90">
              Drop agents here or use the Add Agent button.
            </p>
          )}
        </SortableContext>
      </DndContext>

      {/* Per-group add agent affordance */}
      {onAddAgent && (
        <button
          type="button"
          onClick={onAddAgent}
          className="mt-1 flex w-full items-center justify-center gap-1 rounded-md border border-dashed border-border/40 py-1 text-[10px] text-muted-foreground/70 transition-colors hover:border-primary/30 hover:text-primary dark:border-border/80 dark:bg-background/48 dark:text-muted-foreground/90"
        >
          <Plus className="h-2.5 w-2.5" />
          Add Agent
        </button>
      )}
    </div>
  );
}
