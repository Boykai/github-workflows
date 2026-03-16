import { describe, it, expect, vi } from 'vitest';
import { render } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { AgentsPage } from './AgentsPage';

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

vi.mock('@/hooks/useAgentConfig', () => ({
  useAgentConfig: () => ({
    localMappings: {},
    isDirty: false,
    isColumnDirty: () => false,
    addAgent: vi.fn(),
    removeAgent: vi.fn(),
    cloneAgent: vi.fn(),
    reorderAgents: vi.fn(),
    moveAgentToColumn: vi.fn(),
    applyPreset: vi.fn(),
    save: vi.fn(),
    discard: vi.fn(),
    isSaving: false,
    saveError: null,
    isLoaded: true,
    loadConfig: vi.fn(),
  }),
}));

describe('AgentsPage', () => {
  it('renders without crashing', () => {
    render(<AgentsPage />);
    expect(document.body).toBeDefined();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<AgentsPage />);
    await expectNoA11yViolations(container);
  });
});
