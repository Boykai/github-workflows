/**
 * ChoresPanel — container for the Chores feature on the project board.
 *
 * Renders list of ChoreCards, empty state with "Add Chore" button,
 * and loading / error states. Supports inline editing with dirty tracking.
 */

import { useCallback, useDeferredValue, useEffect, useMemo, useState } from 'react';
import { ScrollText, Search, Sparkles } from 'lucide-react';
import { useChoresList, useChoreTemplates, useInlineUpdateChore } from '@/hooks/useChores';
import { ChoreCard } from './ChoreCard';
import { AddChoreModal } from './AddChoreModal';
import { CleanUpButton } from '@/components/board/CleanUpButton';
import type { Chore, ChoreEditState, ChoreInlineUpdate, ChoreTemplate } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface ChoresPanelProps {
  projectId: string;
  owner?: string;
  repo?: string;
  parentIssueCount?: number;
  onDirtyChange?: (isDirty: boolean) => void;
}

type ChoreStatusFilter = 'all' | 'active' | 'paused';
type ScheduleFilter = 'all' | 'time' | 'count' | 'unscheduled';
type ChoreSortMode = 'attention' | 'updated' | 'name';

export function ChoresPanel({
  projectId,
  owner,
  repo,
  parentIssueCount = 0,
  onDirtyChange,
}: ChoresPanelProps) {
  const { data: chores, isLoading, error } = useChoresList(projectId);
  const { data: repoTemplates } = useChoreTemplates(projectId);
  const [showAddModal, setShowAddModal] = useState(false);
  const [preselectedTemplate, setPreselectedTemplate] = useState<ChoreTemplate | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<ChoreStatusFilter>('all');
  const [scheduleFilter, setScheduleFilter] = useState<ScheduleFilter>('all');
  const [sortMode, setSortMode] = useState<ChoreSortMode>('attention');
  const deferredSearch = useDeferredValue(search);

  // ── Inline Edit State ──
  const [editState, setEditState] = useState<Record<string, ChoreEditState>>({});
  const inlineUpdateMutation = useInlineUpdateChore(projectId);

  const isAnyDirty = useMemo(() => Object.values(editState).some((s) => s.isDirty), [editState]);

  // Notify parent of dirty state changes
  useEffect(() => {
    onDirtyChange?.(isAnyDirty);
  }, [isAnyDirty, onDirtyChange]);

  const handleEditChange = useCallback((choreId: string, updates: Partial<ChoreInlineUpdate>) => {
    setEditState((prev) => {
      const existing = prev[choreId];
      if (!existing) return prev;
      const newCurrent = { ...existing.current, ...updates };
      const isDirty = Object.keys(newCurrent).some((key) => {
        const k = key as keyof ChoreInlineUpdate;
        const original = existing.original[k as keyof Chore];
        return newCurrent[k] !== undefined && newCurrent[k] !== original;
      });
      return { ...prev, [choreId]: { ...existing, current: newCurrent, isDirty } };
    });
  }, []);

  const handleEditStart = useCallback((chore: Chore) => {
    setEditState((prev) => ({
      ...prev,
      [chore.id]: {
        original: chore,
        current: {},
        isDirty: false,
        fileSha: null,
      },
    }));
  }, []);

  const handleEditDiscard = useCallback((choreId: string) => {
    setEditState((prev) => {
      const next = { ...prev };
      delete next[choreId];
      return next;
    });
  }, []);

  const handleEditSave = useCallback(
    async (choreId: string) => {
      const state = editState[choreId];
      if (!state?.isDirty) return;

      try {
        await inlineUpdateMutation.mutateAsync({
          choreId,
          data: state.current,
        });
        // Clear edit state on success
        setEditState((prev) => {
          const next = { ...prev };
          delete next[choreId];
          return next;
        });
      } catch {
        // Error handled by mutation state
      }
    },
    [editState, inlineUpdateMutation]
  );

  const handleTemplateClick = (template: ChoreTemplate) => {
    setPreselectedTemplate(template);
    setShowAddModal(true);
  };

  const handleCloseModal = () => {
    setShowAddModal(false);
    setPreselectedTemplate(null);
  };

  // Filter templates that don't already have a matching created chore
  const uncreatedTemplates = repoTemplates?.filter(
    (tpl) => !chores?.some((c) => c.name === tpl.name)
  );

  const filteredChores = (chores ?? [])
    .filter((chore) => {
      const query = deferredSearch.trim().toLowerCase();
      const matchesSearch =
        query.length === 0 ||
        chore.name.toLowerCase().includes(query) ||
        chore.template_path.toLowerCase().includes(query);

      const matchesStatus = statusFilter === 'all' || chore.status === statusFilter;
      const matchesSchedule =
        scheduleFilter === 'all' ||
        (scheduleFilter === 'unscheduled'
          ? !chore.schedule_type
          : chore.schedule_type === scheduleFilter);

      return matchesSearch && matchesStatus && matchesSchedule;
    })
    .sort((left, right) => {
      if (sortMode === 'name') {
        return left.name.localeCompare(right.name);
      }

      if (sortMode === 'updated') {
        return new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime();
      }

      const attentionScore = (value: typeof left) => {
        if (value.status === 'active' && !value.schedule_type) return 0;
        if (value.current_issue_number) return 1;
        if (value.status === 'paused') return 3;
        return 2;
      };

      return attentionScore(left) - attentionScore(right);
    });

  const spotlightChores = filteredChores.slice(0, 3);
  const activeChores = chores?.filter((chore) => chore.status === 'active').length ?? 0;
  const pausedChores = chores?.filter((chore) => chore.status === 'paused').length ?? 0;
  const unscheduledChores = chores?.filter((chore) => !chore.schedule_type).length ?? 0;

  return (
    <div className="celestial-fade-in flex min-w-0 flex-col gap-6">
      <div className="ritual-stage flex flex-col gap-4 rounded-[1.55rem] p-4 sm:rounded-[1.8rem] sm:p-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">Upkeep studio</p>
          <h3 className="mt-2 text-[1.55rem] font-display font-medium leading-tight sm:text-[1.9rem]">
            Recurring work, given actual breathing room
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Templates, active chores, and manual cleanup controls now sit in one broader workspace
            instead of a single narrow rail.
          </p>
        </div>

        <div className="flex flex-col items-stretch gap-2">
          <CleanUpButton
            key={`${projectId}:${owner ?? ''}/${repo ?? ''}`}
            owner={owner}
            repo={repo}
            projectId={projectId}
          />
          <Button onClick={() => setShowAddModal(true)} size="lg">
            + Add Chore
          </Button>
        </div>
      </div>

      {/* Unsaved changes banner */}
      {isAnyDirty && (
        <div className="flex items-center justify-between gap-4 rounded-[1.2rem] border border-yellow-500/30 bg-yellow-50 px-4 py-3 dark:bg-yellow-900/20">
          <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
            You have unsaved changes
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setEditState({})}>
              Discard All
            </Button>
            <Button
              size="sm"
              onClick={async () => {
                const dirtyIds = Object.keys(editState).filter((id) => editState[id]?.isDirty);
                for (const id of dirtyIds) {
                  await handleEditSave(id);
                }
              }}
              disabled={inlineUpdateMutation.isPending}
            >
              {inlineUpdateMutation.isPending ? 'Saving…' : 'Save All'}
            </Button>
          </div>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-56 rounded-[1.4rem] border border-border bg-background/40 animate-pulse"
            />
          ))}
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="flex flex-col items-center gap-2 rounded-[1.4rem] border border-destructive/30 bg-destructive/5 p-6 text-center">
          <span className="text-sm text-destructive">Failed to load chores</span>
          <p className="text-xs text-muted-foreground">{error.message}</p>
        </div>
      )}

      {/* Empty state */}
      {!isLoading &&
        !error &&
        chores &&
        chores.length === 0 &&
        (!uncreatedTemplates || uncreatedTemplates.length === 0) && (
          <div className="celestial-panel flex flex-col items-center gap-3 rounded-[1.5rem] border-2 border-dashed border-border bg-background/28 p-8 text-center">
            <ScrollText className="h-8 w-8 text-primary/80" />
            <p className="text-lg font-medium text-foreground">No chores yet</p>
            <p className="max-w-md text-sm text-muted-foreground">
              Add a chore to set up recurring maintenance tasks
            </p>
            <Button onClick={() => setShowAddModal(true)}>Create the first chore</Button>
          </div>
        )}

      {!isLoading && !error && (
        <>
          {(uncreatedTemplates && uncreatedTemplates.length > 0) || spotlightChores.length > 0 ? (
            <section
              id="chore-templates"
              className="ritual-stage scroll-mt-6 rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6"
            >
              <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <div className="flex items-center gap-2 text-primary">
                    <Sparkles className="h-4 w-4" />
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
                  <Card className="moonwell rounded-[1.35rem] border-primary/15 shadow-none">
                    <CardContent className="p-4">
                      <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                        Total chores
                      </p>
                      <p className="mt-2 text-2xl font-semibold text-foreground">
                        {chores?.length ?? 0}
                      </p>
                    </CardContent>
                  </Card>
                  <Card className="moonwell rounded-[1.35rem] border-primary/15 shadow-none">
                    <CardContent className="p-4">
                      <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                        Active
                      </p>
                      <p className="mt-2 text-2xl font-semibold text-foreground">{activeChores}</p>
                    </CardContent>
                  </Card>
                  <Card className="moonwell rounded-[1.35rem] border-primary/15 shadow-none">
                    <CardContent className="p-4">
                      <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                        Paused
                      </p>
                      <p className="mt-2 text-2xl font-semibold text-foreground">{pausedChores}</p>
                    </CardContent>
                  </Card>
                  <Card className="moonwell rounded-[1.35rem] border-primary/15 shadow-none">
                    <CardContent className="p-4">
                      <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                        Unscheduled
                      </p>
                      <p className="mt-2 text-2xl font-semibold text-foreground">
                        {unscheduledChores}
                      </p>
                    </CardContent>
                  </Card>
                </div>
              </div>

              {uncreatedTemplates && uncreatedTemplates.length > 0 ? (
                <div className="constellation-grid mt-6 grid gap-4 lg:grid-cols-3">
                  {uncreatedTemplates.slice(0, 3).map((tpl) => (
                    <button
                      key={tpl.path}
                      onClick={() => handleTemplateClick(tpl)}
                      className="text-left"
                      type="button"
                    >
                      <Card className="moonwell h-full rounded-[1.55rem] border-dashed border-primary/25">
                        <CardContent className="flex h-full flex-col gap-4 p-5">
                          <div className="flex items-center justify-between gap-3">
                            <span className="rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[10px] uppercase tracking-[0.16em] text-primary">
                              Repo template
                            </span>
                            <ScrollText className="h-4 w-4 text-primary/70" />
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
                      onEditStart={() => handleEditStart(chore)}
                      onEditChange={(updates) => handleEditChange(chore.id, updates)}
                      onEditSave={() => handleEditSave(chore.id)}
                      onEditDiscard={() => handleEditDiscard(chore.id)}
                      isSaving={inlineUpdateMutation.isPending}
                    />
                  ))}
                </div>
              )}
            </section>
          ) : null}

          {chores && chores.length > 0 && (
            <section
              id="chores-catalog"
              className="ritual-stage scroll-mt-6 rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6"
            >
              <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">
                    Catalog controls
                  </p>
                  <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">
                    Filter active routines
                  </h4>
                </div>

                <div className="flex flex-col gap-3 xl:min-w-[34rem]">
                  <div className="relative">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                      placeholder="Search by name or template path"
                      aria-label="Search chores by name or template path"
                      className="moonwell h-12 rounded-full border-border/60 pl-10"
                    />
                  </div>
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <div className="flex flex-wrap gap-2">
                      {[
                        { value: 'all', label: 'All states' },
                        { value: 'active', label: 'Active' },
                        { value: 'paused', label: 'Paused' },
                      ].map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => setStatusFilter(option.value as ChoreStatusFilter)}
                          className={cn(
                            'rounded-full border px-3 py-1.5 text-xs font-medium uppercase tracking-[0.16em] transition-colors',
                            statusFilter === option.value
                              ? 'solar-chip'
                              : 'solar-chip-soft hover:bg-primary/10 hover:text-foreground'
                          )}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>

                    <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
                      <select
                        className="moonwell h-10 w-full rounded-full border-border/60 px-4 text-sm text-foreground sm:w-auto"
                        value={scheduleFilter}
                        onChange={(event) =>
                          setScheduleFilter(event.target.value as ScheduleFilter)
                        }
                        aria-label="Filter chores by schedule"
                      >
                        <option value="all">All schedules</option>
                        <option value="time">Time-based</option>
                        <option value="count">Count-based</option>
                        <option value="unscheduled">Unscheduled</option>
                      </select>
                      <select
                        className="moonwell h-10 w-full rounded-full border-border/60 px-4 text-sm text-foreground sm:w-auto"
                        value={sortMode}
                        onChange={(event) => setSortMode(event.target.value as ChoreSortMode)}
                        aria-label="Sort chores"
                      >
                        <option value="attention">Needs attention</option>
                        <option value="updated">Recently updated</option>
                        <option value="name">Alphabetical</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              {filteredChores.length === 0 ? (
                <div className="mt-6 rounded-[1.35rem] border border-dashed border-border/80 bg-background/42 p-8 text-center">
                  <p className="text-sm text-muted-foreground">
                    No chores match the current filters.
                  </p>
                  <Button
                    variant="ghost"
                    className="mt-3"
                    onClick={() => {
                      setSearch('');
                      setStatusFilter('all');
                      setScheduleFilter('all');
                      setSortMode('attention');
                    }}
                  >
                    Reset filters
                  </Button>
                </div>
              ) : (
                <div className="constellation-grid mt-6 grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
                  {filteredChores.map((chore) => (
                    <ChoreCard
                      key={chore.id}
                      chore={chore}
                      projectId={projectId}
                      parentIssueCount={parentIssueCount}
                      editState={editState[chore.id]}
                      onEditStart={() => handleEditStart(chore)}
                      onEditChange={(updates) => handleEditChange(chore.id, updates)}
                      onEditSave={() => handleEditSave(chore.id)}
                      onEditDiscard={() => handleEditDiscard(chore.id)}
                      isSaving={inlineUpdateMutation.isPending}
                    />
                  ))}
                </div>
              )}
            </section>
          )}

          {uncreatedTemplates && uncreatedTemplates.length > 3 && (
            <section className="ritual-stage rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6">
              <div>
                <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">
                  Repository templates
                </p>
                <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">
                  More rituals available in the repo
                </h4>
              </div>
              <div className="constellation-grid mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {uncreatedTemplates.slice(3).map((tpl) => (
                  <button
                    key={tpl.path}
                    onClick={() => handleTemplateClick(tpl)}
                    className="flex items-start gap-3 rounded-[1.2rem] border border-dashed border-border bg-background/28 p-4 text-left transition-colors hover:border-primary/40 hover:bg-primary/10"
                    title={tpl.about || tpl.name}
                    type="button"
                  >
                    <ScrollText className="h-4 w-4 shrink-0 text-primary/70" />
                    <div className="flex min-w-0 flex-col gap-1">
                      <span className="text-sm font-medium text-foreground truncate">
                        {tpl.name}
                      </span>
                      {tpl.about && (
                        <span className="text-xs leading-5 text-muted-foreground line-clamp-3">
                          {tpl.about}
                        </span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </section>
          )}
        </>
      )}

      {/* Add Chore Modal */}
      <AddChoreModal
        projectId={projectId}
        isOpen={showAddModal}
        onClose={handleCloseModal}
        initialTemplate={preselectedTemplate}
      />
    </div>
  );
}
