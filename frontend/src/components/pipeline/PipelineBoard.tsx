/**
 * PipelineBoard — main board canvas rendering pipeline stages.
 * Stages are fixed in position (no drag-and-drop).
 * Includes pipeline-level model dropdown and inline validation.
 */

import { useState, useRef, useEffect, useCallback, type CSSProperties } from 'react';
import { Layers, Lock } from 'lucide-react';
import { StageCard } from './StageCard';
import { PipelineModelDropdown } from './PipelineModelDropdown';
import type { PipelineStage, PipelineAgentNode, AvailableAgent, AIModel, PipelineModelOverride, PipelineValidationErrors } from '@/types';

interface PipelineBoardProps {
  columnCount: number;
  stages: PipelineStage[];
  availableAgents: AvailableAgent[];
  agentsLoading?: boolean;
  agentsError?: string | null;
  onRetryAgents?: () => void;
  availableModels: AIModel[];
  isEditMode: boolean;
  pipelineName: string;
  projectId: string;
  modelOverride: PipelineModelOverride;
  validationErrors: PipelineValidationErrors;
  onNameChange: (name: string) => void;
  onModelOverrideChange: (override: PipelineModelOverride) => void;
  onClearValidationError: (field: string) => void;
  onRemoveStage: (stageId: string) => void;
  onAddAgent: (stageId: string, agentSlug: string) => void;
  onRemoveAgent: (stageId: string, agentNodeId: string) => void;
  onUpdateAgent: (stageId: string, agentNodeId: string, updates: Partial<PipelineAgentNode>) => void;
  onUpdateStage: (stageId: string, updates: Partial<PipelineStage>) => void;
  onCloneAgent?: (stageId: string, agentNodeId: string) => void;
  pipelineBlocking: boolean;
  onBlockingChange: (blocking: boolean) => void;
}

export function PipelineBoard({
  columnCount,
  stages,
  availableAgents,
  agentsLoading = false,
  agentsError = null,
  onRetryAgents,
  availableModels,
  isEditMode,
  pipelineName,
  projectId,
  modelOverride,
  validationErrors,
  onNameChange,
  onModelOverrideChange,
  onClearValidationError,
  onRemoveStage,
  onAddAgent,
  onRemoveAgent,
  onUpdateAgent,
  onUpdateStage,
  onCloneAgent,
  pipelineBlocking,
  onBlockingChange,
}: PipelineBoardProps) {
  const [isEditingName, setIsEditingName] = useState(false);
  const [editNameValue, setEditNameValue] = useState(pipelineName);
  const nameInputRef = useRef<HTMLInputElement>(null);
  const showInlineNameInput = isEditMode || isEditingName;

  const gridStyle: CSSProperties = {
    gridTemplateColumns: `repeat(${Math.max(columnCount, 1)}, minmax(14rem, 1fr))`,
  };

  useEffect(() => {
    setEditNameValue(pipelineName);
  }, [pipelineName]);

  useEffect(() => {
    if (showInlineNameInput && nameInputRef.current) {
      nameInputRef.current.focus();
      nameInputRef.current.select();
    }
  }, [showInlineNameInput]);

  const handleNameConfirm = useCallback(() => {
    const trimmed = editNameValue.trim();
    if (trimmed) {
      onNameChange(trimmed);
      onClearValidationError('name');
    } else {
      setEditNameValue(pipelineName);
    }
    setIsEditingName(false);
  }, [editNameValue, pipelineName, onNameChange, onClearValidationError]);

  // Empty state
  if (stages.length === 0) {
    return (
      <div className="flex flex-col gap-4">
        {/* Edit mode banner */}
        {isEditMode && (
          <div className="rounded-[1rem] border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
            ✏️ Editing: {pipelineName || 'Untitled Pipeline'}
          </div>
        )}

        {/* Pipeline name with validation */}
        <div>
          {showInlineNameInput ? (
            <input
              ref={nameInputRef}
              type="text"
              aria-label="Pipeline name"
              value={editNameValue}
              onChange={(e) => { setEditNameValue(e.target.value); onClearValidationError('name'); }}
              onBlur={() => {
                handleNameConfirm();
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleNameConfirm();
                if (e.key === 'Escape') { setEditNameValue(pipelineName); setIsEditingName(false); }
              }}
              className={`rounded-lg border bg-background/70 px-3 py-1.5 text-lg font-semibold outline-none ${
                validationErrors.name ? 'border-red-500' : 'border-primary/30'
              }`}
              placeholder="Pipeline name"
              maxLength={100}
            />
          ) : (
            <button
              type="button"
              onClick={() => { setEditNameValue(pipelineName); setIsEditingName(true); }}
              className={`text-lg font-semibold transition-colors ${
                validationErrors.name ? 'text-red-500' : 'text-foreground hover:text-primary'
              }`}
              title="Click to rename"
            >
              {pipelineName || 'Untitled Pipeline'}
            </button>
          )}
          {validationErrors.name && (
            <p className="mt-1 text-xs text-red-500">{validationErrors.name}</p>
          )}
        </div>

        {/* Pipeline-level model dropdown */}
        <PipelineModelDropdown
          models={availableModels}
          currentOverride={modelOverride}
          onModelChange={onModelOverrideChange}
        />

        {/* Blocking toggle */}
        <div className="flex items-center gap-2 self-start">
          <button
            type="button"
            role="switch"
            aria-checked={pipelineBlocking}
            aria-label="Blocking"
            onClick={() => onBlockingChange(!pipelineBlocking)}
            className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 ${
              pipelineBlocking ? 'bg-amber-500' : 'bg-muted'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition-transform ${
                pipelineBlocking ? 'translate-x-4' : 'translate-x-0'
              }`}
            />
          </button>
          <span className="flex items-center gap-1 text-xs font-medium text-muted-foreground">
            <Lock className="h-3 w-3" />
            Blocking
          </span>
        </div>

        {/* Empty board CTA */}
        <div className="celestial-panel flex flex-col items-center justify-center gap-3 rounded-[1.2rem] border border-dashed border-border/60 bg-background/24 p-8 text-center">
          <Layers className="h-8 w-8 text-muted-foreground/40" />
          <h3 className="text-sm font-semibold text-foreground">No stages yet</h3>
          <p className="text-xs text-muted-foreground">
            Stages are derived from your project board columns. Configure your board to populate pipeline stages.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Edit mode banner */}
      {isEditMode && (
        <div className="rounded-[1rem] border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
          ✏️ Editing: {pipelineName || 'Untitled Pipeline'}
        </div>
      )}

      {/* Pipeline name with validation */}
      <div>
        {showInlineNameInput ? (
          <input
            ref={nameInputRef}
            type="text"
            aria-label="Pipeline name"
            value={editNameValue}
            onChange={(e) => { setEditNameValue(e.target.value); onClearValidationError('name'); }}
            onBlur={() => {
              handleNameConfirm();
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleNameConfirm();
              if (e.key === 'Escape') { setEditNameValue(pipelineName); setIsEditingName(false); }
            }}
            className={`rounded-lg border bg-background/70 px-3 py-1.5 text-lg font-semibold outline-none ${
              validationErrors.name ? 'border-red-500' : 'border-primary/30'
            }`}
            placeholder="Pipeline name"
            maxLength={100}
          />
        ) : (
          <button
            type="button"
            onClick={() => { setEditNameValue(pipelineName); setIsEditingName(true); }}
            className={`text-lg font-semibold transition-colors ${
              validationErrors.name ? 'text-red-500' : 'text-foreground hover:text-primary'
            }`}
            title="Click to rename"
          >
            {pipelineName || 'Untitled Pipeline'}
          </button>
        )}
        {validationErrors.name && (
          <p className="mt-1 text-xs text-red-500">{validationErrors.name}</p>
        )}
      </div>

      {/* Pipeline-level model dropdown */}
      <PipelineModelDropdown
        models={availableModels}
        currentOverride={modelOverride}
        onModelChange={onModelOverrideChange}
      />

      {/* Blocking toggle */}
      <div className="flex items-center gap-2 self-start">
        <button
          type="button"
          role="switch"
          aria-checked={pipelineBlocking}
          aria-label="Blocking"
          onClick={() => onBlockingChange(!pipelineBlocking)}
          className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 ${
            pipelineBlocking ? 'bg-amber-500' : 'bg-muted'
          }`}
        >
          <span
            className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition-transform ${
              pipelineBlocking ? 'translate-x-4' : 'translate-x-0'
            }`}
          />
        </button>
        <span className="flex items-center gap-1 text-xs font-medium text-muted-foreground">
          <Lock className="h-3 w-3" />
          Blocking
        </span>
      </div>

      {/* Stage cards */}
      <div className="overflow-x-auto pb-2">
        <div className="grid min-w-full items-start gap-3" style={gridStyle}>
          {stages.map((stage) => (
            <StageCard
              key={stage.id}
              stage={stage}
              availableAgents={availableAgents}
              agentsLoading={agentsLoading}
              agentsError={agentsError}
              onRetryAgents={onRetryAgents}
              projectId={projectId}
              onUpdate={(updated) => onUpdateStage(stage.id, updated)}
              onRemove={() => onRemoveStage(stage.id)}
              onAddAgent={(slug) => onAddAgent(stage.id, slug)}
              onRemoveAgent={(nodeId) => onRemoveAgent(stage.id, nodeId)}
              onUpdateAgent={(nodeId, updates) => onUpdateAgent(stage.id, nodeId, updates)}
              onCloneAgent={onCloneAgent ? (nodeId) => onCloneAgent(stage.id, nodeId) : undefined}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
