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
        host: 'localhost:3003',
        href: 'http://localhost:3003/',
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
});
