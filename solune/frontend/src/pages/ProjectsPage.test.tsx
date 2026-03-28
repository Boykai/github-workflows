import { beforeEach, describe, expect, it, vi } from 'vitest';
import { screen, render, userEvent } from '@/test/test-utils';
import { ProjectsPage } from './ProjectsPage';

const mocks = vi.hoisted(() => ({
  updateRateLimit: vi.fn(),
  refresh: vi.fn(),
  resetTimer: vi.fn(),
  clearAll: vi.fn(),
  selectProject: vi.fn(),
  selectBoardProject: vi.fn(),
  setQueryData: vi.fn(),
  invalidateQueries: vi.fn(),
  refetchSavedPipelines: vi.fn(),
  mutate: vi.fn(),
  syncStatus: 'connected' as 'connected' | 'polling' | 'connecting' | 'disconnected',
  savedPipelines: {
    pipelines: [
      {
        id: 'pipe-1',
        name: 'Spec Kit Flow',
        stages: [{ name: 'Todo', agents: [{ id: 'agent-1', agent_slug: 'designer' }] }],
      },
    ],
  },
  pipelineAssignment: {
    pipeline_id: 'pipe-1',
  },
  projects: [
    {
      project_id: 'PVT_1',
      name: 'Solune',
      owner_login: 'Boykai',
    },
  ],
  selectedProject: {
    project_id: 'PVT_1',
    name: 'Solune',
    owner_login: 'Boykai',
  },
  boardData: {
    columns: [
      {
        status: { option_id: 'todo', name: 'Todo', color: 'GRAY' },
        items: [],
        item_count: 0,
      },
    ],
  },
  boardControls: {
    controls: {
      filters: { labels: [], assignees: [], milestones: [] },
      sort: { field: null, direction: 'asc' },
      group: { field: null },
    },
    transformedData: {
      columns: [
        {
          status: { option_id: 'todo', name: 'Todo', color: 'GRAY' },
          items: [],
          item_count: 0,
        },
      ],
    },
    setFilters: vi.fn(),
    setSort: vi.fn(),
    setGroup: vi.fn(),
    clearAll: vi.fn(),
    availableLabels: [],
    availableAssignees: [],
    availableMilestones: [],
    hasActiveFilters: true,
    hasActiveSort: false,
    hasActiveGroup: false,
    hasActiveControls: true,
    getGroups: vi.fn(),
  },
  projectBoard: {
    projectsRateLimitInfo: null,
    projectsLoading: false,
    projectsError: null,
    selectedProjectId: 'PVT_1',
    boardData: {
      columns: [
        {
          status: { option_id: 'todo', name: 'Todo', color: 'GRAY' },
          items: [],
          item_count: 0,
        },
      ],
    },
    boardLoading: false,
    isFetching: false,
    boardError: null,
    lastUpdated: new Date('2026-03-10T21:19:34.006Z'),
    selectProject: vi.fn(),
  },
}));

vi.mock('@tanstack/react-query', async () => {
  const actual =
    await vi.importActual<typeof import('@tanstack/react-query')>('@tanstack/react-query');

  return {
    ...actual,
    useQueryClient: () => ({
      setQueryData: mocks.setQueryData,
      invalidateQueries: mocks.invalidateQueries,
    }),
    useQuery: vi.fn(({ queryKey }: { queryKey: string[] }) => {
      if (queryKey[1] === 'assignment') {
        return { data: mocks.pipelineAssignment };
      }

      return {
        data: mocks.savedPipelines,
        isLoading: false,
        error: null,
        refetch: mocks.refetchSavedPipelines,
      };
    }),
    useMutation: vi.fn(() => ({
      mutate: mocks.mutate,
      isPending: false,
    })),
  };
});

vi.mock('@/context/RateLimitContext', () => ({
  useRateLimitStatus: () => ({ updateRateLimit: mocks.updateRateLimit }),
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ user: { selected_project_id: 'PVT_1' } }),
}));

vi.mock('@/hooks/useProjects', () => ({
  useProjects: () => ({
    selectedProject: mocks.selectedProject,
    projects: mocks.projects,
    isLoading: false,
    selectProject: mocks.selectProject,
  }),
}));

vi.mock('@/hooks/useProjectBoard', () => ({
  useProjectBoard: () => mocks.projectBoard,
}));

vi.mock('@/hooks/useBoardRefresh', () => ({
  useBoardRefresh: () => ({
    refresh: mocks.refresh,
    isRefreshing: false,
    error: null,
    rateLimitInfo: null,
    isRateLimitLow: false,
    resetTimer: mocks.resetTimer,
  }),
}));

vi.mock('@/hooks/useRealTimeSync', () => ({
  useRealTimeSync: () => ({
    status: mocks.syncStatus,
    lastUpdate: new Date('2026-03-10T21:19:34.006Z'),
  }),
}));

vi.mock('@/hooks/useAgentConfig', () => ({
  useAvailableAgents: () => ({ agents: [], isLoading: false }),
}));

vi.mock('@/hooks/useBoardControls', () => ({
  useBoardControls: () => mocks.boardControls,
}));

vi.mock('@/components/common/CelestialCatalogHero', () => ({
  CelestialCatalogHero: ({
    title,
    description,
    actions,
  }: {
    title: string;
    description: string;
    actions?: React.ReactNode;
  }) => (
    <section>
      <h1>{title}</h1>
      <p>{description}</p>
      <div>{actions}</div>
    </section>
  ),
}));

vi.mock('@/components/common/CelestialLoadingProgress', () => ({
  CelestialLoadingProgress: ({ phases }: { phases: { label: string; complete: boolean }[] }) => {
    const currentLabel = phases.find((p: { complete: boolean }) => !p.complete)?.label ?? phases[phases.length - 1]?.label ?? '';
    return <div role="progressbar">{currentLabel}</div>;
  },
}));

vi.mock('@/components/common/ProjectSelectionEmptyState', () => ({
  ProjectSelectionEmptyState: ({ description }: { description: string }) => (
    <div>{description}</div>
  ),
}));

vi.mock('@/layout/ProjectSelector', () => ({
  ProjectSelector: () => null,
}));

vi.mock('@/components/board/ProjectBoard', () => ({
  ProjectBoard: () => <div data-testid="project-board" />,
}));

vi.mock('@/components/board/IssueDetailModal', () => ({
  IssueDetailModal: () => null,
}));

vi.mock('@/components/board/BoardToolbar', () => ({
  BoardToolbar: () => <div data-testid="board-toolbar" />,
}));

vi.mock('@/components/board/ProjectIssueLaunchPanel', () => ({
  ProjectIssueLaunchPanel: () => <div data-testid="launch-panel" />,
}));

vi.mock('@/components/board/RefreshButton', () => ({
  RefreshButton: ({ onRefresh }: { onRefresh: () => void }) => (
    <button type="button" onClick={onRefresh}>
      Refresh board
    </button>
  ),
}));

describe('ProjectsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.boardControls.clearAll = mocks.clearAll;
    mocks.boardControls.hasActiveControls = true;
    mocks.projectBoard.boardError = null;
    mocks.projectBoard.boardLoading = false;
    mocks.projectBoard.projectsError = null;
    mocks.projectBoard.projectsLoading = false;
    mocks.projectBoard.selectedProjectId = 'PVT_1';
    mocks.projectBoard.selectProject = mocks.selectBoardProject;
    mocks.syncStatus = 'connected';
  });

  it('renders polished status and empty-state controls for filtered views', async () => {
    render(<ProjectsPage />);

    expect(screen.getByText('Live sync')).toBeInTheDocument();
    expect(screen.getByText(/Updated /)).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Clear all filters' }));

    expect(mocks.clearAll).toHaveBeenCalledTimes(1);
  });

  it('uses the scoped retry CTA for board failures', async () => {
    mocks.projectBoard.boardError = new Error('Board request failed');

    render(<ProjectsPage />);

    await userEvent.click(screen.getByRole('button', { name: 'Retry loading board data' }));

    expect(mocks.selectBoardProject).toHaveBeenCalledWith('PVT_1');
  });

  it('marks the sync status chip with aria-live for screen reader updates', () => {
    render(<ProjectsPage />);

    const chip = screen.getByText('Live sync').closest('[aria-live]');
    expect(chip).toHaveAttribute('aria-live', 'polite');
  });

  it('renders the board error banner with role="alert"', () => {
    mocks.projectBoard.boardError = new Error('Network timeout');

    render(<ProjectsPage />);

    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('Failed to load board data');
    expect(alert).toHaveTextContent('Network timeout');
  });

  it('renders the correct label for each sync status', () => {
    mocks.syncStatus = 'polling';

    const { unmount } = render(<ProjectsPage />);
    expect(screen.getByText('Polling')).toBeInTheDocument();
    unmount();

    mocks.syncStatus = 'disconnected';
    render(<ProjectsPage />);
    expect(screen.getByText('Offline')).toBeInTheDocument();
  });

  it('labels the pipeline stages grid with the heading for accessibility', () => {
    render(<ProjectsPage />);

    const heading = screen.getByText('Pipeline Stages');
    expect(heading).toHaveAttribute('id', 'pipeline-stages-heading');

    const region = screen.getByRole('region', { name: 'Pipeline Stages' });
    expect(region).toBeInTheDocument();
  });

  it('renders the projects error banner with role="alert"', () => {
    mocks.projectBoard.projectsError = new Error('Token expired');

    render(<ProjectsPage />);

    const alerts = screen.getAllByRole('alert');
    const projectsAlert = alerts.find((el) => el.textContent?.includes('Failed to load projects'));
    expect(projectsAlert).toBeDefined();
    expect(projectsAlert).toHaveTextContent('Token expired');
  });

  it('shows loading state when board is loading', () => {
    mocks.projectBoard.boardLoading = true;

    render(<ProjectsPage />);

    expect(screen.getByText('Loading project board…')).toBeInTheDocument();
  });

  it('shows empty state when no project is selected', () => {
    mocks.projectBoard.selectedProjectId = null;
    mocks.projectBoard.projectsLoading = false;

    render(<ProjectsPage />);

    expect(
      screen.getByText(
        'Open one of your GitHub Projects to review its board, column flow, and current delivery state.'
      )
    ).toBeInTheDocument();
  });

  it('renders the "Connecting" sync status label', () => {
    mocks.syncStatus = 'connecting';

    render(<ProjectsPage />);

    expect(screen.getByText('Connecting')).toBeInTheDocument();
  });

  it('fires the refresh callback when the refresh button is clicked', async () => {
    render(<ProjectsPage />);

    await userEvent.click(screen.getByRole('button', { name: 'Refresh board' }));

    expect(mocks.refresh).toHaveBeenCalledTimes(1);
  });
});
