/**
 * Unit tests for useProjects hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useProjects } from './useProjects';
import * as api from '@/services/api';
import type { ReactNode } from 'react';

// Mock the API module
vi.mock('@/services/api', () => ({
  projectsApi: {
    list: vi.fn(),
    select: vi.fn(),
  },
  tasksApi: {
    listByProject: vi.fn(),
  },
}));

const mockProjectsApi = api.projectsApi as unknown as {
  list: ReturnType<typeof vi.fn>;
  select: ReturnType<typeof vi.fn>;
};

const mockTasksApi = api.tasksApi as unknown as {
  listByProject: ReturnType<typeof vi.fn>;
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

describe('useProjects', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should return empty projects initially when loading', () => {
    mockProjectsApi.list.mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useProjects(), {
      wrapper: createWrapper(),
    });

    expect(result.current.projects).toEqual([]);
    expect(result.current.isLoading).toBe(true);
  });

  it('should return projects after loading', async () => {
    const mockProjects = {
      projects: [
        { project_id: 'PVT_123', name: 'Project 1', owner_login: 'user', type: 'user', url: 'https://github.com' },
        { project_id: 'PVT_456', name: 'Project 2', owner_login: 'user', type: 'user', url: 'https://github.com' },
      ],
    };

    mockProjectsApi.list.mockResolvedValue(mockProjects);

    const { result } = renderHook(() => useProjects(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.projects).toHaveLength(2);
    expect(result.current.projects[0].project_id).toBe('PVT_123');
  });

  it('should fetch tasks when selectedProjectId is provided', async () => {
    const mockProjects = {
      projects: [
        { project_id: 'PVT_123', name: 'Project 1', owner_login: 'user', type: 'user', url: 'https://github.com' },
      ],
    };
    const mockTasks = {
      tasks: [
        { task_id: 'TASK_1', title: 'Task 1', status: 'Todo', project_id: 'PVT_123' },
        { task_id: 'TASK_2', title: 'Task 2', status: 'In Progress', project_id: 'PVT_123' },
      ],
    };

    mockProjectsApi.list.mockResolvedValue(mockProjects);
    mockTasksApi.listByProject.mockResolvedValue(mockTasks);

    const { result } = renderHook(() => useProjects('PVT_123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.tasks).toHaveLength(2);
    });

    expect(result.current.tasks[0].task_id).toBe('TASK_1');
    expect(mockTasksApi.listByProject).toHaveBeenCalledWith('PVT_123');
  });

  it('should not fetch tasks when selectedProjectId is null', async () => {
    const mockProjects = { projects: [] };
    mockProjectsApi.list.mockResolvedValue(mockProjects);

    const { result } = renderHook(() => useProjects(null), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockTasksApi.listByProject).not.toHaveBeenCalled();
    expect(result.current.tasks).toEqual([]);
  });

  it('should select project and update query cache', async () => {
    const mockProjects = {
      projects: [
        { project_id: 'PVT_123', name: 'Project 1', owner_login: 'user', type: 'user', url: 'https://github.com' },
      ],
    };
    const mockUser = {
      github_user_id: '12345',
      github_username: 'testuser',
      selected_project_id: 'PVT_123',
    };

    mockProjectsApi.list.mockResolvedValue(mockProjects);
    mockProjectsApi.select.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useProjects(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Select project
    await act(async () => {
      await result.current.selectProject('PVT_123');
    });

    // Check that select was called (TanStack Query passes extra params)
    expect(mockProjectsApi.select).toHaveBeenCalled();
    expect(mockProjectsApi.select.mock.calls[0][0]).toBe('PVT_123');
  });

  it('should find selected project from list', async () => {
    const mockProjects = {
      projects: [
        { project_id: 'PVT_123', name: 'Project 1', owner_login: 'user', type: 'user', url: 'https://github.com' },
        { project_id: 'PVT_456', name: 'Project 2', owner_login: 'user', type: 'user', url: 'https://github.com' },
      ],
    };
    const mockTasks = { tasks: [] };

    mockProjectsApi.list.mockResolvedValue(mockProjects);
    mockTasksApi.listByProject.mockResolvedValue(mockTasks);

    const { result } = renderHook(() => useProjects('PVT_456'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.selectedProject).not.toBeNull();
    });

    expect(result.current.selectedProject?.project_id).toBe('PVT_456');
    expect(result.current.selectedProject?.name).toBe('Project 2');
  });
});
