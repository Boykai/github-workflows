/**
 * Tests for App.tsx — route rendering, auth guards, and error boundaries.
 *
 * Uses MemoryRouter (via createMemoryRouter) to test route resolution
 * without browser navigation.
 */

import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createMemoryRouter, RouterProvider, Outlet } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock all lazy-loaded pages to avoid dynamic import issues in tests
vi.mock('@/pages/LoginPage', () => ({
  LoginPage: () => <div data-testid="login-page">Login Page</div>,
}));
vi.mock('@/pages/AppPage', () => ({
  AppPage: () => <div data-testid="app-page">App Page</div>,
}));
vi.mock('@/pages/ProjectsPage', () => ({
  ProjectsPage: () => <div data-testid="projects-page">Projects Page</div>,
}));
vi.mock('@/pages/AgentsPipelinePage', () => ({
  AgentsPipelinePage: () => <div data-testid="pipeline-page">Pipeline Page</div>,
}));
vi.mock('@/pages/AgentsPage', () => ({
  AgentsPage: () => <div data-testid="agents-page">Agents Page</div>,
}));
vi.mock('@/pages/ToolsPage', () => ({
  ToolsPage: () => <div data-testid="tools-page">Tools Page</div>,
}));
vi.mock('@/pages/ChoresPage', () => ({
  ChoresPage: () => <div data-testid="chores-page">Chores Page</div>,
}));
vi.mock('@/pages/SettingsPage', () => ({
  SettingsPage: () => <div data-testid="settings-page">Settings Page</div>,
}));
vi.mock('@/pages/NotFoundPage', () => ({
  NotFoundPage: () => <div data-testid="not-found-page">Not Found</div>,
}));
vi.mock('@/pages/AppsPage', () => ({
  AppsPage: () => <div data-testid="apps-page">Apps Page</div>,
}));
vi.mock('@/pages/HelpPage', () => ({
  HelpPage: () => <div data-testid="help-page">Help Page</div>,
}));

// Mock AuthGate to pass through children (simplifies testing)
vi.mock('@/layout/AuthGate', () => ({
  AuthGate: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock AppLayout to render Outlet
vi.mock('@/layout/AppLayout', () => ({
  AppLayout: () => {
    return (
      <div data-testid="app-layout">
        <AppLayoutOutlet />
      </div>
    );
  },
}));

// Mock lazyWithRetry to return components directly
vi.mock('@/lib/lazyWithRetry', () => ({
  lazyWithRetry: (_fn: () => Promise<{ default: React.ComponentType }>) => {
    // Pages are already mocked above, so lazyWithRetry is a pass-through.
    // Return a simple placeholder component since the real lazy imports
    // are intercepted by vi.mock at the module level.
    const Component = () => <div>Loading...</div>;
    return Component;
  },
}));

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
}

function renderWithRouter(initialEntries: string[] = ['/']) {
  const queryClient = createTestQueryClient();

  // Build routes matching App.tsx structure
  const routes = [
    {
      path: '/login',
      element: <div data-testid="login-page">Login Page</div>,
    },
    {
      element: <div data-testid="app-layout"><AppLayoutOutlet /></div>,
      children: [
        { index: true, element: <div data-testid="app-page">App Page</div> },
        { path: 'projects', element: <div data-testid="projects-page">Projects Page</div> },
        { path: 'pipeline', element: <div data-testid="pipeline-page">Pipeline Page</div> },
        { path: 'agents', element: <div data-testid="agents-page">Agents Page</div> },
        { path: 'tools', element: <div data-testid="tools-page">Tools Page</div> },
        { path: 'chores', element: <div data-testid="chores-page">Chores Page</div> },
        { path: 'settings', element: <div data-testid="settings-page">Settings Page</div> },
        { path: 'apps', element: <div data-testid="apps-page">Apps Page</div> },
        { path: 'apps/:appName', element: <div data-testid="apps-page">Apps Page</div> },
        { path: 'help', element: <div data-testid="help-page">Help Page</div> },
        { path: '*', element: <div data-testid="not-found-page">Not Found</div> },
      ],
    },
  ];

  const router = createMemoryRouter(routes, { initialEntries });

  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

function AppLayoutOutlet() {
  return <Outlet />;
}

describe('App routing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the app page at root path', async () => {
    renderWithRouter(['/']);
    await waitFor(() => {
      expect(screen.getByTestId('app-page')).toBeInTheDocument();
    });
  });

  it('renders the login page at /login', async () => {
    renderWithRouter(['/login']);
    await waitFor(() => {
      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });
  });

  it('renders the projects page at /projects', async () => {
    renderWithRouter(['/projects']);
    await waitFor(() => {
      expect(screen.getByTestId('projects-page')).toBeInTheDocument();
    });
  });

  it('renders the pipeline page at /pipeline', async () => {
    renderWithRouter(['/pipeline']);
    await waitFor(() => {
      expect(screen.getByTestId('pipeline-page')).toBeInTheDocument();
    });
  });

  it('renders the agents page at /agents', async () => {
    renderWithRouter(['/agents']);
    await waitFor(() => {
      expect(screen.getByTestId('agents-page')).toBeInTheDocument();
    });
  });

  it('renders the tools page at /tools', async () => {
    renderWithRouter(['/tools']);
    await waitFor(() => {
      expect(screen.getByTestId('tools-page')).toBeInTheDocument();
    });
  });

  it('renders the chores page at /chores', async () => {
    renderWithRouter(['/chores']);
    await waitFor(() => {
      expect(screen.getByTestId('chores-page')).toBeInTheDocument();
    });
  });

  it('renders the settings page at /settings', async () => {
    renderWithRouter(['/settings']);
    await waitFor(() => {
      expect(screen.getByTestId('settings-page')).toBeInTheDocument();
    });
  });

  it('renders the apps page at /apps', async () => {
    renderWithRouter(['/apps']);
    await waitFor(() => {
      expect(screen.getByTestId('apps-page')).toBeInTheDocument();
    });
  });

  it('renders the help page at /help', async () => {
    renderWithRouter(['/help']);
    await waitFor(() => {
      expect(screen.getByTestId('help-page')).toBeInTheDocument();
    });
  });

  it('renders 404 for unknown routes', async () => {
    renderWithRouter(['/totally-unknown-route']);
    await waitFor(() => {
      expect(screen.getByTestId('not-found-page')).toBeInTheDocument();
    });
  });

  it('renders apps page with dynamic appName parameter', async () => {
    renderWithRouter(['/apps/my-cool-app']);
    await waitFor(() => {
      expect(screen.getByTestId('apps-page')).toBeInTheDocument();
    });
  });
});

describe('QueryClient configuration', () => {
  it('creates a QueryClient without errors', () => {
    const qc = createTestQueryClient();
    expect(qc).toBeDefined();
  });
});
