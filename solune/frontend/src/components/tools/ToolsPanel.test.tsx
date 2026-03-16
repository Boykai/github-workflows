import { beforeEach, describe, expect, it, vi } from 'vitest';
import userEvent from '@testing-library/user-event';

import { render, screen } from '@/test/test-utils';
import { ApiError } from '@/services/api';

import { ToolsPanel } from './ToolsPanel';

const mockUseToolsList = vi.fn();
const mockUseRepoMcpConfig = vi.fn();
const mockUseMcpPresets = vi.fn();
const mockConfirm = vi.fn();

function createRepoConfigHookResult() {
  return {
    repoConfig: {
      paths_checked: ['.copilot/mcp.json', '.vscode/mcp.json'],
      available_paths: ['.copilot/mcp.json'],
      primary_path: '.copilot/mcp.json',
      servers: [],
    },
    isLoading: false,
    error: null,
    rawError: null,
    refetch: vi.fn(),
    updateRepoServer: vi.fn(),
    isUpdating: false,
    updatingServerName: null,
    updateError: null,
    resetUpdateError: vi.fn(),
    deleteRepoServer: vi.fn(),
    isDeleting: false,
    deletingServerName: null,
    deleteError: null,
    resetDeleteError: vi.fn(),
  };
}

function createMcpPresetsHookResult() {
  return {
    presets: [],
    isLoading: false,
    error: null,
    rawError: null,
    refetch: vi.fn(),
  };
}

vi.mock('@/hooks/useTools', () => ({
  useToolsList: (...args: unknown[]) => mockUseToolsList(...args),
}));

vi.mock('@/hooks/useRepoMcpConfig', () => ({
  useRepoMcpConfig: (...args: unknown[]) => mockUseRepoMcpConfig(...args),
}));

vi.mock('@/hooks/useMcpPresets', () => ({
  useMcpPresets: (...args: unknown[]) => mockUseMcpPresets(...args),
}));

vi.mock('@/hooks/useConfirmation', () => ({
  useConfirmation: () => ({
    confirm: mockConfirm,
  }),
}));

describe('ToolsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseToolsList.mockReturnValue({
      tools: [],
      isLoading: false,
      error: null,
      rawError: null,
      refetch: vi.fn(),
      uploadTool: vi.fn(),
      isUploading: false,
      uploadError: null,
      resetUploadError: vi.fn(),
      updateTool: vi.fn(),
      isUpdating: false,
      updateError: null,
      resetUpdateError: vi.fn(),
      syncTool: vi.fn(),
      syncingId: null,
      deleteTool: vi.fn(),
      deletingId: null,
    });

    mockUseRepoMcpConfig.mockReturnValue(createRepoConfigHookResult());
    mockUseMcpPresets.mockReturnValue(createMcpPresetsHookResult());
  });

  it('surfaces repository config rate-limit errors with a retry action', async () => {
    const user = userEvent.setup();
    const refetchRepoConfig = vi.fn();

    mockUseRepoMcpConfig.mockReturnValue({
      ...createRepoConfigHookResult(),
      repoConfig: null,
      error: 'Too Many Requests',
      rawError: new ApiError(429, { error: 'Too Many Requests' }),
      refetch: refetchRepoConfig,
    });

    render(<ToolsPanel projectId="project-1" />);

    expect(
      screen.getByText('Rate limit reached. Please wait a few minutes before retrying.')
    ).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Retry' }));

    expect(refetchRepoConfig).toHaveBeenCalledTimes(1);
  });

  it('surfaces preset rate-limit errors with a retry action', async () => {
    const user = userEvent.setup();
    const refetchPresets = vi.fn();

    mockUseMcpPresets.mockReturnValue({
      ...createMcpPresetsHookResult(),
      error: 'Too Many Requests',
      rawError: new ApiError(429, { error: 'Too Many Requests' }),
      refetch: refetchPresets,
    });

    render(<ToolsPanel projectId="project-1" />);

    expect(
      screen.getByText('Rate limit reached. Please wait a few minutes before retrying.')
    ).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Retry' }));

    expect(refetchPresets).toHaveBeenCalledTimes(1);
  });
});
