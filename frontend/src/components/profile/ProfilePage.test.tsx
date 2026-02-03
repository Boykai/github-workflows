/**
 * Unit tests for ProfilePage component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProfilePage } from './ProfilePage';
import * as useAuthModule from '@/hooks/useAuth';
import type { ReactNode } from 'react';

// Mock the useAuth hook
vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(),
}));

// Mock the API
vi.mock('@/services/api', () => ({
  authApi: {
    updateProfile: vi.fn(),
  },
}));

const mockUseAuth = useAuthModule.useAuth as ReturnType<typeof vi.fn>;

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

  it('renders profile information in view mode', async () => {
    mockUseAuth.mockReturnValue({
      user: {
        github_user_id: '123',
        github_username: 'testuser',
        github_avatar_url: 'https://example.com/avatar.jpg',
        github_email: 'test@example.com',
        display_name: 'Test User',
        selected_project_id: null,
      },
      isAuthenticated: true,
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refetch: vi.fn(),
    });

    render(<ProfilePage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Profile')).toBeTruthy();
      expect(screen.getByText('Test User')).toBeTruthy();
      expect(screen.getByText('testuser')).toBeTruthy();
      expect(screen.getByText('test@example.com')).toBeTruthy();
    });
  });

  it('shows Edit button in view mode', async () => {
    mockUseAuth.mockReturnValue({
      user: {
        github_user_id: '123',
        github_username: 'testuser',
        github_avatar_url: 'https://example.com/avatar.jpg',
        github_email: 'test@example.com',
        display_name: 'Test User',
        selected_project_id: null,
      },
      isAuthenticated: true,
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refetch: vi.fn(),
    });

    render(<ProfilePage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Edit' })).toBeTruthy();
    });
  });

  it('returns null when user is not available', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refetch: vi.fn(),
    });

    const { container } = render(<ProfilePage />, { wrapper: createWrapper() });
    expect(container.firstChild).toBeNull();
  });
});
