/**
 * FeaturedRitualsPanel — three-card panel showing Next Run, Most Recently Run, Most Run.
 *
 * Computed from the chores list and parentIssueCount.
 */

import { useMemo } from 'react';
import { Clock, PlayCircle, Trophy } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import type { Chore } from '@/types';

interface FeaturedRitualsPanelProps {
  chores: Chore[];
  parentIssueCount: number;
  onChoreClick?: (choreId: string) => void;
}

interface RitualCard {
  choreId: string;
  choreName: string;
  stat: string;
  icon: typeof Clock;
  label: string;
}

function computeRemaining(chore: Chore, parentIssueCount: number): number {
  if (chore.schedule_type !== 'count' || !chore.schedule_value) return Infinity;
  const issuesSince = parentIssueCount - chore.last_triggered_count;
  return Math.max(0, chore.schedule_value - issuesSince);
}

export function FeaturedRitualsPanel({ chores, parentIssueCount, onChoreClick }: FeaturedRitualsPanelProps) {
  const rituals = useMemo(() => {
    if (chores.length === 0) return null;

    const activeChores = chores.filter(c => c.status === 'active');

    // Next Run — lowest remaining count for count-based chores, soonest time for time-based
    let nextRun: RitualCard | null = null;
    let bestNextValue = Infinity;

    for (const chore of activeChores) {
      if (!chore.schedule_type || !chore.schedule_value) continue;

      let value: number;
      let stat: string;

      if (chore.schedule_type === 'count') {
        value = computeRemaining(chore, parentIssueCount);
        stat = value === 0 ? 'Ready to trigger' : `${value} issue${value !== 1 ? 's' : ''} remaining`;
      } else {
        const baseDate = chore.last_triggered_at ?? chore.created_at;
        const base = new Date(baseDate).getTime();
        const nextTrigger = base + chore.schedule_value * 24 * 60 * 60 * 1000;
        value = Math.max(0, nextTrigger - Date.now());
        if (value <= 0) {
          stat = 'Due now';
        } else {
          const days = Math.floor(value / (24 * 60 * 60 * 1000));
          const hours = Math.floor((value % (24 * 60 * 60 * 1000)) / (60 * 60 * 1000));
          stat = days > 0 ? `${days}d ${hours}h remaining` : `${hours}h remaining`;
        }
      }

      if (value < bestNextValue) {
        bestNextValue = value;
        nextRun = { choreId: chore.id, choreName: chore.name, stat, icon: Clock, label: 'Next Run' };
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

    const cards = [nextRun, mostRecentlyRun, mostRun].filter(Boolean) as RitualCard[];
    return cards.length > 0 ? cards : null;
  }, [chores, parentIssueCount]);

  if (!rituals) {
    return null;
  }

  return (
    <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
      {rituals.map((card) => (
        <button
          key={card.label}
          type="button"
          onClick={() => onChoreClick?.(card.choreId)}
          className="text-left"
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
