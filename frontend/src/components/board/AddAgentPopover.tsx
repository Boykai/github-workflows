/**
 * AddAgentPopover component - dropdown popover for adding agents to a column.
 * Displays available agents with slug, display_name, and description.
 * On select, calls addAgent callback. Shows loading/error states (T019).
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import type { AvailableAgent, AgentAssignment } from '@/types';

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
}

export function AddAgentPopover({
  status,
  availableAgents,
  assignedAgents,
  isLoading,
  error,
  onRetry,
  onAddAgent,
}: AddAgentPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [filter, setFilter] = useState('');
  const popoverRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(e.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
        setFilter('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
        setFilter('');
        triggerRef.current?.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  const handleSelect = useCallback(
    (agent: AvailableAgent) => {
      onAddAgent(status, agent);
      setIsOpen(false);
      setFilter('');
    },
    [status, onAddAgent]
  );

  const filteredAgents = availableAgents.filter((a) => {
    if (!filter) return true;
    const lower = filter.toLowerCase();
    return (
      a.slug.toLowerCase().includes(lower) ||
      a.display_name.toLowerCase().includes(lower) ||
      (a.description?.toLowerCase().includes(lower) ?? false)
    );
  });

  // Count how many times each slug is already assigned
  const assignedSlugs = new Set(assignedAgents.map((a) => a.slug));

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        className="w-full py-1.5 px-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors border border-dashed border-border/50 hover:border-border"
        onClick={() => setIsOpen(!isOpen)}
        title={`Add agent to ${status}`}
        type="button"
      >
        + Add Agent
      </button>

      {isOpen && (
        <div ref={popoverRef} className="absolute top-full left-0 mt-1 w-64 bg-popover border border-border rounded-md shadow-md z-50 flex flex-col max-h-80 overflow-hidden" role="listbox" aria-label={`Add agent to ${status}`}>
          {/* Search filter */}
          <div className="p-2 border-b border-border bg-muted/30">
            <input
              type="text"
              className="w-full px-2 py-1 text-sm bg-background border border-input rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="Filter agents..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
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
              <span>⚠ {error}</span>
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
                  return (
                    <button
                      key={agent.slug}
                      className={`w-full text-left p-2 rounded-md hover:bg-muted transition-colors flex flex-col gap-1 relative ${isDuplicate ? 'opacity-70' : ''}`}
                      onClick={() => handleSelect(agent)}
                      type="button"
                      role="option"
                      title={isDuplicate ? `${agent.display_name} (already assigned)` : agent.display_name}
                    >
                      <div className="flex items-center justify-between w-full">
                        <span className="text-sm font-medium text-foreground truncate pr-2">{agent.display_name}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium uppercase tracking-wider shrink-0 ${agent.source === 'builtin' ? 'bg-blue-500/10 text-blue-500' : agent.source === 'repository' ? 'bg-green-500/10 text-green-500' : 'bg-muted text-muted-foreground'}`}>
                          {agent.source}
                        </span>
                      </div>
                      {agent.description && (
                        <div className="text-xs text-muted-foreground line-clamp-2 leading-snug">{agent.description}</div>
                      )}
                      <div className="text-[10px] font-mono text-muted-foreground/70 truncate">{agent.slug}</div>
                      {isDuplicate && (
                        <span className="absolute top-2 right-2 text-[10px] bg-amber-500/10 text-amber-500 px-1.5 py-0.5 rounded">already assigned</span>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
