import { beforeEach, describe, expect, it, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { render, screen } from '@/test/test-utils';
import { ApiError } from '@/services/api';
import { ToolsPanel } from './ToolsPanel';

const mockUseToolsList = vi.fn();
const mockUseRepoMcpConfig = vi.fn();
const mockUseMcpPresets = vi.fn();
const mockConfirm = vi.fn();

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
  useConfirmation: () => ({ confirm: mockConfirm }),
}));

vi.mock('./UploadMcpModal', () => ({
  UploadMcpModal: () => null,
}));

vi.mock('./EditRepoMcpModal', () => ({
  EditRepoMcpModal: () => null,
}));

function createRateLimitError(message = 'Rate limit exceeded') {
  return new ApiError(429, { error: message });
}

describe('ToolsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseToolsList.mockReturnValue({
      tools: [],
      isLoading: false,
      error: null,
      rawError: null,
      refetch: vi.fn().mockResolvedValue(undefined),
      uploadTool: vi.fn(),
      isUploading: false,
      uploadError: null,
      resetUploadError: vi.fn(),
      updateTool: vi.fn(),
      isUpdating: false,
      updateError: null,
      resetUpdateError: vi.fn(),
      syncTool: vi.fn().mockResolvedValue(undefined),
      syncingId: null,
      deleteTool: vi.fn().mockResolvedValue({ success: true, affected_agents: [] }),
      deletingId: null,
    });

    mockUseRepoMcpConfig.mockReturnValue({
      repoConfig: { paths_checked: [], available_paths: [], primary_path: null, servers: [] },
      isLoading: false,
      error: null,
      rawError: null,
      refetch: vi.fn().mockResolvedValue(undefined),
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
    });

    mockUseMcpPresets.mockReturnValue({
      presets: [],
      isLoading: false,
      error: null,
      rawError: null,
      refetch: vi.fn().mockResolvedValue(undefined),
    });
  });

  it('shows the rate limit message for repository config errors and retries through the hook', async () => {
    const user = userEvent.setup();
    const refetch = vi.fn().mockResolvedValue(undefined);

    mockUseRepoMcpConfig.mockReturnValue({
      repoConfig: null,
      isLoading: false,
      error: 'Too many requests',
      rawError: createRateLimitError(),
      refetch,
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
    });

    render(<ToolsPanel projectId="project-1" />);

    expect(
      screen.getByText('Rate limit reached. Please wait a few minutes before retrying.')
    ).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Retry' }));

    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it('shows the rate limit message for presets and retries through the hook', async () => {
    const user = userEvent.setup();
    const refetch = vi.fn().mockResolvedValue(undefined);

    mockUseMcpPresets.mockReturnValue({
      presets: [],
      isLoading: false,
      error: 'Too many requests',
      rawError: createRateLimitError(),
      refetch,
    });

    render(<ToolsPanel projectId="project-1" />);

    expect(
      screen.getByText('Rate limit reached. Please wait a few minutes before retrying.')
    ).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Retry' }));

    expect(refetch).toHaveBeenCalledTimes(1);
  });
});
