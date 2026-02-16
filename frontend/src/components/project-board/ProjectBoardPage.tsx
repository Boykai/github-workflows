/**
 * Main project board page component with Kanban-style layout.
 */

import { useProjectBoard } from '@/hooks/useProjectBoard';
import { BoardColumn } from './BoardColumn';
import { IssueDetailModal } from './IssueDetailModal';

interface ProjectBoardPageProps {
  onNavigateToChat: () => void;
}

export function ProjectBoardPage({ onNavigateToChat }: ProjectBoardPageProps) {
  const {
    projects,
    projectsLoading,
    projectsError,
    refetchProjects,
    selectedProjectId,
    boardData,
    boardLoading,
    boardError,
    boardErrorObj,
    boardFetching,
    refetchBoard,
    isModalOpen,
    selectedCard,
    selectProject,
    openModal,
    closeModal,
  } = useProjectBoard();

  return (
    <div className="project-board-page">
      {/* Header */}
      <div className="board-page-header">
        <button className="board-back-button" onClick={onNavigateToChat}>
          ← Back to Chat
        </button>
        <h2>Project Board</h2>

        {/* Refresh indicator */}
        {boardFetching && !boardLoading && (
          <span className="board-refresh-indicator">Refreshing…</span>
        )}
      </div>

      {/* Project selector */}
      <div className="board-project-selector">
        {projectsLoading ? (
          <div className="board-loading-spinner">
            <div className="spinner" />
            <span>Loading projects…</span>
          </div>
        ) : projectsError ? (
          <div className="board-error-state">
            <p>Failed to load projects.</p>
            <button onClick={() => refetchProjects()}>Retry</button>
          </div>
        ) : projects.length === 0 ? (
          <div className="board-empty-state">
            <p>No GitHub Projects available. Create a project on GitHub to get started.</p>
          </div>
        ) : (
          <select
            className="board-project-select"
            value={selectedProjectId || ''}
            onChange={(e) => {
              if (e.target.value) selectProject(e.target.value);
            }}
          >
            <option value="">Select a project…</option>
            {projects.map((p) => (
              <option key={p.project_id} value={p.project_id}>
                {p.title} ({p.item_count} items)
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Board content */}
      <div className="board-content-area">
        {!selectedProjectId && !projectsLoading && projects.length > 0 && (
          <div className="board-empty-state">
            <p>Select a project from the dropdown above to view its board.</p>
          </div>
        )}

        {selectedProjectId && boardLoading && (
          <div className="board-loading-skeleton">
            <div className="spinner" />
            <span>Loading board…</span>
          </div>
        )}

        {selectedProjectId && boardError && (
          <div className="board-error-state">
            <p>
              {boardErrorObj && 'status' in boardErrorObj && (boardErrorObj as { status: number }).status === 401
                ? 'Your session has expired. Please re-authenticate.'
                : 'Failed to load board data.'}
            </p>
            <button onClick={() => refetchBoard()}>Retry</button>
          </div>
        )}

        {/* Empty columns state */}
        {(() => {
          const showNoColumnsState = selectedProjectId && !boardLoading && !boardError && boardData && !boardFetching && boardData.columns.length === 0;
          return showNoColumnsState ? (
            <div className="board-empty-state">
              <p>This project has no status columns configured.</p>
            </div>
          ) : null;
        })()}

        {boardData && boardData.columns.length > 0 && (
          <div className="board-container-kanban">
            {boardData.columns.map((col) => (
              <BoardColumn
                key={col.option_id || col.name}
                column={col}
                onCardClick={openModal}
              />
            ))}
          </div>
        )}
      </div>

      {/* Detail modal */}
      {selectedCard && (
        <IssueDetailModal
          card={selectedCard}
          isOpen={isModalOpen}
          onClose={closeModal}
        />
      )}
    </div>
  );
}
