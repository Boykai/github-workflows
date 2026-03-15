/**
 * AgentDragOverlay component - renders a styled, read-only preview of the
 * dragged AgentTile inside @dnd-kit's DragOverlay portal.
 */

import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';
import type { AgentAssignment, AvailableAgent } from '@/types';
import { formatAgentName } from '@/utils/formatAgentName';

function getAssignmentModelName(agent: AgentAssignment): string {
  const config = agent.config;
  if (!config || typeof config !== 'object') {
    return '';
  }

  const modelName = config.model_name;
  return typeof modelName === 'string' ? modelName : '';
}

interface AgentDragOverlayProps {
  agent: AgentAssignment;
  availableAgents?: AvailableAgent[];
  width?: number | null;
}

export function AgentDragOverlay({ agent, availableAgents, width }: AgentDragOverlayProps) {
  const displayName = formatAgentName(agent.slug, agent.display_name);
  const metadata = availableAgents?.find((a) => a.slug === agent.slug);
  const assignedModelName = getAssignmentModelName(agent);

  // Build metadata line
  const metaParts: string[] = [];
  if (assignedModelName || metadata?.default_model_name) {
    metaParts.push(assignedModelName || metadata?.default_model_name || '');
  }
  if (metadata?.tools_count && metadata.tools_count > 0)
    metaParts.push(`${metadata.tools_count} tools`);
  const metaLine = metaParts.join(' · ');

  return (
    <div
      className="flex min-w-[280px] max-w-[340px] items-center gap-2 rounded-md border border-primary/50 bg-card p-2 shadow-lg opacity-80 cursor-grabbing"
      style={width != null ? { width } : undefined}
    >
      {/* Drag handle (decorative) */}
      <span className="text-muted-foreground/50 px-1" aria-hidden="true">⠿</span>

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
    </div>
  );
}
