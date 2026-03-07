/**
 * AgentDragOverlay component - renders a styled, read-only preview of the
 * dragged AgentTile inside @dnd-kit's DragOverlay portal.
 */

import { User } from 'lucide-react';
import type { AgentAssignment, AvailableAgent } from '@/types';
import { formatAgentName } from '@/utils/formatAgentName';

interface AgentDragOverlayProps {
  agent: AgentAssignment;
  availableAgents?: AvailableAgent[];
  width?: number | null;
}

export function AgentDragOverlay({ agent, availableAgents, width }: AgentDragOverlayProps) {
  const displayName = formatAgentName(agent.slug, agent.display_name);
  const metadata = availableAgents?.find((a) => a.slug === agent.slug);
  const avatarLetter = displayName.charAt(0).toUpperCase();
  const isHuman = agent.slug === 'human';

  // Build metadata line
  const metaParts: string[] = [];
  if (metadata?.default_model_name) metaParts.push(metadata.default_model_name);
  if (metadata?.tools_count && metadata.tools_count > 0) metaParts.push(`${metadata.tools_count} tools`);
  const metaLine = metaParts.join(' · ');

  return (
    <div
      className="flex min-w-[280px] max-w-[340px] items-center gap-2 rounded-md border border-primary/50 bg-card p-2 shadow-lg opacity-80 cursor-grabbing"
      style={width != null ? { width } : undefined}
    >
      {/* Drag handle (decorative) */}
      <span className="text-muted-foreground/50 px-1">⠿</span>

      {/* Avatar */}
      <span
        className={`flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium shrink-0 overflow-hidden ${isHuman ? 'bg-violet-500/15 text-violet-600 dark:text-violet-400' : 'bg-primary/10 text-primary'}`}
        title={agent.slug}
      >
        {isHuman ? (
          <User className="w-3.5 h-3.5" />
        ) : metadata?.avatar_url ? (
          <img src={metadata.avatar_url} alt={displayName} className="w-full h-full object-cover" />
        ) : (
          avatarLetter
        )}
      </span>

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
