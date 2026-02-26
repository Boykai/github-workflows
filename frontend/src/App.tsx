/**
 * Main application component.
 */

import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider, QueryErrorResetBoundary } from '@tanstack/react-query';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useAppTheme } from '@/hooks/useAppTheme';
import { useUserSettings } from '@/hooks/useSettings';
import { LoginButton } from '@/components/auth/LoginButton';
import { ProjectBoardPage } from '@/pages/ProjectBoardPage';
import { SettingsPage } from '@/pages/SettingsPage';
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
  const { settings: userSettings } = useUserSettings();
  const [activeView, setActiveView] = useState<'chat' | 'board' | 'settings'>('chat');

  // Apply default_view from user settings on first load (FR-014)
  useEffect(() => {
    if (userSettings?.display?.default_view) {
      setActiveView(userSettings.display.default_view);
    }
  }, [userSettings?.display?.default_view]);
  const {
    projects,
    selectedProject,
    selectProject,
  } = useProjects(user?.selected_project_id);

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
        <h1>Agent Projects</h1>
        <p>Manage your GitHub Projects with natural language</p>
        <LoginButton />
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-left">
          <h1>Agent Projects</h1>
          <nav className="header-nav">
            <button
              className={`header-nav-btn ${activeView === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveView('chat')}
            >
              Home
            </button>
            <button
              className={`header-nav-btn ${activeView === 'board' ? 'active' : ''}`}
              onClick={() => setActiveView('board')}
            >
              Project Board
            </button>
            <button
              className={`header-nav-btn ${activeView === 'settings' ? 'active' : ''}`}
              onClick={() => setActiveView('settings')}
            >
              Settings
            </button>
          </nav>
        </div>
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
        {activeView === 'settings' ? (
          <SettingsPage
            projects={projects.map((p) => ({ project_id: p.project_id, name: p.name }))}
            selectedProjectId={selectedProject?.project_id}
          />
        ) : activeView === 'board' ? (
          <ProjectBoardPage
            selectedProjectId={selectedProject?.project_id}
            onProjectSelect={selectProject}
          />
        ) : (
          <div className="homepage-hero">
            <h2>Create Your App Here</h2>
            <button className="homepage-cta-btn" onClick={() => setActiveView('board')}>
              Get Started
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary onReset={reset}>
            <AppContent />
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </QueryClientProvider>
  );
}
