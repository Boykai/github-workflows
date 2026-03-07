/**
 * AgentNode — represents an agent assigned to a pipeline stage.
 * Shows agent name, model selection, tool count badge, and remove button.
 */

import { X, Wrench } from 'lucide-react';
import { ModelSelector } from './ModelSelector';
import type { PipelineAgentNode } from '@/types';

interface AgentNodeProps {
  agentNode: PipelineAgentNode;
  onModelSelect: (modelId: string, modelName: string) => void;
  onRemove: () => void;
  onToolsClick?: () => void;
}

export function AgentNode({ agentNode, onModelSelect, onRemove, onToolsClick }: AgentNodeProps) {
  const toolCount = agentNode.tool_count ?? agentNode.tool_ids?.length ?? 0;

  return (
    <div className="flex items-center gap-2 rounded-lg border border-border/50 bg-background/40 px-2.5 py-2 transition-colors hover:bg-accent/30">
      {/* Agent info */}
      <div className="flex-1 min-w-0">
        <div className="text-xs font-medium text-foreground truncate">
          {agentNode.agent_display_name || agentNode.agent_slug}
        </div>
        <div className="mt-1 flex items-center gap-2">
          <ModelSelector
            selectedModelId={agentNode.model_id || null}
            onSelect={onModelSelect}
          />
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
