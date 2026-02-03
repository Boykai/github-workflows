/**
 * Unit tests for ProfilePage component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProfilePage } from './ProfilePage';
import * as useAuthModule from '@/hooks/useAuth';
import type { ReactNode } from 'react';

// Mock the useAuth hook
vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(),
}));

const mockUseAuth = useAuthModule.useAuth as unknown as ReturnType<typeof vi.fn>;

// Create wrapper with QueryClientProvider
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

describe('ProfilePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should show loading state when auth is loading', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: true,
      isAuthenticated: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refetch: vi.fn(),
    });

    render(<ProfilePage />, { wrapper: createWrapper() });

    expect(screen.getByText('Loading profile...')).toBeTruthy();
  });

  it('should show error when user is not available', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refetch: vi.fn(),
    });

    render(<ProfilePage />, { wrapper: createWrapper() });

    expect(screen.getByText('Unable to load profile. Please try logging in again.')).toBeTruthy();
  });

  it('should render user profile with all fields', () => {
    const mockUser = {
      github_user_id: '12345',
      github_username: 'testuser',
      github_avatar_url: 'https://example.com/avatar.png',
      created_at: '2025-01-15T10:00:00Z',
    };

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refetch: vi.fn(),
    });

    render(<ProfilePage />, { wrapper: createWrapper() });

    expect(screen.getByText('User Profile')).toBeTruthy();
    expect(screen.getByText('testuser')).toBeTruthy();
    expect(screen.getByText('12345')).toBeTruthy();
    expect(screen.getByText('Edit Profile')).toBeTruthy();
  });

  it('should display avatar when user has avatar_url', () => {
    const mockUser = {
      github_user_id: '12345',
      github_username: 'testuser',
      github_avatar_url: 'https://example.com/avatar.png',
    };

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refetch: vi.fn(),
    });

    render(<ProfilePage />, { wrapper: createWrapper() });

    const avatar = screen.getByAltText('testuser');
    expect(avatar).toBeTruthy();
    expect((avatar as HTMLImageElement).src).toBe('https://example.com/avatar.png');
  });

  it('should display placeholder when user has no avatar_url', () => {
    const mockUser = {
      github_user_id: '12345',
      github_username: 'testuser',
    };

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refetch: vi.fn(),
    });

    render(<ProfilePage />, { wrapper: createWrapper() });

    expect(screen.getByText('T')).toBeTruthy(); // First letter placeholder
  });

  it('should format created_at date correctly', () => {
    const mockUser = {
      github_user_id: '12345',
      github_username: 'testuser',
      created_at: '2025-01-15T10:00:00Z',
    };

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refetch: vi.fn(),
    });

    render(<ProfilePage />, { wrapper: createWrapper() });

    // The date should be formatted, not exact match but should contain the text
    expect(screen.getByText(/january|february|march|april|may|june|july|august|september|october|november|december/i)).toBeTruthy();
  });

  it('should show N/A when created_at is not available', () => {
    const mockUser = {
      github_user_id: '12345',
      github_username: 'testuser',
    };

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refetch: vi.fn(),
    });

    render(<ProfilePage />, { wrapper: createWrapper() });

    expect(screen.getByText('N/A')).toBeTruthy();
  });
});
