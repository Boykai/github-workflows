/**
 * AgentTile component - card-style tile for a single agent assignment.
 * Displays agent avatar/icon, display_name or slug, and remove button.
 * Supports drag-and-drop via @dnd-kit (T023) and expand/collapse (T029).
 */

import { useState } from 'react';
import type { AgentAssignment, AvailableAgent } from '@/types';

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

  const displayName = agent.display_name || agent.slug;
  const metadata = availableAgents?.find((a) => a.slug === agent.slug);
  const avatarLetter = displayName.charAt(0).toUpperCase();

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    onRemove?.(agent.id);
  };

  const tileStyle: React.CSSProperties = {
    ...(sortableProps?.style ?? {}),
    opacity: sortableProps?.isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={sortableProps?.setNodeRef}
      className={`flex flex-col bg-card border rounded-md shadow-sm transition-all ${isWarning ? 'border-amber-500/50 bg-amber-500/5' : 'border-border'} ${sortableProps?.isDragging ? 'shadow-md z-10 scale-[1.02]' : ''}`}
      style={tileStyle}
      {...(sortableProps?.attributes ?? {})}
    >
      <div className="flex items-center gap-2 p-2">
        {/* Drag handle */}
        {sortableProps && (
          <span className="cursor-grab text-muted-foreground/50 hover:text-muted-foreground px-1" {...(sortableProps.listeners ?? {})}>
            ⠿
          </span>
        )}

        {/* Avatar */}
        <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-medium shrink-0 overflow-hidden" title={agent.slug}>
          {metadata?.avatar_url ? (
            <img src={metadata.avatar_url} alt={displayName} className="w-full h-full object-cover" />
          ) : (
            avatarLetter
          )}
        </span>

        {/* Name */}
        <span className="flex-1 text-sm font-medium truncate" title={agent.slug}>
          {displayName}
        </span>

        {/* Warning badge (T032) */}
        {isWarning && (
          <span className="text-amber-500 text-xs font-bold px-1" title="Agent not found in available agents">
            ⚠
          </span>
        )}

        {/* Expand toggle (T029) */}
        <button
          className="w-6 h-6 flex items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
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
        <div className="flex flex-col gap-1.5 p-3 pt-0 text-xs border-t border-border/50 mt-1 bg-muted/30 rounded-b-md">
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-muted-foreground font-medium min-w-[70px]">Slug:</span>
            <code className="px-1.5 py-0.5 bg-background rounded border border-border text-[10px] font-mono break-all">{agent.slug}</code>
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
