/**
 * Unit tests for LoginButton component.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LoginButton } from './LoginButton';

// Mock useAuth hook
const mockLogin = vi.fn();
const mockLogout = vi.fn();
let mockAuthState = {
  isAuthenticated: false,
  isLoading: false,
  user: null as { github_username: string; github_avatar_url?: string } | null,
  login: mockLogin,
  logout: mockLogout,
};

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => mockAuthState,
}));

describe('LoginButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAuthState = {
      isAuthenticated: false,
      isLoading: false,
      user: null,
      login: mockLogin,
      logout: mockLogout,
    };
  });

  it('should show loading button when auth is loading', () => {
    mockAuthState.isLoading = true;

    render(<LoginButton />);

    const button = screen.getByRole('button', { name: /loading/i });
    expect(button).toBeDefined();
    expect(button.hasAttribute('disabled')).toBe(true);
  });

  it('should show login button when not authenticated', () => {
    render(<LoginButton />);

    expect(screen.getByText('Login with GitHub')).toBeDefined();
  });

  it('should call login when login button is clicked', () => {
    render(<LoginButton />);

    fireEvent.click(screen.getByText('Login with GitHub'));

    expect(mockLogin).toHaveBeenCalledOnce();
  });

  it('should show user info and logout when authenticated', () => {
    mockAuthState.isAuthenticated = true;
    mockAuthState.user = {
      github_username: 'testuser',
      github_avatar_url: 'https://avatar.example.com',
    };

    render(<LoginButton />);

    expect(screen.getByText('testuser')).toBeDefined();
    expect(screen.getByRole('button', { name: /logout/i })).toBeDefined();
  });

  it('should call logout when logout button is clicked', () => {
    mockAuthState.isAuthenticated = true;
    mockAuthState.user = {
      github_username: 'testuser',
    };

    render(<LoginButton />);

    fireEvent.click(screen.getByRole('button', { name: /logout/i }));

    expect(mockLogout).toHaveBeenCalledOnce();
  });

  it('should render avatar when github_avatar_url is provided', () => {
    mockAuthState.isAuthenticated = true;
    mockAuthState.user = {
      github_username: 'testuser',
      github_avatar_url: 'https://avatar.example.com/123',
    };

    render(<LoginButton />);

    const img = screen.getByAltText('testuser');
    expect(img).toBeDefined();
    expect(img.getAttribute('src')).toBe('https://avatar.example.com/123');
  });
});
