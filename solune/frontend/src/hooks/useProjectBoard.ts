/**
 * Hook for Project Board data fetching with adaptive polling.
 *
 * Uses `useAdaptivePolling` to dynamically adjust the refetch interval
 * based on detected board activity, with exponential backoff on errors
 * and tab-visibility awareness.
 */

import { useState, useCallback, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { boardApi } from '@/services/api';
import { STALE_TIME_PROJECTS, STALE_TIME_SHORT } from '@/constants';
import type { BoardProject, BoardDataResponse, RateLimitInfo } from '@/types';
import { useAdaptivePolling, type AdaptivePollingConfig } from './useAdaptivePolling';

/** Stable empty array to avoid creating new references each render. */
const EMPTY_PROJECTS: BoardProject[] = [];

interface UseProjectBoardOptions {
  /** Externally managed selected project ID (from session) */
  selectedProjectId?: string | null;
  /** Callback when user selects a project (persists to session) */
  onProjectSelect?: (projectId: string) => void;
  /** Optional adaptive polling configuration overrides */
  adaptivePollingConfig?: AdaptivePollingConfig;
}

interface UseProjectBoardReturn {
  /** List of available projects */
  projects: BoardProject[];
  /** Rate-limit information returned with the projects list */
  projectsRateLimitInfo: RateLimitInfo | null;
  /** Whether the projects list is loading */
  projectsLoading: boolean;
  /** Error fetching projects */
  projectsError: Error | null;
  /** Currently selected project ID */
  selectedProjectId: string | null;
  /** Board data for the selected project */
  boardData: BoardDataResponse | null;
  /** Whether board data is loading (initial) */
  boardLoading: boolean;
  /** Whether board data is being refetched in background */
  isFetching: boolean;
  /** Error fetching board data */
  boardError: Error | null;
  /** Last time data was successfully updated */
  lastUpdated: Date | null;
  /** Select a project to display on the board */
  selectProject: (projectId: string) => void;
  /** Current adaptive polling state */
  pollingState: ReturnType<typeof useAdaptivePolling>['state'];
}

export function useProjectBoard(options: UseProjectBoardOptions = {}): UseProjectBoardReturn {
  const { selectedProjectId: externalProjectId, onProjectSelect, adaptivePollingConfig } = options;
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const previousDataRef = useRef<string | null>(null);

  // Use the externally managed project ID (from session)
  const selectedProjectId = externalProjectId ?? null;

  // Adaptive polling integration
  const {
    getRefetchInterval,
    reportPollResult,
    reportPollFailure,
    reportPollSuccess,
    state: pollingState,
  } = useAdaptivePolling(adaptivePollingConfig);

  // Fetch projects list
  const {
    data: projectsData,
    isLoading: projectsLoading,
    error: projectsError,
  } = useQuery({
    queryKey: ['board', 'projects'],
    queryFn: () => boardApi.listProjects(),
    staleTime: STALE_TIME_PROJECTS,
    retry: false,
  });

  // Fetch board data for selected project with adaptive polling.
  const {
    data: boardData,
    isLoading: boardLoading,
    isFetching,
    error: boardError,
  } = useQuery({
    queryKey: ['board', 'data', selectedProjectId],
    queryFn: async () => {
      try {
        const result = await boardApi.getBoardData(selectedProjectId!);
        setLastUpdated(new Date());

        // Report poll result to adaptive polling — detect changes by
        // comparing a lightweight hash of the response data.
        const dataHash = JSON.stringify(result.columns.map(c => c.item_count));
        const hasChanges = previousDataRef.current !== null && previousDataRef.current !== dataHash;
        previousDataRef.current = dataHash;
        reportPollResult(hasChanges);
        reportPollSuccess();

        return result;
      } catch (err) {
        reportPollFailure();
        throw err;
      }
    },
    enabled: !!selectedProjectId,
    staleTime: STALE_TIME_SHORT,
    refetchInterval: getRefetchInterval,
  });

  const selectProject = useCallback(
    (projectId: string) => {
      setLastUpdated(null);
      previousDataRef.current = null;
      if (onProjectSelect) {
        onProjectSelect(projectId);
      }
    },
    [onProjectSelect]
  );

  return {
    projects: projectsData?.projects ?? EMPTY_PROJECTS,
    projectsRateLimitInfo: projectsData?.rate_limit ?? null,
    projectsLoading,
    projectsError: projectsError as Error | null,
    selectedProjectId,
    boardData: boardData ?? null,
    boardLoading,
    isFetching,
    boardError: boardError as Error | null,
    lastUpdated,
    selectProject,
    pollingState,
  };
}
