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
});
