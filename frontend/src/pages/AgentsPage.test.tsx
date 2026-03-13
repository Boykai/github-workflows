import { beforeEach, describe, expect, it, vi } from 'vitest';
import { screen, render } from '@/test/test-utils';
import { AgentsPage } from './AgentsPage';

const mocks = vi.hoisted(() => ({
  selectProject: vi.fn(),
  localMappings: {} as Record<string, Array<{ id: string; slug: string; display_name?: string; config?: Record<string, unknown> }>>,
  addAgent: vi.fn(),
  boardColumns: [
    {
      status: { option_id: 'ready', name: 'Ready', color: 'blue' },
      items: [{ repository: { owner: 'Boykai', name: 'solune' } }],
      item_count: 1,
    },
  ],
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ user: { selected_project_id: 'PVT_1' } }),
}));

vi.mock('@/hooks/useProjects', () => ({
  useProjects: () => ({
    selectedProject: { project_id: 'PVT_1', name: 'Solune', owner_login: 'Boykai' },
    projects: [{ project_id: 'PVT_1', name: 'Solune', owner_login: 'Boykai' }],
    isLoading: false,
    selectProject: mocks.selectProject,
  }),
}));

vi.mock('@/hooks/useProjectBoard', () => ({
  useProjectBoard: () => ({
    boardData: { columns: mocks.boardColumns },
    boardLoading: false,
  }),
}));

vi.mock('@/hooks/useAgentConfig', () => ({
  useAgentConfig: () => ({
    localMappings: mocks.localMappings,
    addAgent: mocks.addAgent,
  }),
}));

vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-query')>('@tanstack/react-query');
  return {
    ...actual,
    useQuery: vi.fn(() => ({
      data: { pipelines: [], total: 0 },
      isError: false,
    })),
  };
});

vi.mock('@/services/api', () => ({
  pipelinesApi: {
    list: vi.fn().mockResolvedValue({ pipelines: [], total: 0 }),
    getAssignment: vi.fn().mockResolvedValue({ pipeline_id: null }),
  },
}));

vi.mock('@/components/agents/AgentsPanel', () => ({
  AgentsPanel: () => <div data-testid="agents-panel">Agents Panel</div>,
}));

vi.mock('@/components/common/CelestialCatalogHero', () => ({
  CelestialCatalogHero: ({ title, actions }: { title: string; actions?: React.ReactNode }) => (
    <section>
      <h1>{title}</h1>
      <div>{actions}</div>
    </section>
  ),
}));

vi.mock('@/components/common/ProjectSelectionEmptyState', () => ({
  ProjectSelectionEmptyState: ({ description }: { description: string }) => (
    <div data-testid="empty-state">{description}</div>
  ),
}));

vi.mock('@/components/common/CelestialLoader', () => ({
  CelestialLoader: ({ label }: { label?: string }) => <div>{label ?? 'Loading'}</div>,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: React.ComponentProps<'button'> & { asChild?: boolean; variant?: string; size?: string }) =>
    props.asChild ? <>{children}</> : <button {...props}>{children}</button>,
}));

vi.mock('@/components/ui/tooltip', () => ({
  Tooltip: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  TooltipProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('@/components/board/colorUtils', () => ({
  statusColorToCSS: () => '#0000ff',
}));

vi.mock('@/utils/formatAgentName', () => ({
  formatAgentName: (_slug: string, display?: string) => display ?? _slug,
}));

vi.mock('@/utils/agentCardMeta', () => ({
  countPendingAssignedSubIssues: () => ({}),
}));

describe('AgentsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.localMappings = {};
    mocks.boardColumns = [
      {
        status: { option_id: 'ready', name: 'Ready', color: 'blue' },
        items: [{ repository: { owner: 'Boykai', name: 'solune' } }],
        item_count: 1,
      },
    ];
  });

  it('renders the hero title and action links', () => {
    render(<AgentsPage />);

    expect(screen.getByText('Shape your agent constellation.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Curate agent rituals' })).toHaveAttribute('href', '#agents-catalog');
    expect(screen.getByRole('link', { name: 'Review assignments' })).toHaveAttribute('href', '#agent-assignments');
  });

  it('renders the agents panel when a project is selected', () => {
    render(<AgentsPage />);

    expect(screen.getByTestId('agents-panel')).toBeInTheDocument();
  });

  it('shows column assignment section with board columns', () => {
    render(<AgentsPage />);

    expect(screen.getByText('Column assignments')).toBeInTheDocument();
    expect(screen.getByText('Ready')).toBeInTheDocument();
    expect(screen.getByText('No agents assigned')).toBeInTheDocument();
  });

  it('shows mapped agent chips when assignments exist', () => {
    mocks.localMappings = {
      Ready: [{ id: 'a1', slug: 'designer', display_name: 'Designer Agent' }],
    };

    render(<AgentsPage />);

    expect(screen.getByText('Designer Agent')).toBeInTheDocument();
    expect(screen.getByText('1 mapped')).toBeInTheDocument();
  });

  it('shows no board columns message when columns are empty', () => {
    mocks.boardColumns = [];

    render(<AgentsPage />);

    expect(screen.getByText('No board columns available')).toBeInTheDocument();
  });
});
