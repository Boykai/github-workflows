import { describe, it, expect, vi } from 'vitest';
import { render } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { ChoresPage } from './ChoresPage';

vi.mock('@tanstack/react-query', async () => {
  const actual =
    await vi.importActual<typeof import('@tanstack/react-query')>('@tanstack/react-query');
  return {
    ...actual,
    useQuery: vi.fn(() => ({ data: undefined, isLoading: false, isError: false })),
    useQueryClient: () => ({ invalidateQueries: vi.fn(), setQueryData: vi.fn() }),
    useMutation: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  };
});

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ user: { login: 'test', selected_project_id: null }, isAuthenticated: true }),
}));

vi.mock('@/hooks/useProjects', () => ({
  useProjects: () => ({
    projects: [],
    selectedProject: null,
    isLoading: false,
    selectProject: vi.fn(),
  }),
}));

vi.mock('@/hooks/useProjectBoard', () => ({
  useProjectBoard: () => ({ boardData: null, boardLoading: false }),
}));

vi.mock('@/hooks/useChores', () => ({
  useChoresListPaginated: () => ({ allItems: [], isLoading: false }),
  useEvaluateChoresTriggers: vi.fn(),
  choreKeys: { list: () => ['chores'] },
}));

vi.mock('@/hooks/useUnsavedChanges', () => ({
  useUnsavedChanges: () => ({ isBlocked: false, blocker: undefined }),
}));

vi.mock('@/services/api', () => ({
  choresApi: { seedPresets: vi.fn().mockResolvedValue(undefined) },
  workflowApi: {},
}));

describe('ChoresPage', () => {
  it('renders without crashing', () => {
    render(<ChoresPage />);
    expect(document.body).toBeDefined();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<ChoresPage />);
    await expectNoA11yViolations(container);
  });
});
