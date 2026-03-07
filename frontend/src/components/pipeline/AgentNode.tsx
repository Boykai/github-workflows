/**
 * AgentNode — represents an agent assigned to a pipeline stage.
 * Shows agent name, model selection, and remove button.
 */

import { X } from 'lucide-react';
import { ModelSelector } from './ModelSelector';
import type { PipelineAgentNode } from '@/types';

interface AgentNodeProps {
  agentNode: PipelineAgentNode;
  onModelSelect: (modelId: string, modelName: string) => void;
  onRemove: () => void;
}

export function AgentNode({ agentNode, onModelSelect, onRemove }: AgentNodeProps) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-border/50 bg-background/40 px-2.5 py-2 transition-colors hover:bg-accent/30">
      {/* Agent info */}
      <div className="flex-1 min-w-0">
        <div className="text-xs font-medium text-foreground truncate">
          {agentNode.agent_display_name || agentNode.agent_slug}
        </div>
        <div className="mt-1">
          <ModelSelector selectedModelId={agentNode.model_id || null} onSelect={onModelSelect} />
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
