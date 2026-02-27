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
import { Button } from '@/components/ui/button';

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

  // Derive initial view from URL hash so refresh stays on the current page.
  const getViewFromHash = (): 'chat' | 'board' | 'settings' => {
    const hash = window.location.hash.replace('#', '');
    if (hash === 'board' || hash === 'settings') return hash;
    return 'chat';
  };

  const [activeView, setActiveView] = useState<'chat' | 'board' | 'settings'>(getViewFromHash);

  // Keep URL hash in sync when view changes
  const changeView = (view: 'chat' | 'board' | 'settings') => {
    setActiveView(view);
    window.location.hash = view === 'chat' ? '' : view;
  };

  // Handle browser back/forward
  useEffect(() => {
    const onHashChange = () => setActiveView(getViewFromHash());
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  // Apply default_view from user settings only when no hash is present (FR-014)
  useEffect(() => {
    if (!window.location.hash && userSettings?.display?.default_view) {
      changeView(userSettings.display.default_view);
    }
  }, [userSettings?.display?.default_view]);
  const {
    projects,
    selectedProject,
    selectProject,
  } = useProjects(user?.selected_project_id);

  if (authLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4">
        <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4 text-center">
        <h1 className="text-4xl font-bold tracking-tight">Agent Projects</h1>
        <p className="text-muted-foreground mb-4">Manage your GitHub Projects with natural language</p>
        <LoginButton />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <header className="flex items-center justify-between px-6 py-3 bg-background border-b border-border">
        <div className="flex items-center gap-6">
          <h1 className="text-lg font-semibold tracking-tight">Agent Projects</h1>
          <nav className="flex gap-1">
            <Button
              variant={activeView === 'chat' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => changeView('chat')}
            >
              Home
            </Button>
            <Button
              variant={activeView === 'board' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => changeView('board')}
            >
              Project Board
            </Button>
            <Button
              variant={activeView === 'settings' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => changeView('settings')}
            >
              Settings
            </Button>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <Button 
            variant="outline"
            size="icon"
            onClick={toggleTheme}
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </Button>
          <LoginButton />
        </div>
      </header>

      <main className="flex flex-1 overflow-hidden">
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
          <div className="flex-1 flex flex-col items-center justify-center text-center gap-6">
            <h2 className="text-4xl font-bold tracking-tight">Create Your App Here</h2>
            <Button 
              size="lg"
              onClick={() => changeView('board')}
            >
              Get Started
            </Button>
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
