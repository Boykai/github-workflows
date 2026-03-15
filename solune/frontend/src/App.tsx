/**
 * Main application component.
 * Uses React Router for page-based navigation.
 */

import { Suspense, lazy } from 'react';
import { QueryClient, QueryClientProvider, QueryErrorResetBoundary } from '@tanstack/react-query';
import {
  Route,
  RouterProvider,
  createBrowserRouter,
  createRoutesFromElements,
} from 'react-router-dom';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { ConfirmationDialogProvider } from '@/hooks/useConfirmation';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ApiError } from '@/services/api';
import { AuthGate } from '@/layout/AuthGate';
import { AppLayout } from '@/layout/AppLayout';

const AppPage = lazy(() =>
  import('@/pages/AppPage').then((module) => ({ default: module.AppPage }))
);
const ProjectsPage = lazy(() =>
  import('@/pages/ProjectsPage').then((module) => ({ default: module.ProjectsPage }))
);
const AgentsPipelinePage = lazy(() =>
  import('@/pages/AgentsPipelinePage').then((module) => ({ default: module.AgentsPipelinePage }))
);
const AgentsPage = lazy(() =>
  import('@/pages/AgentsPage').then((module) => ({ default: module.AgentsPage }))
);
const ToolsPage = lazy(() =>
  import('@/pages/ToolsPage').then((module) => ({ default: module.ToolsPage }))
);
const ChoresPage = lazy(() =>
  import('@/pages/ChoresPage').then((module) => ({ default: module.ChoresPage }))
);
const SettingsPage = lazy(() =>
  import('@/pages/SettingsPage').then((module) => ({ default: module.SettingsPage }))
);
const LoginPage = lazy(() =>
  import('@/pages/LoginPage').then((module) => ({ default: module.LoginPage }))
);
const NotFoundPage = lazy(() =>
  import('@/pages/NotFoundPage').then((module) => ({ default: module.NotFoundPage }))
);
const AppsPage = lazy(() =>
  import('@/pages/AppsPage').then((module) => ({ default: module.AppsPage }))
);
const HelpPage = lazy(() =>
  import('@/pages/HelpPage').then((module) => ({ default: module.HelpPage }))
);

function RouteFallback() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center px-6 py-10">
      <CelestialLoader size="md" label="Loading page…" />
    </div>
  );
}

function withSuspense(element: React.ReactNode) {
  return <Suspense fallback={<RouteFallback />}>{element}</Suspense>;
}

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
      <Route path="/login" element={withSuspense(<LoginPage />)} />
      <Route
        element={
          <AuthGate>
            <AppLayout />
          </AuthGate>
        }
      >
        <Route index element={withSuspense(<AppPage />)} />
        <Route path="projects" element={withSuspense(<ProjectsPage />)} />
        <Route path="pipeline" element={withSuspense(<AgentsPipelinePage />)} />
        <Route path="agents" element={withSuspense(<AgentsPage />)} />
        <Route path="tools" element={withSuspense(<ToolsPage />)} />
        <Route path="chores" element={withSuspense(<ChoresPage />)} />
        <Route path="settings" element={withSuspense(<SettingsPage />)} />
        <Route path="apps" element={withSuspense(<AppsPage />)} />
        <Route path="apps/:appName" element={withSuspense(<AppsPage />)} />
        <Route path="help" element={withSuspense(<HelpPage />)} />
        <Route path="*" element={withSuspense(<NotFoundPage />)} />
      </Route>
    </>
  )
);

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfirmationDialogProvider>
        <TooltipProvider delayDuration={300} skipDelayDuration={300}>
          <QueryErrorResetBoundary>
            {({ reset }) => (
              <ErrorBoundary onReset={reset}>
                <RouterProvider router={router} />
              </ErrorBoundary>
            )}
          </QueryErrorResetBoundary>
        </TooltipProvider>
      </ConfirmationDialogProvider>
    </QueryClientProvider>
  );
}
