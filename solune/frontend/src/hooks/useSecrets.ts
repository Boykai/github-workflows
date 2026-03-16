/**
 * Custom hooks for managing GitHub environment secrets via TanStack Query.
 *
 * Provides queries for listing/checking secrets and mutations for
 * creating, updating, and deleting secrets with cache invalidation.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { secretsApi } from '@/services/api';
import { STALE_TIME_SHORT } from '@/constants';
import type { SecretsListResponse, SecretCheckResponse } from '@/types';

// ── Query Keys ──

export const secretsKeys = {
  all: ['secrets'] as const,
  list: (owner: string, repo: string, env: string) =>
    [...secretsKeys.all, 'list', owner, repo, env] as const,
  check: (owner: string, repo: string, env: string, names: string[]) =>
    [...secretsKeys.all, 'check', owner, repo, env, ...names] as const,
};

// ── List Secrets ──

export function useSecrets(owner: string | undefined, repo: string | undefined, env: string) {
  return useQuery<SecretsListResponse>({
    queryKey: secretsKeys.list(owner ?? '', repo ?? '', env),
    queryFn: () => secretsApi.listSecrets(owner!, repo!, env),
    enabled: !!owner && !!repo,
    staleTime: STALE_TIME_SHORT,
  });
}

// ── Check Secrets ──

export function useCheckSecrets(
  owner: string | undefined,
  repo: string | undefined,
  env: string,
  names: string[]
) {
  return useQuery<SecretCheckResponse>({
    queryKey: secretsKeys.check(owner ?? '', repo ?? '', env, names),
    queryFn: () => secretsApi.checkSecrets(owner!, repo!, env, names),
    enabled: !!owner && !!repo && names.length > 0,
    staleTime: STALE_TIME_SHORT,
  });
}

// ── Set Secret ──

export function useSetSecret() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: {
      owner: string;
      repo: string;
      env: string;
      name: string;
      value: string;
    }) => secretsApi.setSecret(params.owner, params.repo, params.env, params.name, params.value),
    onSuccess: () => {
      // Invalidate all secrets queries to refetch
      void queryClient.invalidateQueries({ queryKey: secretsKeys.all });
    },
  });
}

// ── Delete Secret ──

export function useDeleteSecret() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { owner: string; repo: string; env: string; name: string }) =>
      secretsApi.deleteSecret(params.owner, params.repo, params.env, params.name),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: secretsKeys.all });
    },
  });
}
