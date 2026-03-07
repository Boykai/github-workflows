/**
 * ProjectsPage — Project board with enhanced Kanban view.
 * Migrated from ProjectBoardPage with page header, toolbar, and enhanced cards.
 */

import { useState } from 'react';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useRealTimeSync } from '@/hooks/useRealTimeSync';
import { useBoardRefresh } from '@/hooks/useBoardRefresh';
import { useProjects } from '@/hooks/useProjects';
import { useAuth } from '@/hooks/useAuth';
import { ProjectBoard } from '@/components/board/ProjectBoard';
import { IssueDetailModal } from '@/components/board/IssueDetailModal';
import { AgentConfigRow } from '@/components/board/AgentConfigRow';
import { AddAgentPopover } from '@/components/board/AddAgentPopover';
import { AgentPresetSelector } from '@/components/board/AgentPresetSelector';
import { RefreshButton } from '@/components/board/RefreshButton';
import { useAgentConfig, useAvailableAgents } from '@/hooks/useAgentConfig';
import { formatTimeAgo, formatTimeUntil } from '@/utils/formatTime';
import type { BoardItem } from '@/types';
import { ApiError } from '@/services/api';
import { Filter, ArrowUpDown, Columns3 } from 'lucide-react';

export function ProjectsPage() {
  const { user } = useAuth();
  const {
    projects,
    selectedProject,
    selectProject,
  } = useProjects(user?.selected_project_id);

  const {
    projectsLoading,
    projectsError,
    selectedProjectId,
    boardData,
    boardLoading,
    isFetching,
    boardError,
    lastUpdated,
    selectProject: selectBoardProject,
  } = useProjectBoard({ selectedProjectId: selectedProject?.project_id, onProjectSelect: selectProject });

  const {
    refresh,
    isRefreshing,
    error: refreshError,
    rateLimitInfo,
    isRateLimitLow,
    resetTimer,
  } = useBoardRefresh({ projectId: selectedProjectId, boardData });

  const { status: syncStatus, lastUpdate: syncLastUpdate } = useRealTimeSync(selectedProjectId, {
    onRefreshTriggered: resetTimer,
  });

  const [selectedItem, setSelectedItem] = useState<BoardItem | null>(null);
  const [filterOpen, setFilterOpen] = useState(false);
  const [sortField, setSortField] = useState<string | null>(null);

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
    selectBoardProject(projectId);
  };

  const handleCardClick = (item: BoardItem) => setSelectedItem(item);
  const handleCloseModal = () => setSelectedItem(null);

  // Derive board data with optional sorting
  const sortedBoardData = boardData && sortField
    ? {
        ...boardData,
        columns: boardData.columns.map((col) => ({
          ...col,
          items: [...col.items].sort((a, b) => {
            if (sortField === 'priority') {
              const order: Record<string, number> = { P0: 0, P1: 1, P2: 2, P3: 3 };
              return (order[a.priority?.name ?? 'P2'] ?? 2) - (order[b.priority?.name ?? 'P2'] ?? 2);
            }
            if (sortField === 'title') return a.title.localeCompare(b.title);
            return 0;
          }),
        })),
      }
    : boardData;

  // Calculate progress
  const totalItems = boardData?.columns.reduce((sum, col) => sum + col.item_count, 0) ?? 0;
  const doneItems = boardData?.columns
    .filter((col) => col.status.name.toLowerCase().includes('done') || col.status.name.toLowerCase().includes('closed'))
    .reduce((sum, col) => sum + col.item_count, 0) ?? 0;
  const progressPercent = totalItems > 0 ? Math.round((doneItems / totalItems) * 100) : 0;

  return (
    <div className="flex h-full flex-col gap-5 rounded-[1.75rem] border border-border/70 bg-background/35 p-6 backdrop-blur-sm overflow-hidden">
      {/* Page Header */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <div>
            <p className="mb-1 text-xs uppercase tracking-[0.24em] text-primary/80">Celestial Board</p>
            <h2 className="text-3xl font-display font-medium tracking-[0.04em]">Projects</h2>
          </div>

          {/* Project Selector */}
          <select
            className="flex h-11 w-[280px] items-center justify-between rounded-full border border-input bg-background/70 px-4 py-2 text-sm text-foreground shadow-sm ring-offset-background placeholder:text-muted-foreground backdrop-blur-sm focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
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

        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          {selectedProjectId && (
            <span className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${
                syncStatus === 'connected' ? 'bg-green-500' :
                syncStatus === 'polling' ? 'bg-yellow-500' :
                syncStatus === 'connecting' ? 'bg-blue-500' :
                'bg-red-500'
              }`} />
              {syncStatus === 'connected' && 'Live'}
              {syncStatus === 'polling' && 'Polling'}
              {syncStatus === 'connecting' && 'Connecting...'}
              {syncStatus === 'disconnected' && 'Offline'}
            </span>
          )}

          {selectedProjectId && (
            <RefreshButton
              onRefresh={refresh}
              isRefreshing={isRefreshing || (isFetching && !boardLoading)}
            />
          )}

          {(lastUpdated || syncLastUpdate) && (
            <span className="text-xs">
              Updated {formatTimeAgo(syncLastUpdate ?? lastUpdated!)}
            </span>
          )}
        </div>
      </div>

      {/* Project info header (when a project is selected and has data) */}
      {selectedProjectId && boardData && (
        <div className="celestial-panel flex items-center justify-between shrink-0 rounded-[1.25rem] border border-border/70 px-5 py-4">
          <div className="flex items-center gap-3">
            <h3 className="text-xl font-display font-medium tracking-[0.04em]">{boardData.project.name}</h3>
            <span className="rounded-full bg-secondary px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-secondary-foreground">
              {boardData.project.owner_login}
            </span>
            <span className="text-xs text-muted-foreground">
              {totalItems} items
            </span>
          </div>
          {/* Progress bar */}
          <div className="flex items-center gap-2">
            <div className="h-2 w-32 overflow-hidden rounded-full bg-muted/80">
              <div
                className="h-full rounded-full bg-primary shadow-sm transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <span className="text-xs text-muted-foreground">{progressPercent}%</span>
          </div>
        </div>
      )}

      {/* Toolbar */}
      {selectedProjectId && boardData && (
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setFilterOpen(!filterOpen)}
            className="flex items-center gap-1.5 rounded-full border border-border/70 bg-background/50 px-4 py-2 text-xs font-medium uppercase tracking-[0.16em] transition-colors hover:bg-accent/45"
          >
            <Filter className="w-3.5 h-3.5" />
            Filter
          </button>
          <div className="relative">
            <button
              onClick={() => setSortField(sortField ? null : 'priority')}
              className="flex items-center gap-1.5 rounded-full border border-border/70 bg-background/50 px-4 py-2 text-xs font-medium uppercase tracking-[0.16em] transition-colors hover:bg-accent/45"
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
              Sort{sortField ? `: ${sortField}` : ''}
            </button>
          </div>
          <button
            className="cursor-default flex items-center gap-1.5 rounded-full border border-border/70 bg-background/50 px-4 py-2 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground"
            title="Coming soon"
          >
            <Columns3 className="w-3.5 h-3.5" />
            Group by
          </button>
        </div>
      )}

      {/* Rate limit / error banners */}
      {refreshError?.type === 'rate_limit' && (
        <div className="flex items-start gap-3 rounded-[1.1rem] border border-accent/30 bg-accent/12 p-4 text-accent-foreground">
          <span className="text-lg">⏳</span>
          <div className="flex flex-col gap-1">
            <strong>Rate limit reached</strong>
            <p>{refreshError.retryAfter ? `Resets ${formatTimeUntil(refreshError.retryAfter)}.` : refreshError.message}</p>
          </div>
        </div>
      )}

      {isRateLimitLow && !refreshError && rateLimitInfo && (
        <div className="flex items-start gap-3 rounded-[1.1rem] border border-accent/30 bg-accent/12 p-4 text-accent-foreground">
          <span className="text-lg">⚠️</span>
          <div className="flex flex-col gap-1">
            <strong>Rate limit low</strong>
            <p>Only {rateLimitInfo.remaining} API requests remaining.</p>
          </div>
        </div>
      )}

      {refreshError && refreshError.type !== 'rate_limit' && (
        <div className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive">
          <span className="text-lg">⚠️</span>
          <div className="flex flex-col gap-1">
            <strong>Refresh failed</strong>
            <p>{refreshError.message}</p>
          </div>
        </div>
      )}

      {projectsError && (
        <div className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive">
          <span className="text-lg">⚠️</span>
          <div className="flex flex-col gap-1">
            <strong>Failed to load projects</strong>
            <p>{projectsError.message}</p>
            {(() => {
              if (!(projectsError instanceof ApiError)) return null;
              const reason = projectsError.error.details?.reason;
              return typeof reason === 'string' ? <p className="text-sm opacity-75">{reason}</p> : null;
            })()}
          </div>
        </div>
      )}

      {boardError && !boardLoading && (
        <div className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive">
          <span className="text-lg">⚠️</span>
          <div className="flex flex-col gap-1">
            <strong>Failed to load board data</strong>
            <p>{boardError.message}</p>
          </div>
          <button
            className="px-3 py-1.5 text-sm font-medium bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 transition-colors ml-auto"
            onClick={() => selectBoardProject(selectedProjectId!)}
          >
            Retry
          </button>
        </div>
      )}

      {/* Content area */}
      {!selectedProjectId && !projectsLoading && (
        <div className="celestial-panel flex flex-1 flex-col items-center justify-center gap-4 rounded-[1.4rem] border border-dashed border-border/80 p-8 text-center">
          <div className="text-4xl mb-2">📋</div>
          <h3 className="text-xl font-semibold">Select a project</h3>
          <p className="text-muted-foreground">Choose a project from the dropdown above to view its board</p>
        </div>
      )}

      {selectedProjectId && boardLoading && (
        <div className="flex flex-col items-center justify-center flex-1 gap-4">
          <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
          <p className="text-muted-foreground">Loading board...</p>
        </div>
      )}

      {selectedProjectId && !boardLoading && sortedBoardData && (
        <div className="flex flex-col flex-1 gap-6 overflow-hidden">
          <AgentConfigRow
            columns={sortedBoardData.columns}
            agentConfig={agentConfig}
            availableAgents={availableAgents}
            renderPresetSelector={
              <AgentPresetSelector
                columnNames={sortedBoardData.columns.map((c) => c.status.name)}
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

          <div className="flex flex-1 gap-6 overflow-hidden">
            {sortedBoardData.columns.every((col) => col.items.length === 0) ? (
              <div className="celestial-panel flex flex-1 flex-col items-center justify-center gap-4 rounded-[1.4rem] border border-dashed border-border/80 p-8 text-center">
                <div className="text-4xl mb-2">📭</div>
                <h3 className="text-xl font-semibold">No items yet</h3>
                <p className="text-muted-foreground">This project has no items. Add items in GitHub to see them here.</p>
              </div>
            ) : (
              <ProjectBoard boardData={sortedBoardData} onCardClick={handleCardClick} />
            )}
          </div>
        </div>
      )}

      {selectedItem && (
        <IssueDetailModal item={selectedItem} onClose={handleCloseModal} />
      )}
    </div>
  );
}
