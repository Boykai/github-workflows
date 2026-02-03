/**
 * Main application component.
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useChat } from '@/hooks/useChat';
import { useWorkflow } from '@/hooks/useWorkflow';
import { LoginButton } from '@/components/auth/LoginButton';
import { ProjectSidebar } from '@/components/sidebar/ProjectSidebar';
import { ChatInterface } from '@/components/chat/ChatInterface';
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
        <h1>GitHub Projects Chat</h1>
        <p>Manage your GitHub Projects with natural language</p>
        <a 
          href="https://www.youtube.com/@ntfaqguy" 
          target="_blank" 
          rel="noopener noreferrer"
          className="youtube-logo-link youtube-logo-login"
          aria-label="Visit John Savill's YouTube channel"
        >
          <img 
            src="/john-savill-youtube-logo.svg" 
            alt="John Savill's Technical Training YouTube Channel" 
            className="youtube-logo"
          />
        </a>
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
        <div className="header-left">
          <h1>GitHub Projects Chat</h1>
          <a 
            href="https://www.youtube.com/@ntfaqguy" 
            target="_blank" 
            rel="noopener noreferrer"
            className="youtube-logo-link"
            aria-label="Visit John Savill's YouTube channel"
          >
            <img 
              src="/john-savill-youtube-logo.svg" 
              alt="John Savill's Technical Training YouTube Channel" 
              className="youtube-logo"
            />
          </a>
        </div>
        <LoginButton />
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
