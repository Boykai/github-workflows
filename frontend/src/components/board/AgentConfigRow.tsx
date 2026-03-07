/**
 * AgentConfigRow component - collapsible container that renders one AgentColumnCell
 * per status column, aligned with the board columns below.
 * Includes AgentSaveBar for save/discard workflow.
 * Wraps all columns in a single DndContext for cross-column drag-and-drop.
 */

import { useState, useCallback, useRef } from 'react';
import {
  DndContext,
  DragOverlay,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  TouchSensor,
  useSensors,
  useSensor,
  type DragStartEvent,
  type DragOverEvent,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable';
import type { BoardColumn, AvailableAgent, AgentAssignment } from '@/types';
import { AgentColumnCell } from './AgentColumnCell';
import { AgentDragOverlay } from './AgentDragOverlay';
import { AgentSaveBar } from './AgentSaveBar';
import { useAgentConfig } from '@/hooks/useAgentConfig';

interface AgentConfigRowProps {
  columnCount: number;
  columns: BoardColumn[];
  agentConfig: ReturnType<typeof useAgentConfig>;
  availableAgents?: AvailableAgent[];
  renderPresetSelector?: React.ReactNode;
  renderAddButton?: (status: string) => React.ReactNode;
}

/** Find which column an agent ID belongs to */
function findColumnForAgent(
  mappings: Record<string, AgentAssignment[]>,
  agentId: string
): string | null {
  for (const [status, agents] of Object.entries(mappings)) {
    if (agents.some((a) => a.id === agentId)) {
      return status;
    }
  }
  return null;
}

export function AgentConfigRow({
  columnCount,
  columns,
  agentConfig,
  availableAgents,
  renderPresetSelector,
  renderAddButton,
}: AgentConfigRowProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [activeAgent, setActiveAgent] = useState<AgentAssignment | null>(null);
  const [activeAgentWidth, setActiveAgentWidth] = useState<number | null>(null);
  const snapshotRef = useRef<Record<string, AgentAssignment[]> | null>(null);

  const {
    localMappings,
    isDirty,
    isColumnDirty,
    removeAgent,
    reorderAgents,
    moveAgentToColumn,
    save,
    discard,
    isSaving,
    saveError,
    isLoaded,
  } = agentConfig;

  // Sensors: PointerSensor (mouse), TouchSensor (mobile), KeyboardSensor (a11y)
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 250, tolerance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  // Save snapshot on drag start for cancel-revert
  const handleDragStart = useCallback(
    (event: DragStartEvent) => {
      const agentId = String(event.active.id);
      snapshotRef.current = structuredClone(localMappings);
      setActiveAgentWidth(event.active.rect.current.initial?.width ?? null);

      // Find the active agent across all columns
      for (const agents of Object.values(localMappings)) {
        const found = agents.find((a) => a.id === agentId);
        if (found) {
          setActiveAgent(found);
          return;
        }
      }
    },
    [localMappings]
  );

  // Live preview: move agent between columns as cursor crosses boundaries
  const handleDragOver = useCallback(
    (event: DragOverEvent) => {
      const { active, over } = event;
      if (!over) return;

      const activeId = String(active.id);
      const overId = String(over.id);

      // Determine the source column
      const sourceColumn = findColumnForAgent(localMappings, activeId);
      if (!sourceColumn) return;

      // Determine the target column: either the over item's column, or the droppable column ID
      let targetColumn: string | null = null;
      let targetIndex: number | undefined;

      // Check if over is a column (droppable) or an agent (sortable item)
      const overColumn = findColumnForAgent(localMappings, overId);
      if (overColumn) {
        // Hovering over another agent — target is that agent's column
        targetColumn = overColumn;
        const targetAgents = localMappings[targetColumn] ?? [];
        targetIndex = targetAgents.findIndex((a) => a.id === overId);
      } else {
        // Hovering over an empty column droppable zone
        targetColumn = overId;
        targetIndex = undefined; // Append
      }

      if (!targetColumn || sourceColumn === targetColumn) return;

      moveAgentToColumn(sourceColumn, targetColumn, activeId, targetIndex);
    },
    [localMappings, moveAgentToColumn]
  );

  // Finalize drop: handle same-column reorder or cross-column is already done via handleDragOver
  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      setActiveAgent(null);
      setActiveAgentWidth(null);
      snapshotRef.current = null;

      if (!over || active.id === over.id) return;

      const activeId = String(active.id);
      const overId = String(over.id);

      // Find which column the active agent is in now
      const activeColumn = findColumnForAgent(localMappings, activeId);
      const overColumn = findColumnForAgent(localMappings, overId);

      if (activeColumn && overColumn && activeColumn === overColumn) {
        // Same-column reorder
        const agents = localMappings[activeColumn] ?? [];
        const oldIndex = agents.findIndex((a) => a.id === activeId);
        const newIndex = agents.findIndex((a) => a.id === overId);
        if (oldIndex !== -1 && newIndex !== -1 && oldIndex !== newIndex) {
          const newOrder = arrayMove(agents, oldIndex, newIndex);
          reorderAgents(activeColumn, newOrder);
        }
      }
      // Cross-column moves are already handled by handleDragOver
    },
    [localMappings, reorderAgents]
  );

  // Revert to snapshot on cancel
  const handleDragCancel = useCallback(() => {
    setActiveAgent(null);
    setActiveAgentWidth(null);
    if (snapshotRef.current) {
      const snapshot = snapshotRef.current;
      const snapshotStatuses = new Set(Object.keys(snapshot));

      // Clear any statuses introduced during drag that are not in the snapshot
      for (const status of Object.keys(localMappings)) {
        if (!snapshotStatuses.has(status)) {
          reorderAgents(status, []);
        }
      }

      // Restore each column from the snapshot
      for (const [status, agents] of Object.entries(snapshot)) {
        reorderAgents(status, agents);
      }
      snapshotRef.current = null;
    }
  }, [localMappings, reorderAgents]);

  // Loading skeleton (T030)
  if (!isLoaded) {
    return (
      <div className="celestial-panel flex flex-col rounded-[1.2rem] border border-border/60">
        <div className="flex items-center gap-2 rounded-t-[1.2rem] border-b border-border/40 bg-background/38 p-2">
          <span className="text-sm font-semibold text-foreground flex items-center gap-2">🤖 Agent Pipeline</span>
        </div>
        <div className="p-2">
          <div className="flex gap-4 overflow-x-auto pb-2">
            {columns.map((col) => (
              <div key={col.status.option_id} className="flex-1 min-w-[300px] max-w-[350px] flex flex-col gap-2 p-2 rounded-[1.2rem] border border-border/60 animate-pulse">
                <div className="h-10 bg-muted rounded-md w-full" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="celestial-panel flex flex-col rounded-[1.2rem] border border-border/60 relative">
      {/* Header with toggle and presets */}
      <div className="flex items-center gap-2 rounded-t-[1.2rem] border-b border-border/40 bg-background/38 p-2">
        <button
          className="solar-action flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground transition-colors hover:text-foreground"
          onClick={() => setIsExpanded(!isExpanded)}
          title={isExpanded ? 'Collapse agent row' : 'Expand agent row'}
          type="button"
        >
          {isExpanded ? '▾' : '▸'}
        </button>
        <span className="text-sm font-semibold text-foreground flex items-center gap-2">🤖 Agent Pipeline</span>
        {renderPresetSelector}
      </div>

      {/* Collapsible body */}
      {isExpanded && (
        <div className="py-2">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
            onDragCancel={handleDragCancel}
          >
           <div className="overflow-x-auto">
            <div className="grid min-w-full items-start gap-3 pb-2 px-2" style={{ gridTemplateColumns: `repeat(${Math.max(columnCount, 1)}, minmax(14rem, 1fr))` }}>
              {columns.map((col) => {
                const status = col.status.name;
                const agents = localMappings[status] ?? [];

                return (
                  <AgentColumnCell
                    key={col.status.option_id}
                    status={status}
                    agents={agents}
                    isModified={isColumnDirty(status)}
                    onRemoveAgent={removeAgent}
                    onReorderAgents={reorderAgents}
                    renderAddButton={renderAddButton?.(status)}
                    availableAgents={availableAgents}
                  />
                );
              })}
            </div>
           </div>

            {/* Floating drag overlay */}
            <DragOverlay dropAnimation={{ duration: 200, easing: 'ease' }}>
              {activeAgent ? (
                <AgentDragOverlay
                  agent={activeAgent}
                  availableAgents={availableAgents}
                  width={activeAgentWidth}
                />
              ) : null}
            </DragOverlay>
          </DndContext>
        </div>
      )}

      {/* Floating save bar */}
      {isDirty && (
        <AgentSaveBar
          onSave={save}
          onDiscard={discard}
          isSaving={isSaving}
          error={saveError}
        />
      )}
    </div>
  );
}
