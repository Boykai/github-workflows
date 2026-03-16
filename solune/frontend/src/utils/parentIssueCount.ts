import type { BoardDataResponse, BoardItem } from '@/types';

function isChoreIssue(item: BoardItem): boolean {
  if (item.issue_type && item.issue_type.trim().toLowerCase() === 'chore') {
    return true;
  }
  return item.labels.some((label) => label.name.trim().toLowerCase() === 'chore');
}

function isSubIssueByLabel(item: BoardItem): boolean {
  return item.labels.some((label) => label.name === 'sub-issue');
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
      if (isSubIssueByLabel(item)) continue;
      if (isChoreIssue(item)) continue;

      count += 1;
    }
  }

  return count;
}
