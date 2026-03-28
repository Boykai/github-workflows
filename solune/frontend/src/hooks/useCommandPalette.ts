/**
 * useCommandPalette — search logic, result aggregation, and state management
 * for the global command palette (Ctrl+K / Cmd+K).
 *
 * Aggregates results from navigation routes, entity hooks (agents, pipelines,
 * tools, chores, apps), and quick actions into a single filtered list with
 * keyboard navigation support.
 */

import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Bot,
  GitBranch,
  Wrench,
  ListChecks,
  Boxes,
  Zap,
  SunMoon,
  MessageSquare,
  HelpCircle,
} from '@/lib/icons';
import type { LucideIcon } from '@/lib/icons';
import { NAV_ROUTES } from '@/constants';
import { useAgentsList } from '@/hooks/useAgents';
import { usePipelineConfig } from '@/hooks/usePipelineConfig';
import { useToolsList } from '@/hooks/useTools';
import { useChoresListPaginated } from '@/hooks/useChores';
import { useApps } from '@/hooks/useApps';
import { useAppTheme } from '@/hooks/useAppTheme';

// ============ Types ============

export type CommandCategory =
  | 'pages'
  | 'agents'
  | 'pipelines'
  | 'tools'
  | 'chores'
  | 'apps'
  | 'actions';

export interface CommandPaletteItem {
  id: string;
  label: string;
  category: CommandCategory;
  icon: LucideIcon;
  description?: string;
  keywords: string[];
  action: () => void;
}

export interface UseCommandPaletteOptions {
  projectId: string | null;
  isOpen: boolean;
}

export interface UseCommandPaletteReturn {
  query: string;
  setQuery: (query: string) => void;
  results: CommandPaletteItem[];
  selectedIndex: number;
  moveUp: () => void;
  moveDown: () => void;
  selectCurrent: () => void;
  isLoading: boolean;
}

// ============ Category metadata ============

export const CATEGORY_META: Record<
  CommandCategory,
  { label: string; icon: LucideIcon; order: number }
> = {
  pages: { label: 'Pages', icon: LayoutDashboard, order: 0 },
  agents: { label: 'Agents', icon: Bot, order: 1 },
  pipelines: { label: 'Pipelines', icon: GitBranch, order: 2 },
  tools: { label: 'Tools', icon: Wrench, order: 3 },
  chores: { label: 'Chores', icon: ListChecks, order: 4 },
  apps: { label: 'Apps', icon: Boxes, order: 5 },
  actions: { label: 'Actions', icon: Zap, order: 6 },
};


// ============ Search helper ============

function matchesQuery(item: CommandPaletteItem, query: string): boolean {
  const q = query.toLowerCase();
  if (item.label.toLowerCase().includes(q)) return true;
  return item.keywords.some((kw) => kw.toLowerCase().includes(q));
}

// ============ Hook ============

export function useCommandPalette({
  projectId,
  isOpen,
}: UseCommandPaletteOptions): UseCommandPaletteReturn {
  const navigate = useNavigate();
  const { toggleTheme } = useAppTheme();

  const [query, setQueryRaw] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // ---- Focus save on mount, restore on unmount ----
  // Component is conditionally mounted only when open, so we save the
  // previously-focused element once on mount and restore it on unmount.
  useEffect(() => {
    previousFocusRef.current = document.activeElement as HTMLElement | null;
    return () => {
      const el = previousFocusRef.current;
      if (el && document.body.contains(el)) {
        el.focus();
      }
    };
  }, []);

  // ---- Entity data sources (enabled only when open) ----
  const agentsQuery = useAgentsList(isOpen ? projectId : null);
  const pipelineConfig = usePipelineConfig(isOpen ? projectId ?? null : null);
  const toolsData = useToolsList(isOpen ? projectId : null);
  const choresQuery = useChoresListPaginated(isOpen ? projectId : null);
  const appsQuery = useApps();

  // ---- Build all items ----
  const allItems = useMemo<CommandPaletteItem[]>(() => {
    const items: CommandPaletteItem[] = [];

    // Pages from NAV_ROUTES
    for (const route of NAV_ROUTES) {
      items.push({
        id: `page-${route.path}`,
        label: route.label,
        category: 'pages',
        icon: route.icon as LucideIcon,
        keywords: [route.path],
        action: () => navigate(route.path),
      });
    }

    // Agents
    if (agentsQuery.data) {
      for (const agent of agentsQuery.data) {
        items.push({
          id: `agent-${agent.name}`,
          label: agent.name,
          category: 'agents',
          icon: Bot,
          keywords: [],
          action: () => navigate('/agents'),
        });
      }
    }

    // Pipelines
    if (pipelineConfig.pipelines?.pipelines) {
      for (const pipeline of pipelineConfig.pipelines.pipelines) {
        items.push({
          id: `pipeline-${pipeline.name}`,
          label: pipeline.name,
          category: 'pipelines',
          icon: GitBranch,
          keywords: [pipeline.description ?? ''],
          action: () => navigate('/pipeline'),
        });
      }
    }

    // Tools
    if (toolsData.tools) {
      for (const tool of toolsData.tools) {
        items.push({
          id: `tool-${tool.name}`,
          label: tool.name,
          category: 'tools',
          icon: Wrench,
          keywords: [tool.description ?? ''],
          action: () => navigate('/tools'),
        });
      }
    }

    // Chores
    if (choresQuery.allItems) {
      for (const chore of choresQuery.allItems) {
        items.push({
          id: `chore-${chore.name}`,
          label: chore.name,
          category: 'chores',
          icon: ListChecks,
          keywords: [],
          action: () => navigate('/chores'),
        });
      }
    }

    // Apps
    if (appsQuery.data) {
      for (const app of appsQuery.data) {
        items.push({
          id: `app-${app.name}`,
          label: app.display_name || app.name,
          category: 'apps',
          icon: Boxes,
          keywords: [app.name, app.description ?? ''],
          action: () => navigate(`/apps/${app.name}`),
        });
      }
    }

    // Quick actions
    items.push({
      id: 'action-toggle-theme',
      label: 'Toggle Theme',
      category: 'actions',
      icon: SunMoon,
      description: 'Switch between light and dark mode',
      keywords: ['dark', 'light', 'mode', 'theme'],
      action: toggleTheme,
    });
    items.push({
      id: 'action-focus-chat',
      label: 'Focus Chat',
      category: 'actions',
      icon: MessageSquare,
      description: 'Focus the chat input',
      keywords: ['chat', 'message', 'input'],
      action: () => window.dispatchEvent(new CustomEvent('solune:focus-chat')),
    });
    items.push({
      id: 'action-help',
      label: 'Help',
      category: 'actions',
      icon: HelpCircle,
      description: 'Open the help page',
      keywords: ['help', 'support', 'docs'],
      action: () => navigate('/help'),
    });

    return items;
  }, [
    navigate,
    toggleTheme,
    agentsQuery.data,
    pipelineConfig.pipelines,
    toolsData.tools,
    choresQuery.allItems,
    appsQuery.data,
  ]);

  // ---- Filter and sort results ----
  const results = useMemo<CommandPaletteItem[]>(() => {
    if (!query.trim()) return [];

    const filtered = allItems.filter((item) => matchesQuery(item, query));

    // Sort by category order, then alphabetically within category
    filtered.sort((a, b) => {
      const orderA = CATEGORY_META[a.category].order;
      const orderB = CATEGORY_META[b.category].order;
      if (orderA !== orderB) return orderA - orderB;
      return a.label.localeCompare(b.label);
    });

    return filtered;
  }, [allItems, query]);

  // ---- Update query ----
  const setQuery = useCallback((q: string) => {
    setQueryRaw(q);
    setSelectedIndex(0);
  }, []);

  // ---- Keyboard navigation ----
  const moveUp = useCallback(() => {
    if (results.length === 0) return;
    setSelectedIndex((prev) => (prev <= 0 ? results.length - 1 : prev - 1));
  }, [results.length]);

  const moveDown = useCallback(() => {
    if (results.length === 0) return;
    setSelectedIndex((prev) => (prev >= results.length - 1 ? 0 : prev + 1));
  }, [results.length]);

  const selectCurrent = useCallback(() => {
    if (results.length > 0 && selectedIndex < results.length) {
      results[selectedIndex].action();
    }
  }, [results, selectedIndex]);

  // ---- Loading state ----
  const isLoading =
    agentsQuery.isLoading ||
    pipelineConfig.pipelinesLoading ||
    toolsData.isLoading ||
    choresQuery.isLoading ||
    appsQuery.isLoading;

  return {
    query,
    setQuery,
    results,
    selectedIndex,
    moveUp,
    moveDown,
    selectCurrent,
    isLoading,
  };
}
