/**
 * Main application component.
 */

import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useChat } from '@/hooks/useChat';
import { useWorkflow } from '@/hooks/useWorkflow';
import { useAppTheme } from '@/hooks/useAppTheme';
import { LoginButton } from '@/components/auth/LoginButton';
import { ProjectSidebar } from '@/components/sidebar/ProjectSidebar';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { ProjectBoardPage } from '@/components/project-board/ProjectBoardPage';
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
  const [currentPage, setCurrentPage] = useState<'chat' | 'project-board'>('chat');
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

  // Hash-based navigation
  useEffect(() => {
    const handleHashChange = () => {
      if (window.location.hash === '#/project-board') {
        setCurrentPage('project-board');
      } else {
        setCurrentPage('chat');
      }
    };
    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigateTo = (page: 'chat' | 'project-board') => {
    setCurrentPage(page);
    window.location.hash = page === 'project-board' ? '#/project-board' : '';
  };

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
        {currentPage === 'chat' && (
          <>
            <ProjectSidebar
              projects={projects}
              selectedProject={selectedProject}
              tasks={tasks}
              isLoading={projectsLoading}
              tasksLoading={tasksLoading}
              onProjectSelect={selectProject}
              onNavigate={navigateTo}
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
          </>
        )}

        {currentPage === 'project-board' && (
          <ProjectBoardPage onNavigateToChat={() => navigateTo('chat')} />
        )}
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
