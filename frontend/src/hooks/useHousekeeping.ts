/**
 * Custom hook for managing housekeeping tasks, templates, and trigger history
 * via TanStack Query.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { housekeepingApi } from '@/services/api';
import { STALE_TIME_LONG } from '@/constants';
import type {
  IssueTemplate,
  IssueTemplateCreate,
  IssueTemplateUpdate,
  TemplateListResponse,
  HousekeepingTask,
  HousekeepingTaskCreate,
  HousekeepingTaskUpdate,
  HousekeepingTaskListResponse,
  TriggerHistoryResponse,
} from '@/types';

// ── Query Keys ──

export const housekeepingKeys = {
  all: ['housekeeping'] as const,
  templates: () => [...housekeepingKeys.all, 'templates'] as const,
  templateList: (category?: string) => [...housekeepingKeys.templates(), 'list', category] as const,
  template: (id: string) => [...housekeepingKeys.templates(), id] as const,
  tasks: () => [...housekeepingKeys.all, 'tasks'] as const,
  taskList: (projectId: string) => [...housekeepingKeys.tasks(), 'list', projectId] as const,
  task: (id: string) => [...housekeepingKeys.tasks(), id] as const,
  history: (taskId: string) => [...housekeepingKeys.all, 'history', taskId] as const,
};

// ── Template Queries & Mutations ──

export function useTemplateList(category?: string) {
  return useQuery<TemplateListResponse>({
    queryKey: housekeepingKeys.templateList(category),
    queryFn: () => housekeepingApi.listTemplates(category),
    staleTime: STALE_TIME_LONG,
  });
}

export function useTemplate(templateId: string) {
  return useQuery<IssueTemplate>({
    queryKey: housekeepingKeys.template(templateId),
    queryFn: () => housekeepingApi.getTemplate(templateId),
    enabled: !!templateId,
    staleTime: STALE_TIME_LONG,
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: IssueTemplateCreate) => housekeepingApi.createTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: housekeepingKeys.templates() });
    },
  });
}

export function useUpdateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: IssueTemplateUpdate }) =>
      housekeepingApi.updateTemplate(id, data),
    onSuccess: (updated) => {
      queryClient.setQueryData(housekeepingKeys.template(updated.id), updated);
      queryClient.invalidateQueries({ queryKey: housekeepingKeys.templates() });
    },
  });
}

export function useDeleteTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, force }: { id: string; force?: boolean }) =>
      housekeepingApi.deleteTemplate(id, force),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: housekeepingKeys.templates() });
    },
  });
}

export function useDuplicateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (templateId: string) => housekeepingApi.duplicateTemplate(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: housekeepingKeys.templates() });
    },
  });
}

// ── Task Queries & Mutations ──

export function useTaskList(projectId: string) {
  return useQuery<HousekeepingTaskListResponse>({
    queryKey: housekeepingKeys.taskList(projectId),
    queryFn: () => housekeepingApi.listTasks(projectId),
    enabled: !!projectId,
    staleTime: STALE_TIME_LONG,
  });
}

export function useTask(taskId: string) {
  return useQuery<HousekeepingTask>({
    queryKey: housekeepingKeys.task(taskId),
    queryFn: () => housekeepingApi.getTask(taskId),
    enabled: !!taskId,
    staleTime: STALE_TIME_LONG,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: HousekeepingTaskCreate) => housekeepingApi.createTask(data),
    onSuccess: (task) => {
      queryClient.invalidateQueries({
        queryKey: housekeepingKeys.taskList(task.project_id),
      });
    },
  });
}

export function useUpdateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: HousekeepingTaskUpdate }) =>
      housekeepingApi.updateTask(id, data),
    onSuccess: (updated) => {
      queryClient.setQueryData(housekeepingKeys.task(updated.id), updated);
      queryClient.invalidateQueries({
        queryKey: housekeepingKeys.taskList(updated.project_id),
      });
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) => housekeepingApi.deleteTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: housekeepingKeys.tasks() });
    },
  });
}

export function useToggleTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      housekeepingApi.toggleTask(id, enabled),
    onSuccess: (updated) => {
      queryClient.setQueryData(housekeepingKeys.task(updated.id), updated);
      queryClient.invalidateQueries({
        queryKey: housekeepingKeys.taskList(updated.project_id),
      });
    },
  });
}

// ── Manual Run ──

export function useRunTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, force }: { id: string; force?: boolean }) =>
      housekeepingApi.runTask(id, force),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: housekeepingKeys.task(variables.id),
      });
      queryClient.invalidateQueries({
        queryKey: housekeepingKeys.history(variables.id),
      });
      queryClient.invalidateQueries({ queryKey: housekeepingKeys.tasks() });
    },
  });
}

// ── Trigger History ──

export function useTaskHistory(
  taskId: string,
  limit = 50,
  offset = 0,
  status?: string,
) {
  return useQuery<TriggerHistoryResponse>({
    queryKey: [...housekeepingKeys.history(taskId), limit, offset, status],
    queryFn: () => housekeepingApi.getTaskHistory(taskId, limit, offset, status),
    enabled: !!taskId,
    staleTime: STALE_TIME_LONG,
  });
}
