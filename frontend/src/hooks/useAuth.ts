/**
 * Authentication hook for GitHub OAuth.
 *
 * Session credentials are delivered exclusively via HttpOnly cookies
 * set by the backend on the OAuth callback redirect.  The frontend
 * never reads tokens from URL parameters.
 */

import { useCallback, useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi, ApiError, onAuthExpired } from '@/services/api';
import { clearChatStorage } from '@/hooks/useChatHistory';
import { STALE_TIME_LONG } from '@/constants';
import type { User } from '@/types';

interface UseAuthReturn {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: Error | null;
  login: () => void;
  logout: () => Promise<void>;
  refetch: () => void;
}

export function useAuth(): UseAuthReturn {
  const queryClient = useQueryClient();
  const [error, setError] = useState<Error | null>(null);

  // After OAuth callback, the backend sets an HttpOnly cookie directly
  // on the redirect response — no session_token in the URL.
  // If we land on /auth/callback, just trigger a refetch of /me.
  useEffect(() => {
    if (window.location.pathname === '/auth/callback') {
      // Clean up the callback path from the URL
      window.history.replaceState({}, '', '/');
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
    }
  }, [queryClient]);

  const {
    data: user,
    isLoading: queryLoading,
    isFetched,
    error: queryError,
    refetch,
  } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: authApi.getCurrentUser,
    retry: false,
    staleTime: STALE_TIME_LONG,
  });

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      // Clear all local data on logout (privacy)
      clearChatStorage();
      queryClient.setQueryData(['auth', 'me'], null);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['chat'] });
    },
    onError: (err) => {
      setError(err as Error);
    },
  });

  const login = useCallback(() => {
    authApi.login();
  }, []);

  const logout = useCallback(async () => {
    await logoutMutation.mutateAsync();
  }, [logoutMutation]);

  // Handle auth errors (401 means not logged in, which is expected)
  useEffect(() => {
    if (queryError && !(queryError instanceof ApiError && queryError.status === 401)) {
      setError(queryError as Error);
    }
  }, [queryError]);

  // Auto-logout: when any API call returns 401 (session/token expired),
  // clear the cached user so the app shows the login screen immediately
  // instead of leaving the user stuck on a broken board page.
  useEffect(() => {
    return onAuthExpired(() => {
      queryClient.setQueryData(['auth', 'me'], null);
      queryClient.invalidateQueries({ queryKey: ['board'] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['chat'] });
    });
  }, [queryClient]);

  // Consider loading done if we got a 401 (not authenticated) or if query completed
  const is401Error = queryError instanceof ApiError && queryError.status === 401;
  const isLoading = queryLoading && !is401Error && !isFetched;

  return {
    user: user ?? null,
    isLoading,
    isAuthenticated: !!user,
    error,
    login,
    logout,
    refetch,
  };
}
