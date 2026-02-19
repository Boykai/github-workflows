/**
 * Unit tests for TaskCard component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TaskCard } from './TaskCard';
import type { Task } from '@/types';

function createTask(overrides: Partial<Task> = {}): Task {
  return {
    task_id: 'task-1',
    project_id: 'proj-1',
    github_item_id: 'gi-1',
    title: 'Implement feature',
    status: 'In Progress',
    status_option_id: 'opt-1',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T12:00:00Z',
    ...overrides,
  };
}

describe('TaskCard', () => {
  it('renders task title and status', () => {
    render(<TaskCard task={createTask()} />);
    expect(screen.getByText('Implement feature')).toBeDefined();
    expect(screen.getByText('In Progress')).toBeDefined();
  });

  it('shows description', () => {
    render(<TaskCard task={createTask({ description: 'A short description' })} />);
    expect(screen.getByText('A short description')).toBeDefined();
  });

  it('truncates description longer than 100 chars', () => {
    const longDesc = 'X'.repeat(150);
    render(<TaskCard task={createTask({ description: longDesc })} />);
    expect(screen.getByText('X'.repeat(100) + '...')).toBeDefined();
  });

  it('does not render description when absent', () => {
    const { container } = render(<TaskCard task={createTask()} />);
    expect(container.querySelector('.task-description')).toBeNull();
  });

  it('applies highlighted class when isHighlighted', () => {
    const { container } = render(<TaskCard task={createTask()} isHighlighted />);
    expect(container.querySelector('.task-card--highlighted')).not.toBeNull();
  });

  it('does not apply highlighted class by default', () => {
    const { container } = render(<TaskCard task={createTask()} />);
    expect(container.querySelector('.task-card--highlighted')).toBeNull();
  });

  it('clicking calls onClick', () => {
    const onClick = vi.fn();
    render(<TaskCard task={createTask()} onClick={onClick} />);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
