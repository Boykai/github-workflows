import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { ActivityPage } from './ActivityPage';

const mocks = vi.hoisted(() => ({
  allItems: [] as Array<{
    id: string;
    event_type: string;
    entity_type: string;
    entity_id: string;
    project_id: string;
    actor: string;
    action: string;
    summary: string;
    detail?: Record<string, unknown>;
    created_at: string;
  }>,
  hasNextPage: false,
  isFetchingNextPage: false,
  fetchNextPage: vi.fn(),
  isLoading: false,
  isError: false,
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { login: 'test', selected_project_id: 'PVT_test123' },
    isAuthenticated: true,
  }),
}));

vi.mock('@/hooks/useActivityFeed', () => ({
  useActivityFeed: () => ({
    allItems: mocks.allItems,
    hasNextPage: mocks.hasNextPage,
    isFetchingNextPage: mocks.isFetchingNextPage,
    fetchNextPage: mocks.fetchNextPage,
    isLoading: mocks.isLoading,
    isError: mocks.isError,
  }),
}));

describe('ActivityPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.allItems = [];
    mocks.hasNextPage = false;
    mocks.isFetchingNextPage = false;
    mocks.isLoading = false;
    mocks.isError = false;
  });

  it('renders without crashing', () => {
    render(<ActivityPage />);
    expect(screen.getByRole('heading', { name: 'Activity' })).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<ActivityPage />);
    await expectNoA11yViolations(container);
  });

  it('shows loading state', () => {
    mocks.isLoading = true;

    render(<ActivityPage />);

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Loading activity…')).toBeInTheDocument();
  });

  it('shows empty state when no events exist', () => {
    render(<ActivityPage />);

    expect(screen.getByText('No activity recorded yet')).toBeInTheDocument();
    expect(
      screen.getByText('Events will appear here as you use the system.'),
    ).toBeInTheDocument();
  });

  it('renders event items when data is loaded', () => {
    mocks.allItems = [
      {
        id: 'evt-1',
        event_type: 'pipeline_run',
        entity_type: 'pipeline',
        entity_id: 'pipe-1',
        project_id: 'PVT_test123',
        actor: 'testuser',
        action: 'started',
        summary: 'Pipeline started successfully',
        created_at: new Date().toISOString(),
      },
    ];

    render(<ActivityPage />);

    expect(screen.getByText('Pipeline started successfully')).toBeInTheDocument();
    expect(screen.getByText('testuser')).toBeInTheDocument();
  });

  it('toggles filter chips with aria-pressed', async () => {
    render(<ActivityPage />);

    const pipelineChip = screen.getByRole('button', { name: /Pipeline/i });
    expect(pipelineChip).toHaveAttribute('aria-pressed', 'false');

    await userEvent.click(pipelineChip);
    expect(pipelineChip).toHaveAttribute('aria-pressed', 'true');

    await userEvent.click(pipelineChip);
    expect(pipelineChip).toHaveAttribute('aria-pressed', 'false');
  });

  it('shows filtered empty state when filters are active', async () => {
    render(<ActivityPage />);

    await userEvent.click(screen.getByRole('button', { name: /Pipeline/i }));

    expect(screen.getByText(/no pipeline events found/i)).toBeInTheDocument();
  });

  it('shows and uses the clear all button when filters are active', async () => {
    render(<ActivityPage />);

    // No clear button initially
    expect(screen.queryByRole('button', { name: /clear all/i })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /Pipeline/i }));
    expect(screen.getByRole('button', { name: /clear all/i })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /clear all/i }));
    expect(screen.queryByRole('button', { name: /clear all/i })).not.toBeInTheDocument();

    // Filter chips should all be unpressed
    const pipelineChip = screen.getByRole('button', { name: /Pipeline/i });
    expect(pipelineChip).toHaveAttribute('aria-pressed', 'false');
  });

  it('expands event detail when clicked', async () => {
    mocks.allItems = [
      {
        id: 'evt-detail',
        event_type: 'agent_crud',
        entity_type: 'agent',
        entity_id: 'agent-1',
        project_id: 'PVT_test123',
        actor: 'admin',
        action: 'created',
        summary: 'Agent created',
        detail: { agent_name: 'designer', model: 'gpt-4' },
        created_at: new Date().toISOString(),
      },
    ];

    render(<ActivityPage />);

    // The event button should have aria-expanded
    const eventButton = screen.getByRole('button', { name: /agent created/i });
    expect(eventButton).toHaveAttribute('aria-expanded', 'false');

    await userEvent.click(eventButton);
    expect(eventButton).toHaveAttribute('aria-expanded', 'true');

    // Detail fields should be visible
    expect(screen.getByText('agent_name:')).toBeInTheDocument();
    expect(screen.getByText('designer')).toBeInTheDocument();
  });

  it('does not set aria-expanded on events without detail', () => {
    mocks.allItems = [
      {
        id: 'evt-no-detail',
        event_type: 'status_change',
        entity_type: 'board',
        entity_id: 'board-1',
        project_id: 'PVT_test123',
        actor: 'system',
        action: 'updated',
        summary: 'Status changed',
        created_at: new Date().toISOString(),
      },
    ];

    render(<ActivityPage />);

    const eventButton = screen.getByRole('button', { name: /status changed/i });
    expect(eventButton).not.toHaveAttribute('aria-expanded');
  });

  it('renders all 8 filter category chips', () => {
    render(<ActivityPage />);

    expect(screen.getByRole('button', { name: /Pipeline/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Chore/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Agent/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /App/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Tool/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Webhook/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Cleanup/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Status/ })).toBeInTheDocument();
  });
});
