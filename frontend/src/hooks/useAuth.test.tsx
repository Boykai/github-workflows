/**
 * Unit tests for useAuth hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth } from './useAuth';
import * as api from '@/services/api';
import type { ReactNode } from 'react';

// Mock the API module
vi.mock('@/services/api', () => ({
  authApi: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    setSessionFromToken: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(public status: number, public error: { error: string }) {
      super(error.error);
      this.name = 'ApiError';
    }
  },
}));

const mockAuthApi = api.authApi as unknown as {
  getCurrentUser: ReturnType<typeof vi.fn>;
  login: ReturnType<typeof vi.fn>;
  logout: ReturnType<typeof vi.fn>;
  setSessionFromToken: ReturnType<typeof vi.fn>;
};

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

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset window.location.search
    Object.defineProperty(window, 'location', {
      value: {
        protocol: 'http:',
        host: 'localhost:5173',
        href: 'http://localhost:5173/',
        pathname: '/',
        search: '',
        hash: '',
      },
      writable: true,
    });
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should return null user when not authenticated', async () => {
    mockAuthApi.getCurrentUser.mockRejectedValue(
      new api.ApiError(401, { error: 'Not authenticated' })
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('should return user when authenticated', async () => {
    const mockUser = {
      github_user_id: '12345',
      github_username: 'testuser',
      github_avatar_url: 'https://avatar.example.com',
      selected_project_id: null,
    };

    mockAuthApi.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.user?.github_username).toBe('testuser');
  });

  it('should have login function that redirects', async () => {
    mockAuthApi.getCurrentUser.mockRejectedValue(
      new api.ApiError(401, { error: 'Not authenticated' })
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Login function should exist
    expect(typeof result.current.login).toBe('function');
  });

  it('should logout and clear user', async () => {
    const mockUser = {
      github_user_id: '12345',
      github_username: 'testuser',
      selected_project_id: null,
    };

    mockAuthApi.getCurrentUser.mockResolvedValue(mockUser);
    mockAuthApi.logout.mockResolvedValue({ message: 'Logged out' });

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    // Perform logout
    await act(async () => {
      await result.current.logout();
    });

    await waitFor(() => {
      expect(result.current.user).toBeNull();
    });

    expect(mockAuthApi.logout).toHaveBeenCalled();
  });

  it('should return selected_project_id when user has one', async () => {
    const mockUser = {
      github_user_id: '12345',
      github_username: 'testuser',
      selected_project_id: 'PVT_abc123',
    };

    mockAuthApi.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    expect(result.current.user?.selected_project_id).toBe('PVT_abc123');
  });

  describe('session token handling', () => {
    it('should process session_token from URL and exchange it', async () => {
      const mockUser = {
        github_user_id: '12345',
        github_username: 'testuser',
        selected_project_id: null,
      };

      // Set up URL with session_token
      Object.defineProperty(window, 'location', {
        value: {
          protocol: 'http:',
          host: 'localhost:5173',
          href: 'http://localhost:5173/?session_token=test-session-token',
          pathname: '/',
          search: '?session_token=test-session-token',
          hash: '',
        },
        writable: true,
      });

      // Mock history.replaceState
      const replaceStateSpy = vi.spyOn(window.history, 'replaceState');

      mockAuthApi.setSessionFromToken.mockResolvedValue(mockUser);
      mockAuthApi.getCurrentUser.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockAuthApi.setSessionFromToken).toHaveBeenCalledWith('test-session-token');
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      // Should clean up URL
      expect(replaceStateSpy).toHaveBeenCalledWith({}, '', '/');
    });

    it('should handle session token exchange failure', async () => {
      Object.defineProperty(window, 'location', {
        value: {
          protocol: 'http:',
          host: 'localhost:5173',
          href: 'http://localhost:5173/?session_token=bad-token',
          pathname: '/',
          search: '?session_token=bad-token',
          hash: '',
        },
        writable: true,
      });

      mockAuthApi.setSessionFromToken.mockRejectedValue(new Error('Invalid token'));
      mockAuthApi.getCurrentUser.mockRejectedValue(
        new api.ApiError(401, { error: 'Not authenticated' })
      );

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });

      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('error handling', () => {
    it('should set error for non-401 API errors', async () => {
      mockAuthApi.getCurrentUser.mockRejectedValue(
        new api.ApiError(500, { error: 'Server error' })
      );

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });

      expect(result.current.error?.message).toBe('Server error');
    });

    it('should not set error for 401 (expected when not logged in)', async () => {
      mockAuthApi.getCurrentUser.mockRejectedValue(
        new api.ApiError(401, { error: 'Not authenticated' })
      );

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // 401 should not be treated as an error
      expect(result.current.error).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should handle logout failure', async () => {
      const mockUser = {
        github_user_id: '12345',
        github_username: 'testuser',
        selected_project_id: null,
      };

      mockAuthApi.getCurrentUser.mockResolvedValue(mockUser);
      mockAuthApi.logout.mockRejectedValue(new Error('Logout failed'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      // Attempt logout
      await act(async () => {
        try {
          await result.current.logout();
        } catch {
          // Expected to throw
        }
      });

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });
    });
  });

  describe('loading states', () => {
    it('should show loading while fetching user', async () => {
      let resolveUser: (user: unknown) => void;
      const userPromise = new Promise((resolve) => {
        resolveUser = resolve;
      });

      mockAuthApi.getCurrentUser.mockReturnValue(userPromise);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      // Initially loading
      expect(result.current.isLoading).toBe(true);

      // Resolve the promise
      await act(async () => {
        resolveUser!({
          github_user_id: '12345',
          github_username: 'testuser',
          selected_project_id: null,
        });
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('should stop loading on 401 error', async () => {
      mockAuthApi.getCurrentUser.mockRejectedValue(
        new api.ApiError(401, { error: 'Not authenticated' })
      );

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('refetch', () => {
    it('should have a refetch function', async () => {
      mockAuthApi.getCurrentUser.mockRejectedValue(
        new api.ApiError(401, { error: 'Not authenticated' })
      );

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(typeof result.current.refetch).toBe('function');
    });
  });
});
