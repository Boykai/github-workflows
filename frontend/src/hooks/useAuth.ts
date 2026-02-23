/**
 * Authentication hook for GitHub OAuth.
 */

import { useCallback, useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi, ApiError } from '@/services/api';
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
  const [isProcessingToken, setIsProcessingToken] = useState(false);

  // Handle session_token from URL (OAuth callback)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionToken = params.get('session_token');
    
    if (sessionToken && !isProcessingToken) {
      setIsProcessingToken(true);
      
      // Exchange token for cookie via proxy
      authApi.setSessionFromToken(sessionToken)
        .then((user) => {
          // Update query cache with user data
          queryClient.setQueryData(['auth', 'me'], user);
          
          // Clean up URL (remove session_token param)
          const newUrl = window.location.pathname;
          window.history.replaceState({}, '', newUrl);
        })
        .catch((err) => {
          console.error('Failed to set session from token:', err);
          setError(err as Error);
        })
        .finally(() => {
          setIsProcessingToken(false);
        });
    }
  }, [queryClient, isProcessingToken]);

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
    // Don't run query while processing token
    enabled: !isProcessingToken,
  });

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
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

  // Consider loading done if we got a 401 (not authenticated) or if query completed
  const is401Error = queryError instanceof ApiError && queryError.status === 401;
  const isLoading = (queryLoading || isProcessingToken) && !is401Error && !isFetched;

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
