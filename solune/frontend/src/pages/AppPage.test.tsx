import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, userEvent } from '@/test/test-utils';
import { AppPage } from './AppPage';

const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mocks.navigate,
  };
});

describe('AppPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the apps quick-launch button', () => {
    render(<AppPage />);

    expect(screen.getByRole('button', { name: /open apps page/i })).toBeInTheDocument();
  });

  it('navigates to the apps page when the animated icon button is clicked', async () => {
    render(<AppPage />);

    await userEvent.click(screen.getByRole('button', { name: /open apps page/i }));

    expect(mocks.navigate).toHaveBeenCalledWith('/apps');
  });
});