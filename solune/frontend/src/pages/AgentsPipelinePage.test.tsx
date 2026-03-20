import { describe, expect, it, beforeEach, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import { render, screen } from '@/test/test-utils';
import { AgentsPipelinePage } from './AgentsPipelinePage';

const mockInvalidateQueries = vi.fn();
const mockNewPipeline = vi.fn();
const mockLoadPipeline = vi.fn();
const mockDuplicatePipeline = vi.fn();
const mockDeletePipeline = vi.fn();
const mockSavePipeline = vi.fn();
const mockDiscardChanges = vi.fn();
const mockRefetchAgents = vi.fn();

const mockPipelineConfig = {
  boardState: 'editing' as const,
  isDirty: true,
  isSaving: false,
  isPreset: false,
  pipeline: {
    id: 'pipeline-1',
    name: 'Existing Pipeline',
    description: '',
    stages: [
      {
        id: 'stage-1',
        name: 'Ready',
        order: 0,
        agents: [],
      },
    ],
    is_preset: false,
    preset_id: '',
    created_at: '2026-03-10T18:00:00Z',
    updated_at: '2026-03-10T18:00:00Z',
    project_id: 'project-1',
  },
  pipelines: {
    pipelines: [],
    total: 0,
  },
  editingPipelineId: 'pipeline-1',
  assignedPipelineId: '',
  pipelinesLoading: false,
  validationErrors: {},
  modelOverride: { mode: 'auto' as const, modelId: '', modelName: '' },
  saveError: null as string | null,
  newPipeline: mockNewPipeline,
  loadPipeline: mockLoadPipeline,
  duplicatePipeline: mockDuplicatePipeline,
  deletePipeline: mockDeletePipeline,
  savePipeline: mockSavePipeline,
  discardChanges: mockDiscardChanges,
  saveAsCopy: vi.fn(),
  assignPipeline: vi.fn(),
  setPipelineName: vi.fn(),
  setModelOverride: vi.fn(),
  clearValidationError: vi.fn(),
  removeStage: vi.fn(),
  addAgentToStage: vi.fn(),
  removeAgentFromStage: vi.fn(),
  updateAgentInStage: vi.fn(),
  updateStage: vi.fn(),
  cloneAgentInStage: vi.fn(),
  reorderAgentsInStage: vi.fn(),
};

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useBlocker: vi.fn(() => ({ state: 'idle', reset: vi.fn(), proceed: vi.fn() })),
  };
});

vi.mock('@tanstack/react-query', async () => {
  const actual =
    await vi.importActual<typeof import('@tanstack/react-query')>('@tanstack/react-query');
  return {
    ...actual,
    useQueryClient: () => ({
      invalidateQueries: mockInvalidateQueries,
    }),
  };
});

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      selected_project_id: 'project-1',
    },
  }),
}));

vi.mock('@/hooks/useProjects', () => ({
  useProjects: () => ({
    selectedProject: {
      project_id: 'project-1',
      owner_login: 'Boykai',
      name: 'Project Solune',
    },
    projects: [],
    isLoading: false,
    selectProject: vi.fn(),
  }),
}));

vi.mock('@/hooks/useProjectBoard', () => ({
  useProjectBoard: () => ({
    boardData: {
      columns: [
        {
          status: {
            name: 'Ready',
            option_id: 'status-ready',
            color: 'blue',
          },
          item_count: 2,
        },
      ],
    },
    boardLoading: false,
  }),
}));

vi.mock('@/hooks/useAgentConfig', () => ({
  useAgentConfig: () => ({
    localMappings: {},
    addAgent: vi.fn(),
  }),
  useAvailableAgents: () => ({
    agents: [],
    isLoading: false,
    error: null,
    refetch: mockRefetchAgents,
  }),
}));

vi.mock('@/hooks/usePipelineConfig', () => ({
  usePipelineConfig: () => mockPipelineConfig,
  pipelineKeys: {
    list: (projectId: string) => ['pipelines', 'list', projectId],
  },
}));

vi.mock('@/hooks/useModels', () => ({
  useModels: () => ({
    models: [],
  }),
}));

vi.mock('@/hooks/useConfirmation', () => ({
  useConfirmation: () => ({
    confirm: vi.fn().mockResolvedValue(true),
  }),
}));

vi.mock('@/services/api', () => ({
  pipelinesApi: {
    seedPresets: vi.fn().mockResolvedValue(undefined),
  },
}));

vi.mock('@/components/common/CelestialLoader', () => ({
  CelestialLoader: ({ label }: { label: string }) => <div>{label}</div>,
}));

vi.mock('@/components/pipeline/PipelineBoard', () => ({
  PipelineBoard: () => <div>Pipeline Board</div>,
}));

vi.mock('@/components/pipeline/PipelineToolbar', () => ({
  PipelineToolbar: () => <div>Pipeline Toolbar</div>,
}));

vi.mock('@/components/pipeline/SavedWorkflowsList', () => ({
  SavedWorkflowsList: ({
    onSelect,
    onCopy,
  }: {
    onSelect: (pipelineId: string) => void;
    onCopy?: (pipelineId: string) => void;
  }) => (
    <div id="saved-pipelines">
      <button type="button" onClick={() => onSelect('pipeline-2')}>
        Select Workflow
      </button>
      <button type="button" onClick={() => onCopy?.('pipeline-2')}>
        Copy Workflow
      </button>
    </div>
  ),
}));

vi.mock('@/components/pipeline/UnsavedChangesDialog', () => ({
  UnsavedChangesDialog: ({
    isOpen,
    actionDescription,
  }: {
    isOpen: boolean;
    actionDescription: string;
  }) =>
    isOpen ? (
      <div role="dialog">
        <p>{actionDescription}</p>
      </div>
    ) : null,
}));

vi.mock('@/components/pipeline/PipelineFlowGraph', () => ({
  PipelineFlowGraph: () => <div>Pipeline Flow Graph</div>,
}));

vi.mock('@/components/pipeline/PipelineRunHistory', () => ({
  PipelineRunHistory: () => null,
}));

vi.mock('@/components/common/ProjectSelectionEmptyState', () => ({
  ProjectSelectionEmptyState: () => <div>Select a project</div>,
}));

vi.mock('@/components/common/CelestialCatalogHero', () => ({
  CelestialCatalogHero: ({ title, actions }: { title: string; actions: ReactNode }) => (
    <section>
      <h1>{title}</h1>
      <div>{actions}</div>
    </section>
  ),
}));

vi.mock('@/components/ui/tooltip', () => ({
  TooltipProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
  Tooltip: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock('@/components/common/ThemedAgentIcon', () => ({
  ThemedAgentIcon: () => <div>Constellation icon</div>,
}));

describe('AgentsPipelinePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPipelineConfig.isDirty = true;
    mockPipelineConfig.boardState = 'editing';
  });

  it('does not render a Current Pipeline section', () => {
    render(<AgentsPipelinePage />);

    expect(screen.queryByText('Current Pipeline')).not.toBeInTheDocument();
  });

  it('guards the hero new pipeline action when there are unsaved changes', async () => {
    const user = userEvent.setup();

    render(<AgentsPipelinePage />);

    await user.click(screen.getByRole('button', { name: 'New pipeline' }));

    expect(mockNewPipeline).not.toHaveBeenCalled();
    expect(
      screen.getByText('Creating a new pipeline will discard your changes')
    ).toBeInTheDocument();
  });

  it('guards copying a saved workflow when there are unsaved changes', async () => {
    const user = userEvent.setup();

    render(<AgentsPipelinePage />);

    await user.click(screen.getByRole('button', { name: 'Copy Workflow' }));

    expect(mockDuplicatePipeline).not.toHaveBeenCalled();
    expect(
      screen.getByText('Copying a saved workflow will discard your changes')
    ).toBeInTheDocument();
  });

  it('renders Pipeline Analytics section when pipelines exist', () => {
    const pipelines = Array.from({ length: 5 }, (_, i) => ({
      id: `pipeline-${i}`,
      name: `Pipeline ${i}`,
      description: '',
      stage_count: 1,
      agent_count: 1,
      total_tool_count: 0,
      is_preset: false,
      preset_id: '',
      updated_at: '2026-03-10T18:00:00Z',
      stages: [],
    }));

    mockPipelineConfig.pipelines = { pipelines, total: 5 };

    render(<AgentsPipelinePage />);

    expect(screen.getByText('Pipeline Analytics')).toBeInTheDocument();
  });

  it('shows analytics empty state when no pipelines exist', () => {
    const pipelines: unknown[] = [];

    mockPipelineConfig.pipelines = { pipelines, total: 0 };

    render(<AgentsPipelinePage />);

    expect(screen.getByText(/Analytics will appear once pipelines are created/)).toBeInTheDocument();
  });
});
