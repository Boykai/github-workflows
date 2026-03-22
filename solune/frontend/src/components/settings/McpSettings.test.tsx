import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { McpSettings } from './McpSettings';
import type { McpConfiguration } from '@/types';

// ── Mocks ──

const mockUseMcpSettings = vi.fn();

vi.mock('@/hooks/useMcpSettings', () => ({
  useMcpSettings: () => mockUseMcpSettings(),
}));

vi.mock('@/services/api', () => ({
  authApi: { login: vi.fn() },
  ApiError: class ApiError extends Error {
    status: number;
    error: unknown;
    constructor(message: string, status: number, error?: unknown) {
      super(message);
      this.status = status;
      this.error = error;
    }
  },
}));

// ── Helpers ──

function createMcp(overrides: Partial<McpConfiguration> = {}): McpConfiguration {
  return {
    id: 'mcp-1',
    name: 'Test MCP',
    endpoint_url: 'https://example.com/mcp',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

function defaultHookReturn(overrides = {}) {
  return {
    mcps: [] as McpConfiguration[],
    count: 0,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
    createMcp: vi.fn(),
    isCreating: false,
    createError: null,
    resetCreateError: vi.fn(),
    deleteMcp: vi.fn(),
    deletingId: null,
    deleteError: null,
    resetDeleteError: vi.fn(),
    authError: false,
    ...overrides,
  };
}

// ── Tests ──

describe('McpSettings', () => {
  beforeEach(() => {
    mockUseMcpSettings.mockReturnValue(defaultHookReturn());
  });

  it('renders the MCP list with configured servers', () => {
    mockUseMcpSettings.mockReturnValue(
      defaultHookReturn({
        mcps: [
          createMcp({ id: 'mcp-1', name: 'Server Alpha' }),
          createMcp({ id: 'mcp-2', name: 'Server Beta' }),
        ],
        count: 2,
      })
    );

    render(<McpSettings />);

    expect(screen.getByText('Server Alpha')).toBeInTheDocument();
    expect(screen.getByText('Server Beta')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    mockUseMcpSettings.mockReturnValue(
      defaultHookReturn({ isLoading: true })
    );

    render(<McpSettings />);

    expect(screen.getByText(/loading mcp configurations/i)).toBeInTheDocument();
  });

  it('shows error state when loading fails', () => {
    mockUseMcpSettings.mockReturnValue(
      defaultHookReturn({ error: new Error('Network error') })
    );

    render(<McpSettings />);

    expect(screen.getByText(/failed to load mcp configurations/i)).toBeInTheDocument();
  });

  it('shows auth error with Sign In button', () => {
    mockUseMcpSettings.mockReturnValue(
      defaultHookReturn({ authError: true })
    );

    render(<McpSettings />);

    expect(screen.getByText(/session has expired/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('renders the Add New MCP form', () => {
    render(<McpSettings />);

    expect(screen.getByText('Add New MCP')).toBeInTheDocument();
    expect(screen.getByLabelText('Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Endpoint URL')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /add mcp/i })).toBeInTheDocument();
  });

  it('shows empty state when no MCPs are configured', () => {
    render(<McpSettings />);

    expect(screen.getByText(/no mcps configured yet/i)).toBeInTheDocument();
  });
});
