/**
 * Unit tests for ProjectBoardPage component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

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
});
