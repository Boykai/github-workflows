/**
 * useRecentParentIssues — derives recent parent issues from board data.
 * Returns up to MAX_RECENT recent parent issues with project board status colors.
 *
 * Filters: content_type === 'issue' only, excludes sub-issues,
 * captures status color from the parent column context.
 * Items not present in BoardDataResponse (deleted) are implicitly excluded.
 */

import { useMemo } from 'react';
import type { BoardDataResponse, RecentInteraction } from '@/types';

const MAX_RECENT = 8;

export function useRecentParentIssues(boardData: BoardDataResponse | null): RecentInteraction[] {
  return useMemo(() => {
    if (!boardData) return [];

    // Build a set of all sub-issue numbers to exclude them from recent interactions
    const subIssueNumbers = new Set<number>();
    for (const column of boardData.columns) {
      for (const item of column.items) {
        for (const si of item.sub_issues) {
          subIssueNumbers.add(si.number);
        }
      }
    }

    // Collect parent issues with status colors from column context
    const seen = new Set<string>();
    const recent: RecentInteraction[] = [];

    for (const column of boardData.columns) {
      for (const item of column.items) {
        // Only include GitHub Issues (exclude draft_issue, pull_request)
        if (item.content_type !== 'issue') continue;

        // Exclude sub-issues — only parent issues allowed
        if (item.number != null && subIssueNumbers.has(item.number)) continue;
        if (item.labels.some((label) => label.name === 'sub-issue')) continue;

        // Deduplicate by item_id
        if (seen.has(item.item_id)) continue;
        seen.add(item.item_id);

        recent.push({
          item_id: item.item_id,
          title: item.title,
          number: item.number,
          repository: item.repository
            ? { owner: item.repository.owner, name: item.repository.name }
            : undefined,
          updatedAt: new Date().toISOString(),
          status: column.status.name,
          statusColor: column.status.color ?? 'GRAY',
        });

        if (recent.length >= MAX_RECENT) break;
      }
      if (recent.length >= MAX_RECENT) break;
    }

    return recent;
  }, [boardData]);
}
