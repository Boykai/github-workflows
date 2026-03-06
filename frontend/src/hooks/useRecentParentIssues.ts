/**
 * useRecentParentIssues — derives recent parent issues from board data.
 * Returns up to 8 recent items sorted by board position (most recently updated first).
 */

import { useMemo } from 'react';
import type { BoardDataResponse } from '@/types';
import type { RecentInteraction } from '@/types';

const MAX_RECENT = 8;

export function useRecentParentIssues(boardData: BoardDataResponse | null): RecentInteraction[] {
  return useMemo(() => {
    if (!boardData) return [];

    // Collect all board items across columns — API returns them in recency order
    const allItems = boardData.columns.flatMap((col) => col.items);

    // Deduplicate by item_id and take the first MAX_RECENT
    const seen = new Set<string>();
    const recent: RecentInteraction[] = [];

    for (const item of allItems) {
      if (seen.has(item.item_id)) continue;
      seen.add(item.item_id);

      recent.push({
        item_id: item.item_id,
        title: item.title,
        number: item.number,
        repository: item.repository ? { owner: item.repository.owner, name: item.repository.name } : undefined,
        updatedAt: new Date().toISOString(),
      });

      if (recent.length >= MAX_RECENT) break;
    }

    return recent;
  }, [boardData]);
}
