/**
 * Custom hooks for managing GitHub Actions environment secrets via TanStack Query.
 *
 * Provides queries for listing/checking secrets and mutations for
 * creating, updating, and deleting them.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { secretsApi } from '@/services/api';
import { STALE_TIME_MEDIUM } from '@/constants';
import type { SecretsListResponse, SecretCheckResponse } from '@/types';

// ── Query Keys ──

export const secretsKeys = {
  all: ['secrets'] as const,
  list: (owner: string, repo: string, env: string) =>
    [...secretsKeys.all, 'list', owner, repo, env] as const,
  check: (owner: string, repo: string, env: string, names: string[]) =>
    [...secretsKeys.all, 'check', owner, repo, env, names] as const,
};

// ── List Secrets ──

/**
 * Query hook that returns secret metadata (names + timestamps) for a
 * given repository environment.  Secret values are never returned.
 */
export function useSecrets(
  owner: string | undefined,
  repo: string | undefined,
  env: string | undefined
) {
  const query = useQuery<SecretsListResponse>({
    queryKey: secretsKeys.list(owner ?? '', repo ?? '', env ?? ''),
    queryFn: () => secretsApi.listSecrets(owner!, repo!, env!),
    enabled: Boolean(owner && repo && env),
    staleTime: STALE_TIME_MEDIUM,
  });

  return {
    data: query.data,
    secrets: query.data?.secrets ?? [],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}

// ── Set Secret ──

interface SetSecretVars {
  owner: string;
  repo: string;
  env: string;
  name: string;
  value: string;
}

/**
 * Mutation hook to create or update a secret in a repository environment.
 * Invalidates the secrets list on success.
 */
export function useSetSecret() {
  const queryClient = useQueryClient();

  const mutation = useMutation<void, Error, SetSecretVars>({
    mutationFn: ({ owner, repo, env, name, value }) =>
      secretsApi.setSecret(owner, repo, env, name, value),
    onSuccess: (_data, { owner, repo, env }) => {
      queryClient.invalidateQueries({ queryKey: secretsKeys.list(owner, repo, env) });
    },
  });

  return {
    setSecret: mutation.mutateAsync,
    isPending: mutation.isPending,
    error: mutation.error,
    reset: mutation.reset,
  };
}

// ── Delete Secret ──

interface DeleteSecretVars {
  owner: string;
  repo: string;
  env: string;
  name: string;
}

/**
 * Mutation hook to delete a secret from a repository environment.
 * Invalidates the secrets list on success.
 */
export function useDeleteSecret() {
  const queryClient = useQueryClient();

  const mutation = useMutation<void, Error, DeleteSecretVars>({
    mutationFn: ({ owner, repo, env, name }) =>
      secretsApi.deleteSecret(owner, repo, env, name),
    onSuccess: (_data, { owner, repo, env }) => {
      queryClient.invalidateQueries({ queryKey: secretsKeys.list(owner, repo, env) });
    },
  });

  return {
    deleteSecret: mutation.mutateAsync,
    isPending: mutation.isPending,
    error: mutation.error,
  };
}

// ── Check Secrets ──

/**
 * Query hook that checks whether specific secrets exist in a repository environment.
 * Returns a map of secret name → boolean.
 */
export function useCheckSecrets(
  owner: string | undefined,
  repo: string | undefined,
  env: string | undefined,
  names: string[]
) {
  const query = useQuery<SecretCheckResponse>({
    queryKey: secretsKeys.check(owner ?? '', repo ?? '', env ?? '', names),
    queryFn: () => secretsApi.checkSecrets(owner!, repo!, env!, names),
    enabled: Boolean(owner && repo && env && names.length > 0),
    staleTime: STALE_TIME_MEDIUM,
  });

  return {
    results: query.data?.results ?? {},
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}
