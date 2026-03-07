/**
 * AppLayout — main authenticated layout with Sidebar, TopBar, and page content via Outlet.
 * ChatPopup is rendered globally here so it persists across route navigation.
 */

import { Outlet } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useAppTheme } from '@/hooks/useAppTheme';
import { useChat } from '@/hooks/useChat';
import { useWorkflow } from '@/hooks/useWorkflow';
import { useSignalBanners, useDismissBanner } from '@/hooks/useSettings';
import { useSidebarState } from '@/hooks/useSidebarState';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useRecentParentIssues } from '@/hooks/useRecentParentIssues';
import { useNotifications } from '@/hooks/useNotifications';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { ChatPopup } from '@/components/chat/ChatPopup';

/** Dismissible Signal conflict banner bar. */
function SignalBannerBar() {
  const { banners } = useSignalBanners();
  const { dismissBanner, isPending } = useDismissBanner();

  if (banners.length === 0) return null;

  return (
    <div className="w-full border-b border-accent bg-accent/10 text-accent-foreground dark:bg-accent/20 dark:text-accent-foreground">
      {banners.map((b) => (
        <div key={b.id} className="flex items-center gap-2 px-4 py-2 text-sm">
          <span className="text-lg">⚠️</span>
          <span className="flex-1">{b.message}</span>
          <button
            className="ml-2 inline-flex h-6 w-6 items-center justify-center rounded-full border border-accent/50 text-xs font-medium text-accent-foreground hover:bg-accent/20 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50 dark:border-accent/40 dark:text-accent-foreground dark:hover:bg-accent/30"
            onClick={() => dismissBanner(b.id)}
            disabled={isPending}
            type="button"
            aria-label="Dismiss Signal banner"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}

export function AppLayout() {
  const { user } = useAuth();
  const { isDarkMode, toggleTheme } = useAppTheme();
  const { isCollapsed, toggle: toggleSidebar } = useSidebarState();
  const {
    selectedProject,
    projects,
    isLoading: projectsLoading,
    selectProject,
  } = useProjects(user?.selected_project_id);

  // Board data for recent interactions
  const { boardData } = useProjectBoard({ selectedProjectId: selectedProject?.project_id ?? null });
  const recentInteractions = useRecentParentIssues(boardData);
  const { notifications, unreadCount, markAllRead } = useNotifications();

  // Chat hooks — global so chat persists across navigation
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

  return (
    <div className="celestial-shell starfield relative flex h-screen overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none absolute inset-0 opacity-80">
        <div className="celestial-orbit left-[18%] top-[-28%] h-[30rem] w-[30rem]" />
        <div className="celestial-orbit bottom-[-22%] right-[-6%] h-[24rem] w-[24rem] border-primary/20" />
        <div className="absolute left-[22%] top-10 h-3 w-3 rounded-full bg-primary/45 blur-[1px]" />
        <div className="absolute bottom-20 right-[18%] h-2.5 w-2.5 rounded-full bg-primary/55" />
      </div>

      <Sidebar
        isCollapsed={isCollapsed}
        onToggle={toggleSidebar}
        selectedProject={selectedProject ? {
          project_id: selectedProject.project_id,
          name: selectedProject.name,
          owner_login: selectedProject.owner_login,
        } : undefined}
        recentInteractions={recentInteractions}
        projects={projects}
        projectsLoading={projectsLoading}
        onSelectProject={selectProject}
      />
      <div className="relative z-10 flex flex-1 flex-col overflow-hidden">
        <TopBar
          isDarkMode={isDarkMode}
          onToggleTheme={toggleTheme}
          user={user ? { login: user.github_username, avatar_url: user.github_avatar_url } : undefined}
          notifications={notifications}
          unreadCount={unreadCount}
          onMarkAllRead={markAllRead}
        />
        <SignalBannerBar />
        <main className="relative flex-1 overflow-auto px-2 pb-2">
          <Outlet />
        </main>
      </div>

      {/* Global ChatPopup */}
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
