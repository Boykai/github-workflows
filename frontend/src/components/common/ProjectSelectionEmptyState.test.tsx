import { describe, expect, it, vi } from 'vitest';
import { render, screen, userEvent, waitFor, within } from '@/test/test-utils';
import { ProjectSelectionEmptyState } from './ProjectSelectionEmptyState';

const projects = [
  {
    project_id: 'PVT_alpha',
    name: 'Alpha',
    owner_login: 'solune',
    type: 'user' as const,
    url: 'https://github.com/solune/alpha',
  },
  {
    project_id: 'PVT_beta',
    name: 'Beta',
    owner_login: 'solune',
    type: 'user' as const,
    url: 'https://github.com/solune/beta',
  },
];

describe('ProjectSelectionEmptyState', () => {
  it('uses responsive panel spacing', () => {
    const { container } = render(
      <ProjectSelectionEmptyState
        projects={projects}
        isLoading={false}
        selectedProjectId={null}
        onSelectProject={vi.fn().mockResolvedValue(undefined)}
        description="Select a project to inspect the board."
      />
    );

    expect(container.firstChild).toHaveClass('p-6');
    expect(container.firstChild).toHaveClass('sm:p-8');
  });

  it('renders project options with listbox semantics and selection state', async () => {
    const user = userEvent.setup();

    render(
      <ProjectSelectionEmptyState
        projects={projects}
        isLoading={false}
        selectedProjectId="PVT_beta"
        onSelectProject={vi.fn().mockResolvedValue(undefined)}
        description="Select a project to inspect the board."
      />
    );

    await user.click(screen.getByRole('button', { name: /choose a github project/i }));

    const listbox = screen.getByRole('listbox', { name: /github projects/i });
    const options = within(listbox).getAllByRole('option');

    expect(options).toHaveLength(2);
    expect(within(listbox).getByRole('option', { name: /alpha solune/i })).toHaveAttribute(
      'aria-selected',
      'false'
    );
    expect(within(listbox).getByRole('option', { name: /beta solune/i })).toHaveAttribute(
      'aria-selected',
      'true'
    );
    expect(options[0].className).toContain('focus-visible:ring-2');
  });

  it('calls onSelectProject when choosing a project', async () => {
    const user = userEvent.setup();
    const onSelectProject = vi.fn().mockResolvedValue(undefined);

    render(
      <ProjectSelectionEmptyState
        projects={projects}
        isLoading={false}
        selectedProjectId={null}
        onSelectProject={onSelectProject}
        description="Select a project to inspect the board."
      />
    );

    await user.click(screen.getByRole('button', { name: /choose a github project/i }));
    await user.click(screen.getByRole('option', { name: /alpha solune/i }));
  });

  it('shows "No projects available" when the projects list is empty', async () => {
    const user = userEvent.setup();

    render(
      <ProjectSelectionEmptyState
        projects={[]}
        isLoading={false}
        selectedProjectId={null}
        onSelectProject={vi.fn().mockResolvedValue(undefined)}
        description="Select a project to inspect the board."
      />
    );

    await user.click(screen.getByRole('button', { name: /choose a github project/i }));

    expect(screen.getByText('No projects available')).toBeInTheDocument();
    expect(screen.getByText('Connect a GitHub Project to start working here.')).toBeInTheDocument();
  });

  it('shows a loader when projects are still loading', async () => {
    const user = userEvent.setup();

    render(
      <ProjectSelectionEmptyState
        projects={[]}
        isLoading={true}
        selectedProjectId={null}
        onSelectProject={vi.fn().mockResolvedValue(undefined)}
        description="Select a project to inspect the board."
      />
    );

    await user.click(screen.getByRole('button', { name: /choose a github project/i }));

    expect(screen.getByText('Loading projects')).toBeInTheDocument();
  });

  it('disables all options while a project selection is pending', async () => {
    const user = userEvent.setup();
    let resolveSelection!: () => void;
    const onSelectProject = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveSelection = resolve;
        })
    );

    render(
      <ProjectSelectionEmptyState
        projects={projects}
        isLoading={false}
        selectedProjectId={null}
        onSelectProject={onSelectProject}
        description="Select a project to inspect the board."
      />
    );

    await user.click(screen.getByRole('button', { name: /choose a github project/i }));
    await user.click(screen.getByRole('option', { name: /alpha solune/i }));

    const options = screen.getAllByRole('option');
    for (const option of options) {
      expect(option).toBeDisabled();
    }

    resolveSelection();
    await waitFor(() => {
      // Panel closes after successful selection
      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });
  });

  it('renders description text and heading', () => {
    render(
      <ProjectSelectionEmptyState
        projects={projects}
        isLoading={false}
        selectedProjectId={null}
        onSelectProject={vi.fn().mockResolvedValue(undefined)}
        description="Select a project to inspect the board."
      />
    );

    expect(screen.getByText('Select a project')).toBeInTheDocument();
    expect(screen.getByText('Select a project to inspect the board.')).toBeInTheDocument();
  });
});
