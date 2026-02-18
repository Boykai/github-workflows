/**
 * AgentConfigRow component - collapsible container that renders one AgentColumnCell
 * per status column, aligned with the board columns below.
 * Includes AgentSaveBar for save/discard workflow.
 */

import { useState } from 'react';
import type { BoardColumn, AvailableAgent } from '@/types';
import { AgentColumnCell } from './AgentColumnCell';
import { AgentSaveBar } from './AgentSaveBar';
import type { useAgentConfig } from '@/hooks/useAgentConfig';

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
      <div className="agent-config-row">
        <div className="agent-config-row-header">
          <span className="agent-config-row-title">🤖 Agent Pipeline</span>
        </div>
        <div className="agent-config-row-body">
          <div className="agent-config-row-columns">
            {columns.map((col) => (
              <div key={col.status.option_id} className="agent-column-cell agent-column-cell--skeleton">
                <div className="agent-tile-skeleton" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="agent-config-row">
      {/* Header with toggle and presets */}
      <div className="agent-config-row-header">
        <button
          className="agent-config-row-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
          title={isExpanded ? 'Collapse agent row' : 'Expand agent row'}
          type="button"
        >
          {isExpanded ? '▾' : '▸'}
        </button>
        <span className="agent-config-row-title">🤖 Agent Pipeline</span>
        {renderPresetSelector}
      </div>

      {/* Collapsible body */}
      {isExpanded && (
        <div className="agent-config-row-body">
          <div className="agent-config-row-columns">
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
