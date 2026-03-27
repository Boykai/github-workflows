/**
 * useBoardStatusUpdate — Optimistic board-item status mutation.
 * Extracted from ProjectsPage for readability.
 */

import { useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { BoardDataResponse, BoardItem } from '@/types';
import { boardApi } from '@/services/api';

export function useBoardStatusUpdate(projectId: string | null) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: ({ itemId, newStatus }: { itemId: string; newStatus: string }) =>
      boardApi.updateItemStatus(projectId!, itemId, newStatus),
    onMutate: async ({ itemId, newStatus }) => {
      if (!projectId) return;
      const queryKey = ['board', 'data', projectId];
      await queryClient.cancelQueries({ queryKey });
      const snapshot = queryClient.getQueryData<BoardDataResponse>(queryKey);
      if (!snapshot) return;

      queryClient.setQueryData<BoardDataResponse>(queryKey, (old) => {
        if (!old) return old;
        let movedItem: BoardItem | undefined;
        const columns = old.columns.map((col) => {
          const found = col.items.find((item) => item.item_id === itemId);
          if (found) {
            movedItem = { ...found, status: newStatus };
            return {
              ...col,
              items: col.items.filter((item) => item.item_id !== itemId),
              item_count: col.item_count - 1,
            };
          }
          return col;
        });

        if (!movedItem) return old;

        return {
          ...old,
          columns: columns.map((col) => {
            if (col.status.name === newStatus) {
              const updatedItem = { ...movedItem!, status_option_id: col.status.option_id };
              return {
                ...col,
                items: [...col.items, updatedItem],
                item_count: col.item_count + 1,
              };
            }
            return col;
          }),
        };
      });

      return { snapshot, queryKey };
    },
    onError: (_error, _variables, context) => {
      if (context?.snapshot && context.queryKey) {
        queryClient.setQueryData(context.queryKey, context.snapshot);
      }
    },
    onSettled: (_data, _error, _variables, context) => {
      if (context?.queryKey) {
        queryClient.invalidateQueries({ queryKey: context.queryKey });
      }
    },
  });

  return useCallback(
    async (itemId: string, newStatus: string) => {
      await mutation.mutateAsync({ itemId, newStatus });
    },
    [mutation],
  );
}
