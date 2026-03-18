/**
 * AgentConfigRow component - collapsible container that renders one AgentColumnCell
 * per status column, aligned with the board columns below.
 * Includes AgentSaveBar for save/discard workflow.
 * Wraps all columns in a single DndContext for cross-column drag-and-drop.
 */

import { useState, useCallback, useRef, useMemo } from 'react';
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
import { arrayMove, sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import type { BoardColumn, AvailableAgent, AgentAssignment } from '@/types';
import { AgentColumnCell } from './AgentColumnCell';
import { AgentDragOverlay } from './AgentDragOverlay';
import { AgentSaveBar } from './AgentSaveBar';
import { useAgentConfig } from '@/hooks/useAgentConfig';
import { cn } from '@/lib/utils';

function AgentPipelineSigil() {
  return (
    <span className="celestial-sigil golden-ring relative inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-primary/30 bg-[radial-gradient(circle_at_34%_28%,hsl(var(--glow)/0.26),hsl(var(--background)/0.94)_48%,hsl(var(--night)/0.96)_100%)] shadow-[0_0_30px_hsl(var(--night)/0.2)]">
      <span className="celestial-orbit inset-[3px] border-primary/20" />
      <svg viewBox="0 0 24 24" className="relative z-10 h-5 w-5" aria-hidden="true">
        <circle cx="8.1" cy="8.3" r="3.15" fill="hsl(var(--gold))" opacity="0.94" />
        <circle cx="8.1" cy="8.3" r="1.55" fill="hsl(var(--glow))" opacity="0.92" />
        <g stroke="hsl(var(--gold))" strokeWidth="0.9" strokeLinecap="round" opacity="0.88">
          <path d="M8.1 3.1v1.6" />
          <path d="M8.1 12.1v1.6" />
          <path d="M2.9 8.3h1.6" />
          <path d="M11.9 8.3h1.6" />
          <path d="m4.4 4.6 1.15 1.15" />
          <path d="m10.65 10.85 1.15 1.15" />
          <path d="m4.4 12 1.15-1.15" />
          <path d="m10.65 5.75 1.15-1.15" />
        </g>
        <path
          d="M15.6 5.8a4.7 4.7 0 1 0 0 9.4c.92-.78 1.45-2.12 1.45-4.7 0-2.22-.56-3.88-1.45-4.7Z"
          fill="hsl(var(--foreground))"
          opacity="0.96"
        />
        <path
          d="M5.2 16.55c1.9-2.1 4.9-3.38 8.1-3.38 2.08 0 3.96.46 5.58 1.34"
          stroke="hsl(var(--border))"
          strokeWidth="1.05"
          strokeLinecap="round"
          fill="none"
          opacity="0.9"
        />
        <circle cx="18.1" cy="16.55" r="1.05" fill="hsl(var(--gold))" opacity="0.92" />
        <path
          d="M18.35 3.9 18.9 5.35 20.35 5.9 18.9 6.45 18.35 7.9 17.8 6.45 16.35 5.9 17.8 5.35 18.35 3.9Z"
          fill="hsl(var(--star))"
        />
      </svg>
      <span className="absolute -bottom-0.5 -right-0.5 z-10 h-2.5 w-2.5 rounded-full border border-background/85 bg-primary/85 shadow-[0_0_12px_hsl(var(--glow)/0.3)]" />
    </span>
  );
}

interface AgentConfigRowProps {
  columnCount: number;
  columns: BoardColumn[];
  agentConfig: ReturnType<typeof useAgentConfig>;
  availableAgents?: AvailableAgent[];
  renderPresetSelector?: React.ReactNode;
  renderAddButton?: (status: string) => React.ReactNode;
  variant?: 'default' | 'compact';
  title?: string;
  workflowEnabled?: boolean | null;
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
  variant = 'default',
  title = 'Agents Pipelines',
  workflowEnabled = null,
}: AgentConfigRowProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [activeAgent, setActiveAgent] = useState<AgentAssignment | null>(null);
  const [activeAgentWidth, setActiveAgentWidth] = useState<number | null>(null);
  const snapshotRef = useRef<Record<string, AgentAssignment[]> | null>(null);
  const isCompact = variant === 'compact';

  const {
    localMappings,
    isDirty,
    isColumnDirty,
    removeAgent,
    cloneAgent,
    reorderAgents,
    moveAgentToColumn,
    save,
    discard,
    isSaving,
    saveError,
    isLoaded,
  } = agentConfig;

  const compactConstellation = useMemo(() => {
    if (!isCompact || columns.length === 0) {
      return { nodes: [], edges: [], stars: [] };
    }

    const visibleColumns = columns.slice(0, Math.max(columnCount, 1));
    const leftInset = visibleColumns.length === 1 ? 50 : 8;
    const rightInset = visibleColumns.length === 1 ? 50 : 8;
    const topInset = 24;
    const bottomInset = 16;
    const usableHeight = Math.max(24, 100 - topInset - bottomInset);

    const nodes = visibleColumns.flatMap((column, columnIndex) => {
      const agents = localMappings[column.status.name] ?? [];
      if (agents.length === 0) return [];

      const x =
        visibleColumns.length === 1
          ? 50
          : leftInset +
            (columnIndex * (100 - leftInset - rightInset)) / (visibleColumns.length - 1);

      const rows =
        agents.length === 1
          ? [topInset + usableHeight / 2]
          : agents.map(
              (_, agentIndex) => topInset + (agentIndex * usableHeight) / (agents.length - 1)
            );

      return agents.map((agent, agentIndex) => ({
        id: agent.id,
        x,
        y: rows[agentIndex],
      }));
    });

    const edges = nodes.slice(0, -1).map((node, index) => {
      const next = nodes[index + 1];
      const controlX = (node.x + next.x) / 2;
      const controlY = Math.min(node.y, next.y) - (Math.abs(node.x - next.x) > 1 ? 8 : 0);
      return {
        id: `${node.id}-${next.id}`,
        path: `M ${node.x} ${node.y} Q ${controlX} ${controlY} ${next.x} ${next.y}`,
      };
    });

    const stars = [
      { id: 'c1', x: 6, y: 18, r: 1.1 },
      { id: 'c2', x: 26, y: 82, r: 1.2 },
      { id: 'c3', x: 54, y: 10, r: 1 },
      { id: 'c4', x: 78, y: 74, r: 1.15 },
      { id: 'c5', x: 94, y: 22, r: 1.05 },
    ];

    return { nodes, edges, stars };
  }, [columnCount, columns, isCompact, localMappings]);

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
      let targetColumn: string | null;
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
      <div
        className={cn('celestial-panel flex flex-col border border-border/60', isCompact ? 'rounded-[1rem]' : 'rounded-[1.2rem]')}
      >
        <div
          className={cn('flex items-center gap-2 border-b border-border/40 bg-background/38', isCompact ? 'rounded-t-[1rem] px-3 py-1.5' : 'rounded-t-[1.2rem] p-2')}
        >
          <span
            className={cn('flex items-center gap-2 font-semibold text-foreground', isCompact ? 'text-xs uppercase tracking-[0.18em]' : 'text-sm')}
          >
            <AgentPipelineSigil />
            {title}
          </span>
          {workflowEnabled !== null && (
            <span
              className={cn('ml-2 rounded-full px-3 py-0.5 text-[10px] font-semibold uppercase tracking-[0.18em] shadow-sm', workflowEnabled
                  ? 'solar-chip-success'
                  : 'solar-chip-soft border-amber-300/60 text-amber-800 dark:text-amber-300')}
            >
              {workflowEnabled ? 'Workflow enabled' : 'Workflow disabled'}
            </span>
          )}
        </div>
        <div className={isCompact ? 'p-1.5' : 'p-2'}>
          <div className={cn('flex overflow-x-auto', isCompact ? 'gap-2 pb-1' : 'gap-4 pb-2')}>
            {columns.map((col) => (
              <div
                key={col.status.option_id}
                className={cn('flex flex-1 flex-col border border-border/60 animate-pulse', isCompact ? 'min-w-[220px] max-w-[280px] gap-1.5 rounded-[1rem] p-1.5' : 'min-w-[300px] max-w-[350px] gap-2 rounded-[1.2rem] p-2')}
              >
                <div className="h-10 bg-muted rounded-md w-full" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      role="region"
      aria-label="Agent column assignments"
      className={cn('celestial-panel relative flex flex-col border border-border/60', isCompact ? 'rounded-[1rem] bg-[radial-gradient(circle_at_50%_-10%,hsl(var(--glow)/0.12),transparent_26%),linear-gradient(180deg,hsl(var(--background)/0.58),hsl(var(--background)/0.78))]' : 'rounded-[1.2rem]')}
    >
      {/* Header with toggle and presets */}
      <div
        className={cn('flex items-center gap-2 border-b border-border/40 bg-background/38', isCompact ? 'rounded-t-[1rem] px-3 py-1.5' : 'rounded-t-[1.2rem] p-2')}
      >
        <button
          className={cn('celestial-focus solar-action flex items-center justify-center rounded-md text-muted-foreground transition-colors hover:text-foreground', isCompact ? 'h-5 w-5 text-xs' : 'h-6 w-6')}
          onClick={() => setIsExpanded(!isExpanded)}
          aria-label={isExpanded ? 'Collapse agent row' : 'Expand agent row'}
          type="button"
        >
          {isExpanded ? '▾' : '▸'}
        </button>
        <span
          className={cn('flex items-center gap-2 font-semibold text-foreground', isCompact ? 'text-[11px] uppercase tracking-[0.18em]' : 'text-sm')}
        >
          <AgentPipelineSigil />
          {title}
        </span>
        {workflowEnabled !== null && (
          <span
            className={cn('ml-2 rounded-full px-3 py-0.5 text-[10px] font-semibold uppercase tracking-[0.18em] shadow-sm', workflowEnabled
                ? 'solar-chip-success'
                : 'solar-chip-soft border-amber-300/60 text-amber-800 dark:text-amber-300')}
          >
            {workflowEnabled ? 'Workflow enabled' : 'Workflow disabled'}
          </span>
        )}
        {renderPresetSelector}
      </div>

      {/* Collapsible body */}
      {isExpanded && (
        <div className={isCompact ? 'py-1.5' : 'py-2'}>
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
            onDragCancel={handleDragCancel}
          >
            <div className="overflow-x-auto">
              <div
                className={cn('relative grid min-w-full items-start', isCompact ? 'gap-2 px-2 pb-1' : 'gap-3 px-2 pb-2')}
                style={{
                  gridTemplateColumns: `repeat(${Math.max(columnCount, 1)}, minmax(${isCompact ? '12rem' : '14rem'}, 1fr))`,
                }}
              >
                {isCompact && compactConstellation.nodes.length > 1 && (
                  <svg
                    className="pointer-events-none absolute inset-0 h-full w-full overflow-visible"
                    viewBox="0 0 100 100"
                    preserveAspectRatio="none"
                    aria-hidden="true"
                  >
                    {compactConstellation.edges.map((edge, index) => (
                      <g key={edge.id}>
                        <path
                          d={edge.path}
                          fill="none"
                          stroke="hsl(var(--border) / 0.24)"
                          strokeWidth="1.8"
                          strokeLinecap="round"
                        />
                        <path
                          d={edge.path}
                          fill="none"
                          stroke={
                            index % 2 === 0
                              ? 'hsl(var(--gold) / 0.5)'
                              : 'hsl(var(--primary) / 0.46)'
                          }
                          strokeWidth="0.72"
                          strokeLinecap="round"
                        />
                      </g>
                    ))}
                    {compactConstellation.stars.map((star) => (
                      <circle
                        key={star.id}
                        cx={star.x}
                        cy={star.y}
                        r={star.r}
                        fill="hsl(var(--star) / 0.8)"
                      />
                    ))}
                  </svg>
                )}
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
                      onCloneAgent={cloneAgent}
                      onReorderAgents={reorderAgents}
                      renderAddButton={renderAddButton?.(status)}
                      availableAgents={availableAgents}
                      variant={variant}
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
        <AgentSaveBar onSave={save} onDiscard={discard} isSaving={isSaving} error={saveError} />
      )}
    </div>
  );
}
