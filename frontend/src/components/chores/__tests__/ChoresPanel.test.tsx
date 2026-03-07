/**
 * Tests for ChoresPanel component.
 *
 * Covers: empty state rendering, chore list rendering, loading state.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChoresPanel } from '../ChoresPanel';
import type { Chore } from '@/types';
import type { ReactNode } from 'react';

// ── Mock API ──

const mockList = vi.fn();

vi.mock('@/services/api', () => ({
  choresApi: {
    list: (...args: unknown[]) => mockList(...args),
  },
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      public error: { error: string }
    ) {
      super(error.error);
    }
  },
}));

// ── Wrapper ──

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

// ── Factory ──

function createChore(overrides: Partial<Chore> = {}): Chore {
  return {
    id: 'chore-1',
    project_id: 'PVT_1',
    name: 'Bug Bash',
    template_path: '.github/ISSUE_TEMPLATE/bug-bash.md',
    template_content: '---\nname: Bug Bash\n---\nContent',
    schedule_type: 'time',
    schedule_value: 14,
    status: 'active',
    last_triggered_at: null,
    last_triggered_count: 0,
    current_issue_number: null,
    current_issue_node_id: null,
    pr_number: null,
    pr_url: null,
    tracking_issue_number: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

// ── Tests ──

describe('ChoresPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when no chores exist', async () => {
    mockList.mockResolvedValue([]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('No chores yet')).toBeInTheDocument();
    });

    expect(screen.getByText(/Add a chore to set up/)).toBeInTheDocument();
  });

  it('renders chore list with ChoreCards', async () => {
    mockList.mockResolvedValue([
      createChore({ id: 'c1', name: 'Bug Bash' }),
      createChore({
        id: 'c2',
        name: 'Dependency Update',
        schedule_type: 'count',
        schedule_value: 5,
      }),
    ]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Bug Bash')).toBeInTheDocument();
    });

    expect(screen.getByText('Dependency Update')).toBeInTheDocument();
  });

  it('renders loading state with skeleton placeholders', () => {
    // Never resolve the promise to keep loading state
    mockList.mockReturnValue(new Promise(() => {}));

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    // Should show animated placeholder skeletons
    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThanOrEqual(1);
  });

  it('renders error state when API call fails', async () => {
    mockList.mockRejectedValue(new Error('Network error'));

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Failed to load chores')).toBeInTheDocument();
    });
  });

  it('displays the Chores header', async () => {
    mockList.mockResolvedValue([]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/Chores/)).toBeInTheDocument();
    });
  });

  it('shows Active badge for active chores', async () => {
    mockList.mockResolvedValue([createChore({ status: 'active' })]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument();
    });
  });

  it('shows Paused badge for paused chores', async () => {
    mockList.mockResolvedValue([createChore({ status: 'paused' })]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Paused')).toBeInTheDocument();
    });
  });
});
