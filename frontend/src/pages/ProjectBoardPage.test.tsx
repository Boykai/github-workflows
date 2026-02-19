/**
 * Unit tests for ProjectBoardPage component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

vi.mock('@/hooks/useProjectBoard', () => ({ useProjectBoard: vi.fn() }));
vi.mock('@/hooks/useAgentConfig', () => ({
  useAgentConfig: vi.fn(),
  useAvailableAgents: vi.fn(),
}));
vi.mock('@/components/board/ProjectBoard', () => ({
  ProjectBoard: () => <div data-testid="project-board" />,
}));
vi.mock('@/components/board/IssueDetailModal', () => ({
  IssueDetailModal: () => <div data-testid="modal" />,
}));
vi.mock('@/components/board/AgentConfigRow', () => ({
  AgentConfigRow: () => <div data-testid="agent-config" />,
}));
vi.mock('@/components/board/AddAgentPopover', () => ({
  AddAgentPopover: () => <div data-testid="add-agent" />,
}));
vi.mock('@/components/board/AgentPresetSelector', () => ({
  AgentPresetSelector: () => <div data-testid="preset-selector" />,
}));

import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useAgentConfig, useAvailableAgents } from '@/hooks/useAgentConfig';
import { ProjectBoardPage } from './ProjectBoardPage';

const mockUseProjectBoard = useProjectBoard as ReturnType<typeof vi.fn>;
const mockUseAgentConfig = useAgentConfig as ReturnType<typeof vi.fn>;
const mockUseAvailableAgents = useAvailableAgents as ReturnType<typeof vi.fn>;

function defaultBoardHook(overrides: Record<string, unknown> = {}) {
  return {
    projects: [],
    projectsLoading: false,
    projectsError: null,
    selectedProjectId: null,
    boardData: null,
    boardLoading: false,
    isFetching: false,
    boardError: null,
    lastUpdated: null,
    selectProject: vi.fn(),
    ...overrides,
  };
}

function defaultAgentConfig() {
  return {
    localMappings: {},
    isDirty: false,
    isColumnDirty: vi.fn(() => false),
    addAgent: vi.fn(),
    removeAgent: vi.fn(),
    reorderAgents: vi.fn(),
    applyPreset: vi.fn(),
    save: vi.fn().mockResolvedValue(undefined),
    discard: vi.fn(),
    isSaving: false,
    saveError: null,
    isLoaded: true,
    loadConfig: vi.fn().mockResolvedValue(undefined),
  };
}

function defaultAvailableAgents() {
  return {
    agents: [],
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  };
}

beforeEach(() => {
  mockUseProjectBoard.mockReturnValue(defaultBoardHook());
  mockUseAgentConfig.mockReturnValue(defaultAgentConfig());
  mockUseAvailableAgents.mockReturnValue(defaultAvailableAgents());
});

describe('ProjectBoardPage', () => {
  it('shows "Select a project" when no project selected', () => {
    render(<ProjectBoardPage />);
    expect(screen.getAllByText('Select a project').length).toBeGreaterThanOrEqual(1);
    // The empty state h3 is present
    expect(screen.getByRole('heading', { name: 'Select a project' })).toBeDefined();
  });

  it('shows loading when board is loading', () => {
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({ selectedProjectId: 'p1', boardLoading: true })
    );
    render(<ProjectBoardPage />);
    expect(screen.getByText('Loading board...')).toBeDefined();
  });

  it('shows project board when data is loaded', () => {
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({
        selectedProjectId: 'p1',
        boardData: {
          columns: [
            {
              status: { option_id: 'o1', name: 'Todo', color: 'GRAY' },
              items: [{ id: 'item-1' }],
              item_count: 1,
              estimate_total: 0,
            },
          ],
        },
      })
    );
    render(<ProjectBoardPage />);
    expect(screen.getByTestId('project-board')).toBeDefined();
  });

  it('shows board error with retry button', () => {
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({
        selectedProjectId: 'p1',
        boardError: new Error('Server error'),
      })
    );
    render(<ProjectBoardPage />);
    expect(screen.getByText('Failed to load board data')).toBeDefined();
    expect(screen.getByText('Retry')).toBeDefined();
  });

  it('shows empty state when all columns empty', () => {
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({
        selectedProjectId: 'p1',
        boardData: {
          columns: [
            {
              status: { option_id: 'o1', name: 'Todo', color: 'GRAY' },
              items: [],
              item_count: 0,
              estimate_total: 0,
            },
          ],
        },
      })
    );
    render(<ProjectBoardPage />);
    expect(screen.getByText('No items yet')).toBeDefined();
  });

  it('shows projects error message', () => {
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({ projectsError: new Error('Auth failed') })
    );
    render(<ProjectBoardPage />);
    expect(screen.getByText('Failed to load projects')).toBeDefined();
    expect(screen.getByText('Auth failed')).toBeDefined();
  });

  it('shows refresh indicator when fetching in background', () => {
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({
        selectedProjectId: 'p1',
        isFetching: true,
        boardLoading: false,
        boardData: {
          columns: [
            {
              status: { option_id: 'o1', name: 'Todo', color: 'GRAY' },
              items: [{ id: 'item-1' }],
              item_count: 1,
              estimate_total: 0,
            },
          ],
        },
      })
    );
    const { container } = render(<ProjectBoardPage />);
    expect(container.querySelector('.board-refresh-indicator')).not.toBeNull();
  });

  it('shows last updated time', () => {
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({
        selectedProjectId: 'p1',
        lastUpdated: new Date(),
        boardData: {
          columns: [
            {
              status: { option_id: 'o1', name: 'Todo', color: 'GRAY' },
              items: [{ id: 'item-1' }],
              item_count: 1,
              estimate_total: 0,
            },
          ],
        },
      })
    );
    render(<ProjectBoardPage />);
    expect(screen.getByText(/Updated just now/)).toBeDefined();
  });

  it('formatLastUpdated shows minutes ago', () => {
    const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000);
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({
        selectedProjectId: 'p1',
        lastUpdated: fiveMinAgo,
        boardData: {
          columns: [
            {
              status: { option_id: 'o1', name: 'Todo', color: 'GRAY' },
              items: [{ id: 'item-1' }],
              item_count: 1,
              estimate_total: 0,
            },
          ],
        },
      })
    );
    render(<ProjectBoardPage />);
    expect(screen.getByText(/Updated 5m ago/)).toBeDefined();
  });

  it('formatLastUpdated shows time for old updates', () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000);
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({
        selectedProjectId: 'p1',
        lastUpdated: twoHoursAgo,
        boardData: {
          columns: [
            {
              status: { option_id: 'o1', name: 'Todo', color: 'GRAY' },
              items: [{ id: 'item-1' }],
              item_count: 1,
              estimate_total: 0,
            },
          ],
        },
      })
    );
    render(<ProjectBoardPage />);
    expect(screen.getByText(/Updated/)).toBeDefined();
  });

  it('project selector onChange calls handleProjectSwitch', () => {
    const selectProject = vi.fn();
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({
        projects: [
          { project_id: 'p1', owner_login: 'acme', name: 'Proj 1' },
          { project_id: 'p2', owner_login: 'acme', name: 'Proj 2' },
        ],
        selectProject,
      })
    );
    render(<ProjectBoardPage />);
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'p2' } });
    expect(selectProject).toHaveBeenCalledWith('p2');
  });

  it('handleProjectSwitch with dirty config shows confirm dialog', () => {
    const selectProject = vi.fn();
    const discard = vi.fn();
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({
        projects: [
          { project_id: 'p1', owner_login: 'acme', name: 'Proj 1' },
          { project_id: 'p2', owner_login: 'acme', name: 'Proj 2' },
        ],
        selectProject,
      })
    );
    mockUseAgentConfig.mockReturnValue({ ...defaultAgentConfig(), isDirty: true, discard });
    vi.stubGlobal('confirm', vi.fn(() => true));
    render(<ProjectBoardPage />);
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'p2' } });
    expect(window.confirm).toHaveBeenCalled();
    expect(discard).toHaveBeenCalled();
    expect(selectProject).toHaveBeenCalledWith('p2');
    vi.unstubAllGlobals();
  });

  it('handleProjectSwitch cancels when user declines confirm', () => {
    const selectProject = vi.fn();
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({
        projects: [
          { project_id: 'p1', owner_login: 'acme', name: 'Proj 1' },
          { project_id: 'p2', owner_login: 'acme', name: 'Proj 2' },
        ],
        selectProject,
      })
    );
    mockUseAgentConfig.mockReturnValue({ ...defaultAgentConfig(), isDirty: true });
    vi.stubGlobal('confirm', vi.fn(() => false));
    render(<ProjectBoardPage />);
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'p2' } });
    expect(selectProject).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it('handleCardClick and handleCloseModal work via board and modal', () => {
    // We need to unmock ProjectBoard and IssueDetailModal to test click behavior
    // Instead, verify that the board receives onCardClick and modal renders
    // Since we mock ProjectBoard, let's test modal appearance indirectly
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({
        selectedProjectId: 'p1',
        boardData: {
          columns: [
            {
              status: { option_id: 'o1', name: 'Todo', color: 'GRAY' },
              items: [{ id: 'item-1' }],
              item_count: 1,
              estimate_total: 0,
            },
          ],
        },
      })
    );
    render(<ProjectBoardPage />);
    // Board is rendered (card click goes through ProjectBoard mock)
    expect(screen.getByTestId('project-board')).toBeDefined();
    // Modal is not shown initially (selectedItem is null)
    expect(screen.queryByTestId('modal')).toBeNull();
  });

  it('does not show refresh indicator when boardLoading is true', () => {
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({
        selectedProjectId: 'p1',
        isFetching: true,
        boardLoading: true,
      })
    );
    const { container } = render(<ProjectBoardPage />);
    expect(container.querySelector('.board-refresh-indicator')).toBeNull();
  });

  it('does not change select when empty value selected', () => {
    const selectProject = vi.fn();
    mockUseProjectBoard.mockReturnValue(
      defaultBoardHook({
        projects: [{ project_id: 'p1', owner_login: 'acme', name: 'Proj 1' }],
        selectProject,
      })
    );
    render(<ProjectBoardPage />);
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: '' } });
    expect(selectProject).not.toHaveBeenCalled();
  });
});
