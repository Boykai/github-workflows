/**
 * useWorkflow Hook
 *
 * Provides functions for confirming and rejecting AI-generated
 * issue recommendations, communicating with the workflow API.
 */

import { useState, useCallback } from 'react';
import type { WorkflowResult, WorkflowConfiguration } from '../types';

const API_BASE = '/api/v1';

interface UseWorkflowReturn {
  confirmRecommendation: (recommendationId: string) => Promise<WorkflowResult>;
  rejectRecommendation: (recommendationId: string) => Promise<void>;
  getConfig: () => Promise<WorkflowConfiguration>;
  updateConfig: (config: Partial<WorkflowConfiguration>) => Promise<WorkflowConfiguration>;
  isLoading: boolean;
  error: string | null;
}

export function useWorkflow(): UseWorkflowReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const confirmRecommendation = useCallback(
    async (recommendationId: string): Promise<WorkflowResult> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${API_BASE}/workflow/recommendations/${recommendationId}/confirm`,
          {
            method: 'POST',
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
            },
          }
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.error || `Failed to confirm: ${response.status}`);
        }

        const result: WorkflowResult = await response.json();
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to confirm recommendation';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const rejectRecommendation = useCallback(
    async (recommendationId: string): Promise<void> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${API_BASE}/workflow/recommendations/${recommendationId}/reject`,
          {
            method: 'POST',
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
            },
          }
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.error || `Failed to reject: ${response.status}`);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to reject recommendation';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const getConfig = useCallback(async (): Promise<WorkflowConfiguration> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/workflow/config`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Failed to get config: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get workflow config';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateConfig = useCallback(
    async (config: Partial<WorkflowConfiguration>): Promise<WorkflowConfiguration> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE}/workflow/config`, {
          method: 'PUT',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(config),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.error || `Failed to update config: ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update workflow config';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  return {
    confirmRecommendation,
    rejectRecommendation,
    getConfig,
    updateConfig,
    isLoading,
    error,
  };
}

export default useWorkflow;
