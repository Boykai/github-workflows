/**
 * ChoresSpotlight — featured rituals section showing stats cards,
 * uncreated repository templates, or spotlight chores.
 *
 * Extracted from ChoresPanel for single-responsibility.
 */

import { ScrollText, Sparkles } from '@/lib/icons';
import { ChoreCard } from './ChoreCard';
import { Card, CardContent } from '@/components/ui/card';
import type { Chore, ChoreEditState, ChoreInlineUpdate, ChoreTemplate } from '@/types';

interface ChoresSpotlightProps {
  chores: Chore[];
  uncreatedTemplates: ChoreTemplate[];
  spotlightChores: Chore[];
  projectId: string;
  parentIssueCount: number;
  activeCount: number;
  pausedCount: number;
  unscheduledCount: number;
  editState: Record<string, ChoreEditState>;
  onEditStart: (chore: Chore) => void;
  onEditChange: (choreId: string, updates: Partial<ChoreInlineUpdate>) => void;
  onEditSave: (choreId: string) => void;
  onEditDiscard: (choreId: string) => void;
  isSaving: boolean;
  onTemplateClick: (template: ChoreTemplate) => void;
}

export function ChoresSpotlight({
  chores,
  uncreatedTemplates,
  spotlightChores,
  projectId,
  parentIssueCount,
  activeCount,
  pausedCount,
  unscheduledCount,
  editState,
  onEditStart,
  onEditChange,
  onEditSave,
  onEditDiscard,
  isSaving,
  onTemplateClick,
}: ChoresSpotlightProps) {
  if (uncreatedTemplates.length === 0 && spotlightChores.length === 0) return null;

  return (
    <section
      id="chore-templates"
      className="ritual-stage scroll-mt-6 rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6"
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex items-center gap-2 text-primary">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            <p className="text-[11px] uppercase tracking-[0.24em]">Featured rituals</p>
          </div>
          <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">
            Start from templates, then monitor what needs attention
          </h4>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            Uncreated repository templates stay visible in the spotlight so they do not
            disappear behind existing chores.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            { label: 'Total chores', value: chores.length },
            { label: 'Active', value: activeCount },
            { label: 'Paused', value: pausedCount },
            { label: 'Unscheduled', value: unscheduledCount },
          ].map((stat) => (
            <Card key={stat.label} className="moonwell rounded-[1.35rem] border-primary/15 shadow-none">
              <CardContent className="p-4">
                <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                  {stat.label}
                </p>
                <p className="mt-2 text-2xl font-semibold text-foreground">{stat.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {uncreatedTemplates.length > 0 ? (
        <div className="constellation-grid mt-6 grid gap-4 lg:grid-cols-3">
          {uncreatedTemplates.slice(0, 3).map((tpl) => (
            <button
              key={tpl.path}
              onClick={() => onTemplateClick(tpl)}
              className="celestial-focus text-left focus-visible:outline-none"
              type="button"
            >
              <Card className="moonwell h-full rounded-[1.55rem] border-dashed border-primary/25">
                <CardContent className="flex h-full flex-col gap-4 p-5">
                  <div className="flex items-center justify-between gap-3">
                    <span className="rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[10px] uppercase tracking-[0.16em] text-primary">
                      Repo template
                    </span>
                    <ScrollText className="h-4 w-4 text-primary/70" aria-hidden="true" />
                  </div>
                  <div>
                    <h5 className="text-lg font-semibold text-foreground">{tpl.name}</h5>
                    {tpl.about && (
                      <p className="mt-2 text-sm leading-6 text-muted-foreground line-clamp-3">
                        {tpl.about}
                      </p>
                    )}
                  </div>
                  <p className="mt-auto text-xs uppercase tracking-[0.18em] text-muted-foreground">
                    Tap to seed this ritual
                  </p>
                </CardContent>
              </Card>
            </button>
          ))}
        </div>
      ) : (
        <div className="constellation-grid mt-6 grid gap-4 lg:grid-cols-3">
          {spotlightChores.map((chore) => (
            <ChoreCard
              key={chore.id}
              chore={chore}
              projectId={projectId}
              variant="spotlight"
              parentIssueCount={parentIssueCount}
              editState={editState[chore.id]}
              onEditStart={() => onEditStart(chore)}
              onEditChange={(updates) => onEditChange(chore.id, updates)}
              onEditSave={() => onEditSave(chore.id)}
              onEditDiscard={() => onEditDiscard(chore.id)}
              isSaving={isSaving}
            />
          ))}
        </div>
      )}
    </section>
  );
}
