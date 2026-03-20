/**
 * Main application component.
 * Uses React Router for page-based navigation.
 */

import { Suspense } from 'react';
import { QueryClient, QueryClientProvider, QueryErrorResetBoundary } from '@tanstack/react-query';
import {
  Route,
  RouterProvider,
  createBrowserRouter,
  createRoutesFromElements,
  useRouteError,
} from 'react-router-dom';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { lazyWithRetry } from '@/lib/lazyWithRetry';
import { ConfirmationDialogProvider } from '@/hooks/useConfirmation';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ApiError } from '@/services/api';
import { AuthGate } from '@/layout/AuthGate';
import { AppLayout } from '@/layout/AppLayout';

const AppPage = lazyWithRetry(() =>
  import('@/pages/AppPage').then((module) => ({ default: module.AppPage }))
);
const ProjectsPage = lazyWithRetry(() =>
  import('@/pages/ProjectsPage').then((module) => ({ default: module.ProjectsPage }))
);
const AgentsPipelinePage = lazyWithRetry(() =>
  import('@/pages/AgentsPipelinePage').then((module) => ({ default: module.AgentsPipelinePage }))
);
const AgentsPage = lazyWithRetry(() =>
  import('@/pages/AgentsPage').then((module) => ({ default: module.AgentsPage }))
);
const ToolsPage = lazyWithRetry(() =>
  import('@/pages/ToolsPage').then((module) => ({ default: module.ToolsPage }))
);
const ChoresPage = lazyWithRetry(() =>
  import('@/pages/ChoresPage').then((module) => ({ default: module.ChoresPage }))
);
const SettingsPage = lazyWithRetry(() =>
  import('@/pages/SettingsPage').then((module) => ({ default: module.SettingsPage }))
);
const LoginPage = lazyWithRetry(() =>
  import('@/pages/LoginPage').then((module) => ({ default: module.LoginPage }))
);
const NotFoundPage = lazyWithRetry(() =>
  import('@/pages/NotFoundPage').then((module) => ({ default: module.NotFoundPage }))
);
const AppsPage = lazyWithRetry(() =>
  import('@/pages/AppsPage').then((module) => ({ default: module.AppsPage }))
);
const ActivityPage = lazyWithRetry(() =>
  import('@/pages/ActivityPage').then((module) => ({ default: module.ActivityPage }))
);
const HelpPage = lazyWithRetry(() =>
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

/**
 * Route-level error element for React Router.
 * Catches errors like stale dynamic imports that slip past lazyWithRetry.
 */
function RouteErrorFallback() {
  const error = useRouteError();
  const message = error instanceof Error ? error.message : 'An unexpected error occurred';
  const isChunkError = message.includes('dynamically imported module') ||
    message.includes('Failed to fetch') ||
    message.includes('Loading chunk');

  return (
    <div
      role="alert"
      className="starfield flex h-full min-h-[60vh] flex-col items-center justify-center gap-4 p-8 text-center"
    >
      <span className="text-6xl font-bold text-destructive/30 celestial-float">!</span>
      <h2 className="text-3xl font-display font-medium tracking-[0.06em] celestial-fade-in">
        {isChunkError ? 'App updated — reloading' : 'Something went wrong'}
      </h2>
      <pre className="max-w-lg rounded-lg bg-muted/50 px-4 py-3 text-sm text-destructive whitespace-pre-wrap">
        {message}
      </pre>
      <button
        type="button"
        onClick={() => window.location.reload()}
        className="celestial-focus mt-2 rounded-full bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground shadow-sm transition-all hover:-translate-y-0.5 hover:bg-primary/90 hover:shadow-md"
      >
        Reload
      </button>
    </div>
  );
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
      <Route path="/login" element={withSuspense(<LoginPage />)} errorElement={<RouteErrorFallback />} />
      <Route
        element={
          <AuthGate>
            <AppLayout />
          </AuthGate>
        }
        errorElement={<RouteErrorFallback />}
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
        <Route path="activity" element={withSuspense(<ActivityPage />)} />
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
