/**
 * Unit tests for ProjectSelector component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProjectSelector } from './ProjectSelector';
import type { Project } from '@/types';

function createProject(overrides: Partial<Project> = {}): Project {
  return {
    project_id: 'proj-1',
    owner_id: 'owner-1',
    owner_login: 'acme',
    name: 'My Project',
    type: 'organization',
    url: 'https://github.com/orgs/acme/projects/1',
    status_columns: [],
    cached_at: '2024-01-15T10:00:00Z',
    ...overrides,
  };
}

describe('ProjectSelector', () => {
  it('renders select dropdown with projects', () => {
    const projects = [
      createProject({ project_id: 'p1', name: 'Alpha', owner_login: 'acme' }),
      createProject({ project_id: 'p2', name: 'Beta', owner_login: 'acme' }),
    ];
    render(
      <ProjectSelector projects={projects} selectedProjectId={null} onSelect={vi.fn()} />
    );
    const select = screen.getByLabelText('Select Project') as HTMLSelectElement;
    expect(select).toBeDefined();
    expect(select.options.length).toBe(3); // placeholder + 2 projects
  });

  it('shows loading state', () => {
    render(
      <ProjectSelector projects={[]} selectedProjectId={null} onSelect={vi.fn()} isLoading />
    );
    expect(screen.getByText('Loading projects...')).toBeDefined();
  });

  it('calls onSelect when changed', () => {
    const onSelect = vi.fn();
    const projects = [createProject({ project_id: 'p1', name: 'Alpha' })];
    render(
      <ProjectSelector projects={projects} selectedProjectId={null} onSelect={onSelect} />
    );
    fireEvent.change(screen.getByLabelText('Select Project'), { target: { value: 'p1' } });
    expect(onSelect).toHaveBeenCalledWith('p1');
  });

  it('shows project type icons', () => {
    const projects = [
      createProject({ project_id: 'p1', name: 'Org Project', type: 'organization', owner_login: 'acme' }),
      createProject({ project_id: 'p2', name: 'User Project', type: 'user', owner_login: 'john' }),
      createProject({ project_id: 'p3', name: 'Repo Project', type: 'repository', owner_login: 'acme' }),
    ];
    render(
      <ProjectSelector projects={projects} selectedProjectId={null} onSelect={vi.fn()} />
    );
    // Check that type icons appear in the option labels
    const select = screen.getByLabelText('Select Project') as HTMLSelectElement;
    const optionTexts = Array.from(select.options).map((o) => o.textContent);
    expect(optionTexts.some((t) => t?.includes('🏢'))).toBe(true);
    expect(optionTexts.some((t) => t?.includes('👤'))).toBe(true);
    expect(optionTexts.some((t) => t?.includes('📁'))).toBe(true);
  });

  it('shows link to selected project', () => {
    const projects = [createProject({ project_id: 'p1', url: 'https://github.com/orgs/acme/projects/1' })];
    render(
      <ProjectSelector projects={projects} selectedProjectId="p1" onSelect={vi.fn()} />
    );
    const link = screen.getByTitle('Open in GitHub');
    expect(link).toBeDefined();
    expect((link as HTMLAnchorElement).href).toBe('https://github.com/orgs/acme/projects/1');
  });
});
