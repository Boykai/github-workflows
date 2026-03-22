/**
 * StageCard — a named step within the pipeline board.
 * Contains execution groups, each with their own agent nodes.
 * Supports inline renaming, tool selection, and add-group.
 */

import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Lock, Plus, Trash2, Layers } from '@/lib/icons';
import { ExecutionGroupCard } from './ExecutionGroupCard';
import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';
import { ToolSelectorModal } from '@/components/tools/ToolSelectorModal';
import { Tooltip } from '@/components/ui/tooltip';
import type { PipelineStage, PipelineAgentNode, AvailableAgent, ExecutionGroup } from '@/types';
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
  onAddAgent: (agentSlug: string, groupId?: string) => void;
  onRemoveAgent: (agentNodeId: string) => void;
  onUpdateAgent: (agentNodeId: string, updates: Partial<PipelineAgentNode>) => void;
  onCloneAgent?: (agentNodeId: string) => void;
  onReorderAgents: (newOrder: PipelineAgentNode[]) => void;
  onAddGroup?: () => void;
  onRemoveGroup?: (groupId: string) => void;
  onToggleGroupMode?: (groupId: string, mode: 'sequential' | 'parallel') => void;
  onReorderAgentsInGroup?: (groupId: string, newOrder: PipelineAgentNode[]) => void;
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
  onAddGroup,
  onRemoveGroup,
  onToggleGroupMode,
  onReorderAgentsInGroup,
}: StageCardProps) {
  const groups: ExecutionGroup[] = stage.groups ?? [];
  const totalAgents = groups.reduce((acc, g) => acc + g.agents.length, 0);
  const hasAgents = totalAgents > 0;
  const hasMultipleGroups = groups.length > 1;

  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(stage.name);
  const [showAgentPicker, setShowAgentPicker] = useState(false);
  const [agentPickerGroupId, setAgentPickerGroupId] = useState<string | null>(null);
  const [pickerPosition, setPickerPosition] = useState<{
    top: number;
    left: number;
    width: number;
  } | null>(null);
  const [toolModalAgent, setToolModalAgent] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const addButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const [prevShowAgentPicker, setPrevShowAgentPicker] = useState(showAgentPicker);
  if (showAgentPicker !== prevShowAgentPicker) {
    setPrevShowAgentPicker(showAgentPicker);
    if (!showAgentPicker) setPickerPosition(null);
  }

  useEffect(() => {
    if (!showAgentPicker) return;

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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleRenameConfirm();
    if (e.key === 'Escape') {
      setEditName(stage.name);
      setIsEditing(false);
    }
  };

  // Find selected tool ids across all groups for the tool modal
  const findAgentToolIds = (agentId: string): string[] => {
    for (const g of groups) {
      const agent = g.agents.find((a) => a.id === agentId);
      if (agent) return agent.tool_ids ?? [];
    }
    return [];
  };

  const openAgentPicker = (groupId?: string) => {
    setAgentPickerGroupId(groupId ?? groups[0]?.id ?? null);
    setShowAgentPicker(true);
  };

  return (
    <div className="celestial-panel celestial-fade-in pipeline-column-surface pipeline-stage-card flex h-full min-w-0 flex-col gap-2 rounded-xl border border-border/70 p-3 shadow-sm backdrop-blur-sm dark:border-border/90 dark:bg-[linear-gradient(180deg,hsl(var(--night)/0.97)_0%,hsl(var(--panel)/0.93)_100%)] dark:shadow-[0_24px_48px_hsl(var(--night)/0.52)]">
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
              className="celestial-focus w-full rounded-md border border-primary/30 bg-background/72 px-2 py-0.5 text-sm font-medium focus-visible:outline-none dark:border-primary/45 dark:bg-background/88"
              maxLength={100}
            />
          ) : (
            <Tooltip contentKey="pipeline.stage.rename" side="bottom">
              <button
                type="button"
                onClick={() => {
                  setEditName(stage.name);
                  setIsEditing(true);
                }}
                className="celestial-focus w-full truncate text-left text-sm font-medium text-foreground transition-colors hover:text-primary focus-visible:outline-none"
              >
                {stage.name}
              </button>
            </Tooltip>
          )}

          <div className="mt-1 flex flex-wrap items-center gap-1.5">
            <span className="text-[10px] text-muted-foreground">
              {hasAgents
                ? `${totalAgents} agent${totalAgents === 1 ? '' : 's'} · ${groups.length} group${groups.length === 1 ? '' : 's'}`
                : 'Add an agent to begin this stage'}
            </span>
          </div>
        </div>

        <Tooltip contentKey="pipeline.stage.deleteButton">
          <button
            type="button"
            onClick={onRemove}
            aria-label="Remove stage"
            className="celestial-focus shrink-0 rounded-md p-1 text-muted-foreground/50 transition-colors hover:bg-destructive/10 hover:text-destructive focus-visible:outline-none"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </Tooltip>
      </div>

      {/* Execution Groups */}
      <div className="flex flex-col gap-2">
        {groups.map((group) => (
          <ExecutionGroupCard
            key={group.id}
            group={group}
            stageId={stage.id}
            canDelete={hasMultipleGroups}
            onRemoveGroup={() => onRemoveGroup?.(group.id)}
            onToggleMode={(mode) => onToggleGroupMode?.(group.id, mode)}
            onRemoveAgent={onRemoveAgent}
            onUpdateAgent={onUpdateAgent}
            onCloneAgent={onCloneAgent}
            onReorderAgents={(newOrder) =>
              onReorderAgentsInGroup
                ? onReorderAgentsInGroup(group.id, newOrder)
                : onReorderAgents(newOrder)
            }
            onToolsClick={(agentId) => setToolModalAgent(agentId)}
            onAddAgent={hasMultipleGroups ? () => openAgentPicker(group.id) : undefined}
          />
        ))}
      </div>

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
          initialSelectedIds={findAgentToolIds(toolModalAgent)}
          projectId={projectId}
        />
      )}

      {/* Add agent button */}
      <div className="relative">
        <Tooltip contentKey="pipeline.stage.addAgentButton">
          <button
            ref={addButtonRef}
            type="button"
            onClick={() => openAgentPicker()}
            className="pipeline-stage-add flex w-full items-center justify-center gap-1 rounded-lg border border-dashed border-border/50 py-1.5 text-[11px] text-muted-foreground transition-colors hover:border-primary/30 hover:text-primary dark:border-border/75 dark:text-muted-foreground/85"
          >
            <Plus className="h-3 w-3" />
            Add Agent
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
                          className="celestial-focus rounded-md border border-destructive/20 bg-background px-2 py-1 text-[11px] hover:bg-destructive/10 focus-visible:outline-none"
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
                            onAddAgent(agent.slug, agentPickerGroupId ?? undefined);
                            setShowAgentPicker(false);
                          }}
                          className="celestial-focus flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs transition-colors hover:bg-primary/10 focus-visible:outline-none"
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

      {/* Add group button */}
      {onAddGroup && (
        <Tooltip contentKey="pipeline.stage.addGroupButton">
          <button
            type="button"
            onClick={onAddGroup}
            className="flex w-full items-center justify-center gap-1 rounded-lg border border-dashed border-border/50 py-1 text-[10px] text-muted-foreground transition-colors hover:border-primary/30 hover:text-primary"
          >
            <Layers className="h-3 w-3" />
            Add Execution Group
          </button>
        </Tooltip>
      )}
    </div>
  );
}
