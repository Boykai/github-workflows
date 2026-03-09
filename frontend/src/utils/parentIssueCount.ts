import type { BoardDataResponse, BoardItem } from '@/types';

function isChoreIssue(item: BoardItem): boolean {
  return item.labels.some((label) => label.name.trim().toLowerCase() === 'chore');
}

export function countParentIssues(boardData: BoardDataResponse | null | undefined): number {
  if (!boardData?.columns) return 0;

  const subIssueNumbers = new Set<number>();
  const seenItemIds = new Set<string>();
  let count = 0;

  for (const column of boardData.columns) {
    for (const item of column.items ?? []) {
      for (const subIssue of item.sub_issues ?? []) {
        subIssueNumbers.add(subIssue.number);
      }
    }
  }

  for (const column of boardData.columns) {
    for (const item of column.items ?? []) {
      if (item.content_type !== 'issue') continue;
      if (seenItemIds.has(item.item_id)) continue;
      seenItemIds.add(item.item_id);

      if (item.number != null && subIssueNumbers.has(item.number)) continue;
      if (isChoreIssue(item)) continue;

      count += 1;
    }
  }

  return count;
}
