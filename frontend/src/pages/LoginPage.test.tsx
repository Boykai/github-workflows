import { describe, expect, it, vi } from 'vitest';
import { screen, render } from '@/test/test-utils';
import { LoginPage } from './LoginPage';

vi.mock('@/components/auth/LoginButton', () => ({
  LoginButton: () => <button data-testid="login-button">Sign in with GitHub</button>,
}));

vi.mock('@/components/AnimatedBackground', () => ({
  AnimatedBackground: () => <div data-testid="animated-bg" />,
}));

const mockTheme = vi.hoisted(() => ({
  theme: 'dark' as string,
  setTheme: vi.fn(),
}));

vi.mock('@/components/ThemeProvider', () => ({
  useTheme: () => mockTheme,
}));

describe('LoginPage', () => {
  it('renders the Solune branding', () => {
    render(<LoginPage />);
    expect(screen.getByText('Solune')).toBeInTheDocument();
  });

  it('renders the login button', () => {
    render(<LoginPage />);
    expect(screen.getByTestId('login-button')).toBeInTheDocument();
  });

  it('renders the animated background', () => {
    render(<LoginPage />);
    expect(screen.getByTestId('animated-bg')).toBeInTheDocument();
  });

  it('renders the headline', () => {
    render(<LoginPage />);
    expect(screen.getByText('Change your workflow mindset.')).toBeInTheDocument();
  });

  it('shows GitHub sign in required note', () => {
    render(<LoginPage />);
    expect(screen.getByText('GitHub sign in required')).toBeInTheDocument();
  });

  it('shows theme toggle button with correct aria-label', () => {
    mockTheme.theme = 'dark';
    render(<LoginPage />);
    expect(screen.getByRole('button', { name: 'Switch to light theme' })).toBeInTheDocument();
  });
});
