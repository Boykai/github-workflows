import { describe, it, expect, vi } from 'vitest';
import { render } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { ToolsPage } from './ToolsPage';

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

vi.mock('@/hooks/useTools', () => ({
  useToolsList: () => ({ tools: [], isLoading: false, error: null }),
  useToolsListPaginated: () => ({ allItems: [], hasNextPage: false, isFetchingNextPage: false, fetchNextPage: () => {}, isError: false, isLoading: false }),
}));

describe('ToolsPage', () => {
  it('renders without crashing', () => {
    render(<ToolsPage />);
    expect(document.body).toBeDefined();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<ToolsPage />);
    await expectNoA11yViolations(container);
  });
});
