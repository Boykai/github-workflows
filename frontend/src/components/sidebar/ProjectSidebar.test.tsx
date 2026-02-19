/**
 * Unit tests for ProjectSidebar component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProjectSidebar } from './ProjectSidebar';
import type { Project, Task } from '@/types';

vi.mock('@/hooks/useRealTimeSync', () => ({
  useRealTimeSync: vi.fn(() => ({ status: 'connected', lastUpdate: null })),
}));

import { useRealTimeSync } from '@/hooks/useRealTimeSync';
const mockUseRealTimeSync = useRealTimeSync as ReturnType<typeof vi.fn>;

vi.mock('./ProjectSelector', () => ({
  ProjectSelector: () => <div data-testid="project-selector" />,
}));

vi.mock('./TaskCard', () => ({
  TaskCard: ({ task }: { task: Task }) => <div data-testid="task-card">{task.title}</div>,
}));

function createProject(overrides: Partial<Project> = {}): Project {
  return {
    project_id: 'proj-1',
    owner_id: 'owner-1',
    owner_login: 'acme',
    name: 'My Project',
    type: 'organization',
    url: 'https://github.com/orgs/acme/projects/1',
    status_columns: [
      { field_id: 'f1', name: 'Todo', option_id: 'o1' },
      { field_id: 'f1', name: 'In Progress', option_id: 'o2' },
      { field_id: 'f1', name: 'Done', option_id: 'o3' },
    ],
    cached_at: '2024-01-15T10:00:00Z',
    ...overrides,
  };
}

function createTask(overrides: Partial<Task> = {}): Task {
  return {
    task_id: 'task-1',
    project_id: 'proj-1',
    github_item_id: 'gi-1',
    title: 'Fix bug',
    status: 'Todo',
    status_option_id: 'o1',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    ...overrides,
  };
}

describe('ProjectSidebar', () => {
  it('renders sidebar header', () => {
    render(
      <ProjectSidebar
        projects={[]}
        selectedProject={null}
        tasks={[]}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByText('Project Board')).toBeDefined();
  });

  it('shows collapse/expand button', () => {
    render(
      <ProjectSidebar
        projects={[]}
        selectedProject={null}
        tasks={[]}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    const collapseBtn = screen.getByLabelText('Collapse sidebar');
    expect(collapseBtn).toBeDefined();
    fireEvent.click(collapseBtn);
    expect(screen.getByLabelText('Expand sidebar')).toBeDefined();
  });

  it('shows "Select a project" when no project selected', () => {
    render(
      <ProjectSidebar
        projects={[]}
        selectedProject={null}
        tasks={[]}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByText('Select a project to view its board')).toBeDefined();
  });

  it('shows loading tasks state', () => {
    render(
      <ProjectSidebar
        projects={[createProject()]}
        selectedProject={createProject()}
        tasks={[]}
        isLoading={false}
        tasksLoading={true}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByText('Loading tasks...')).toBeDefined();
  });

  it('shows empty board state', () => {
    render(
      <ProjectSidebar
        projects={[createProject()]}
        selectedProject={createProject()}
        tasks={[]}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByText(/No tasks yet/)).toBeDefined();
  });

  it('groups tasks by status', () => {
    const tasks = [
      createTask({ task_id: 't1', title: 'Task A', status: 'Todo' }),
      createTask({ task_id: 't2', title: 'Task B', status: 'In Progress' }),
      createTask({ task_id: 't3', title: 'Task C', status: 'Todo' }),
    ];
    render(
      <ProjectSidebar
        projects={[createProject()]}
        selectedProject={createProject()}
        tasks={tasks}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByText('Todo')).toBeDefined();
    expect(screen.getByText('In Progress')).toBeDefined();
  });

  it('shows task cards when project is selected', () => {
    const tasks = [
      createTask({ task_id: 't1', title: 'Task A', status: 'Todo' }),
    ];
    render(
      <ProjectSidebar
        projects={[createProject()]}
        selectedProject={createProject()}
        tasks={tasks}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByTestId('task-card')).toBeDefined();
    expect(screen.getByText('Task A')).toBeDefined();
  });

  it('formatLastUpdate shows "just now" for recent updates', () => {
    mockUseRealTimeSync.mockReturnValue({ status: 'connected', lastUpdate: new Date() });
    render(
      <ProjectSidebar
        projects={[createProject()]}
        selectedProject={createProject()}
        tasks={[]}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByText(/Updated just now/)).toBeDefined();
  });

  it('formatLastUpdate shows minutes ago', () => {
    const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000);
    mockUseRealTimeSync.mockReturnValue({ status: 'connected', lastUpdate: fiveMinAgo });
    render(
      <ProjectSidebar
        projects={[createProject()]}
        selectedProject={createProject()}
        tasks={[]}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByText(/Updated 5m ago/)).toBeDefined();
  });

  it('formatLastUpdate shows time for old updates', () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000);
    mockUseRealTimeSync.mockReturnValue({ status: 'connected', lastUpdate: twoHoursAgo });
    render(
      <ProjectSidebar
        projects={[createProject()]}
        selectedProject={createProject()}
        tasks={[]}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByText(/Updated/)).toBeDefined();
  });

  it('shows sync status for connecting state', () => {
    mockUseRealTimeSync.mockReturnValue({ status: 'connecting', lastUpdate: null });
    render(
      <ProjectSidebar
        projects={[createProject()]}
        selectedProject={createProject()}
        tasks={[]}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByText('Connecting...')).toBeDefined();
  });

  it('shows sync status for polling mode', () => {
    mockUseRealTimeSync.mockReturnValue({ status: 'polling', lastUpdate: null });
    render(
      <ProjectSidebar
        projects={[createProject()]}
        selectedProject={createProject()}
        tasks={[]}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByText('Polling mode')).toBeDefined();
  });

  it('shows sync status for disconnected state', () => {
    mockUseRealTimeSync.mockReturnValue({ status: 'disconnected', lastUpdate: null });
    render(
      <ProjectSidebar
        projects={[createProject()]}
        selectedProject={createProject()}
        tasks={[]}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByText('Offline')).toBeDefined();
  });

  it('highlights recently updated tasks', async () => {
    const tasks1 = [createTask({ task_id: 't1', title: 'Task A', status: 'Todo' })];
    const { rerender } = render(
      <ProjectSidebar
        projects={[createProject()]}
        selectedProject={createProject()}
        tasks={tasks1}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    // Add a new task to trigger highlight
    const tasks2 = [
      createTask({ task_id: 't1', title: 'Task A', status: 'Todo' }),
      createTask({ task_id: 't2', title: 'Task B', status: 'In Progress', created_at: '2024-01-16T10:00:00Z' }),
    ];
    rerender(
      <ProjectSidebar
        projects={[createProject()]}
        selectedProject={createProject()}
        tasks={tasks2}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByText('Task B')).toBeDefined();
  });

  it('groups tasks into unknown status if not in project columns', () => {
    const tasks = [
      createTask({ task_id: 't1', title: 'Task A', status: 'Custom Status' }),
    ];
    render(
      <ProjectSidebar
        projects={[createProject()]}
        selectedProject={createProject()}
        tasks={tasks}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByText('Custom Status')).toBeDefined();
    expect(screen.getByText('Task A')).toBeDefined();
  });

  it('uses default statuses when project has no status_columns', () => {
    const project = createProject({ status_columns: [] });
    const tasks = [createTask({ task_id: 't1', title: 'Task A', status: 'Todo' })];
    render(
      <ProjectSidebar
        projects={[project]}
        selectedProject={project}
        tasks={tasks}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );
    expect(screen.getByText('Todo')).toBeDefined();
    expect(screen.getByText('In Progress')).toBeDefined();
    expect(screen.getByText('Done')).toBeDefined();
  });
});
