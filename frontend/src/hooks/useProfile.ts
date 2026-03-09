/**
 * React Query hook for user profile data management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { profileApi } from '@/services/api';
import { STALE_TIME_LONG } from '@/constants';
import type { UserProfile, UserProfileUpdate } from '@/types';

interface UseProfileReturn {
  profile: UserProfile | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
  updateProfile: (data: UserProfileUpdate) => Promise<UserProfile>;
  uploadAvatar: (file: File) => Promise<UserProfile>;
  isSaving: boolean;
  saveError: Error | null;
}

export function useProfile(): UseProfileReturn {
  const queryClient = useQueryClient();

  const {
    data: profile,
    isLoading,
    error: queryError,
    refetch,
  } = useQuery({
    queryKey: ['profile'],
    queryFn: profileApi.getProfile,
    staleTime: STALE_TIME_LONG,
  });

  const updateMutation = useMutation({
    mutationFn: profileApi.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
    },
  });

  const avatarMutation = useMutation({
    mutationFn: profileApi.uploadAvatar,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
    },
  });

  return {
    profile: profile ?? null,
    isLoading,
    error: queryError,
    refetch,
    updateProfile: (data: UserProfileUpdate) => updateMutation.mutateAsync(data),
    uploadAvatar: (file: File) => avatarMutation.mutateAsync(file),
    isSaving: updateMutation.isPending || avatarMutation.isPending,
    saveError: updateMutation.error || avatarMutation.error,
  };
}
