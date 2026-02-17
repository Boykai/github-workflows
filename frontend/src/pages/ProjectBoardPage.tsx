/**
 * ProjectBoardPage component - main page with project selector and board view.
 */

import { useState } from 'react';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { ProjectBoard } from '@/components/board/ProjectBoard';
import { IssueDetailModal } from '@/components/board/IssueDetailModal';
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

  const handleCardClick = (item: BoardItem) => {
    setSelectedItem(item);
  };

  const handleCloseModal = () => {
    setSelectedItem(null);
  };

  // Format last updated time
  const formatLastUpdated = () => {
    if (!lastUpdated) return '';
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - lastUpdated.getTime()) / 1000);
    if (diffSec < 60) return 'just now';
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    return lastUpdated.toLocaleTimeString();
  };

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
            onChange={(e) => e.target.value && selectProject(e.target.value)}
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
