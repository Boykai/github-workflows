/**
 * Projects hook for listing and selecting GitHub Projects.
 */

import { useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, tasksApi } from '@/services/api';
import { STALE_TIME_LONG, STALE_TIME_MEDIUM } from '@/constants';
import type { Project, Task } from '@/types';

interface UseProjectsReturn {
  projects: Project[];
  isLoading: boolean;
  error: Error | null;
  selectedProject: Project | null;
  tasks: Task[];
  tasksLoading: boolean;
  selectProject: (projectId: string) => Promise<void>;
  refreshProjects: () => void;
  refreshTasks: () => void;
}

export function useProjects(selectedProjectId?: string | null): UseProjectsReturn {
  const queryClient = useQueryClient();

  // Fetch projects list
  const {
    data: projectsData,
    isLoading,
    error,
    refetch: refreshProjects,
  } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
    staleTime: STALE_TIME_LONG,
  });

  // Fetch tasks for selected project
  const {
    data: tasksData,
    isLoading: tasksLoading,
    refetch: refreshTasks,
  } = useQuery({
    queryKey: ['projects', selectedProjectId, 'tasks'],
    queryFn: () => tasksApi.listByProject(selectedProjectId!),
    enabled: !!selectedProjectId,
    staleTime: STALE_TIME_MEDIUM,
  });

  // Select project mutation
  const selectMutation = useMutation({
    mutationFn: projectsApi.select,
    onSuccess: (user) => {
      // Update auth with the returned user (includes selected_project_id)
      queryClient.setQueryData(['auth', 'me'], user);
      // Also invalidate projects to refresh task data
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const selectProject = useCallback(
    async (projectId: string) => {
      await selectMutation.mutateAsync(projectId);
    },
    [selectMutation]
  );

  // Find currently selected project from list
  const selectedProject =
    projectsData?.projects.find((p) => p.project_id === selectedProjectId) ?? null;

  return {
    projects: projectsData?.projects ?? [],
    isLoading,
    error: error as Error | null,
    selectedProject,
    tasks: tasksData?.tasks ?? [],
    tasksLoading,
    selectProject,
    refreshProjects,
    refreshTasks,
  };
}
