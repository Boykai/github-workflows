import type { BoardDataResponse } from '@/types';

const RECENT_AGENT_WINDOW_MS = 3 * 24 * 60 * 60 * 1000;

export function formatAgentCreatedLabel(
  createdAt: string | null | undefined,
  nowMs = Date.now()
): string {
  if (!createdAt) {
    return 'Recently added';
  }

  const createdMs = Date.parse(createdAt);
  if (Number.isNaN(createdMs)) {
    return 'Recently added';
  }

  if (nowMs - createdMs < RECENT_AGENT_WINDOW_MS) {
    return 'Recently added';
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(createdMs);
}

export function countPendingAssignedSubIssues(
  boardData: BoardDataResponse | null | undefined
): Record<string, number> {
  if (!boardData?.columns) {
    return {};
  }

  const counts: Record<string, number> = {};

  for (const column of boardData.columns) {
    for (const item of column.items) {
      for (const subIssue of item.sub_issues ?? []) {
        const assignedAgent = subIssue.assigned_agent?.trim().toLowerCase();
        if (!assignedAgent || subIssue.state === 'closed') {
          continue;
        }
        counts[assignedAgent] = (counts[assignedAgent] ?? 0) + 1;
      }
    }
  }

  return counts;
}
