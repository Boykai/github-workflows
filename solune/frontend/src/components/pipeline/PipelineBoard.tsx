/**
 * PipelineBoard — main board canvas rendering pipeline stages.
 * Stages are fixed in position (no drag-and-drop).
 * Includes pipeline-level model dropdown and inline validation.
 */

import { useState, useRef, useEffect, useCallback, type CSSProperties } from 'react';
import { GitBranch, Layers, PencilLine } from '@/lib/icons';
import { StageCard } from './StageCard';
import { PipelineModelDropdown } from './PipelineModelDropdown';
import { cn } from '@/lib/utils';
import type {
  PipelineStage,
  PipelineAgentNode,
  AvailableAgent,
  AIModel,
  PipelineModelOverride,
  PipelineValidationErrors,
} from '@/types';

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
  onAddAgent: (stageId: string, agentSlug: string, groupId?: string) => void;
  onRemoveAgent: (stageId: string, agentNodeId: string) => void;
  onUpdateAgent: (
    stageId: string,
    agentNodeId: string,
    updates: Partial<PipelineAgentNode>
  ) => void;
  onUpdateStage: (stageId: string, updates: Partial<PipelineStage>) => void;
  onCloneAgent?: (stageId: string, agentNodeId: string) => void;
  onReorderAgents: (stageId: string, newOrder: PipelineAgentNode[]) => void;
  onAddGroup?: (stageId: string) => void;
  onRemoveGroup?: (stageId: string, groupId: string) => void;
  onToggleGroupMode?: (stageId: string, groupId: string, mode: 'sequential' | 'parallel') => void;
  onReorderAgentsInGroup?: (stageId: string, groupId: string, newOrder: PipelineAgentNode[]) => void;
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
  onReorderAgents,
  onAddGroup,
  onRemoveGroup,
  onToggleGroupMode,
  onReorderAgentsInGroup,
}: PipelineBoardProps) {
  const [isEditingName, setIsEditingName] = useState(false);
  const [editNameValue, setEditNameValue] = useState(pipelineName);
  const nameInputRef = useRef<HTMLInputElement>(null);
  const showInlineNameInput = isEditMode || isEditingName;
  const hasParallelGroup = stages.some(
    (stage) => (stage.groups ?? []).some((g) => g.execution_mode === 'parallel' && g.agents.length > 1)
  );
  const minStageWidthRem = hasParallelGroup ? 20 : 14;

  const gridStyle: CSSProperties = {
    gridTemplateColumns: `repeat(${Math.max(columnCount, 1)}, minmax(${minStageWidthRem}rem, 1fr))`,
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
      <div className="celestial-fade-in flex flex-col gap-4">
        {/* Edit mode banner */}
        {isEditMode && (
          <div className="flex items-center gap-2 rounded-[1rem] border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
            <PencilLine className="h-4 w-4" />
            Editing: {pipelineName || 'Untitled Pipeline'}
          </div>
        )}

        {/* Pipeline name with validation */}
        <div>
          {showInlineNameInput ? (
            <input
              ref={nameInputRef}
              type="text"
              aria-label="Pipeline name"
              aria-invalid={validationErrors.name ? "true" : undefined}
              aria-describedby={validationErrors.name ? "pipeline-name-error" : undefined}
              value={editNameValue}
              onChange={(e) => {
                setEditNameValue(e.target.value);
                onClearValidationError('name');
              }}
              onBlur={() => {
                handleNameConfirm();
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleNameConfirm();
                if (e.key === 'Escape') {
                  setEditNameValue(pipelineName);
                  setIsEditingName(false);
                }
              }}
              className={cn('rounded-lg border bg-background/70 px-3 py-1.5 text-lg font-semibold outline-none dark:bg-background/80', validationErrors.name ? 'border-red-500' : 'border-primary/30 dark:border-primary/45')}
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
              className={cn('text-lg font-semibold transition-colors', validationErrors.name ? 'text-red-500' : 'text-foreground hover:text-primary')}
              title="Click to rename"
            >
              {pipelineName || 'Untitled Pipeline'}
            </button>
          )}
          {validationErrors.name && (
            <p id="pipeline-name-error" className="mt-1 text-xs text-red-500">{validationErrors.name}</p>
          )}
        </div>

        {/* Pipeline-level model dropdown */}
        <PipelineModelDropdown
          models={availableModels}
          currentOverride={modelOverride}
          onModelChange={onModelOverrideChange}
        />

        {/* Empty board CTA */}
        <div className="celestial-panel flex flex-col items-center justify-center gap-3 rounded-[1.2rem] border border-dashed border-border/60 bg-background/24 p-8 text-center dark:border-border/75 dark:bg-background/40">
          <Layers className="h-8 w-8 text-muted-foreground/40" />
          <h3 className="text-sm font-semibold text-foreground">No stages yet</h3>
          <p className="text-xs text-muted-foreground">
            Stages are derived from your project board columns. Configure your board to populate
            pipeline stages.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="celestial-fade-in flex flex-col gap-4">
      {/* Edit mode banner */}
      {isEditMode && (
        <div className="flex items-center gap-2 rounded-[1rem] border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
          <PencilLine className="h-4 w-4" />
          Editing: {pipelineName || 'Untitled Pipeline'}
        </div>
      )}

      {/* Pipeline name with validation */}
      <div>
        {showInlineNameInput ? (
          <input
            ref={nameInputRef}
            type="text"
            aria-label="Pipeline name"
            aria-invalid={validationErrors.name ? "true" : undefined}
            aria-describedby={validationErrors.name ? "pipeline-name-error" : undefined}
            value={editNameValue}
            onChange={(e) => {
              setEditNameValue(e.target.value);
              onClearValidationError('name');
            }}
            onBlur={() => {
              handleNameConfirm();
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleNameConfirm();
              if (e.key === 'Escape') {
                setEditNameValue(pipelineName);
                setIsEditingName(false);
              }
            }}
            className={cn('rounded-lg border bg-background/70 px-3 py-1.5 text-lg font-semibold outline-none dark:bg-background/80', validationErrors.name ? 'border-red-500' : 'border-primary/30 dark:border-primary/45')}
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
            className={cn('text-lg font-semibold transition-colors', validationErrors.name ? 'text-red-500' : 'text-foreground hover:text-primary')}
            title="Click to rename"
          >
            {pipelineName || 'Untitled Pipeline'}
          </button>
        )}
        {validationErrors.name && (
          <p id="pipeline-name-error" className="mt-1 text-xs text-red-500">{validationErrors.name}</p>
        )}
      </div>

      {/* Pipeline-level model dropdown */}
      <PipelineModelDropdown
        models={availableModels}
        currentOverride={modelOverride}
        onModelChange={onModelOverrideChange}
      />

      {hasParallelGroup && (
        <div className="flex flex-wrap items-center gap-2 rounded-[1rem] border border-primary/20 bg-primary/8 px-3 py-2 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1.5 font-semibold text-primary">
            <GitBranch className="h-3.5 w-3.5" />
            Parallel groups
          </span>
          <span>
            Agents in a parallel group run concurrently. Each stage completes when all its groups finish.
          </span>
        </div>
      )}

      {/* Stage cards */}
      <div className="overflow-x-auto pb-2">
        <div data-testid="pipeline-stage-grid" className="grid min-w-full items-start gap-3" style={gridStyle}>
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
              onAddAgent={(slug, groupId) => onAddAgent(stage.id, slug, groupId)}
              onRemoveAgent={(nodeId) => onRemoveAgent(stage.id, nodeId)}
              onUpdateAgent={(nodeId, updates) => onUpdateAgent(stage.id, nodeId, updates)}
              onCloneAgent={onCloneAgent ? (nodeId) => onCloneAgent(stage.id, nodeId) : undefined}
              onReorderAgents={(newOrder) => onReorderAgents(stage.id, newOrder)}
              onAddGroup={onAddGroup ? () => onAddGroup(stage.id) : undefined}
              onRemoveGroup={onRemoveGroup ? (groupId) => onRemoveGroup(stage.id, groupId) : undefined}
              onToggleGroupMode={onToggleGroupMode ? (groupId, mode) => onToggleGroupMode(stage.id, groupId, mode) : undefined}
              onReorderAgentsInGroup={onReorderAgentsInGroup ? (groupId, newOrder) => onReorderAgentsInGroup(stage.id, groupId, newOrder) : undefined}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
