/**
 * Accessibility test helpers for Vitest.
 *
 * Provides reusable utilities for running automated accessibility
 * assertions in component tests using axe-core via jest-axe.
 */

import { axe, toHaveNoViolations } from 'jest-axe';
import { renderWithProviders } from './test-utils';
import type { ReactElement } from 'react';
import type { RenderResult } from '@testing-library/react';

// Extend Vitest matchers with axe-core assertions
expect.extend(toHaveNoViolations);

/**
 * Run an axe-core accessibility audit on a rendered container.
 *
 * Usage:
 * ```ts
 * const { container } = renderWithProviders(<MyComponent />);
 * await expectNoA11yViolations(container);
 * ```
 */
export async function expectNoA11yViolations(container: HTMLElement): Promise<void> {
  const results = await axe(container);
  expect(results).toHaveNoViolations();
}

/**
 * Render a component with providers and immediately assert no
 * accessibility violations. Returns the render result for further assertions.
 *
 * Usage:
 * ```ts
 * const result = await renderAndCheckA11y(<MyComponent />);
 * expect(result.getByRole('button')).toBeInTheDocument();
 * ```
 */
export async function renderAndCheckA11y(
  ui: ReactElement
): Promise<RenderResult & { queryClient: import('@tanstack/react-query').QueryClient }> {
  const result = renderWithProviders(ui);
  await expectNoA11yViolations(result.container);
  return result;
}
