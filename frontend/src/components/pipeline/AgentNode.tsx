/**
 * AgentNode — represents an agent assigned to a pipeline stage.
 * Shows agent name, model selection, tool count badge, and remove button.
 */

import { X, Wrench, Copy } from 'lucide-react';
import { ModelSelector } from './ModelSelector';
import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';
import type { PipelineAgentNode } from '@/types';

interface AgentNodeProps {
  agentNode: PipelineAgentNode;
  onModelSelect: (modelId: string, modelName: string) => void;
  onRemove: () => void;
  onToolsClick?: () => void;
  onClone?: () => void;
}

export function AgentNode({ agentNode, onModelSelect, onRemove, onToolsClick, onClone }: AgentNodeProps) {
  const toolCount = agentNode.tool_count ?? agentNode.tool_ids?.length ?? 0;
  const displayName = agentNode.agent_display_name || agentNode.agent_slug;

  return (
    <div className="flex items-center gap-2 rounded-lg border border-border/50 bg-background/48 px-2.5 py-2 transition-colors hover:bg-primary/10">
      <ThemedAgentIcon slug={agentNode.agent_slug} name={displayName} size="md" />

      {/* Agent info */}
      <div className="flex-1 min-w-0">
        <div className="text-xs font-medium text-foreground truncate">
          {displayName}
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <div className="flex min-w-[10rem] flex-1 items-center gap-1.5">
            <span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
              Model
            </span>
            <ModelSelector
              selectedModelId={agentNode.model_id || null}
              selectedModelName={agentNode.model_name || null}
              onSelect={onModelSelect}
              allowAuto={true}
              autoLabel="Agent default"
              triggerClassName="min-w-0 flex-1 justify-between"
            />
          </div>
          <button
            type="button"
            onClick={onToolsClick}
            className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] transition-colors hover:bg-primary/10"
            title="Select tools"
          >
            <Wrench className="h-3 w-3 text-muted-foreground" />
            {toolCount > 0 ? (
              <span className="font-medium text-primary">{toolCount} tool{toolCount !== 1 ? 's' : ''}</span>
            ) : (
              <span className="text-muted-foreground">+ Tools</span>
            )}
          </button>
        </div>
      </div>

      {/* Clone button */}
      {onClone && (
        <button
          type="button"
          onClick={onClone}
          className="shrink-0 rounded-md p-1 text-muted-foreground/60 transition-colors hover:bg-primary/10 hover:text-primary"
          title="Clone agent"
        >
          <Copy className="h-3.5 w-3.5" />
        </button>
      )}

      {/* Remove button */}
      <button
        type="button"
        onClick={onRemove}
        className="shrink-0 rounded-md p-1 text-muted-foreground/60 transition-colors hover:bg-destructive/10 hover:text-destructive"
        title="Remove agent"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
