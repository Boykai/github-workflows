import type { BoardColumn, BoardDataResponse } from '@/types';

/**
 * Filters board columns to only include parent GitHub issues.
 *
 * Sub-issues are identified by cross-referencing each item's `number` against
 * the `sub_issues[].number` arrays of all items across every column. Items
 * whose `content_type` is not `'issue'` (e.g. draft issues, pull requests)
 * are also excluded. Column `item_count` and `estimate_total` are recalculated
 * to reflect the filtered set.
 */
export function filterParentIssueColumns(boardData: BoardDataResponse): BoardColumn[] {
  const subIssueNumbers = new Set<number>();

  for (const column of boardData.columns) {
    for (const item of column.items) {
      for (const subIssue of item.sub_issues) {
        subIssueNumbers.add(subIssue.number);
      }
    }
  }

  return boardData.columns.map((column) => {
    const items = column.items.filter(
      (item) =>
        item.content_type === 'issue' &&
        (item.number == null || !subIssueNumbers.has(item.number)),
    );

    return {
      ...column,
      items,
      item_count: items.length,
      estimate_total: items.reduce((sum, it) => sum + (it.estimate ?? 0), 0),
    };
  });
}
