/**
 * AgentsPanel — container for the Agents feature on the project board.
 *
 * Renders below ChoresPanel. Shows agent cards, empty state with docs link,
 * and loading / error states. Mirrors ChoresPanel pattern.
 */

import { useState } from 'react';
import { useAgentsList } from '@/hooks/useAgents';
import { AgentCard } from './AgentCard';
import { AddAgentModal } from './AddAgentModal';
import type { AgentConfig } from '@/services/api';

interface AgentsPanelProps {
  projectId: string;
  owner?: string;
  repo?: string;
}

export function AgentsPanel({ projectId }: AgentsPanelProps) {
  const { data: agents, isLoading, error } = useAgentsList(projectId);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editAgent, setEditAgent] = useState<AgentConfig | null>(null);

  return (
    <div className="flex flex-col gap-3 w-72 shrink-0">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
          🤖 Agents
        </h3>
        <button
          className="px-2 py-1 text-xs font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          onClick={() => setShowAddModal(true)}
        >
          + Add Agent
        </button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex flex-col gap-2">
          {[1, 2].map((i) => (
            <div
              key={i}
              className="h-24 rounded-md border border-border bg-muted/30 animate-pulse"
            />
          ))}
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="flex flex-col items-center gap-2 p-4 rounded-md border border-destructive/30 bg-destructive/5 text-center">
          <span className="text-sm text-destructive">Failed to load agents</span>
          <p className="text-xs text-muted-foreground">{error.message}</p>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && agents && agents.length === 0 && (
        <div className="flex flex-col items-center gap-2 p-6 rounded-md border-2 border-dashed border-border bg-muted/10 text-center">
          <span className="text-2xl">🤖</span>
          <p className="text-sm text-muted-foreground">No agents yet</p>
          <p className="text-xs text-muted-foreground">
            Add an agent to create custom GitHub Copilot agents for your repository.
          </p>
          <p className="text-xs text-muted-foreground/70 mt-1">
            See <span className="font-medium">docs/custom-agents-best-practices.md</span> for
            guidance.
          </p>
        </div>
      )}

      {/* Agent list */}
      {!isLoading && !error && agents && agents.length > 0 && (
        <div className="flex flex-col gap-2 overflow-y-auto max-h-[calc(100vh-280px)]">
          {agents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              projectId={projectId}
              onEdit={(a) => setEditAgent(a)}
            />
          ))}
        </div>
      )}

      {/* Add Agent Modal */}
      <AddAgentModal
        projectId={projectId}
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
      />

      {/* Edit Agent Modal */}
      {editAgent && (
        <AddAgentModal
          projectId={projectId}
          isOpen={true}
          onClose={() => setEditAgent(null)}
          editAgent={editAgent}
        />
      )}
    </div>
  );
}
