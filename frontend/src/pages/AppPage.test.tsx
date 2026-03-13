import { describe, expect, it, vi } from 'vitest';
import { screen, render } from '@/test/test-utils';
import { AppPage } from './AppPage';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

describe('AppPage', () => {
  it('renders the main headline', () => {
    render(<AppPage />);
    expect(screen.getByText('Change your project mindset.')).toBeInTheDocument();
  });

  it('renders all four quick-link cards', () => {
    render(<AppPage />);
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('Agents Pipelines')).toBeInTheDocument();
    expect(screen.getByText('Agents')).toBeInTheDocument();
    expect(screen.getByText('Chores')).toBeInTheDocument();
  });

  it('navigates to correct paths on card click', async () => {
    const { userEvent } = await import('@/test/test-utils');
    const user = userEvent.setup();
    render(<AppPage />);

    await user.click(screen.getByText('Projects'));
    expect(mockNavigate).toHaveBeenCalledWith('/projects');

    await user.click(screen.getByText('Agents'));
    expect(mockNavigate).toHaveBeenCalledWith('/agents');
  });

  it('shows card descriptions', () => {
    render(<AppPage />);
    expect(screen.getByText('View and manage your Kanban board')).toBeInTheDocument();
    expect(screen.getByText('Configure and manage agents')).toBeInTheDocument();
  });
});
