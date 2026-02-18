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
      className={`agent-tile${isWarning ? ' agent-tile--warning' : ''}${sortableProps?.isDragging ? ' agent-tile--dragging' : ''}`}
      style={tileStyle}
      {...(sortableProps?.attributes ?? {})}
    >
      <div className="agent-tile-main">
        {/* Drag handle */}
        {sortableProps && (
          <span className="agent-tile-drag-handle" {...(sortableProps.listeners ?? {})}>
            ⠿
          </span>
        )}

        {/* Avatar */}
        <span className="agent-tile-avatar" title={agent.slug}>
          {metadata?.avatar_url ? (
            <img src={metadata.avatar_url} alt={displayName} className="agent-tile-avatar-img" />
          ) : (
            avatarLetter
          )}
        </span>

        {/* Name */}
        <span className="agent-tile-name" title={agent.slug}>
          {displayName}
        </span>

        {/* Warning badge (T032) */}
        {isWarning && (
          <span className="agent-tile-warning-badge" title="Agent not found in available agents">
            ⚠
          </span>
        )}

        {/* Expand toggle (T029) */}
        <button
          className="agent-tile-expand-btn"
          onClick={() => setIsExpanded(!isExpanded)}
          title={isExpanded ? 'Collapse' : 'Expand'}
          type="button"
        >
          {isExpanded ? '▾' : '▸'}
        </button>

        {/* Remove button */}
        {onRemove && (
          <button
            className="agent-tile-remove-btn"
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
        <div className="agent-tile-details">
          <div className="agent-tile-detail-row">
            <span className="agent-tile-detail-label">Slug:</span>
            <code className="agent-tile-detail-value">{agent.slug}</code>
          </div>
          {metadata?.source && (
            <div className="agent-tile-detail-row">
              <span className="agent-tile-detail-label">Source:</span>
              <span className="agent-tile-detail-value">{metadata.source}</span>
            </div>
          )}
          <div className="agent-tile-detail-row">
            <span className="agent-tile-detail-label">Description:</span>
            <span className="agent-tile-detail-value">
              {metadata?.description || 'No description available'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
