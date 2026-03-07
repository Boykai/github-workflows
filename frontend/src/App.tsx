/**
 * Main application component.
 * Uses React Router for page-based navigation.
 */

import { QueryClient, QueryClientProvider, QueryErrorResetBoundary } from '@tanstack/react-query';
import { Route, RouterProvider, createBrowserRouter, createRoutesFromElements } from 'react-router-dom';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { ApiError } from '@/services/api';
import { AuthGate } from '@/layout/AuthGate';
import { AppLayout } from '@/layout/AppLayout';
import { AppPage } from '@/pages/AppPage';
import { ProjectsPage } from '@/pages/ProjectsPage';
import { AgentsPipelinePage } from '@/pages/AgentsPipelinePage';
import { AgentsPage } from '@/pages/AgentsPage';
import { ChoresPage } from '@/pages/ChoresPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { LoginPage } from '@/pages/LoginPage';
import { NotFoundPage } from '@/pages/NotFoundPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        if (error instanceof ApiError) {
          if (error.status === 401 || error.status === 403 || error.status === 404) {
            return false;
          }
          if (error.status === 429) {
            return false;
          }
        }
        return failureCount < 1;
      },
    },
  },
});

const router = createBrowserRouter(
  createRoutesFromElements(
    <>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<AuthGate><AppLayout /></AuthGate>}>
        <Route index element={<AppPage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="pipeline" element={<AgentsPipelinePage />} />
        <Route path="agents" element={<AgentsPage />} />
        <Route path="chores" element={<ChoresPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </>,
  ),
);

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary onReset={reset}>
            <RouterProvider router={router} />
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </QueryClientProvider>
  );
}
