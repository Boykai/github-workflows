/**
 * Shared test utilities for React component tests.
 *
 * Provides `renderWithProviders()` — a drop-in replacement for RTL's `render`
 * that wraps the component tree in the same providers used by the production app.
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render as rtlRender, type RenderOptions } from '@testing-library/react';
import type { ReactElement, ReactNode } from 'react';
import { ConfirmationDialogProvider } from '@/hooks/useConfirmation';
import { TooltipProvider } from '@/components/ui/tooltip';

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
  { queryClient = createTestQueryClient(), ...options }: ExtendedRenderOptions = {}
) {
  function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={queryClient}>
        <ConfirmationDialogProvider>{children}</ConfirmationDialogProvider>
        <TooltipProvider delayDuration={0}>{children}</TooltipProvider>
      </QueryClientProvider>
    );
  }

  return {
    ...rtlRender(ui, { wrapper: Wrapper, ...options }),
    queryClient,
  };
}

// Re-export everything from RTL so tests can import from one place.
// Override `render` to always wrap with TooltipProvider so Radix tooltips work.
export {
  screen,
  waitFor,
  within,
  act,
  cleanup,
  fireEvent,
  waitForElementToBeRemoved,
  prettyDOM,
  queries,
  queryByAttribute,
  buildQueries,
} from '@testing-library/react';
export type { RenderResult } from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';

/**
 * Custom `render` that wraps the UI with `TooltipProvider` so any component
 * using `<Tooltip>` can be rendered without manually adding the provider.
 */
function tooltipAwareRender(ui: ReactElement, options?: RenderOptions) {
  const Wrapper = options?.wrapper;
  function TooltipWrapper({ children }: { children: ReactNode }) {
    const inner = <TooltipProvider delayDuration={0}>{children}</TooltipProvider>;
    return Wrapper ? <Wrapper>{inner}</Wrapper> : inner;
  }
  return rtlRender(ui, { ...options, wrapper: TooltipWrapper });
}
export { tooltipAwareRender as render };
