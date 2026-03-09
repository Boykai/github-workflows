/**
 * FeaturedRitualsPanel — three-card panel showing Next Run, Most Recently Run, Most Run.
 *
 * Computed from the chores list and parentIssueCount.
 */

import { useMemo } from 'react';
import { Clock, PlayCircle, Trophy, type LucideIcon } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import type { Chore } from '@/types';

interface FeaturedRitualsPanelProps {
  chores: Chore[];
  parentIssueCount: number;
  onChoreClick?: (choreId: string) => void;
}

interface RitualCard {
  choreId: string | null;
  choreName: string;
  stat: string;
  icon: LucideIcon;
  label: string;
  isEmpty?: boolean;
}

function computeRemaining(chore: Chore, parentIssueCount: number): number {
  if (chore.schedule_type !== 'count' || !chore.schedule_value) return Infinity;
  const issuesSince = parentIssueCount - chore.last_triggered_count;
  return Math.max(0, chore.schedule_value - issuesSince);
}

function computeNextRunCandidate(chore: Chore, parentIssueCount: number) {
  if (!chore.schedule_type || !chore.schedule_value || chore.status !== 'active') {
    return null;
  }

  if (chore.schedule_type === 'count') {
    const remaining = computeRemaining(chore, parentIssueCount);
    const threshold = chore.schedule_value;
    const progress = threshold > 0 ? (threshold - remaining) / threshold : 0;
    return {
      stat: remaining === 0 ? 'Ready to trigger' : `${remaining} issue${remaining !== 1 ? 's' : ''} remaining`,
      isDue: remaining === 0,
      progress,
    };
  }

  const thresholdMs = chore.schedule_value * 24 * 60 * 60 * 1000;
  const baseDate = chore.last_triggered_at ?? chore.created_at;
  const elapsedMs = Math.max(0, Date.now() - new Date(baseDate).getTime());
  const remainingMs = Math.max(0, thresholdMs - elapsedMs);
  const progress = thresholdMs > 0 ? Math.min(1, elapsedMs / thresholdMs) : 0;
  const days = Math.floor(remainingMs / (24 * 60 * 60 * 1000));
  const hours = Math.floor((remainingMs % (24 * 60 * 60 * 1000)) / (60 * 60 * 1000));

  return {
    stat: remainingMs === 0 ? 'Due now' : days > 0 ? `${days}d ${hours}h remaining` : `${hours}h remaining`,
    isDue: remainingMs === 0,
    progress,
  };
}

export function FeaturedRitualsPanel({ chores, parentIssueCount, onChoreClick }: FeaturedRitualsPanelProps) {
  const rituals = useMemo(() => {
    if (chores.length === 0) {
      return [];
    }

    const activeChores = chores.filter(c => c.status === 'active');

    // Next Run — compare normalized progress toward the next trigger across schedule types.
    let nextRun: RitualCard | null = null;
    let bestNextIsDue = false;
    let bestNextProgress = -1;

    for (const chore of activeChores) {
      const candidate = computeNextRunCandidate(chore, parentIssueCount);
      if (!candidate) continue;

      const outranksCurrent =
        (candidate.isDue && !bestNextIsDue) ||
        (candidate.isDue === bestNextIsDue && candidate.progress > bestNextProgress);

      if (outranksCurrent) {
        bestNextIsDue = candidate.isDue;
        bestNextProgress = candidate.progress;
        nextRun = {
          choreId: chore.id,
          choreName: chore.name,
          stat: candidate.stat,
          icon: Clock,
          label: 'Next Run',
        };
      }
    }

    // Most Recently Run — latest last_triggered_at
    let mostRecentlyRun: RitualCard | null = null;
    let latestTimestamp = 0;

    for (const chore of chores) {
      if (!chore.last_triggered_at) continue;
      const ts = new Date(chore.last_triggered_at).getTime();
      if (ts > latestTimestamp) {
        latestTimestamp = ts;
        const ago = Date.now() - ts;
        const hoursAgo = Math.floor(ago / (60 * 60 * 1000));
        const daysAgo = Math.floor(hoursAgo / 24);
        const stat = daysAgo > 0 ? `Run ${daysAgo}d ago` : hoursAgo > 0 ? `Run ${hoursAgo}h ago` : 'Run just now';
        mostRecentlyRun = { choreId: chore.id, choreName: chore.name, stat, icon: PlayCircle, label: 'Most Recently Run' };
      }
    }

    // Most Run — highest execution_count
    let mostRun: RitualCard | null = null;
    let highestCount = 0;

    for (const chore of chores) {
      if (chore.execution_count > highestCount) {
        highestCount = chore.execution_count;
        mostRun = {
          choreId: chore.id,
          choreName: chore.name,
          stat: `${chore.execution_count} run${chore.execution_count !== 1 ? 's' : ''}`,
          icon: Trophy,
          label: 'Most Run',
        };
      }
    }

    return [
      nextRun ?? {
        choreId: null,
        choreName: 'No active schedule yet',
        stat: 'Add or resume a chore cadence to see the next run.',
        icon: Clock,
        label: 'Next Run',
        isEmpty: true,
      },
      mostRecentlyRun ?? {
        choreId: null,
        choreName: 'Nothing has run yet',
        stat: 'Trigger a chore to start a recent-run history.',
        icon: PlayCircle,
        label: 'Most Recently Run',
        isEmpty: true,
      },
      mostRun ?? {
        choreId: null,
        choreName: 'No execution data yet',
        stat: 'Execution counts will appear after chores start running.',
        icon: Trophy,
        label: 'Most Run',
        isEmpty: true,
      },
    ];
  }, [chores, parentIssueCount]);

  if (chores.length === 0) {
    return (
      <div className="rounded-[1.3rem] border border-dashed border-border/70 bg-background/35 p-6 text-center">
        <p className="text-sm font-medium text-foreground">No rituals yet</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Create your first chore to surface upcoming runs, recent activity, and execution leaders here.
        </p>
      </div>
    );
  }

  return (
    <div className="celestial-fade-in grid gap-4 grid-cols-1 sm:grid-cols-3">
      {rituals.map((card) => (
        <button
          key={card.label}
          type="button"
          onClick={() => card.choreId && onChoreClick?.(card.choreId)}
          className="text-left disabled:cursor-default"
          disabled={!card.choreId}
        >
          <Card className="moonwell h-full rounded-[1.35rem] border-primary/15 shadow-none transition-colors hover:border-primary/30">
            <CardContent className="flex flex-col gap-3 p-4">
              <div className="flex items-center gap-2">
                <card.icon className="h-4 w-4 text-primary" />
                <span className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">{card.label}</span>
              </div>
              <h5 className="text-sm font-semibold text-foreground truncate" title={card.choreName}>
                {card.choreName}
              </h5>
              <p className="text-xs text-muted-foreground">{card.stat}</p>
            </CardContent>
          </Card>
        </button>
      ))}
    </div>
  );
}
