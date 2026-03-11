/**
 * StageCard — a named step within the pipeline board.
 * Contains agent nodes and supports inline renaming and tool selection.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { GitBranch, Lock, Plus, Trash2 } from 'lucide-react';
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
  useSortable,
  sortableKeyboardCoordinates,
  arrayMove,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { AgentNode } from './AgentNode';
import { ParallelStageGroup } from './ParallelStageGroup';
import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';
import { ToolSelectorModal } from '@/components/tools/ToolSelectorModal';
import { Tooltip } from '@/components/ui/tooltip';
import { useConfirmation } from '@/hooks/useConfirmation';
import type { PipelineStage, PipelineAgentNode, AvailableAgent } from '@/types';
import { cn } from '@/lib/utils';
import { formatAgentName } from '@/utils/formatAgentName';

interface StageCardProps {
  stage: PipelineStage;
  availableAgents: AvailableAgent[];
  agentsLoading?: boolean;
  agentsError?: string | null;
  onRetryAgents?: () => void;
  projectId: string;
  onUpdate: (updatedStage: PipelineStage) => void;
  onRemove: () => void;
  onAddAgent: (agentSlug: string) => void;
  onRemoveAgent: (agentNodeId: string) => void;
  onUpdateAgent: (agentNodeId: string, updates: Partial<PipelineAgentNode>) => void;
  onCloneAgent?: (agentNodeId: string) => void;
  onReorderAgents: (newOrder: PipelineAgentNode[]) => void;
}

/** Thin sortable wrapper so each AgentNode participates in the DnD context. */
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

export function StageCard({
  stage,
  availableAgents,
  agentsLoading = false,
  agentsError = null,
  onRetryAgents,
  projectId,
  onUpdate,
  onRemove,
  onAddAgent,
  onRemoveAgent,
  onUpdateAgent,
  onCloneAgent,
  onReorderAgents,
}: StageCardProps) {
  const { confirm } = useConfirmation();
  const hasAgents = stage.agents.length > 0;
  const isParallelStage =
    stage.execution_mode === 'parallel' && stage.agents.length > 1;
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(stage.name);
  const [showAgentPicker, setShowAgentPicker] = useState(false);
  const [pickerPosition, setPickerPosition] = useState<{
    top: number;
    left: number;
    width: number;
  } | null>(null);
  const [toolModalAgent, setToolModalAgent] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const addButtonRef = useRef<HTMLButtonElement>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const handleAgentDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = stage.agents.findIndex((a) => a.id === active.id);
    const newIndex = stage.agents.findIndex((a) => a.id === over.id);
    if (oldIndex === -1 || newIndex === -1) return;
    onReorderAgents(arrayMove(stage.agents, oldIndex, newIndex));
  };

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  useEffect(() => {
    if (!showAgentPicker) {
      setPickerPosition(null);
      return;
    }

    const updatePickerPosition = () => {
      if (!addButtonRef.current) return;
      const rect = addButtonRef.current.getBoundingClientRect();
      const width = Math.max(rect.width, 220);
      const maxLeft = Math.max(window.innerWidth - width - 12, 12);
      setPickerPosition({
        top: rect.bottom + 4,
        left: Math.min(rect.left, maxLeft),
        width,
      });
    };

    updatePickerPosition();

    // Throttle scroll/resize recalculations to once per animation frame to
    // prevent layout thrashing from repeated getBoundingClientRect calls.
    let rafId = 0;
    const scheduleUpdate = () => {
      if (rafId) return;
      rafId = requestAnimationFrame(() => {
        rafId = 0;
        updatePickerPosition();
      });
    };

    window.addEventListener('resize', scheduleUpdate);
    window.addEventListener('scroll', scheduleUpdate, { capture: true, passive: true });

    return () => {
      window.removeEventListener('resize', scheduleUpdate);
      window.removeEventListener('scroll', scheduleUpdate, { capture: true });
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, [showAgentPicker]);

  const handleRenameConfirm = () => {
    const trimmed = editName.trim();
    if (trimmed && trimmed !== stage.name) {
      onUpdate({ ...stage, name: trimmed });
    } else {
      setEditName(stage.name);
    }
    setIsEditing(false);
  };

  const handleRemoveStage = useCallback(async () => {
    const agentCount = stage.agents.length;
    const description =
      agentCount > 0
        ? `Remove stage "${stage.name}" and its ${agentCount} assigned agent${agentCount !== 1 ? 's' : ''}? This change takes effect when you save the pipeline.`
        : `Remove stage "${stage.name}"? This change takes effect when you save the pipeline.`;

    const confirmed = await confirm({
      title: 'Remove Pipeline Stage',
      description,
      variant: 'warning',
      confirmLabel: 'Remove Stage',
    });
    if (confirmed) {
      onRemove();
    }
  }, [confirm, stage.name, stage.agents.length, onRemove]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleRenameConfirm();
    if (e.key === 'Escape') {
      setEditName(stage.name);
      setIsEditing(false);
    }
  };

  return (
    <div className="celestial-panel celestial-fade-in pipeline-column-surface pipeline-stage-card flex h-full min-w-0 flex-col gap-2 rounded-xl border border-border/70 p-3 shadow-sm backdrop-blur-sm">
      {/* Header: lock icon + name + remove */}
      <div className="flex items-start gap-2">
        <Tooltip contentKey="pipeline.stage.lockIcon">
          <span role="img" aria-label="Stage position is locked" className="pt-0.5">
            <Lock aria-hidden="true" className="h-4 w-4 shrink-0 text-muted-foreground/40" />
          </span>
        </Tooltip>

        <div className="min-w-0 flex-1">
          {isEditing ? (
            <input
              ref={inputRef}
              type="text"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              onBlur={handleRenameConfirm}
              onKeyDown={handleKeyDown}
              className="w-full rounded-md border border-primary/30 bg-background/72 px-2 py-0.5 text-sm font-medium outline-none"
              maxLength={100}
            />
          ) : (
            <button
              type="button"
              onClick={() => {
                setEditName(stage.name);
                setIsEditing(true);
              }}
              className="w-full truncate text-left text-sm font-medium text-foreground transition-colors hover:text-primary"
              title="Click to rename"
            >
              {stage.name}
            </button>
          )}

          <div className="mt-1 flex flex-wrap items-center gap-1.5">
            <Tooltip
              contentKey={
                isParallelStage ? 'pipeline.stage.parallelGroup' : 'pipeline.stage.sequentialGroup'
              }
            >
              <span
                className={cn(
                  'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.16em]',
                  isParallelStage
                    ? 'border-primary/30 bg-primary/10 text-primary'
                    : 'border-border/60 bg-background/40 text-muted-foreground'
                )}
              >
                {isParallelStage && <GitBranch className="h-3 w-3" />}
                {isParallelStage ? 'Grouped Stage' : 'Sequential Stage'}
              </span>
            </Tooltip>
            <span className="text-[10px] text-muted-foreground">
              {hasAgents
                ? `${stage.agents.length} agent${stage.agents.length === 1 ? '' : 's'} assigned`
                : 'Add an agent to begin this stage'}
            </span>
          </div>
        </div>

        <Tooltip contentKey="pipeline.stage.deleteButton">
          <button
            type="button"
            onClick={handleRemoveStage}
            aria-label="Remove stage"
            className="shrink-0 rounded-md p-1 text-muted-foreground/50 transition-colors hover:bg-destructive/10 hover:text-destructive"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </Tooltip>
      </div>

      {/* Agent nodes */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleAgentDragEnd}
      >
        <SortableContext
          items={stage.agents.map((a) => a.id)}
          strategy={isParallelStage ? rectSortingStrategy : verticalListSortingStrategy}
        >
          {isParallelStage ? (
              <ParallelStageGroup>
                {stage.agents.map((agent) => (
                  <SortableAgentNode
                    key={agent.id}
                    agent={agent}
                    isParallel
                    onModelSelect={(modelId, modelName) =>
                      onUpdateAgent(agent.id, { model_id: modelId, model_name: modelName })
                    }
                    onRemove={() => onRemoveAgent(agent.id)}
                    onToolsClick={() => setToolModalAgent(agent.id)}
                    onClone={onCloneAgent ? () => onCloneAgent(agent.id) : undefined}
                  />
                ))}
              </ParallelStageGroup>
            ) : (
              <div className="rounded-xl border border-border/50 bg-background/18 p-2">
                {hasAgents ? (
                  <div className="flex flex-col gap-1.5">
                    {stage.agents.map((agent) => (
                      <SortableAgentNode
                        key={agent.id}
                        agent={agent}
                        onModelSelect={(modelId, modelName) =>
                          onUpdateAgent(agent.id, { model_id: modelId, model_name: modelName })
                        }
                        onRemove={() => onRemoveAgent(agent.id)}
                        onToolsClick={() => setToolModalAgent(agent.id)}
                        onClone={onCloneAgent ? () => onCloneAgent(agent.id) : undefined}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="rounded-lg border border-dashed border-border/60 bg-background/20 px-3 py-3 text-xs text-muted-foreground">
                    Add your first agent here. Once a stage has multiple agents, they appear side by
                    side so the stage reads as a coordinated group.
                  </p>
                )}
              </div>
            )}
        </SortableContext>
      </DndContext>

      {/* Tool Selector Modal */}
      {toolModalAgent && (
        <ToolSelectorModal
          isOpen={!!toolModalAgent}
          onClose={() => setToolModalAgent(null)}
          onConfirm={(selectedToolIds) => {
            onUpdateAgent(toolModalAgent, {
              tool_ids: selectedToolIds,
              tool_count: selectedToolIds.length,
            });
            setToolModalAgent(null);
          }}
          initialSelectedIds={stage.agents.find((a) => a.id === toolModalAgent)?.tool_ids ?? []}
          projectId={projectId}
        />
      )}

      {/* Add agent */}
      <div className="relative">
        <Tooltip contentKey="pipeline.stage.addAgentButton">
          <button
            ref={addButtonRef}
            type="button"
            onClick={() => setShowAgentPicker(!showAgentPicker)}
            className="pipeline-stage-add flex w-full items-center justify-center gap-1 rounded-lg border border-dashed border-border/50 py-1.5 text-[11px] text-muted-foreground transition-colors hover:border-primary/30 hover:text-primary"
          >
            <Plus className="h-3 w-3" />
            {hasAgents ? 'Add Agent to Group' : 'Add Agent'}
          </button>
        </Tooltip>

        {showAgentPicker &&
          pickerPosition &&
          createPortal(
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowAgentPicker(false)}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') setShowAgentPicker(false);
                }}
                role="button"
                tabIndex={0}
                aria-label="Close agent picker"
              />
              <div
                className="fixed z-50 rounded-lg border border-border/80 bg-popover/95 shadow-lg backdrop-blur-sm"
                style={{
                  top: pickerPosition.top,
                  left: pickerPosition.left,
                  width: pickerPosition.width,
                }}
              >
                <div className="max-h-40 overflow-y-auto p-1">
                  {agentsLoading && (
                    <div className="flex items-center justify-center gap-2 py-3 text-xs text-muted-foreground">
                      <span className="h-3.5 w-3.5 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
                      Loading agents...
                    </div>
                  )}
                  {!agentsLoading && agentsError && (
                    <div className="flex flex-col gap-2 p-2 text-xs text-destructive">
                      <span>Failed to load agents</span>
                      {onRetryAgents && (
                        <button
                          type="button"
                          className="rounded-md border border-destructive/20 bg-background px-2 py-1 text-[11px] hover:bg-destructive/10"
                          onClick={onRetryAgents}
                        >
                          Retry
                        </button>
                      )}
                    </div>
                  )}
                  {!agentsLoading && !agentsError && availableAgents.length === 0 && (
                    <div className="py-2 text-center text-xs text-muted-foreground">
                      No agents available
                    </div>
                  )}
                  {!agentsLoading &&
                    !agentsError &&
                    availableAgents.map((agent) => {
                      const displayName = formatAgentName(agent.slug, agent.display_name);

                      return (
                        <button
                          key={agent.slug}
                          type="button"
                          onClick={() => {
                            onAddAgent(agent.slug);
                            setShowAgentPicker(false);
                          }}
                          className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs transition-colors hover:bg-primary/10"
                        >
                          <ThemedAgentIcon
                            slug={agent.slug}
                            name={displayName}
                            avatarUrl={agent.avatar_url}
                            iconName={agent.icon_name}
                            size="sm"
                          />
                          <span className="font-medium">{displayName}</span>
                          <span className="text-[10px] text-muted-foreground">({agent.slug})</span>
                        </button>
                      );
                    })}
                </div>
              </div>
            </>,
            document.body
          )}
      </div>
    </div>
  );
}
