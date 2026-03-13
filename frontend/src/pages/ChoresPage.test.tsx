import { describe, expect, it, vi, beforeEach } from 'vitest';
import { screen, render } from '@/test/test-utils';
import { ChoresPage } from './ChoresPage';

const mocks = vi.hoisted(() => ({
  selectProject: vi.fn(),
  isAnyDirty: false,
  isBlocked: false,
  blockerReset: vi.fn(),
  blockerProceed: vi.fn(),
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ user: { selected_project_id: 'PVT_1' } }),
}));

vi.mock('@/hooks/useProjects', () => ({
  useProjects: () => ({
    selectedProject: { project_id: 'PVT_1', name: 'Solune', owner_login: 'Boykai' },
    projects: [{ project_id: 'PVT_1', name: 'Solune' }],
    isLoading: false,
    selectProject: mocks.selectProject,
  }),
}));

vi.mock('@/hooks/useProjectBoard', () => ({
  useProjectBoard: () => ({
    boardData: {
      columns: [
        {
          status: { option_id: 'ready', name: 'Ready', color: 'blue' },
          items: [{ repository: { owner: 'Boykai', name: 'solune' } }],
          item_count: 1,
        },
      ],
    },
    boardLoading: false,
  }),
}));

vi.mock('@/hooks/useChores', () => ({
  useChoresList: () => ({ data: [] }),
  useEvaluateChoresTriggers: vi.fn(),
  choreKeys: { list: (id: string) => ['chores', 'list', id] },
}));

vi.mock('@/hooks/useUnsavedChanges', () => ({
  useUnsavedChanges: () => ({
    isBlocked: mocks.isBlocked,
    blocker: { reset: mocks.blockerReset, proceed: mocks.blockerProceed },
  }),
}));

vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-query')>('@tanstack/react-query');
  return {
    ...actual,
    useQueryClient: () => ({ invalidateQueries: vi.fn() }),
    useQuery: vi.fn(() => ({ data: undefined, isError: false })),
  };
});

vi.mock('@/services/api', () => ({
  workflowApi: { getConfig: vi.fn().mockResolvedValue({}) },
  choresApi: { seedPresets: vi.fn().mockResolvedValue(undefined) },
}));

vi.mock('@/components/chores/ChoresPanel', () => ({
  ChoresPanel: () => <div data-testid="chores-panel">Chores Panel</div>,
}));

vi.mock('@/components/chores/FeaturedRitualsPanel', () => ({
  FeaturedRitualsPanel: () => <div data-testid="featured-rituals">Featured Rituals</div>,
}));

vi.mock('@/components/common/CelestialCatalogHero', () => ({
  CelestialCatalogHero: ({ title, actions }: { title: string; actions?: React.ReactNode }) => (
    <div>
      <h1>{title}</h1>
      {actions}
    </div>
  ),
}));

vi.mock('@/components/common/ProjectSelectionEmptyState', () => ({
  ProjectSelectionEmptyState: ({ description }: { description: string }) => (
    <div data-testid="empty-state">{description}</div>
  ),
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: React.ComponentProps<'button'> & { asChild?: boolean; variant?: string; size?: string }) =>
    props.asChild ? <>{children}</> : <button {...props}>{children}</button>,
}));

vi.mock('@/utils/parentIssueCount', () => ({
  countParentIssues: () => 0,
}));

describe('ChoresPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.isBlocked = false;
  });

  it('renders the hero title', () => {
    render(<ChoresPage />);
    expect(screen.getByText('Turn upkeep into a visible rhythm.')).toBeInTheDocument();
  });

  it('renders the chores panel when a project is selected', () => {
    render(<ChoresPage />);
    expect(screen.getByTestId('chores-panel')).toBeInTheDocument();
  });

  it('renders featured rituals panel', () => {
    render(<ChoresPage />);
    expect(screen.getByTestId('featured-rituals')).toBeInTheDocument();
  });

  it('shows hero action links', () => {
    render(<ChoresPage />);
    expect(screen.getByRole('link', { name: 'Plan recurring work' })).toHaveAttribute('href', '#chores-catalog');
    expect(screen.getByRole('link', { name: 'Review upkeep cadence' })).toHaveAttribute('href', '#chore-templates');
  });
});
