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

const mockBoardApi = api.boardApi as unknown as {
  listProjects: ReturnType<typeof vi.fn>;
  getBoardData: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
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

  it('should return projects list', async () => {
    const projects = [
      { project_id: 'PVT_1', name: 'Project 1', url: 'https://github.com', owner_login: 'user', status_field: { id: 'f1', name: 'Status' } },
      { project_id: 'PVT_2', name: 'Project 2', url: 'https://github.com', owner_login: 'user', status_field: { id: 'f2', name: 'Status' } },
    ];
    mockBoardApi.listProjects.mockResolvedValue({ projects });

    const { result } = renderHook(() => useProjectBoard(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.projectsLoading).toBe(false);
    });

    expect(result.current.projects).toEqual(projects);
    expect(result.current.projects).toHaveLength(2);
  });

  it('should return empty projects initially', async () => {
    mockBoardApi.listProjects.mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useProjectBoard(), {
      wrapper: createWrapper(),
    });

    expect(result.current.projects).toEqual([]);
    expect(result.current.projectsLoading).toBe(true);
  });

  it('should return boardData when project is selected', async () => {
    mockBoardApi.listProjects.mockResolvedValue({ projects: [] });
    const boardData = {
      project: { project_id: 'PVT_1', name: 'Project 1' },
      columns: [{ name: 'Todo', items: [] }],
    };
    mockBoardApi.getBoardData.mockResolvedValue(boardData);

    const { result } = renderHook(
      () => useProjectBoard({ selectedProjectId: 'PVT_1' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.boardData).not.toBeNull();
    });

    expect(result.current.boardData).toEqual(boardData);
    expect(mockBoardApi.getBoardData).toHaveBeenCalledWith('PVT_1');
  });

  it('selectProject calls onProjectSelect callback', async () => {
    mockBoardApi.listProjects.mockResolvedValue({ projects: [] });
    const onSelect = vi.fn();

    const { result } = renderHook(
      () => useProjectBoard({ onProjectSelect: onSelect }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.projectsLoading).toBe(false);
    });

    act(() => {
      result.current.selectProject('PVT_1');
    });

    expect(onSelect).toHaveBeenCalledWith('PVT_1');
  });

  it('should handle loading states correctly', async () => {
    mockBoardApi.listProjects.mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useProjectBoard(), {
      wrapper: createWrapper(),
    });

    expect(result.current.projectsLoading).toBe(true);
    expect(result.current.boardLoading).toBe(false);
  });

  it('should handle no project selected', async () => {
    mockBoardApi.listProjects.mockResolvedValue({ projects: [] });

    const { result } = renderHook(
      () => useProjectBoard({ selectedProjectId: null }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.projectsLoading).toBe(false);
    });

    expect(result.current.boardData).toBeNull();
    expect(result.current.selectedProjectId).toBeNull();
    expect(mockBoardApi.getBoardData).not.toHaveBeenCalled();
  });

  it('should handle projects error', async () => {
    mockBoardApi.listProjects.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useProjectBoard(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.projectsLoading).toBe(false);
    });

    expect(result.current.projectsError).not.toBeNull();
    expect(result.current.projectsError?.message).toBe('Network error');
  });

  it('should handle board data error', async () => {
    mockBoardApi.listProjects.mockResolvedValue({ projects: [] });
    mockBoardApi.getBoardData.mockRejectedValue(new Error('Board fetch failed'));

    const { result } = renderHook(
      () => useProjectBoard({ selectedProjectId: 'PVT_1' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.boardError).not.toBeNull();
    });

    expect(result.current.boardError?.message).toBe('Board fetch failed');
  });

  it('should set lastUpdated after board data loads', async () => {
    mockBoardApi.listProjects.mockResolvedValue({ projects: [] });
    mockBoardApi.getBoardData.mockResolvedValue({
      project: { project_id: 'PVT_1' },
      columns: [],
    });

    const { result } = renderHook(
      () => useProjectBoard({ selectedProjectId: 'PVT_1' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.boardData).not.toBeNull();
    });

    expect(result.current.lastUpdated).toBeInstanceOf(Date);
  });
});
