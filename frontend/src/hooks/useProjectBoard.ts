/**
 * Hook for Project Board data fetching with auto-refresh polling.
 */

import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { boardApi } from '@/services/api';
import type { BoardProject, BoardDataResponse } from '@/types';

const POLL_INTERVAL_MS = 15000; // 15 seconds

interface UseProjectBoardOptions {
  /** Externally managed selected project ID (from session) */
  selectedProjectId?: string | null;
  /** Callback when user selects a project (persists to session) */
  onProjectSelect?: (projectId: string) => void;
}

interface UseProjectBoardReturn {
  /** List of available projects */
  projects: BoardProject[];
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
}

export function useProjectBoard(options: UseProjectBoardOptions = {}): UseProjectBoardReturn {
  const { selectedProjectId: externalProjectId, onProjectSelect } = options;
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Use the externally managed project ID (from session)
  const selectedProjectId = externalProjectId ?? null;

  // Fetch projects list
  const {
    data: projectsData,
    isLoading: projectsLoading,
    error: projectsError,
  } = useQuery({
    queryKey: ['board', 'projects'],
    queryFn: () => boardApi.listProjects(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Fetch board data for selected project with polling
  const {
    data: boardData,
    isLoading: boardLoading,
    isFetching,
    error: boardError,
  } = useQuery({
    queryKey: ['board', 'data', selectedProjectId],
    queryFn: async () => {
      const result = await boardApi.getBoardData(selectedProjectId!);
      setLastUpdated(new Date());
      return result;
    },
    enabled: !!selectedProjectId,
    staleTime: 10000, // 10 seconds
    refetchInterval: POLL_INTERVAL_MS,
    refetchIntervalInBackground: false,
  });

  const selectProject = useCallback((projectId: string) => {
    setLastUpdated(null);
    if (onProjectSelect) {
      onProjectSelect(projectId);
    }
  }, [onProjectSelect]);

  return {
    projects: projectsData?.projects ?? [],
    projectsLoading,
    projectsError: projectsError as Error | null,
    selectedProjectId,
    boardData: boardData ?? null,
    boardLoading,
    isFetching,
    boardError: boardError as Error | null,
    lastUpdated,
    selectProject,
  };
}
