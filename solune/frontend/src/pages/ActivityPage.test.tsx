import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent, waitFor } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { ActivityPage } from './ActivityPage';

// ── Mocks ──

const mocks = vi.hoisted(() => ({
  useActivityFeed: vi.fn(),
  useAuth: vi.fn(),
}));

vi.mock('@/hooks/useActivityFeed', () => ({
  useActivityFeed: (...args: unknown[]) => mocks.useActivityFeed(...args),
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => mocks.useAuth(),
}));

vi.mock('@/components/common/InfiniteScrollContainer', () => ({
  InfiniteScrollContainer: ({
    children,
    hasNextPage,
    isFetchingNextPage,
  }: {
    children: React.ReactNode;
    hasNextPage: boolean;
    isFetchingNextPage: boolean;
    fetchNextPage: () => void;
    isError: boolean;
  }) => (
    <div data-testid="infinite-scroll">
      {children}
      {hasNextPage && <span>has-next</span>}
      {isFetchingNextPage && <span>fetching-next</span>}
    </div>
  ),
}));

// ── Test Data ──

function createMockEvent(overrides: Record<string, unknown> = {}) {
  return {
    id: 'evt-1',
    event_type: 'pipeline_run',
    entity_type: 'pipeline',
    entity_id: 'pipe-1',
    project_id: 'proj-1',
    actor: 'testuser',
    action: 'run',
    summary: 'Pipeline completed successfully',
    detail: undefined as Record<string, unknown> | undefined,
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

// ── Defaults ──

function setupDefaults() {
  mocks.useAuth.mockReturnValue({
    user: { login: 'test', selected_project_id: 'proj-1' },
    isAuthenticated: true,
  });

  mocks.useActivityFeed.mockReturnValue({
    allItems: [],
    hasNextPage: false,
    isFetchingNextPage: false,
    fetchNextPage: vi.fn(),
    isLoading: false,
    isError: false,
  });
}

// ── Tests ──

describe('ActivityPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaults();
  });

  // ── Rendering ──

  it('renders the Activity heading', () => {
    render(<ActivityPage />);
    expect(screen.getByText('Activity')).toBeInTheDocument();
  });

  it('renders all filter category chips', () => {
    render(<ActivityPage />);

    const expectedCategories = [
      'Pipeline',
      'Chore',
      'Agent',
      'App',
      'Tool',
      'Webhook',
      'Cleanup',
      'Status',
    ];

    for (const cat of expectedCategories) {
      expect(screen.getByRole('button', { name: cat })).toBeInTheDocument();
    }
  });

  // ── Loading State ──

  it('shows loading indicator when data is loading', () => {
    mocks.useActivityFeed.mockReturnValue({
      allItems: [],
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      isLoading: true,
      isError: false,
    });

    render(<ActivityPage />);
    expect(screen.getByText('Loading activity…')).toBeInTheDocument();
  });

  it('hides event list while loading', () => {
    mocks.useActivityFeed.mockReturnValue({
      allItems: [createMockEvent()],
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      isLoading: true,
      isError: false,
    });

    render(<ActivityPage />);
    expect(screen.queryByText('Pipeline completed successfully')).not.toBeInTheDocument();
  });

  // ── Empty State ──

  it('shows empty state when no events exist', () => {
    render(<ActivityPage />);
    expect(screen.getByText('No activity recorded yet')).toBeInTheDocument();
    expect(
      screen.getByText('Events will appear here as you use the system.'),
    ).toBeInTheDocument();
  });

  it('shows filtered empty state when categories are selected but no events match', async () => {
    const user = userEvent.setup();
    render(<ActivityPage />);

    await user.click(screen.getByRole('button', { name: 'Pipeline' }));

    expect(screen.getByText(/no pipeline events found/i)).toBeInTheDocument();
  });

  // ── Event List ──

  it('renders event items when data is available', () => {
    mocks.useActivityFeed.mockReturnValue({
      allItems: [
        createMockEvent({ id: 'evt-1', summary: 'First event', actor: 'alice' }),
        createMockEvent({ id: 'evt-2', summary: 'Second event', actor: 'bob' }),
      ],
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      isLoading: false,
      isError: false,
    });

    render(<ActivityPage />);

    expect(screen.getByText('First event')).toBeInTheDocument();
    expect(screen.getByText('Second event')).toBeInTheDocument();
    expect(screen.getByText('alice')).toBeInTheDocument();
    expect(screen.getByText('bob')).toBeInTheDocument();
  });

  it('shows end-of-activity indicator when no more pages', () => {
    mocks.useActivityFeed.mockReturnValue({
      allItems: [createMockEvent()],
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      isLoading: false,
      isError: false,
    });

    render(<ActivityPage />);
    expect(screen.getByText('End of activity log')).toBeInTheDocument();
  });

  it('does not show end indicator when more pages exist', () => {
    mocks.useActivityFeed.mockReturnValue({
      allItems: [createMockEvent()],
      hasNextPage: true,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      isLoading: false,
      isError: false,
    });

    render(<ActivityPage />);
    expect(screen.queryByText('End of activity log')).not.toBeInTheDocument();
  });

  // ── Filter Chips ──

  it('toggles a category filter chip on click', async () => {
    const user = userEvent.setup();
    render(<ActivityPage />);

    const pipelineBtn = screen.getByRole('button', { name: 'Pipeline' });

    // Initially no "Clear all" button
    expect(screen.queryByText('Clear all')).not.toBeInTheDocument();

    // Click to activate
    await user.click(pipelineBtn);

    // "Clear all" appears after selecting a category
    expect(screen.getByText('Clear all')).toBeInTheDocument();

    // Click again to deactivate
    await user.click(pipelineBtn);

    // "Clear all" hidden when no filters active
    expect(screen.queryByText('Clear all')).not.toBeInTheDocument();
  });

  it('clears all filters when "Clear all" is clicked', async () => {
    const user = userEvent.setup();
    render(<ActivityPage />);

    await user.click(screen.getByRole('button', { name: 'Pipeline' }));
    await user.click(screen.getByRole('button', { name: 'Agent' }));

    expect(screen.getByText('Clear all')).toBeInTheDocument();

    await user.click(screen.getByText('Clear all'));

    expect(screen.queryByText('Clear all')).not.toBeInTheDocument();
  });

  it('passes selected event types to useActivityFeed', async () => {
    const user = userEvent.setup();
    render(<ActivityPage />);

    await user.click(screen.getByRole('button', { name: 'Pipeline' }));

    // useActivityFeed should be called with the pipeline event types
    const lastCall = mocks.useActivityFeed.mock.calls.at(-1);
    expect(lastCall?.[0]).toBe('proj-1');
    expect(lastCall?.[1]).toEqual(['pipeline_run', 'pipeline_stage']);
  });

  it('passes undefined eventTypes when no filters are selected', () => {
    render(<ActivityPage />);

    const lastCall = mocks.useActivityFeed.mock.calls.at(-1);
    expect(lastCall?.[0]).toBe('proj-1');
    expect(lastCall?.[1]).toBeUndefined();
  });

  // ── Expand/Collapse Detail ──

  it('expands event detail on click when detail exists', async () => {
    const user = userEvent.setup();
    mocks.useActivityFeed.mockReturnValue({
      allItems: [
        createMockEvent({
          id: 'evt-detail',
          summary: 'Event with detail',
          detail: { branch: 'main', status: 'success' },
        }),
      ],
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      isLoading: false,
      isError: false,
    });

    render(<ActivityPage />);

    // Detail not visible initially
    expect(screen.queryByText('branch:')).not.toBeInTheDocument();

    // Click to expand
    await user.click(screen.getByText('Event with detail'));

    expect(screen.getByText('branch:')).toBeInTheDocument();
    expect(screen.getByText('main')).toBeInTheDocument();
    expect(screen.getByText('status:')).toBeInTheDocument();
    expect(screen.getByText('success')).toBeInTheDocument();
  });

  it('collapses event detail on second click', async () => {
    const user = userEvent.setup();
    mocks.useActivityFeed.mockReturnValue({
      allItems: [
        createMockEvent({
          id: 'evt-collapse',
          summary: 'Collapsible event',
          detail: { key: 'value' },
        }),
      ],
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      isLoading: false,
      isError: false,
    });

    render(<ActivityPage />);

    // Expand
    await user.click(screen.getByText('Collapsible event'));
    expect(screen.getByText('key:')).toBeInTheDocument();

    // Collapse
    await user.click(screen.getByText('Collapsible event'));
    expect(screen.queryByText('key:')).not.toBeInTheDocument();
  });

  it('does not toggle expansion when event has no detail', async () => {
    const user = userEvent.setup();
    mocks.useActivityFeed.mockReturnValue({
      allItems: [
        createMockEvent({
          id: 'evt-no-detail',
          summary: 'No-detail event',
          detail: undefined,
        }),
      ],
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      isLoading: false,
      isError: false,
    });

    render(<ActivityPage />);

    await user.click(screen.getByText('No-detail event'));

    // No detail view should appear — nothing expanded
    expect(screen.queryByText('key:')).not.toBeInTheDocument();
  });

  it('does not toggle expansion when event detail is empty object', async () => {
    const user = userEvent.setup();
    mocks.useActivityFeed.mockReturnValue({
      allItems: [
        createMockEvent({
          id: 'evt-empty-detail',
          summary: 'Empty detail event',
          detail: {},
        }),
      ],
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      isLoading: false,
      isError: false,
    });

    render(<ActivityPage />);

    await user.click(screen.getByText('Empty detail event'));

    // Empty detail should not trigger expansion (hasDetail check fails for empty objects)
    // The component checks Object.keys(detail).length > 0
    expect(screen.queryByTestId('detail-view')).not.toBeInTheDocument();
  });

  // ── Edge Cases ──

  it('uses empty string for projectId when user has no selected project', () => {
    mocks.useAuth.mockReturnValue({
      user: { login: 'test', selected_project_id: null },
      isAuthenticated: true,
    });

    render(<ActivityPage />);

    const lastCall = mocks.useActivityFeed.mock.calls.at(-1);
    expect(lastCall?.[0]).toBe('');
  });

  it('handles null user gracefully', () => {
    mocks.useAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
    });

    render(<ActivityPage />);

    const lastCall = mocks.useActivityFeed.mock.calls.at(-1);
    expect(lastCall?.[0]).toBe('');
  });

  it('renders events with unknown event_type using fallback icon', () => {
    mocks.useActivityFeed.mockReturnValue({
      allItems: [
        createMockEvent({
          id: 'evt-unknown',
          event_type: 'unknown_type',
          summary: 'Unknown type event',
        }),
      ],
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      isLoading: false,
      isError: false,
    });

    render(<ActivityPage />);
    expect(screen.getByText('Unknown type event')).toBeInTheDocument();
  });

  it('renders detail with nested object values as JSON', async () => {
    const user = userEvent.setup();
    mocks.useActivityFeed.mockReturnValue({
      allItems: [
        createMockEvent({
          id: 'evt-nested',
          summary: 'Nested detail',
          detail: { config: { nested: true } },
        }),
      ],
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      isLoading: false,
      isError: false,
    });

    render(<ActivityPage />);
    await user.click(screen.getByText('Nested detail'));

    expect(screen.getByText('config:')).toBeInTheDocument();
    expect(screen.getByText('{"nested":true}')).toBeInTheDocument();
  });

  // ── Multiple filter categories ──

  it('combines event types from multiple selected categories', async () => {
    const user = userEvent.setup();
    render(<ActivityPage />);

    await user.click(screen.getByRole('button', { name: 'Pipeline' }));
    await user.click(screen.getByRole('button', { name: 'Chore' }));

    const lastCall = mocks.useActivityFeed.mock.calls.at(-1);
    expect(lastCall?.[1]).toEqual([
      'pipeline_run',
      'pipeline_stage',
      'chore_trigger',
      'chore_crud',
    ]);
  });

  // ── Accessibility ──

  it('has no accessibility violations', async () => {
    const { container } = render(<ActivityPage />);
    await expectNoA11yViolations(container);
  });

  it('has no accessibility violations with events rendered', async () => {
    mocks.useActivityFeed.mockReturnValue({
      allItems: [
        createMockEvent({ id: 'evt-a11y', summary: 'A11y event' }),
      ],
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      isLoading: false,
      isError: false,
    });

    const { container } = render(<ActivityPage />);
    await expectNoA11yViolations(container);
  });

  it('filter chip buttons are keyboard-accessible', async () => {
    const user = userEvent.setup();
    render(<ActivityPage />);

    // Tab to first filter chip and press Enter
    await user.tab();
    const focused = document.activeElement;
    expect(focused?.tagName).toBe('BUTTON');

    await waitFor(() => {
      // First button should be one of the filter chips
      expect(focused?.textContent).toMatch(/Pipeline|Chore|Agent|App|Tool|Webhook|Cleanup|Status/);
    });
  });
});
