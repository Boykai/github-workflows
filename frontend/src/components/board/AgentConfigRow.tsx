/**
 * AgentConfigRow component - collapsible container that renders one AgentColumnCell
 * per status column, aligned with the board columns below.
 * Includes AgentSaveBar for save/discard workflow.
 */

import { useState } from 'react';
import type { BoardColumn, AvailableAgent } from '@/types';
import { AgentColumnCell } from './AgentColumnCell';
import { AgentSaveBar } from './AgentSaveBar';
import { useAgentConfig } from '@/hooks/useAgentConfig';

interface AgentConfigRowProps {
  columns: BoardColumn[];
  agentConfig: ReturnType<typeof useAgentConfig>;
  availableAgents?: AvailableAgent[];
  renderPresetSelector?: React.ReactNode;
  renderAddButton?: (status: string) => React.ReactNode;
}

export function AgentConfigRow({
  columns,
  agentConfig,
  availableAgents,
  renderPresetSelector,
  renderAddButton,
}: AgentConfigRowProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const {
    localMappings,
    isDirty,
    isColumnDirty,
    removeAgent,
    reorderAgents,
    save,
    discard,
    isSaving,
    saveError,
    isLoaded,
  } = agentConfig;

  // Loading skeleton (T030)
  if (!isLoaded) {
    return (
      <div className="flex flex-col bg-card border-b border-border">
        <div className="flex items-center gap-2 p-2 border-b border-border/50 bg-muted/30">
          <span className="text-sm font-semibold text-foreground flex items-center gap-2">🤖 Agent Pipeline</span>
        </div>
        <div className="p-2 bg-muted/10">
          <div className="flex gap-4 overflow-x-auto pb-2">
            {columns.map((col) => (
              <div key={col.status.option_id} className="flex-1 min-w-[300px] max-w-[350px] flex flex-col gap-2 p-2 bg-muted/20 rounded-md border border-border/50 animate-pulse">
                <div className="h-10 bg-muted rounded-md w-full" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col bg-card border-b border-border relative">
      {/* Header with toggle and presets */}
      <div className="flex items-center gap-2 p-2 border-b border-border/50 bg-muted/30">
        <button
          className="w-6 h-6 flex items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          onClick={() => setIsExpanded(!isExpanded)}
          title={isExpanded ? 'Collapse agent row' : 'Expand agent row'}
          type="button"
        >
          {isExpanded ? '▾' : '▸'}
        </button>
        <span className="text-sm font-semibold text-foreground flex items-center gap-2">🤖 Agent Pipeline</span>
        {renderPresetSelector}
      </div>

      {/* Collapsible body */}
      {isExpanded && (
        <div className="p-2 bg-muted/10">
          <div className="flex gap-4 overflow-x-auto pb-2">
            {columns.map((col) => {
              const status = col.status.name;
              const agents = localMappings[status] ?? [];

              return (
                <AgentColumnCell
                  key={col.status.option_id}
                  status={status}
                  agents={agents}
                  isModified={isColumnDirty(status)}
                  onRemoveAgent={removeAgent}
                  onReorderAgents={reorderAgents}
                  renderAddButton={renderAddButton?.(status)}
                  availableAgents={availableAgents}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Floating save bar */}
      {isDirty && (
        <AgentSaveBar
          onSave={save}
          onDiscard={discard}
          isSaving={isSaving}
          error={saveError}
        />
      )}
    </div>
  );
}
