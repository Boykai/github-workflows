/**
 * AgentTile component - card-style tile for a single agent assignment.
 * Displays formatted agent name, model/tool metadata, avatar/icon, and remove button.
 * Supports drag-and-drop via @dnd-kit (T023) and expand/collapse (T029).
 */

import { useState } from 'react';
import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';
import type { AgentAssignment, AvailableAgent } from '@/types';
import { formatAgentName } from '@/utils/formatAgentName';

interface AgentTileProps {
  agent: AgentAssignment;
  onRemove?: (agentInstanceId: string) => void;
  /** Sorted item props from useSortable (injected by AgentColumnCell) */
  sortableProps?: {
    attributes: Record<string, unknown>;
    listeners: Record<string, unknown>;
    setNodeRef: (node: HTMLElement | null) => void;
    style: React.CSSProperties;
    isDragging: boolean;
  };
  /** Available agents list for metadata lookup */
  availableAgents?: AvailableAgent[];
  /** Whether this agent is missing from available agents */
  isWarning?: boolean;
}

export function AgentTile({ agent, onRemove, sortableProps, availableAgents, isWarning }: AgentTileProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const displayName = formatAgentName(agent.slug, agent.display_name);
  const metadata = availableAgents?.find((a) => a.slug === agent.slug);

  // Build metadata line: model · N tools
  const metaParts: string[] = [];
  if (metadata?.default_model_name) metaParts.push(metadata.default_model_name);
  if (metadata && metadata.tools_count != null) metaParts.push(`${metadata.tools_count} tool${metadata.tools_count !== 1 ? 's' : ''}`);
  const metaLine = metaParts.join(' · ');

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    onRemove?.(agent.id);
  };

  const tileStyle: React.CSSProperties = {
    ...(sortableProps?.style ?? {}),
    opacity: sortableProps?.isDragging ? 0.3 : 1,
  };

  return (
    <div
      ref={sortableProps?.setNodeRef}
      className={`flex flex-col rounded-md border bg-card shadow-sm transition-all ${isWarning ? 'border-amber-400/45 bg-amber-500/8' : 'border-border'} ${sortableProps?.isDragging ? 'border-dashed opacity-30 shadow-none' : ''}`}
      style={tileStyle}
      {...(sortableProps?.attributes ?? {})}
      aria-roledescription="sortable agent"
    >
      <div className="flex items-center gap-2 p-2">
        {/* Drag handle */}
        {sortableProps && (
          <span className="cursor-grab text-muted-foreground/50 hover:text-muted-foreground px-1" {...(sortableProps.listeners ?? {})}>
            ⠿
          </span>
        )}

        {/* Avatar */}
        <ThemedAgentIcon slug={agent.slug} name={displayName} avatarUrl={metadata?.avatar_url} iconName={metadata?.icon_name} size="sm" title={agent.slug} />

        {/* Name and metadata */}
        <div className="flex-1 min-w-0">
          <span className="block text-sm font-medium truncate" title={agent.slug}>
            {displayName}
          </span>
          {metaLine && (
            <span className="block text-[10px] text-muted-foreground truncate">{metaLine}</span>
          )}
        </div>

        {/* Warning badge (T032) */}
        {isWarning && (
          <span className="rounded-md border border-amber-400/45 bg-amber-500/12 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-amber-700 dark:text-amber-300" title="Agent not found in available agents">
            ⚠
          </span>
        )}

        {/* Expand toggle (T029) */}
        <button
          className="solar-action flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground transition-colors hover:text-foreground"
          onClick={() => setIsExpanded(!isExpanded)}
          title={isExpanded ? 'Collapse' : 'Expand'}
          type="button"
        >
          {isExpanded ? '▾' : '▸'}
        </button>

        {/* Remove button */}
        {onRemove && (
          <button
            className="w-6 h-6 flex items-center justify-center rounded-md text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
            onClick={handleRemove}
            title="Remove agent"
            type="button"
          >
            ✕
          </button>
        )}
      </div>

      {/* Expanded detail (T029) */}
      {isExpanded && (
        <div className="mt-1 flex flex-col gap-1.5 rounded-b-md border-t border-border/50 bg-background/46 p-3 pt-0 text-xs">
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-muted-foreground font-medium min-w-[70px]">Slug:</span>
            <code className="solar-chip-soft rounded border px-1.5 py-0.5 text-[10px] font-mono break-all">{agent.slug}</code>
          </div>
          {metadata?.source && (
            <div className="flex items-baseline gap-2">
              <span className="text-muted-foreground font-medium min-w-[70px]">Source:</span>
              <span className="text-foreground">{metadata.source}</span>
            </div>
          )}
          <div className="flex items-baseline gap-2">
            <span className="text-muted-foreground font-medium min-w-[70px]">Description:</span>
            <span className="text-foreground leading-relaxed">
              {metadata?.description || 'No description available'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
