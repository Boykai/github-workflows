import { TriangleAlert } from '@/lib/icons';

/**
 * AddAgentPopover component - dropdown popover for adding agents to a column.
 * Displays available agents with slug, display_name, and description.
 * On select, calls addAgent callback. Shows loading/error states (T019).
 *
 * Uses Radix Popover for portal rendering, positioning, click-outside
 * dismissal, and Escape-key handling.
 */

import { useState, useCallback, useMemo } from 'react';
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';
import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';
import type { AvailableAgent, AgentAssignment } from '@/types';
import { formatAgentName } from '@/utils/formatAgentName';
import { cn } from '@/lib/utils';

interface AddAgentPopoverProps {
  /** Status column name */
  status: string;
  /** Available agents from discovery */
  availableAgents: AvailableAgent[];
  /** Currently assigned agents in this column (for duplicate indicator) */
  assignedAgents: AgentAssignment[];
  /** Whether agents are loading */
  isLoading: boolean;
  /** Error message from agent fetch */
  error: string | null;
  /** Retry fetching agents */
  onRetry: () => void;
  /** Called when user selects an agent */
  onAddAgent: (status: string, agent: AvailableAgent) => void;
  compact?: boolean;
}

export function AddAgentPopover({
  status,
  availableAgents,
  assignedAgents,
  isLoading,
  error,
  onRetry,
  onAddAgent,
  compact = false,
}: AddAgentPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [filter, setFilter] = useState('');

  const handleOpenChange = useCallback((open: boolean) => {
    setIsOpen(open);
    if (!open) setFilter('');
  }, []);

  const handleSelect = useCallback(
    (agent: AvailableAgent) => {
      onAddAgent(status, agent);
      handleOpenChange(false);
    },
    [status, onAddAgent, handleOpenChange]
  );

  const filteredAgents = useMemo(
    () =>
      availableAgents.filter((a) => {
        if (!filter) return true;
        const lower = filter.toLowerCase();
        return (
          a.slug.toLowerCase().includes(lower) ||
          a.display_name.toLowerCase().includes(lower) ||
          (a.description?.toLowerCase().includes(lower) ?? false)
        );
      }),
    [availableAgents, filter],
  );

  // Memoize assigned slug set to avoid re-creating on every render (T024).
  const assignedSlugs = useMemo(
    () => new Set(assignedAgents.map((a) => a.slug)),
    [assignedAgents],
  );

  return (
    <Popover open={isOpen} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <button
          className={
            compact
              ? 'celestial-focus w-full rounded-full border border-dashed border-primary/30 bg-background/22 px-2 py-1 text-[11px] font-medium text-muted-foreground transition-colors hover:border-primary/45 hover:bg-primary/10 hover:text-foreground'
              : 'celestial-focus w-full rounded-md border border-dashed border-border/50 bg-background/26 px-2 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:border-border hover:bg-primary/10 hover:text-foreground'
          }
          aria-label={`Add agent to ${status}`}
          type="button"
        >
          + Add Agent
        </button>
      </PopoverTrigger>

      <PopoverContent
        side="bottom"
        align="start"
        className="flex max-h-80 w-64 flex-col overflow-hidden rounded-[1rem] border-border bg-popover p-0 shadow-lg backdrop-blur-sm"
        aria-label={`Add agent to ${status}`}
        aria-busy={isLoading}
      >
        {/* Search filter */}
        <div className="border-b border-border bg-background/40 p-2">
          <input
            type="text"
            className="celestial-focus w-full rounded-md border border-input bg-background/72 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
            placeholder="Filter agents..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            /* eslint-disable-next-line jsx-a11y/no-autofocus */
            autoFocus
          />
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="p-4 text-sm text-muted-foreground flex items-center justify-center gap-2">
            <span className="w-4 h-4 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
            Loading agents...
          </div>
        )}

        {/* Error */}
        {error && !isLoading && (
          <div className="p-3 text-sm text-destructive bg-destructive/10 flex flex-col gap-2">
            <span className="inline-flex items-center gap-2">
              <TriangleAlert className="h-4 w-4" />
              {error}
            </span>
            <button
              className="px-2 py-1 bg-background border border-destructive/20 rounded text-xs hover:bg-destructive/20 transition-colors"
              onClick={onRetry}
              type="button"
            >
              Retry
            </button>
          </div>
        )}

        {/* Agent list */}
        {!isLoading && !error && (
          <div className="overflow-y-auto flex-1 p-1">
            {filteredAgents.length === 0 ? (
              <div className="p-3 text-sm text-muted-foreground text-center">
                {filter ? 'No matching agents' : 'No agents available'}
              </div>
            ) : (
              filteredAgents.map((agent) => {
                const isDuplicate = assignedSlugs.has(agent.slug);
                const displayName = formatAgentName(agent.slug, agent.display_name);
                return (
                  <button
                    key={agent.slug}
                    className={cn(
                      'relative flex w-full flex-col gap-1 rounded-md p-2 text-left transition-colors hover:bg-primary/10',
                      isDuplicate ? 'opacity-70' : ''
                    )}
                    onClick={() => handleSelect(agent)}
                    type="button"
                    aria-label={isDuplicate ? `${displayName} (already assigned)` : displayName}
                  >
                    <div className="flex items-start justify-between gap-2 w-full">
                      <div className="flex min-w-0 items-start gap-2">
                        <ThemedAgentIcon
                          slug={agent.slug}
                          name={displayName}
                          avatarUrl={agent.avatar_url}
                          iconName={agent.icon_name}
                          size="md"
                          className="mt-0.5"
                        />
                        <span className="text-sm font-medium text-foreground truncate pr-2">
                          {displayName}
                        </span>
                      </div>
                      <span
                        className={cn(
                          'text-[10px] px-1.5 py-0.5 rounded-full font-medium uppercase tracking-wider shrink-0',
                          agent.source === 'builtin'
                            ? 'solar-chip-neutral'
                            : agent.source === 'repository'
                              ? 'solar-chip-success'
                              : 'bg-muted text-muted-foreground'
                        )}
                      >
                        {agent.source}
                      </span>
                    </div>
                    {agent.description && (
                      <div className="text-xs text-muted-foreground line-clamp-2 leading-snug">
                        {agent.description}
                      </div>
                    )}
                    <div className="text-[10px] font-mono text-muted-foreground/70 truncate">
                      {agent.slug}
                    </div>
                    {isDuplicate && (
                      <span className="absolute top-2 right-2 rounded bg-primary/10 px-1.5 py-0.5 text-[10px] text-primary">
                        already assigned
                      </span>
                    )}
                  </button>
                );
              })
            )}
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
