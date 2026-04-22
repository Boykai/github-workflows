/**
 * Main application component.
 */

import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useChat } from '@/hooks/useChat';
import { useWorkflow } from '@/hooks/useWorkflow';
import { useAppTheme, type ThemeMode } from '@/hooks/useAppTheme';
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
    isRetroMode,
    themeMode,
    isPreviewingRetro,
    toggleTheme,
    setTheme,
    previewRetroTheme,
    cancelRetroPreview,
  } = useAppTheme();
  const [showThemeSettings, setShowThemeSettings] = useState(false);
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
          <button
            className="theme-toggle-btn"
            onClick={toggleTheme}
            aria-label={
              themeMode === 'light'
                ? 'Switch to dark mode'
                : themeMode === 'dark'
                  ? 'Switch to retro mode'
                  : 'Switch to light mode'
            }
            title={
              themeMode === 'light'
                ? 'Dark mode'
                : themeMode === 'dark'
                  ? 'Retro mode'
                  : 'Light mode'
            }
          >
            {themeMode === 'light' ? '🌙' : themeMode === 'dark' ? '🕹️' : '☀️'}
          </button>
          <div className="theme-settings-wrapper">
            <button
              className="theme-settings-btn"
              onClick={() => {
                setShowThemeSettings((v) => !v);
                if (isPreviewingRetro) cancelRetroPreview();
              }}
              aria-label="Theme settings"
              aria-expanded={showThemeSettings}
            >
              ⚙️
            </button>
            {showThemeSettings && (
              <div className="theme-settings-panel" role="dialog" aria-label="Theme settings">
                <div className="theme-settings-header">
                  <span className="theme-settings-title">Theme Settings</span>
                  <button
                    className="theme-settings-close"
                    onClick={() => {
                      setShowThemeSettings(false);
                      cancelRetroPreview();
                    }}
                    aria-label="Close theme settings"
                  >
                    ✕
                  </button>
                </div>
                <div className="theme-options">
                  {(['light', 'dark', 'retro'] as ThemeMode[]).map((mode) => (
                    <div key={mode} className="theme-option">
                      <button
                        className={`theme-option-btn${themeMode === mode ? ' active' : ''}`}
                        onClick={() => {
                          setTheme(mode);
                          setShowThemeSettings(false);
                        }}
                        aria-pressed={themeMode === mode}
                      >
                        <span className="theme-option-icon">
                          {mode === 'light' ? '☀️' : mode === 'dark' ? '🌙' : '🕹️'}
                        </span>
                        <span className="theme-option-label">
                          {mode === 'light' ? 'Light' : mode === 'dark' ? 'Dark' : 'Retro 90s'}
                        </span>
                        {themeMode === mode && (
                          <span className="theme-option-active-badge">Active</span>
                        )}
                      </button>
                      {mode === 'retro' && themeMode !== 'retro' && (
                        <button
                          className={`theme-preview-btn${isPreviewingRetro ? ' previewing' : ''}`}
                          onMouseEnter={previewRetroTheme}
                          onMouseLeave={cancelRetroPreview}
                          onClick={() => {
                            setTheme('retro');
                            setShowThemeSettings(false);
                          }}
                          aria-label="Preview retro theme"
                        >
                          {isPreviewingRetro ? 'Apply' : 'Preview'}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                {isRetroMode && (
                  <p className="theme-settings-note">
                    🕹️ Retro 90s theme active! Totally radical.
                  </p>
                )}
              </div>
            )}
          </div>
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
