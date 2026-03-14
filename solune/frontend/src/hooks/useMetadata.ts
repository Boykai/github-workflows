/**
 * useMetadata hook — fetches and caches repository metadata from the backend.
 *
 * Provides labels, branches, milestones, and collaborators for the active
 * repository, with a refresh() function for on-demand cache invalidation.
 */

import { useCallback, useEffect, useState } from 'react';
import type { RepositoryMetadata } from '@/types';
import { metadataApi } from '@/services/api';

interface UseMetadataResult {
  metadata: RepositoryMetadata | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useMetadata(owner: string | null, repo: string | null): UseMetadataResult {
  const [metadata, setMetadata] = useState<RepositoryMetadata | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMetadata = useCallback(async () => {
    if (!owner || !repo) return;
    setLoading(true);
    setError(null);
    try {
      const data = await metadataApi.getMetadata(owner, repo);
      setMetadata(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch metadata');
    } finally {
      setLoading(false);
    }
  }, [owner, repo]);

  const refresh = useCallback(async () => {
    if (!owner || !repo) return;
    setLoading(true);
    setError(null);
    try {
      const data = await metadataApi.refreshMetadata(owner, repo);
      setMetadata(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh metadata');
    } finally {
      setLoading(false);
    }
  }, [owner, repo]);

  useEffect(() => {
    fetchMetadata();
  }, [fetchMetadata]);

  return { metadata, loading, error, refresh };
}
