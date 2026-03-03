/**
 * ProjectBoardPage component - main page with project selector and board view.
 */

import { useState } from 'react';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useRealTimeSync } from '@/hooks/useRealTimeSync';
import { useBoardRefresh } from '@/hooks/useBoardRefresh';
import { useChat } from '@/hooks/useChat';
import { useWorkflow } from '@/hooks/useWorkflow';
import { ProjectBoard } from '@/components/board/ProjectBoard';
import { IssueDetailModal } from '@/components/board/IssueDetailModal';
import { AgentConfigRow } from '@/components/board/AgentConfigRow';
import { AddAgentPopover } from '@/components/board/AddAgentPopover';
import { AgentPresetSelector } from '@/components/board/AgentPresetSelector';
import { RefreshButton } from '@/components/board/RefreshButton';
import { ChatPopup } from '@/components/chat/ChatPopup';
import { useAgentConfig, useAvailableAgents } from '@/hooks/useAgentConfig';
import { formatTimeAgo, formatTimeUntil } from '@/utils/formatTime';
import { ChoresPanel } from '@/components/chores/ChoresPanel';
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

  // Board refresh orchestration: manual refresh, auto-refresh, rate limit tracking
  const {
    refresh,
    isRefreshing,
    error: refreshError,
    rateLimitInfo,
    isRateLimitLow,
    resetTimer,
  } = useBoardRefresh({ projectId: selectedProjectId, boardData });

  // Real-time sync: WebSocket with polling fallback — drives board auto-refresh
  const { status: syncStatus, lastUpdate: syncLastUpdate } = useRealTimeSync(selectedProjectId, {
    onRefreshTriggered: resetTimer,
  });

  // Chat hooks (moved from App.tsx so chat API calls only fire on the board page)
  const {
    messages,
    pendingProposals,
    pendingStatusChanges,
    pendingRecommendations,
    isSending,
    sendMessage,
    confirmProposal,
    confirmStatusChange,
    rejectProposal,
    removePendingRecommendation,
    clearChat,
  } = useChat();

  const {
    confirmRecommendation,
    rejectRecommendation,
  } = useWorkflow();

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

  // Derive repository info for cleanup button from the first board item with a repository
  const cleanupRepo = selectedProjectId && boardData
    ? boardData.columns.flatMap(c => c.items).find(i => i.repository)?.repository
    : undefined;

  // Cleanup repo info to pass to ChoresPanel
  const cleanupOwner = cleanupRepo?.owner;
  const cleanupRepoName = cleanupRepo?.name;

  return (
    <div className="flex flex-col h-full p-6 gap-6 overflow-hidden">
      {/* Page Header */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold tracking-tight">Project Board</h2>

          {/* Project Selector */}
          <select
            className="flex h-9 w-[250px] items-center justify-between rounded-md border border-input bg-background text-foreground px-3 py-2 text-sm shadow-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
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
          {/* Sync status */}
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

          {/* Manual refresh button */}
          {selectedProjectId && (
            <RefreshButton
              onRefresh={refresh}
              isRefreshing={isRefreshing || (isFetching && !boardLoading)}
            />
          )}

          {/* Last updated */}
          {(lastUpdated || syncLastUpdate) && (
            <span className="text-xs">
              Updated {formatTimeAgo(syncLastUpdate ?? lastUpdated!)}
            </span>
          )}
        </div>
      </div>

      {/* Rate limit warning banner */}
      {refreshError?.type === 'rate_limit' && (
        <div className="flex items-start gap-3 p-4 rounded-md bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border border-yellow-500/20">
          <span className="text-lg">⏳</span>
          <div className="flex flex-col gap-1">
            <strong>Rate limit reached</strong>
            <p>
              {refreshError.retryAfter
                ? `Resets ${formatTimeUntil(refreshError.retryAfter)}.`
                : refreshError.message}
            </p>
          </div>
        </div>
      )}

      {/* Low rate limit preemptive warning */}
      {isRateLimitLow && !refreshError && rateLimitInfo && (
        <div className="flex items-start gap-3 p-4 rounded-md bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border border-yellow-500/20">
          <span className="text-lg">⚠️</span>
          <div className="flex flex-col gap-1">
            <strong>Rate limit low</strong>
            <p>Only {rateLimitInfo.remaining} API requests remaining.</p>
          </div>
        </div>
      )}

      {/* Non-rate-limit refresh error banner */}
      {refreshError && refreshError.type !== 'rate_limit' && (
        <div className="flex items-start gap-3 p-4 rounded-md bg-destructive/10 text-destructive border border-destructive/20">
          <span className="text-lg">⚠️</span>
          <div className="flex flex-col gap-1">
            <strong>Refresh failed</strong>
            <p>{refreshError.message}</p>
          </div>
        </div>
      )}

      {/* Error states */}
      {projectsError && (
        <div className="flex items-start gap-3 p-4 rounded-md bg-destructive/10 text-destructive border border-destructive/20">
          <span className="text-lg">⚠️</span>
          <div className="flex flex-col gap-1">
            <strong>Failed to load projects</strong>
            <p>{projectsError.message}</p>
          </div>
        </div>
      )}

      {boardError && !boardLoading && (
        <div className="flex items-start gap-3 p-4 rounded-md bg-destructive/10 text-destructive border border-destructive/20">
          <span className="text-lg">⚠️</span>
          <div className="flex flex-col gap-1">
            <strong>Failed to load board data</strong>
            <p>{boardError.message}</p>
          </div>
          <button
            className="px-3 py-1.5 text-sm font-medium bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 transition-colors ml-auto"
            onClick={() => selectProject(selectedProjectId!)}
          >
            Retry
          </button>
        </div>
      )}

      {/* Content area */}
      {!selectedProjectId && !projectsLoading && (
        <div className="flex flex-col items-center justify-center flex-1 gap-4 text-center p-8 border-2 border-dashed border-border rounded-lg bg-muted/10">
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

      {selectedProjectId && !boardLoading && boardData && (
        <div className="flex flex-col flex-1 gap-6 overflow-hidden">
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

          <div className="flex flex-1 gap-6 overflow-hidden">
            {boardData.columns.every((col) => col.items.length === 0) ? (
              <div className="flex flex-col items-center justify-center flex-1 gap-4 text-center p-8 border-2 border-dashed border-border rounded-lg bg-muted/10">
                <div className="text-4xl mb-2">📭</div>
                <h3 className="text-xl font-semibold">No items yet</h3>
                <p className="text-muted-foreground">This project has no items. Add items in GitHub to see them here.</p>
              </div>
            ) : (
              <ProjectBoard boardData={boardData} onCardClick={handleCardClick} />
            )}

            {/* Chores Panel — right side of board */}
            <ChoresPanel
              projectId={selectedProjectId}
              cleanupOwner={cleanupOwner}
              cleanupRepo={cleanupRepoName}
            />
          </div>
        </div>
      )}

      {/* Detail Modal (US2) */}
      {selectedItem && (
        <IssueDetailModal item={selectedItem} onClose={handleCloseModal} />
      )}

      {/* Chat Pop-Up Module */}
      <ChatPopup
        messages={messages}
        pendingProposals={pendingProposals}
        pendingStatusChanges={pendingStatusChanges}
        pendingRecommendations={pendingRecommendations}
        isSending={isSending}
        onSendMessage={sendMessage}
        onConfirmProposal={async (proposalId) => {
          await confirmProposal(proposalId);
        }}
        onConfirmStatusChange={confirmStatusChange}
        onConfirmRecommendation={async (recommendationId) => {
          const result = await confirmRecommendation(recommendationId);
          if (result.success) {
            removePendingRecommendation(recommendationId);
          }
          return result;
        }}
        onRejectProposal={rejectProposal}
        onRejectRecommendation={async (recommendationId) => {
          await rejectRecommendation(recommendationId);
          removePendingRecommendation(recommendationId);
        }}
        onNewChat={clearChat}
      />
    </div>
  );
}
