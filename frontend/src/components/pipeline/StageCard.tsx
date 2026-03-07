/**
 * StageCard — a named step within the pipeline board.
 * Contains agent nodes and supports inline renaming.
 */

import { useState, useRef, useEffect } from 'react';
import { GripVertical, Plus, Trash2 } from 'lucide-react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { AgentNode } from './AgentNode';
import type { PipelineStage, PipelineAgentNode, AvailableAgent } from '@/types';

interface StageCardProps {
  stage: PipelineStage;
  availableAgents: AvailableAgent[];
  onUpdate: (updatedStage: PipelineStage) => void;
  onRemove: () => void;
  onAddAgent: (agentSlug: string) => void;
  onRemoveAgent: (agentNodeId: string) => void;
  onUpdateAgent: (agentNodeId: string, updates: Partial<PipelineAgentNode>) => void;
}

export function StageCard({
  stage,
  availableAgents,
  onUpdate,
  onRemove,
  onAddAgent,
  onRemoveAgent,
  onUpdateAgent,
}: StageCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(stage.name);
  const [showAgentPicker, setShowAgentPicker] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: stage.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

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
      ref={setNodeRef}
      style={style}
      className={`flex min-w-[220px] flex-col gap-2 rounded-xl border border-border/70 bg-card/80 p-3 backdrop-blur-sm transition-shadow ${
        isDragging ? 'shadow-lg ring-2 ring-primary/30' : 'shadow-sm'
      }`}
    >
      {/* Header: drag handle + name + remove */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="cursor-grab touch-none text-muted-foreground/50 hover:text-muted-foreground"
          {...attributes}
          {...listeners}
        >
          <GripVertical className="h-4 w-4" />
        </button>

        {isEditing ? (
          <input
            ref={inputRef}
            type="text"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            onBlur={handleRenameConfirm}
            onKeyDown={handleKeyDown}
            className="flex-1 rounded-md border border-primary/30 bg-background/50 px-2 py-0.5 text-sm font-medium outline-none"
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

        <button
          type="button"
          onClick={onRemove}
          className="shrink-0 rounded-md p-1 text-muted-foreground/50 transition-colors hover:bg-destructive/10 hover:text-destructive"
          title="Remove stage"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Agent nodes */}
      <div className="flex flex-col gap-1.5">
        {stage.agents.map((agent) => (
          <AgentNode
            key={agent.id}
            agentNode={agent}
            onModelSelect={(modelId, modelName) =>
              onUpdateAgent(agent.id, { model_id: modelId, model_name: modelName })
            }
            onRemove={() => onRemoveAgent(agent.id)}
          />
        ))}
      </div>

      {/* Add agent */}
      <div className="relative">
        <button
          type="button"
          onClick={() => setShowAgentPicker(!showAgentPicker)}
          className="flex w-full items-center justify-center gap-1 rounded-lg border border-dashed border-border/50 py-1.5 text-[11px] text-muted-foreground transition-colors hover:border-primary/30 hover:text-primary"
        >
          <Plus className="h-3 w-3" />
          Add Agent
        </button>

        {showAgentPicker && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setShowAgentPicker(false)} onKeyDown={(e) => { if (e.key === 'Escape') setShowAgentPicker(false); }} role="button" tabIndex={-1} aria-label="Close agent picker" />
            <div className="absolute left-0 top-full z-50 mt-1 w-full rounded-lg border border-border/80 bg-card/95 shadow-lg backdrop-blur-sm">
              <div className="max-h-40 overflow-y-auto p-1">
                {availableAgents.length === 0 && (
                  <div className="py-2 text-center text-xs text-muted-foreground">
                    No agents available
                  </div>
                )}
                {availableAgents.map((agent) => (
                  <button
                    key={agent.slug}
                    type="button"
                    onClick={() => {
                      onAddAgent(agent.slug);
                      setShowAgentPicker(false);
                    }}
                    className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs transition-colors hover:bg-accent/50"
                  >
                    <span className="font-medium">{agent.display_name}</span>
                    <span className="text-[10px] text-muted-foreground">({agent.slug})</span>
                  </button>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
