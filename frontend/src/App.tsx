/**
 * Main application component.
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useChat } from '@/hooks/useChat';
import { useWorkflow } from '@/hooks/useWorkflow';
import { useAppTheme } from '@/hooks/useAppTheme';
import { LoginButton } from '@/components/auth/LoginButton';
import { ProjectSidebar } from '@/components/sidebar/ProjectSidebar';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { LocalTime } from '@/components/common/LocalTime';
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppContent() {
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const { isDarkMode, toggleTheme } = useAppTheme();
  const {
    projects,
    selectedProject,
    tasks,
    isLoading: projectsLoading,
    tasksLoading,
    selectProject,
    refreshTasks,
  } = useProjects(user?.selected_project_id);

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

  if (authLoading) {
    return (
      <div className="app-loading">
        <div className="spinner" />
        <p>Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="app-login">
        <h1>Welcome to Tech Connect 2026!</h1>
        <p>Manage your GitHub Projects with natural language</p>
        <LoginButton />
      </div>
    );
  }

  const handleConfirmProposal = async (proposalId: string) => {
    await confirmProposal(proposalId);
    // Refresh tasks after creating a new one
    refreshTasks();
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Welcome to Tech Connect 2026!</h1>
        <div className="header-actions">
          <LocalTime />
          <button 
            className="theme-toggle-btn"
            onClick={toggleTheme}
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>
          <LoginButton />
        </div>
      </header>

      <main className="app-main">
        <ProjectSidebar
          projects={projects}
          selectedProject={selectedProject}
          tasks={tasks}
          isLoading={projectsLoading}
          tasksLoading={tasksLoading}
          onProjectSelect={selectProject}
        />

        <section className="chat-section">
          {selectedProject ? (
            <ChatInterface
              messages={messages}
              pendingProposals={pendingProposals}
              pendingStatusChanges={pendingStatusChanges}
              pendingRecommendations={pendingRecommendations}
              isSending={isSending}
              onSendMessage={sendMessage}
              onConfirmProposal={handleConfirmProposal}
              onConfirmStatusChange={confirmStatusChange}
              onConfirmRecommendation={async (recommendationId) => {
                const result = await confirmRecommendation(recommendationId);
                removePendingRecommendation(recommendationId);
                refreshTasks();
                return result;
              }}
              onRejectProposal={rejectProposal}
              onRejectRecommendation={async (recommendationId) => {
                await rejectRecommendation(recommendationId);
                removePendingRecommendation(recommendationId);
              }}
              onNewChat={clearChat}
            />
          ) : (
            <div className="chat-placeholder">
              <p>Select a project from the sidebar to start chatting</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
