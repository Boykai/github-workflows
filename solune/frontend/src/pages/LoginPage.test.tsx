import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { LoginPage } from './LoginPage';

vi.mock('@/components/ThemeProvider', () => ({
  useTheme: () => ({ theme: 'dark', setTheme: vi.fn() }),
}));

vi.mock('@/components/AnimatedBackground', () => ({
  AnimatedBackground: () => <div data-testid="animated-bg" />,
}));

vi.mock('@/components/auth/LoginButton', () => ({
  LoginButton: () => <button>Sign in with GitHub</button>,
}));

describe('LoginPage', () => {
  it('renders with Solune branding', () => {
    render(<LoginPage />);
    expect(screen.getByText(/Change your workflow mindset/i)).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<LoginPage />);
    await expectNoA11yViolations(container);
  });
});
