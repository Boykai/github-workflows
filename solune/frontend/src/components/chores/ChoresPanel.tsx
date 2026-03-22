/**
 * ChoresPanel — container for the Chores feature on the project board.
 *
 * Composes ChoresToolbar, ChoresGrid, ChoresSaveAllBar, ChoresSpotlight,
 * and AddChoreModal. Handles inline editing with dirty tracking, filtering,
 * sorting, and loading/error/empty states.
 */

import { useCallback, useDeferredValue, useEffect, useMemo, useState } from 'react';
import { ScrollText } from '@/lib/icons';
import { useChoresListPaginated, useChoreTemplates, useInlineUpdateChore, useAllChoreNames } from '@/hooks/useChores';
import type { ChoresFilterParams } from '@/hooks/useChores';
import { AddChoreModal } from './AddChoreModal';
import { ChoresToolbar } from './ChoresToolbar';
import { ChoresGrid } from './ChoresGrid';
import { ChoresSaveAllBar } from './ChoresSaveAllBar';
import { ChoresSpotlight } from './ChoresSpotlight';
import { CleanUpButton } from '@/components/board/CleanUpButton';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { isRateLimitApiError } from '@/utils/rateLimit';
import type { Chore, ChoreEditState, ChoreInlineUpdate, ChoreTemplate } from '@/types';
import type { ChoreStatusFilter, ScheduleFilter, ChoreSortMode } from './ChoresToolbar';
import { Button } from '@/components/ui/button';

interface ChoresPanelProps {
  projectId: string;
  owner?: string;
  repo?: string;
  parentIssueCount?: number;
  onDirtyChange?: (isDirty: boolean) => void;
}

export function ChoresPanel({
  projectId,
  owner,
  repo,
  parentIssueCount = 0,
  onDirtyChange,
}: ChoresPanelProps) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [preselectedTemplate, setPreselectedTemplate] = useState<ChoreTemplate | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<ChoreStatusFilter>('all');
  const [scheduleFilter, setScheduleFilter] = useState<ScheduleFilter>('all');
  const [sortMode, setSortMode] = useState<ChoreSortMode>('attention');
  const deferredSearch = useDeferredValue(search);

  // ── Server-side filter params ──
  const sortMap: Record<ChoreSortMode, Pick<ChoresFilterParams, 'sort' | 'order'>> = {
    attention: { sort: 'attention', order: 'asc' },
    updated: { sort: 'updated_at', order: 'desc' },
    name: { sort: 'name', order: 'asc' },
  };
  const filterParams: ChoresFilterParams = {
    ...(statusFilter !== 'all' ? { status: statusFilter } : {}),
    ...(scheduleFilter !== 'all' ? { scheduleType: scheduleFilter } : {}),
    ...(deferredSearch.trim() ? { search: deferredSearch.trim() } : {}),
    ...sortMap[sortMode],
  };

  const {
    allItems: chores,
    isLoading,
    error,
    refetch,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  } = useChoresListPaginated(projectId, filterParams);
  const { data: repoTemplates } = useChoreTemplates(projectId);
  const { data: allChoreNames } = useAllChoreNames(projectId);
  // ── Inline Edit State ──
  const [editState, setEditState] = useState<Record<string, ChoreEditState>>({});
  const inlineUpdateMutation = useInlineUpdateChore(projectId);

  const isAnyDirty = useMemo(() => Object.values(editState).some((s) => s.isDirty), [editState]);

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
      [chore.id]: { original: chore, current: {}, isDirty: false, fileSha: null },
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
        await inlineUpdateMutation.mutateAsync({ choreId, data: state.current });
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

  const handleSaveAll = useCallback(async () => {
    const dirtyIds = Object.keys(editState).filter((id) => editState[id]?.isDirty);
    for (const id of dirtyIds) {
      await handleEditSave(id);
    }
  }, [editState, handleEditSave]);

  const handleTemplateClick = (template: ChoreTemplate) => {
    setPreselectedTemplate(template);
    setShowAddModal(true);
  };

  const handleCloseModal = () => {
    setShowAddModal(false);
    setPreselectedTemplate(null);
  };

  const handleResetFilters = useCallback(() => {
    setSearch('');
    setStatusFilter('all');
    setScheduleFilter('all');
    setSortMode('attention');
  }, []);

  const allChoreNameSet = useMemo(
    () => new Set(allChoreNames ?? []),
    [allChoreNames]
  );
  const uncreatedTemplates = useMemo(
    () => repoTemplates?.filter((tpl) => !allChoreNameSet.has(tpl.name)) ?? [],
    [repoTemplates, allChoreNameSet]
  );

  const spotlightChores = chores.slice(0, 3);
  const activeChores = chores.filter((chore) => chore.status === 'active').length;
  const pausedChores = chores.filter((chore) => chore.status === 'paused').length;
  const unscheduledChores = chores.filter((chore) => !chore.schedule_type).length;
  const isRateLimited = isRateLimitApiError(error);
  const hasActiveFilters =
    statusFilter !== 'all' || scheduleFilter !== 'all' || deferredSearch.trim() !== '';

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
            + Create Chore
          </Button>
        </div>
      </div>

      <ChoresSaveAllBar
        isVisible={isAnyDirty}
        isSaving={inlineUpdateMutation.isPending}
        onDiscardAll={() => setEditState({})}
        onSaveAll={handleSaveAll}
      />

      {isLoading && (
        <div className="flex flex-col items-center justify-center gap-3 py-12">
          <CelestialLoader size="md" label="Loading chores…" />
        </div>
      )}

      {error && !isLoading && (
        <div className="flex flex-col items-center gap-3 rounded-[1.4rem] border border-destructive/30 bg-destructive/5 p-6 text-center">
          <span className="text-sm font-medium text-destructive">
            {isRateLimited ? 'Rate limit reached' : 'Could not load chores'}
          </span>
          <p className="text-xs text-muted-foreground">
            {isRateLimited
              ? 'Too many requests. Please wait a moment and try again.'
              : `${error.message}. Check your connection and retry.`}
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      )}

      {!isLoading &&
        !error &&
        !hasActiveFilters &&
        chores.length === 0 &&
        uncreatedTemplates.length === 0 && (
          <div className="celestial-panel flex flex-col items-center gap-3 rounded-[1.5rem] border-2 border-dashed border-border bg-background/28 p-8 text-center">
            <ScrollText className="h-8 w-8 text-primary/80" aria-hidden="true" />
            <p className="text-lg font-medium text-foreground">No chores yet</p>
            <p className="max-w-md text-sm text-muted-foreground">
              Create a chore to set up recurring maintenance routines for your project.
            </p>
            <Button onClick={() => setShowAddModal(true)}>Create First Chore</Button>
          </div>
        )}

      {!isLoading && !error && (
        <>
          <ChoresSpotlight
            chores={chores}
            uncreatedTemplates={uncreatedTemplates}
            spotlightChores={spotlightChores}
            projectId={projectId}
            parentIssueCount={parentIssueCount}
            activeCount={activeChores}
            pausedCount={pausedChores}
            unscheduledCount={unscheduledChores}
            editState={editState}
            onEditStart={handleEditStart}
            onEditChange={handleEditChange}
            onEditSave={handleEditSave}
            onEditDiscard={handleEditDiscard}
            isSaving={inlineUpdateMutation.isPending}
            onTemplateClick={handleTemplateClick}
          />

          {(chores.length > 0 || hasActiveFilters) && (
            <section
              id="chores-catalog"
              className="ritual-stage scroll-mt-6 rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6"
            >
              <ChoresToolbar
                search={search}
                onSearchChange={setSearch}
                statusFilter={statusFilter}
                onStatusFilterChange={setStatusFilter}
                scheduleFilter={scheduleFilter}
                onScheduleFilterChange={setScheduleFilter}
                sortMode={sortMode}
                onSortModeChange={setSortMode}
              />
              <ChoresGrid
                chores={chores}
                projectId={projectId}
                parentIssueCount={parentIssueCount}
                editState={editState}
                onEditStart={handleEditStart}
                onEditChange={handleEditChange}
                onEditSave={handleEditSave}
                onEditDiscard={handleEditDiscard}
                isSaving={inlineUpdateMutation.isPending}
                onResetFilters={handleResetFilters}
                hasNextPage={hasNextPage}
                isFetchingNextPage={isFetchingNextPage}
                fetchNextPage={fetchNextPage}
              />
            </section>
          )}

          {uncreatedTemplates.length > 3 && (
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
                    className="celestial-focus flex items-start gap-3 rounded-[1.2rem] border border-dashed border-border bg-background/28 p-4 text-left transition-colors hover:border-primary/40 hover:bg-primary/10 focus-visible:outline-none"
                    title={tpl.about || tpl.name}
                    type="button"
                  >
                    <ScrollText className="h-4 w-4 shrink-0 text-primary/70" aria-hidden="true" />
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

      <AddChoreModal
        projectId={projectId}
        isOpen={showAddModal}
        onClose={handleCloseModal}
        initialTemplate={preselectedTemplate}
      />
    </div>
  );
}
