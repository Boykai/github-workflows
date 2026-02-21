/**
 * Shared test utilities for React component tests.
 *
 * Provides `renderWithProviders()` — a drop-in replacement for RTL's `render`
 * that wraps the component tree in the same providers used by the production app.
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, type RenderOptions } from '@testing-library/react';
import type { ReactElement, ReactNode } from 'react';

/**
 * Create a fresh QueryClient configured for tests:
 * - no retries (tests should fail fast)
 * - no refetch on window focus
 * - gcTime = Infinity so cached data survives the test
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        refetchOnWindowFocus: false,
        gcTime: Infinity,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

interface WrapperProps {
  children: ReactNode;
}

interface ExtendedRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
}

/**
 * Render a React element wrapped in `QueryClientProvider`.
 *
 * Usage:
 * ```ts
 * const { getByText } = renderWithProviders(<MyComponent />);
 * ```
 */
export function renderWithProviders(
  ui: ReactElement,
  { queryClient = createTestQueryClient(), ...options }: ExtendedRenderOptions = {},
) {
  function Wrapper({ children }: WrapperProps) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...options }),
    queryClient,
  };
}

// Re-export everything from RTL so tests can import from one place.
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
