/**
 * Unit tests for ProjectSidebar component - Title verification
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProjectSidebar } from './ProjectSidebar';
import type { Project, Task } from '@/types';

// Mock the child components
vi.mock('./ProjectSelector', () => ({
  ProjectSelector: () => <div data-testid="project-selector">Project Selector</div>,
}));

vi.mock('./TaskCard', () => ({
  TaskCard: ({ task }: { task: Task }) => <div data-testid={`task-${task.task_id}`}>{task.title}</div>,
}));

vi.mock('@/hooks/useRealTimeSync', () => ({
  useRealTimeSync: () => ({
    status: 'connected',
    lastUpdate: null,
  }),
}));

describe('ProjectSidebar Component - Tech Connect 2026 Branding', () => {
  const mockProjects: Project[] = [
    {
      project_id: 'PVT_123',
      title: 'Test Project',
      number: 1,
      url: 'https://github.com/test/project',
      status_columns: [
        { name: 'Todo' },
        { name: 'In Progress' },
        { name: 'Done' },
      ],
    },
  ];

  const mockTasks: Task[] = [
    {
      task_id: 'TASK_1',
      title: 'Test Task',
      status: 'Todo',
      project_id: 'PVT_123',
      created_at: '2024-01-01T00:00:00Z',
      url: 'https://github.com/test/task/1',
      field_values: [],
    },
  ];

  it('displays "Welcome to Tech Connect 2026" in sidebar header', () => {
    render(
      <ProjectSidebar
        projects={mockProjects}
        selectedProject={mockProjects[0]}
        tasks={mockTasks}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );

    // Check for the welcome message in the sidebar header
    const heading = screen.getByRole('heading', { level: 2 });
    expect(heading.textContent).toBe('Welcome to Tech Connect 2026 - Project Board');
  });

  it('displays "Welcome to Tech Connect 2026" even when no project is selected', () => {
    render(
      <ProjectSidebar
        projects={mockProjects}
        selectedProject={null}
        tasks={[]}
        isLoading={false}
        tasksLoading={false}
        onProjectSelect={vi.fn()}
      />
    );

    // Check for the welcome message in the sidebar header
    const heading = screen.getByRole('heading', { level: 2 });
    expect(heading.textContent).toBe('Welcome to Tech Connect 2026 - Project Board');
  });
});
