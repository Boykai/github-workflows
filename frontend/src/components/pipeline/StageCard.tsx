/**
 * StageCard — a named step within the pipeline board.
 * Contains agent nodes and supports inline renaming and tool selection.
 */

import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Lock, Plus, Trash2 } from 'lucide-react';
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
  verticalListSortingStrategy,
  useSortable,
  sortableKeyboardCoordinates,
  arrayMove,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { AgentNode } from './AgentNode';
import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';
import { ToolSelectorModal } from '@/components/tools/ToolSelectorModal';
import { Tooltip } from '@/components/ui/tooltip';
import type { PipelineStage, PipelineAgentNode, AvailableAgent } from '@/types';
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
}: {
  agent: PipelineAgentNode;
  onModelSelect: (modelId: string, modelName: string) => void;
  onRemove: () => void;
  onToolsClick?: () => void;
  onClone?: () => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: agent.id });

  return (
    <AgentNode
      agentNode={agent}
      onModelSelect={onModelSelect}
      onRemove={onRemove}
      onToolsClick={onToolsClick}
      onClone={onClone}
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
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(stage.name);
  const [showAgentPicker, setShowAgentPicker] = useState(false);
  const [pickerPosition, setPickerPosition] = useState<{ top: number; left: number; width: number } | null>(null);
  const [toolModalAgent, setToolModalAgent] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const addButtonRef = useRef<HTMLButtonElement>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
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
    window.addEventListener('resize', updatePickerPosition);
    window.addEventListener('scroll', updatePickerPosition, { capture: true, passive: true });

    return () => {
      window.removeEventListener('resize', updatePickerPosition);
      window.removeEventListener('scroll', updatePickerPosition, { capture: true });
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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleRenameConfirm();
    if (e.key === 'Escape') {
      setEditName(stage.name);
      setIsEditing(false);
    }
  };

  return (
    <div
    className="pipeline-column-surface pipeline-stage-card flex h-full min-w-0 flex-col gap-2 rounded-xl border border-border/70 p-3 shadow-sm backdrop-blur-sm"
    >
      {/* Header: lock icon + name + remove */}
      <div className="flex items-center gap-2">
        <Tooltip contentKey="pipeline.stage.lockIcon">
          <span role="img" aria-label="Stage position is locked">
            <Lock aria-hidden="true" className="h-4 w-4 shrink-0 text-muted-foreground/40" />
          </span>
        </Tooltip>

        {isEditing ? (
          <input
            ref={inputRef}
            type="text"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            onBlur={handleRenameConfirm}
            onKeyDown={handleKeyDown}
            className="flex-1 rounded-md border border-primary/30 bg-background/72 px-2 py-0.5 text-sm font-medium outline-none"
            maxLength={100}
          />
        ) : (
          <button
            type="button"
            onClick={() => { setEditName(stage.name); setIsEditing(true); }}
            className="flex-1 text-left text-sm font-medium text-foreground hover:text-primary transition-colors truncate"
            title="Click to rename"
          >
            {stage.name}
          </button>
        )}

        <Tooltip contentKey="pipeline.stage.deleteButton">
          <button
            type="button"
            onClick={onRemove}
            aria-label="Remove stage"
            className="shrink-0 rounded-md p-1 text-muted-foreground/50 transition-colors hover:bg-destructive/10 hover:text-destructive"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </Tooltip>
      </div>

      {/* Agent nodes */}
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleAgentDragEnd}>
        <SortableContext items={stage.agents.map((a) => a.id)} strategy={verticalListSortingStrategy}>
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
          initialSelectedIds={
            stage.agents.find((a) => a.id === toolModalAgent)?.tool_ids ?? []
          }
          projectId={projectId}
        />
      )}

      {/* Add agent */}
      <div className="relative">
        <button
          ref={addButtonRef}
          type="button"
          onClick={() => setShowAgentPicker(!showAgentPicker)}
          className="pipeline-stage-add flex w-full items-center justify-center gap-1 rounded-lg border border-dashed border-border/50 py-1.5 text-[11px] text-muted-foreground transition-colors hover:border-primary/30 hover:text-primary"
        >
          <Plus className="h-3 w-3" />
          Add Agent
        </button>

        {showAgentPicker && pickerPosition && createPortal(
          <>
            <div className="fixed inset-0 z-40" onClick={() => setShowAgentPicker(false)} onKeyDown={(e) => { if (e.key === 'Escape') setShowAgentPicker(false); }} role="button" tabIndex={0} aria-label="Close agent picker" />
            <div
              className="fixed z-50 rounded-lg border border-border/80 bg-popover/95 shadow-lg backdrop-blur-sm"
              style={{ top: pickerPosition.top, left: pickerPosition.left, width: pickerPosition.width }}
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
                {!agentsLoading && !agentsError && availableAgents.map((agent) => {
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
                      <ThemedAgentIcon slug={agent.slug} name={displayName} avatarUrl={agent.avatar_url} iconName={agent.icon_name} size="sm" />
                      <span className="font-medium">{displayName}</span>
                      <span className="text-[10px] text-muted-foreground">({agent.slug})</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </>,
          document.body,
        )}
      </div>
    </div>
  );
}
