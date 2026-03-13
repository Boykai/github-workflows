import { describe, expect, it, vi } from 'vitest';
import { screen, render } from '@/test/test-utils';
import { ToolsPage } from './ToolsPage';

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ user: { selected_project_id: 'PVT_1' } }),
}));

vi.mock('@/hooks/useProjects', () => ({
  useProjects: () => ({
    selectedProject: { project_id: 'PVT_1', name: 'Solune', owner_login: 'Boykai' },
    projects: [{ project_id: 'PVT_1', name: 'Solune' }],
    isLoading: false,
    selectProject: vi.fn(),
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

vi.mock('@/components/tools/ToolsPanel', () => ({
  ToolsPanel: () => <div data-testid="tools-panel">Tools Panel</div>,
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

describe('ToolsPage', () => {
  it('renders hero title', () => {
    render(<ToolsPage />);
    expect(screen.getByText('Equip your agents with MCP tools.')).toBeInTheDocument();
  });

  it('renders tools panel when project is selected', () => {
    render(<ToolsPage />);
    expect(screen.getByTestId('tools-panel')).toBeInTheDocument();
  });

  it('renders action links in hero', () => {
    render(<ToolsPage />);
    expect(screen.getByRole('link', { name: 'Browse tools' })).toHaveAttribute('href', '#tools-catalog');
  });
});
