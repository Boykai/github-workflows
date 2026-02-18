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
    <div className="add-agent-popover-container">
      <button
        ref={triggerRef}
        className="add-agent-trigger-btn"
        onClick={() => setIsOpen(!isOpen)}
        title={`Add agent to ${status}`}
        type="button"
      >
        + Add Agent
      </button>

      {isOpen && (
        <div ref={popoverRef} className="add-agent-popover" role="listbox" aria-label={`Add agent to ${status}`}>
          {/* Search filter */}
          <div className="add-agent-popover-search">
            <input
              type="text"
              className="add-agent-popover-filter"
              placeholder="Filter agents..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              autoFocus
            />
          </div>

          {/* Loading */}
          {isLoading && (
            <div className="add-agent-popover-loading">
              <span className="add-agent-popover-spinner" />
              Loading agents...
            </div>
          )}

          {/* Error */}
          {error && !isLoading && (
            <div className="add-agent-popover-error">
              <span>⚠ {error}</span>
              <button
                className="add-agent-popover-retry"
                onClick={onRetry}
                type="button"
              >
                Retry
              </button>
            </div>
          )}

          {/* Agent list */}
          {!isLoading && !error && (
            <div className="add-agent-popover-list">
              {filteredAgents.length === 0 ? (
                <div className="add-agent-popover-empty">
                  {filter ? 'No matching agents' : 'No agents available'}
                </div>
              ) : (
                filteredAgents.map((agent) => {
                  const isDuplicate = assignedSlugs.has(agent.slug);
                  return (
                    <button
                      key={agent.slug}
                      className={`add-agent-popover-item${isDuplicate ? ' add-agent-popover-item--duplicate' : ''}`}
                      onClick={() => handleSelect(agent)}
                      type="button"
                      role="option"
                      title={isDuplicate ? `${agent.display_name} (already assigned)` : agent.display_name}
                    >
                      <div className="add-agent-popover-item-header">
                        <span className="add-agent-popover-item-name">{agent.display_name}</span>
                        <span className={`add-agent-popover-item-source add-agent-popover-item-source--${agent.source}`}>
                          {agent.source}
                        </span>
                      </div>
                      {agent.description && (
                        <div className="add-agent-popover-item-desc">{agent.description}</div>
                      )}
                      <div className="add-agent-popover-item-slug">{agent.slug}</div>
                      {isDuplicate && (
                        <span className="add-agent-popover-item-badge">already assigned</span>
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
