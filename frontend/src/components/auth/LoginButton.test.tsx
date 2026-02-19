/**
 * Unit tests for LoginButton component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LoginButton } from './LoginButton';

// Mock useAuth hook
const mockLogin = vi.fn();
const mockLogout = vi.fn();
const mockUseAuth = vi.fn();

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

describe('LoginButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading button when isLoading', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      user: null,
      login: mockLogin,
      logout: mockLogout,
    });

    render(<LoginButton />);
    const button = screen.getByText('Loading...');
    expect(button).toBeDefined();
    expect(button.closest('button')?.disabled).toBe(true);
  });

  it('shows login button when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      login: mockLogin,
      logout: mockLogout,
    });

    render(<LoginButton />);
    expect(screen.getByText('Login with GitHub')).toBeDefined();
  });

  it('shows user info with logout when authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        github_user_id: '123',
        github_username: 'testuser',
      },
      login: mockLogin,
      logout: mockLogout,
    });

    render(<LoginButton />);
    expect(screen.getByText('testuser')).toBeDefined();
    expect(screen.getByText('Logout')).toBeDefined();
  });

  it('shows avatar when user has github_avatar_url', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        github_user_id: '123',
        github_username: 'testuser',
        github_avatar_url: 'https://avatar.example.com/testuser',
      },
      login: mockLogin,
      logout: mockLogout,
    });

    render(<LoginButton />);
    const avatar = screen.getByAltText('testuser');
    expect(avatar).toBeDefined();
    expect(avatar.getAttribute('src')).toBe('https://avatar.example.com/testuser');
  });

  it('does not show avatar when user has no github_avatar_url', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        github_user_id: '123',
        github_username: 'noavatar',
      },
      login: mockLogin,
      logout: mockLogout,
    });

    render(<LoginButton />);
    expect(screen.queryByRole('img')).toBeNull();
  });

  it('login button calls login', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      login: mockLogin,
      logout: mockLogout,
    });

    render(<LoginButton />);
    fireEvent.click(screen.getByText('Login with GitHub'));
    expect(mockLogin).toHaveBeenCalledOnce();
  });

  it('logout button calls logout', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        github_user_id: '123',
        github_username: 'testuser',
      },
      login: mockLogin,
      logout: mockLogout,
    });

    render(<LoginButton />);
    fireEvent.click(screen.getByText('Logout'));
    expect(mockLogout).toHaveBeenCalledOnce();
  });
});
