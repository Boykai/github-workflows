/**
 * PipelineBoard — main board canvas rendering pipeline stages.
 * Supports drag-and-drop stage reordering via @dnd-kit.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { SortableContext, horizontalListSortingStrategy, arrayMove } from '@dnd-kit/sortable';
import { Plus, Layers } from 'lucide-react';
import { StageCard } from './StageCard';
import type { PipelineStage, PipelineAgentNode, AvailableAgent } from '@/types';
import type { DragEndEvent } from '@dnd-kit/core';

interface PipelineBoardProps {
  stages: PipelineStage[];
  availableAgents: AvailableAgent[];
  isEditMode: boolean;
  pipelineName: string;
  onStagesChange: (stages: PipelineStage[]) => void;
  onNameChange: (name: string) => void;
  onAddStage: () => void;
  onRemoveStage: (stageId: string) => void;
  onAddAgent: (stageId: string, agentSlug: string) => void;
  onRemoveAgent: (stageId: string, agentNodeId: string) => void;
  onUpdateAgent: (
    stageId: string,
    agentNodeId: string,
    updates: Partial<PipelineAgentNode>
  ) => void;
  onUpdateStage: (stageId: string, updates: Partial<PipelineStage>) => void;
}

export function PipelineBoard({
  stages,
  availableAgents,
  isEditMode,
  pipelineName,
  onStagesChange,
  onNameChange,
  onAddStage,
  onRemoveStage,
  onAddAgent,
  onRemoveAgent,
  onUpdateAgent,
  onUpdateStage,
}: PipelineBoardProps) {
  const [isEditingName, setIsEditingName] = useState(false);
  const [editNameValue, setEditNameValue] = useState(pipelineName);
  const nameInputRef = useRef<HTMLInputElement>(null);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

  useEffect(() => {
    setEditNameValue(pipelineName);
  }, [pipelineName]);

  useEffect(() => {
    if (isEditingName && nameInputRef.current) {
      nameInputRef.current.focus();
      nameInputRef.current.select();
    }
  }, [isEditingName]);

  const handleNameConfirm = useCallback(() => {
    const trimmed = editNameValue.trim();
    if (trimmed) onNameChange(trimmed);
    else setEditNameValue(pipelineName);
    setIsEditingName(false);
  }, [editNameValue, pipelineName, onNameChange]);

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id) return;
      const oldIndex = stages.findIndex((s) => s.id === active.id);
      const newIndex = stages.findIndex((s) => s.id === over.id);
      if (oldIndex === -1 || newIndex === -1) return;
      onStagesChange(arrayMove(stages, oldIndex, newIndex));
    },
    [stages, onStagesChange]
  );

  // Empty state
  if (stages.length === 0) {
    return (
      <div className="flex flex-col gap-4">
        {/* Edit mode banner */}
        {isEditMode && (
          <div className="rounded-lg bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
            ✏️ Editing: {pipelineName || 'Untitled Pipeline'}
          </div>
        )}

        {/* Pipeline name */}
        <div>
          {isEditingName ? (
            <input
              ref={nameInputRef}
              type="text"
              value={editNameValue}
              onChange={(e) => setEditNameValue(e.target.value)}
              onBlur={handleNameConfirm}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleNameConfirm();
                if (e.key === 'Escape') {
                  setEditNameValue(pipelineName);
                  setIsEditingName(false);
                }
              }}
              className="rounded-lg border border-primary/30 bg-background/50 px-3 py-1.5 text-lg font-semibold outline-none"
              placeholder="Pipeline name"
              maxLength={100}
            />
          ) : (
            <button
              type="button"
              onClick={() => {
                setEditNameValue(pipelineName);
                setIsEditingName(true);
              }}
              className="text-lg font-semibold text-foreground hover:text-primary transition-colors"
              title="Click to rename"
            >
              {pipelineName || 'Untitled Pipeline'}
            </button>
          )}
        </div>

        {/* Empty board CTA */}
        <div className="celestial-panel flex flex-col items-center justify-center gap-3 rounded-[1.2rem] border border-dashed border-border/60 p-8 text-center">
          <Layers className="h-8 w-8 text-muted-foreground/40" />
          <h3 className="text-sm font-semibold text-foreground">Add your first stage</h3>
          <p className="text-xs text-muted-foreground">
            Stages define the steps in your pipeline. Add agents to each stage to build your
            workflow.
          </p>
          <button
            type="button"
            onClick={onAddStage}
            className="mt-1 inline-flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            <Plus className="h-3.5 w-3.5" />
            Add Stage
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Edit mode banner */}
      {isEditMode && (
        <div className="rounded-lg bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
          ✏️ Editing: {pipelineName || 'Untitled Pipeline'}
        </div>
      )}

      {/* Pipeline name */}
      <div>
        {isEditingName ? (
          <input
            ref={nameInputRef}
            type="text"
            value={editNameValue}
            onChange={(e) => setEditNameValue(e.target.value)}
            onBlur={handleNameConfirm}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleNameConfirm();
              if (e.key === 'Escape') {
                setEditNameValue(pipelineName);
                setIsEditingName(false);
              }
            }}
            className="rounded-lg border border-primary/30 bg-background/50 px-3 py-1.5 text-lg font-semibold outline-none"
            placeholder="Pipeline name"
            maxLength={100}
          />
        ) : (
          <button
            type="button"
            onClick={() => {
              setEditNameValue(pipelineName);
              setIsEditingName(true);
            }}
            className="text-lg font-semibold text-foreground hover:text-primary transition-colors"
            title="Click to rename"
          >
            {pipelineName || 'Untitled Pipeline'}
          </button>
        )}
      </div>

      {/* Stage cards with drag-and-drop */}
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={stages.map((s) => s.id)} strategy={horizontalListSortingStrategy}>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {stages.map((stage) => (
              <StageCard
                key={stage.id}
                stage={stage}
                availableAgents={availableAgents}
                onUpdate={(updated) => onUpdateStage(stage.id, updated)}
                onRemove={() => onRemoveStage(stage.id)}
                onAddAgent={(slug) => onAddAgent(stage.id, slug)}
                onRemoveAgent={(nodeId) => onRemoveAgent(stage.id, nodeId)}
                onUpdateAgent={(nodeId, updates) => onUpdateAgent(stage.id, nodeId, updates)}
              />
            ))}

            {/* Add stage button */}
            <button
              type="button"
              onClick={onAddStage}
              className="flex min-w-[160px] flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border/50 p-4 text-muted-foreground transition-colors hover:border-primary/30 hover:text-primary"
            >
              <Plus className="h-5 w-5" />
              <span className="text-xs font-medium">Add Stage</span>
            </button>
          </div>
        </SortableContext>
      </DndContext>
    </div>
  );
}
