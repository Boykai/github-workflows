/**
 * Unit tests for useProjectBoard hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useProjectBoard } from './useProjectBoard';
import * as api from '@/services/api';
import type { ReactNode } from 'react';

// Mock the API module
vi.mock('@/services/api', () => ({
  boardApi: {
    listProjects: vi.fn(),
    getBoardData: vi.fn(),
  },
}));

// Mock constants so queries fire immediately
vi.mock('@/constants', () => ({
  STALE_TIME_LONG: 0,
  STALE_TIME_SHORT: 0,
}));

const mockBoardApi = api.boardApi as unknown as {
  listProjects: ReturnType<typeof vi.fn>;
  getBoardData: ReturnType<typeof vi.fn>;
};

// Create wrapper with QueryClientProvider
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

describe('useProjectBoard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should return empty projects initially while loading', () => {
    mockBoardApi.listProjects.mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useProjectBoard(), {
      wrapper: createWrapper(),
    });

    expect(result.current.projects).toEqual([]);
    expect(result.current.projectsLoading).toBe(true);
  });

  it('should return projects after loading', async () => {
    // Use type-accurate BoardProjectListResponse shape — status_field uses
    // field_id (not id) to match the real BoardStatusField interface.
    const mockProjects = {
      projects: [
        { project_id: 'PVT_1', name: 'Board Alpha', url: 'https://github.com', owner_login: 'user', status_field: { field_id: 'sf1', options: [] } },
        { project_id: 'PVT_2', name: 'Board Beta', url: 'https://github.com', owner_login: 'user', status_field: { field_id: 'sf2', options: [] } },
      ],
    };

    mockBoardApi.listProjects.mockResolvedValue(mockProjects);

    const { result } = renderHook(() => useProjectBoard(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.projectsLoading).toBe(false);
    });

    expect(result.current.projects).toHaveLength(2);
    expect(result.current.projects[0].project_id).toBe('PVT_1');
    expect(result.current.projects[1].name).toBe('Board Beta');
  });

  it('should fetch board data when selectedProjectId is provided', async () => {
    // Use type-accurate shapes matching BoardProject / BoardDataResponse.
    const mockProjects = {
      projects: [
        { project_id: 'PVT_1', name: 'Board Alpha', url: 'https://github.com', owner_login: 'user', status_field: { field_id: 'sf1', options: [] } },
      ],
    };
    const mockBoardData = {
      project: mockProjects.projects[0],
      columns: [
        {
          status: { option_id: 'opt1', name: 'Todo', color: 'GRAY' },
          items: [],
          item_count: 0,
          estimate_total: 0,
        },
      ],
    };

    mockBoardApi.listProjects.mockResolvedValue(mockProjects);
    mockBoardApi.getBoardData.mockResolvedValue(mockBoardData);

    const { result } = renderHook(
      () => useProjectBoard({ selectedProjectId: 'PVT_1' }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.boardData).not.toBeNull();
    });

    expect(result.current.boardData?.columns).toHaveLength(1);
    expect(mockBoardApi.getBoardData).toHaveBeenCalledWith('PVT_1');
  });

  it('selectProject should call onProjectSelect callback', async () => {
    mockBoardApi.listProjects.mockResolvedValue({ projects: [] });
    const onProjectSelect = vi.fn();

    const { result } = renderHook(
      () => useProjectBoard({ onProjectSelect }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.projectsLoading).toBe(false);
    });

    act(() => {
      result.current.selectProject('PVT_99');
    });

    expect(onProjectSelect).toHaveBeenCalledWith('PVT_99');
  });

  it('should handle error when fetching projects fails', async () => {
    mockBoardApi.listProjects.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useProjectBoard(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.projectsLoading).toBe(false);
    });

    expect(result.current.projectsError).toBeInstanceOf(Error);
    expect(result.current.projectsError?.message).toBe('Network error');
  });
});
