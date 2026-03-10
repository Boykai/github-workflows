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
  it('uses responsive panel spacing and accessible focus styles on triggers', () => {
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

    const browseButton = screen.getByRole('button', { name: /browse github projects/i });
    expect(browseButton.className).toContain('focus-visible:ring-2');
    expect(browseButton.className).toContain('focus-visible:ring-offset-background');
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

    await user.click(screen.getByRole('button', { name: /browse github projects/i }));

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

  it('closes the list after choosing a project', async () => {
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

    await user.click(screen.getByRole('button', { name: /browse github projects/i }));
    await user.click(screen.getByRole('option', { name: /alpha solune/i }));

    await waitFor(() => expect(onSelectProject).toHaveBeenCalledWith('PVT_alpha'));
    await waitFor(() =>
      expect(screen.queryByRole('listbox', { name: /github projects/i })).not.toBeInTheDocument()
    );
  });
});
