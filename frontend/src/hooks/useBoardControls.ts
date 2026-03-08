/**
 * useBoardControls hook — manages filter, sort, and group-by state for the
 * Project Board with localStorage persistence and in-memory transforms.
 */

import { useState, useMemo, useCallback, useEffect } from 'react';
import type { BoardDataResponse, BoardItem, BoardColumn } from '@/types';

// ─── State interfaces ─────────────────────────────────────────────────────────

export interface BoardFilterState {
  labels: string[];
  assignees: string[];
  milestones: string[];
}

export interface BoardSortState {
  field: 'created' | 'updated' | 'priority' | 'title' | null;
  direction: 'asc' | 'desc';
}

export interface BoardGroupState {
  field: 'label' | 'assignee' | 'milestone' | null;
}

export interface BoardControlsState {
  filters: BoardFilterState;
  sort: BoardSortState;
  group: BoardGroupState;
}

export interface BoardGroup {
  name: string;
  items: BoardItem[];
}

// ─── Defaults ─────────────────────────────────────────────────────────────────

const DEFAULT_FILTERS: BoardFilterState = { labels: [], assignees: [], milestones: [] };
const DEFAULT_SORT: BoardSortState = { field: null, direction: 'asc' };
const DEFAULT_GROUP: BoardGroupState = { field: null };

const VALID_SORT_FIELDS: Array<BoardSortState['field']> = ['created', 'updated', 'priority', 'title', null];
const VALID_SORT_DIRECTIONS: Array<BoardSortState['direction']> = ['asc', 'desc'];
const VALID_GROUP_FIELDS: Array<BoardGroupState['field']> = ['label', 'assignee', 'milestone', null];

function cloneFilters(filters: BoardFilterState = DEFAULT_FILTERS): BoardFilterState {
  return {
    labels: [...filters.labels],
    assignees: [...filters.assignees],
    milestones: [...filters.milestones],
  };
}

function defaultControls(): BoardControlsState {
  return {
    filters: cloneFilters(),
    sort: { ...DEFAULT_SORT },
    group: { ...DEFAULT_GROUP },
  };
}

// ─── localStorage helpers ─────────────────────────────────────────────────────

function storageKey(projectId: string) {
  return `board-controls-${projectId}`;
}

function mergeStoredControlsWithDefaults(value: unknown): BoardControlsState {
  const base = defaultControls();

  if (!value || typeof value !== 'object') {
    return base;
  }

  const parsed = value as {
    filters?: Partial<BoardFilterState>;
    sort?: Partial<BoardSortState>;
    group?: Partial<BoardGroupState>;
  };

  const filters = parsed.filters ?? {};
  const sort = parsed.sort ?? {};
  const group = parsed.group ?? {};

  return {
    filters: {
      labels: Array.isArray(filters.labels) ? [...filters.labels] : base.filters.labels,
      assignees: Array.isArray(filters.assignees) ? [...filters.assignees] : base.filters.assignees,
      milestones: Array.isArray(filters.milestones) ? [...filters.milestones] : base.filters.milestones,
    },
    sort: {
      field: VALID_SORT_FIELDS.includes(sort.field ?? null) ? (sort.field ?? null) : base.sort.field,
      direction: VALID_SORT_DIRECTIONS.includes(sort.direction ?? 'asc')
        ? (sort.direction ?? 'asc')
        : base.sort.direction,
    },
    group: {
      field: VALID_GROUP_FIELDS.includes(group.field ?? null) ? (group.field ?? null) : base.group.field,
    },
  };
}

function loadControls(projectId: string | null): BoardControlsState {
  if (!projectId) return defaultControls();
  try {
    const raw = localStorage.getItem(storageKey(projectId));
    if (!raw) return defaultControls();
    return mergeStoredControlsWithDefaults(JSON.parse(raw));
  } catch {
    return defaultControls();
  }
}

function saveControls(projectId: string | null, state: BoardControlsState) {
  if (!projectId) return;
  try {
    localStorage.setItem(storageKey(projectId), JSON.stringify(state));
  } catch {
    // Ignore storage errors so board rendering stays functional.
  }
}

// ─── Priority mapping ─────────────────────────────────────────────────────────

const PRIORITY_ORDER: Record<string, number> = { P0: 0, P1: 1, P2: 2, P3: 3 };

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useBoardControls(projectId: string | null, boardData: BoardDataResponse | undefined) {
  const [controls, setControlsState] = useState<BoardControlsState>(() => loadControls(projectId));
  const [hydratedProjectId, setHydratedProjectId] = useState<string | null>(projectId);

  // Reload controls when projectId changes
  useEffect(() => {
    setControlsState(loadControls(projectId));
    setHydratedProjectId(projectId);
  }, [projectId]);

  // Persist on change
  useEffect(() => {
    if (!projectId || hydratedProjectId !== projectId) {
      return;
    }
    saveControls(projectId, controls);
  }, [projectId, hydratedProjectId, controls]);

  // ── Setters ───────────────────────────────────────────────────────────────

  const setFilters = useCallback((filters: BoardFilterState) => {
    setControlsState((prev) => ({ ...prev, filters }));
  }, []);

  const setSort = useCallback((sort: BoardSortState) => {
    setControlsState((prev) => ({ ...prev, sort }));
  }, []);

  const setGroup = useCallback((group: BoardGroupState) => {
    setControlsState((prev) => ({ ...prev, group }));
  }, []);

  const clearAll = useCallback(() => {
    setControlsState(defaultControls());
  }, []);

  // ── Available options (derived from raw board data) ───────────────────────

  const availableLabels = useMemo(() => {
    if (!boardData) return [];
    const set = new Set<string>();
    for (const col of boardData.columns) {
      for (const item of col.items) {
        for (const label of item.labels ?? []) {
          set.add(label.name);
        }
      }
    }
    return Array.from(set).sort();
  }, [boardData]);

  const availableAssignees = useMemo(() => {
    if (!boardData) return [];
    const set = new Set<string>();
    for (const col of boardData.columns) {
      for (const item of col.items) {
        for (const a of item.assignees) {
          set.add(a.login);
        }
      }
    }
    return Array.from(set).sort();
  }, [boardData]);

  const availableMilestones = useMemo(() => {
    if (!boardData) return [];
    const set = new Set<string>();
    for (const col of boardData.columns) {
      for (const item of col.items) {
        if (item.milestone) set.add(item.milestone);
      }
    }
    return Array.from(set).sort();
  }, [boardData]);

  // ── Transform: filter → sort → (group is applied at render time) ──────────

  const transformedData = useMemo((): BoardDataResponse | undefined => {
    if (!boardData) return undefined;

    const { filters, sort } = controls;

    const transformColumn = (col: BoardColumn): BoardColumn => {
      let items = col.items;

      // Filter
      if (filters.labels.length > 0) {
        items = items.filter((item) =>
          filters.labels.some((lbl) => (item.labels ?? []).some((l) => l.name === lbl))
        );
      }
      if (filters.assignees.length > 0) {
        items = items.filter((item) =>
          filters.assignees.some((a) => item.assignees.some((ia) => ia.login === a))
        );
      }
      if (filters.milestones.length > 0) {
        items = items.filter((item) =>
          item.milestone != null && filters.milestones.includes(item.milestone)
        );
      }

      // Sort
      if (sort.field) {
        items = [...items].sort((a, b) => {
          let cmp = 0;
          switch (sort.field) {
            case 'created':
              cmp = (a.created_at ?? '').localeCompare(b.created_at ?? '');
              break;
            case 'updated':
              cmp = (a.updated_at ?? '').localeCompare(b.updated_at ?? '');
              break;
            case 'priority': {
              const pa = PRIORITY_ORDER[a.priority?.name ?? ''] ?? 99;
              const pb = PRIORITY_ORDER[b.priority?.name ?? ''] ?? 99;
              cmp = pa - pb;
              break;
            }
            case 'title':
              cmp = a.title.localeCompare(b.title);
              break;
          }
          return sort.direction === 'desc' ? -cmp : cmp;
        });
      }

      return {
        ...col,
        items,
        item_count: items.length,
        estimate_total: items.reduce((s, it) => s + (it.estimate ?? 0), 0),
      };
    };

    return {
      ...boardData,
      columns: boardData.columns.map(transformColumn),
    };
  }, [boardData, controls]);

  // ── Group helper ──────────────────────────────────────────────────────────

  const getGroups = useCallback(
    (items: BoardItem[]): BoardGroup[] | null => {
      const { group } = controls;
      if (!group.field) return null;

      const map = new Map<string, BoardItem[]>();

      for (const item of items) {
        let key: string;
        switch (group.field) {
          case 'label':
            key = (item.labels ?? [])[0]?.name ?? 'No Label';
            break;
          case 'assignee':
            key = item.assignees[0]?.login ?? 'Unassigned';
            break;
          case 'milestone':
            key = item.milestone ?? 'No Milestone';
            break;
          default:
            key = 'Other';
        }
        const existing = map.get(key) ?? [];
        existing.push(item);
        map.set(key, existing);
      }

      return Array.from(map.entries())
        .map(([name, groupItems]) => ({ name, items: groupItems }))
        .sort((a, b) => a.name.localeCompare(b.name));
    },
    [controls]
  );

  // ── Active state checks ───────────────────────────────────────────────────

  const hasActiveFilters =
    controls.filters.labels.length > 0 ||
    controls.filters.assignees.length > 0 ||
    controls.filters.milestones.length > 0;

  const hasActiveSort = controls.sort.field !== null;
  const hasActiveGroup = controls.group.field !== null;
  const hasActiveControls = hasActiveFilters || hasActiveSort || hasActiveGroup;

  return {
    controls,
    setFilters,
    setSort,
    setGroup,
    clearAll,
    availableLabels,
    availableAssignees,
    availableMilestones,
    transformedData,
    getGroups,
    hasActiveFilters,
    hasActiveSort,
    hasActiveGroup,
    hasActiveControls,
  };
}
