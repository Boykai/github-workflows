/**
 * Tests for McpSettings confirmation flow.
 *
 * Covers: confirmation dialog on MCP removal, cancel skips deletion,
 * and confirm triggers the delete mutation.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, userEvent, within } from '@/test/test-utils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { ConfirmationDialogProvider } from '@/hooks/useConfirmation';
import { McpSettings } from './McpSettings';

const mockUseMcpSettings = vi.fn();

vi.mock('@/hooks/useMcpSettings', () => ({
  useMcpSettings: (...args: unknown[]) => mockUseMcpSettings(...args),
}));

vi.mock('@/services/api', () => ({
  authApi: { login: vi.fn() },
  ApiError: class ApiError extends Error {
    status: number;
    error: unknown;
    constructor(message: string, status: number, error: unknown) {
      super(message);
      this.status = status;
      this.error = error;
    }
  },
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <ConfirmationDialogProvider>{children}</ConfirmationDialogProvider>
      </QueryClientProvider>
    );
  };
}

function defaultMcpHookState(overrides: Record<string, unknown> = {}) {
  return {
    mcps: [],
    isLoading: false,
    error: null,
    createMcp: vi.fn().mockResolvedValue({}),
    isCreating: false,
    createError: null,
    resetCreateError: vi.fn(),
    deleteMcp: vi.fn().mockResolvedValue({}),
    deletingId: null,
    deleteError: null,
    resetDeleteError: vi.fn(),
    authError: false,
    ...overrides,
  };
}

describe('McpSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows a confirmation dialog when clicking Remove on an MCP', async () => {
    const deleteMcp = vi.fn().mockResolvedValue({});
    mockUseMcpSettings.mockReturnValue(
      defaultMcpHookState({
        mcps: [{ id: 'mcp-1', name: 'Test Server', endpoint_url: 'https://example.com', is_active: true }],
        deleteMcp,
      })
    );

    render(<McpSettings />, { wrapper: createWrapper() });
    const user = userEvent.setup();

    // Click the Remove button
    await user.click(screen.getByRole('button', { name: 'Remove' }));

    // Confirmation dialog should appear
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
    expect(screen.getByText('Remove MCP Configuration')).toBeInTheDocument();
    expect(screen.getByText(/Remove "Test Server" from your MCP configurations/)).toBeInTheDocument();

    // Delete should not have been called yet
    expect(deleteMcp).not.toHaveBeenCalled();
  });

  it('deletes the MCP after confirming the dialog', async () => {
    const deleteMcp = vi.fn().mockResolvedValue({});
    mockUseMcpSettings.mockReturnValue(
      defaultMcpHookState({
        mcps: [{ id: 'mcp-1', name: 'My MCP', endpoint_url: 'https://example.com', is_active: true }],
        deleteMcp,
      })
    );

    render(<McpSettings />, { wrapper: createWrapper() });
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: 'Remove' }));

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Confirm the deletion via the dialog button
    const dialog = screen.getByRole('dialog');
    await user.click(within(dialog).getByRole('button', { name: 'Remove' }));

    await waitFor(() => {
      expect(deleteMcp).toHaveBeenCalledWith('mcp-1');
    });
  });

  it('does not delete the MCP when cancelling the confirmation dialog', async () => {
    const deleteMcp = vi.fn().mockResolvedValue({});
    mockUseMcpSettings.mockReturnValue(
      defaultMcpHookState({
        mcps: [{ id: 'mcp-2', name: 'Another MCP', endpoint_url: 'https://other.com', is_active: false }],
        deleteMcp,
      })
    );

    render(<McpSettings />, { wrapper: createWrapper() });
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: 'Remove' }));

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Cancel the removal
    await user.click(screen.getByText('Cancel'));

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
    expect(deleteMcp).not.toHaveBeenCalled();
  });
});
