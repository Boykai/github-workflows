/**
 * AgentTile component - card-style tile for a single agent assignment.
 * Displays formatted agent name, model/tool metadata, avatar/icon, and remove button.
 * Supports drag-and-drop via @dnd-kit (T023) and expand/collapse (T029).
 */

import { useState } from 'react';
import { TriangleAlert, X } from '@/lib/icons';
import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';
import type { AgentAssignment, AvailableAgent } from '@/types';
import { formatAgentName } from '@/utils/formatAgentName';
import { cn } from '@/lib/utils';
import { Tooltip } from '@/components/ui/tooltip';

function getAssignmentModelName(agent: AgentAssignment): string {
  const config = agent.config;
  if (!config || typeof config !== 'object') {
    return '';
  }

  const modelName = config.model_name;
  return typeof modelName === 'string' ? modelName : '';
}

interface AgentTileProps {
  agent: AgentAssignment;
  onRemove?: (agentInstanceId: string) => void;
  onClone?: (agentInstanceId: string) => void;
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
  variant?: 'default' | 'compact';
  compactIndex?: number;
  compactCount?: number;
}

function DoubleMoonIcon() {
  return (
    <svg viewBox="0 0 20 20" className="h-3.5 w-3.5" aria-hidden="true">
      <circle cx="7.1" cy="9" r="3.45" fill="hsl(var(--gold))" opacity="0.88" />
      <circle cx="8.9" cy="8.1" r="3.15" fill="hsl(var(--background))" />
      <circle cx="12.6" cy="10.7" r="3.15" fill="hsl(var(--foreground))" opacity="0.88" />
      <circle cx="14.1" cy="9.9" r="2.85" fill="hsl(var(--background))" />
      <circle cx="15.7" cy="5.1" r="0.85" fill="hsl(var(--glow))" />
      <circle cx="4.2" cy="4.8" r="0.7" fill="hsl(var(--star))" opacity="0.95" />
    </svg>
  );
}

export function AgentTile({
  agent,
  onRemove,
  onClone,
  sortableProps,
  availableAgents,
  isWarning,
  variant = 'default',
  compactIndex = 0,
  compactCount = 1,
}: AgentTileProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const displayName = formatAgentName(agent.slug, agent.display_name);
  const metadata = availableAgents?.find((a) => a.slug === agent.slug);
  const assignedModelName = getAssignmentModelName(agent);
  const effectiveModelName = assignedModelName || metadata?.default_model_name || '';

  // Build metadata line: model · N tools
  const metaParts: string[] = [];
  if (effectiveModelName) metaParts.push(effectiveModelName);
  if (metadata && metadata.tools_count != null)
    metaParts.push(`${metadata.tools_count} tool${metadata.tools_count !== 1 ? 's' : ''}`);
  const metaLine = metaParts.join(' · ');

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    onRemove?.(agent.id);
  };

  const handleClone = (e: React.MouseEvent) => {
    e.stopPropagation();
    onClone?.(agent.id);
  };

  const stopDragPointerPropagation = (event: React.PointerEvent<HTMLElement>) => {
    event.stopPropagation();
  };

  const tileStyle: React.CSSProperties = {
    ...(sortableProps?.style ?? {}),
    opacity: sortableProps?.isDragging ? 0.3 : 1,
  };

  const isCompact = variant === 'compact';

  if (isCompact) {
    return (
      <div
        ref={sortableProps?.setNodeRef}
        role="listitem"
        className={cn('group relative flex items-center gap-2 overflow-hidden rounded-[0.95rem] border px-2 py-1.5 shadow-sm transition-all', isWarning ? 'border-amber-400/45 bg-amber-500/8' : 'border-border/55 bg-[radial-gradient(circle_at_18%_24%,hsl(var(--glow)/0.18),transparent_32%),linear-gradient(180deg,hsl(var(--background)/0.82),hsl(var(--background)/0.92))]', sortableProps?.isDragging ? 'border-dashed opacity-30 shadow-none' : 'hover:border-primary/35 hover:bg-primary/8', sortableProps ? ' cursor-grab active:cursor-grabbing touch-none' : '')}
        style={tileStyle}
        {...(sortableProps?.attributes ?? {})}
        {...(sortableProps?.listeners ?? {})}
        aria-roledescription="sortable agent"
      >
        {(compactIndex > 0 || compactIndex < compactCount - 1) && (
          <span className="pointer-events-none absolute left-[1.05rem] top-0 bottom-0 w-px opacity-80">
            {compactIndex > 0 && (
              <span className="absolute bottom-1/2 top-0 left-0 w-px bg-gradient-to-b from-primary/10 via-primary/35 to-primary/55" />
            )}
            {compactIndex < compactCount - 1 && (
              <span className="absolute top-1/2 bottom-0 left-0 w-px bg-gradient-to-b from-primary/55 via-primary/35 to-primary/10" />
            )}
          </span>
        )}

        <span className="relative z-10 rounded-full p-[2px] shadow-[0_0_18px_hsl(var(--gold)/0.15)]">
          <span className="absolute inset-0 rounded-full border border-primary/18 bg-background/18" />
          <ThemedAgentIcon
            slug={agent.slug}
            name={displayName}
            avatarUrl={metadata?.avatar_url}
            iconName={metadata?.icon_name}
            size="sm"
            className="relative border-border/50"
            title={agent.slug}
          />
        </span>

        <div className="min-w-0 flex-1">
          <span
            className="block truncate text-[11px] font-semibold tracking-[0.02em] text-foreground"
            title={agent.slug}
          >
            {displayName}
          </span>
          {effectiveModelName && (
            <span className="block truncate text-[9px] uppercase tracking-[0.12em] text-muted-foreground/80">
              {effectiveModelName}
            </span>
          )}
        </div>

        {isWarning && (
          <span
            className="rounded-full border border-amber-400/45 bg-amber-500/12 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-[0.12em] text-amber-700 dark:text-amber-300"
            title="Agent not found in available agents"
          >
            !
          </span>
        )}

        {onClone && (
          <Tooltip contentKey="board.agentTile.clone">
            <button
              className="celestial-focus flex h-5 w-5 items-center justify-center rounded-full text-muted-foreground/60 transition-colors hover:bg-primary/10 hover:text-primary"
              onClick={handleClone}
              onPointerDown={stopDragPointerPropagation}
              aria-label={`Clone ${displayName}`}
              type="button"
            >
              <DoubleMoonIcon />
            </button>
          </Tooltip>
        )}

        {onRemove && (
          <Tooltip contentKey="board.agentTile.remove">
            <button
              className="celestial-focus flex h-5 w-5 items-center justify-center rounded-full text-muted-foreground/60 transition-colors hover:bg-destructive/10 hover:text-destructive"
              onClick={handleRemove}
              onPointerDown={stopDragPointerPropagation}
              aria-label={`Remove ${displayName}`}
              type="button"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </Tooltip>
        )}
      </div>
    );
  }

  return (
    <div
      ref={sortableProps?.setNodeRef}
      role="listitem"
      className={cn('celestial-panel flex flex-col rounded-md border bg-card shadow-sm', isWarning ? 'border-amber-400/45 bg-amber-500/8' : 'border-border', sortableProps?.isDragging ? 'border-dashed opacity-30 shadow-none' : '', sortableProps ? ' cursor-grab active:cursor-grabbing touch-none' : '')}
      style={tileStyle}
      {...(sortableProps?.attributes ?? {})}
      {...(sortableProps?.listeners ?? {})}
      aria-roledescription="sortable agent"
    >
      <div className="flex items-center gap-2 p-2">

        {/* Avatar */}
        <ThemedAgentIcon
          slug={agent.slug}
          name={displayName}
          avatarUrl={metadata?.avatar_url}
          iconName={metadata?.icon_name}
          size="sm"
          title={agent.slug}
        />

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
          <span
            className="rounded-md border border-amber-400/45 bg-amber-500/12 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-amber-700 dark:text-amber-300"
            title="Agent not found in available agents"
          >
            <TriangleAlert className="h-3.5 w-3.5" />
          </span>
        )}

        {/* Expand toggle (T029) */}
        <Tooltip content={isExpanded ? 'Collapse details' : 'Expand details'}>
          <button
            className="celestial-focus solar-action flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground transition-colors hover:text-foreground"
            onClick={() => setIsExpanded(!isExpanded)}
            onPointerDown={stopDragPointerPropagation}
            aria-label={isExpanded ? `Collapse ${displayName} details` : `Expand ${displayName} details`}
            type="button"
          >
            {isExpanded ? '▾' : '▸'}
          </button>
        </Tooltip>

        {onClone && (
          <Tooltip contentKey="board.agentTile.clone">
            <button
              className="celestial-focus solar-action flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground transition-colors hover:text-primary"
              onClick={handleClone}
              onPointerDown={stopDragPointerPropagation}
              aria-label={`Clone ${displayName}`}
              type="button"
            >
              <DoubleMoonIcon />
            </button>
          </Tooltip>
        )}

        {/* Remove button */}
        {onRemove && (
          <Tooltip contentKey="board.agentTile.remove">
            <button
              className="celestial-focus w-6 h-6 flex items-center justify-center rounded-md text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
              onClick={handleRemove}
              onPointerDown={stopDragPointerPropagation}
              aria-label={`Remove ${displayName}`}
              type="button"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </Tooltip>
        )}
      </div>

      {/* Expanded detail (T029) */}
      {isExpanded && (
        <div className="mt-1 flex flex-col gap-1.5 rounded-b-md border-t border-border/50 bg-background/46 p-3 pt-0 text-xs">
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-muted-foreground font-medium min-w-[70px]">Slug:</span>
            <code className="solar-chip-soft rounded border px-1.5 py-0.5 text-[10px] font-mono break-all">
              {agent.slug}
            </code>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-muted-foreground font-medium min-w-[70px]">Model:</span>
            <span className="text-foreground">{effectiveModelName || 'No model selected'}</span>
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
