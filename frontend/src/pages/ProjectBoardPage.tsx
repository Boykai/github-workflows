/**
 * ProjectBoardPage component - main page with project selector and board view.
 */

import { useState } from 'react';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { ProjectBoard } from '@/components/board/ProjectBoard';
import { IssueDetailModal } from '@/components/board/IssueDetailModal';
import { AgentConfigRow } from '@/components/board/AgentConfigRow';
import { AddAgentPopover } from '@/components/board/AddAgentPopover';
import { AgentPresetSelector } from '@/components/board/AgentPresetSelector';
import { useAgentConfig, useAvailableAgents } from '@/hooks/useAgentConfig';
import { formatTimeAgo } from '@/utils/formatTime';
import type { BoardItem } from '@/types';

interface ProjectBoardPageProps {
  /** Currently selected project ID (shared with chat page) */
  selectedProjectId?: string | null;
  /** Callback when user selects a project (persists to session) */
  onProjectSelect?: (projectId: string) => void;
}

export function ProjectBoardPage({ selectedProjectId: externalProjectId, onProjectSelect }: ProjectBoardPageProps) {
  const {
    projects,
    projectsLoading,
    projectsError,
    selectedProjectId,
    boardData,
    boardLoading,
    isFetching,
    boardError,
    lastUpdated,
    selectProject,
  } = useProjectBoard({ selectedProjectId: externalProjectId, onProjectSelect });

  // Modal state (US2)
  const [selectedItem, setSelectedItem] = useState<BoardItem | null>(null);

  // Agent config state (004-agent-workflow-config-ui)
  const agentConfig = useAgentConfig(selectedProjectId);
  const { agents: availableAgents, isLoading: agentsLoading, error: agentsError, refetch: refetchAgents } = useAvailableAgents(selectedProjectId);

  const handleProjectSwitch = (projectId: string) => {
    if (agentConfig.isDirty) {
      const confirmed = window.confirm(
        'You have unsaved agent configuration changes. Discard and switch projects?'
      );
      if (!confirmed) return;
      agentConfig.discard();
    }
    selectProject(projectId);
  };

  const handleCardClick = (item: BoardItem) => {
    setSelectedItem(item);
  };

  const handleCloseModal = () => {
    setSelectedItem(null);
  };

  // Format last updated time
  const formatLastUpdated = () => lastUpdated ? formatTimeAgo(lastUpdated) : '';

  return (
    <div className="board-page">
      {/* Page Header */}
      <div className="board-page-header">
        <div className="board-page-header-left">
          <h2 className="board-page-title">Project Board</h2>

          {/* Project Selector */}
          <select
            className="board-project-select"
            value={selectedProjectId ?? ''}
            onChange={(e) => e.target.value && handleProjectSwitch(e.target.value)}
            disabled={projectsLoading}
          >
            <option value="">
              {projectsLoading ? 'Loading projects...' : 'Select a project'}
            </option>
            {projects.map((project) => (
              <option key={project.project_id} value={project.project_id}>
                {project.owner_login}/{project.name}
              </option>
            ))}
          </select>
        </div>

        <div className="board-page-header-right">
          {/* Refresh indicator */}
          {isFetching && !boardLoading && (
            <span className="board-refresh-indicator" title="Refreshing...">
              <span className="board-refresh-spinner" />
            </span>
          )}

          {/* Last updated */}
          {lastUpdated && (
            <span className="board-last-updated">
              Updated {formatLastUpdated()}
            </span>
          )}
        </div>
      </div>

      {/* Error states */}
      {projectsError && (
        <div className="board-error">
          <span className="board-error-icon">⚠️</span>
          <div className="board-error-content">
            <strong>Failed to load projects</strong>
            <p>{projectsError.message}</p>
          </div>
        </div>
      )}

      {boardError && !boardLoading && (
        <div className="board-error">
          <span className="board-error-icon">⚠️</span>
          <div className="board-error-content">
            <strong>Failed to load board data</strong>
            <p>{boardError.message}</p>
          </div>
          <button
            className="board-retry-btn"
            onClick={() => selectProject(selectedProjectId!)}
          >
            Retry
          </button>
        </div>
      )}

      {/* Content area */}
      {!selectedProjectId && !projectsLoading && (
        <div className="board-empty-state">
          <div className="board-empty-icon">📋</div>
          <h3>Select a project</h3>
          <p>Choose a project from the dropdown above to view its board</p>
        </div>
      )}

      {selectedProjectId && boardLoading && (
        <div className="board-loading">
          <div className="spinner" />
          <p>Loading board...</p>
        </div>
      )}

      {selectedProjectId && !boardLoading && boardData && (
        <>
          {/* Agent Configuration Row */}
          <AgentConfigRow
            columns={boardData.columns}
            agentConfig={agentConfig}
            availableAgents={availableAgents}
            renderPresetSelector={
              <AgentPresetSelector
                columnNames={boardData.columns.map((c) => c.status.name)}
                currentMappings={agentConfig.localMappings}
                onApplyPreset={agentConfig.applyPreset}
              />
            }
            renderAddButton={(status: string) => (
              <AddAgentPopover
                status={status}
                availableAgents={availableAgents}
                assignedAgents={agentConfig.localMappings[status] ?? []}
                isLoading={agentsLoading}
                error={agentsError}
                onRetry={refetchAgents}
                onAddAgent={agentConfig.addAgent}
              />
            )}
          />

          {boardData.columns.every((col) => col.items.length === 0) ? (
            <div className="board-empty-state">
              <div className="board-empty-icon">📭</div>
              <h3>No items yet</h3>
              <p>This project has no items. Add items in GitHub to see them here.</p>
            </div>
          ) : (
            <ProjectBoard boardData={boardData} onCardClick={handleCardClick} />
          )}
        </>
      )}

      {/* Detail Modal (US2) */}
      {selectedItem && (
        <IssueDetailModal item={selectedItem} onClose={handleCloseModal} />
      )}
    </div>
  );
}
