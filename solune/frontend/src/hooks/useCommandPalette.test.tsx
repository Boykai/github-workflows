import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

const mockNavigate = vi.fn();
const mockToggleTheme = vi.fn();

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock('lucide-react', () => ({
  LayoutDashboard: 'LayoutDashboard',
  Bot: 'Bot',
  GitBranch: 'GitBranch',
  Wrench: 'Wrench',
  ListChecks: 'ListChecks',
  Boxes: 'Boxes',
  Zap: 'Zap',
  SunMoon: 'SunMoon',
  MessageSquare: 'MessageSquare',
  HelpCircle: 'HelpCircle',
  Kanban: 'Kanban',
  Clock: 'Clock',
  Settings: 'Settings',
}));

vi.mock('@/constants', () => ({
  NAV_ROUTES: [
    { path: '/', label: 'App', icon: 'LayoutDashboard' },
    { path: '/agents', label: 'Agents', icon: 'Bot' },
    { path: '/pipeline', label: 'Agents Pipelines', icon: 'GitBranch' },
  ],
}));

vi.mock('@/hooks/useAgents', () => ({
  useAgentsList: vi.fn(),
}));

vi.mock('@/hooks/usePipelineConfig', () => ({
  usePipelineConfig: vi.fn(),
}));

vi.mock('@/hooks/useTools', () => ({
  useToolsList: vi.fn(),
}));

vi.mock('@/hooks/useChores', () => ({
  useChoresListPaginated: vi.fn(),
}));

vi.mock('@/hooks/useApps', () => ({
  useApps: vi.fn(),
}));

vi.mock('@/hooks/useAppTheme', () => ({
  useAppTheme: () => ({ isDarkMode: false, toggleTheme: mockToggleTheme }),
}));

import { useCommandPalette } from './useCommandPalette';
import { useAgentsList } from '@/hooks/useAgents';
import { usePipelineConfig } from '@/hooks/usePipelineConfig';
import { useToolsList } from '@/hooks/useTools';
import { useChoresListPaginated } from '@/hooks/useChores';
import { useApps } from '@/hooks/useApps';

const mockUseAgentsList = useAgentsList as ReturnType<typeof vi.fn>;
const mockUsePipelineConfig = usePipelineConfig as ReturnType<typeof vi.fn>;
const mockUseToolsList = useToolsList as ReturnType<typeof vi.fn>;
const mockUseChoresListPaginated = useChoresListPaginated as ReturnType<typeof vi.fn>;
const mockUseApps = useApps as ReturnType<typeof vi.fn>;

function setupDefaultMocks({
  agentsData = undefined as { name: string }[] | undefined,
  pipelinesData = undefined as { pipelines: { name: string; description?: string }[] } | undefined,
  toolsData = [] as { name: string; description?: string }[],
  choresData = undefined as { name: string }[] | undefined,
  appsData = undefined as { name: string; display_name: string; description?: string }[] | undefined,
  isLoading = false,
} = {}) {
  mockUseAgentsList.mockReturnValue({ data: agentsData, isLoading });
  mockUsePipelineConfig.mockReturnValue({ pipelines: pipelinesData, pipelinesLoading: isLoading });
  mockUseToolsList.mockReturnValue({ tools: toolsData, isLoading });
  mockUseChoresListPaginated.mockReturnValue({ allItems: choresData ?? [], isLoading });
  mockUseApps.mockReturnValue({ data: appsData, isLoading });
}

describe('useCommandPalette', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  it('returns empty results with empty query', () => {
    const { result } = renderHook(() =>
      useCommandPalette({ projectId: 'proj-1', isOpen: true }),
    );

    expect(result.current.results).toEqual([]);
    expect(result.current.query).toBe('');
  });

  it('filters results by query matching labels', () => {
    setupDefaultMocks({
      agentsData: [{ name: 'AgentSmith' }],
    });

    const { result } = renderHook(() =>
      useCommandPalette({ projectId: 'proj-1', isOpen: true }),
    );

    act(() => {
      result.current.setQuery('Agent');
    });

    const labels = result.current.results.map((r) => r.label);
    expect(labels).toContain('Agents');
    expect(labels).toContain('AgentSmith');
  });

  it('filters results by query matching keywords', () => {
    const { result } = renderHook(() =>
      useCommandPalette({ projectId: 'proj-1', isOpen: true }),
    );

    act(() => {
      result.current.setQuery('/agents');
    });

    const labels = result.current.results.map((r) => r.label);
    expect(labels).toContain('Agents');
  });

  it('resets selectedIndex when query changes', () => {
    setupDefaultMocks({
      agentsData: [{ name: 'Agent1' }, { name: 'Agent2' }],
    });

    const { result } = renderHook(() =>
      useCommandPalette({ projectId: 'proj-1', isOpen: true }),
    );

    act(() => result.current.setQuery('Agent'));
    act(() => result.current.moveDown());
    expect(result.current.selectedIndex).toBe(1);

    act(() => result.current.setQuery('Agent1'));
    expect(result.current.selectedIndex).toBe(0);
  });

  it('moveDown wraps around to the beginning', () => {
    const { result } = renderHook(() =>
      useCommandPalette({ projectId: 'proj-1', isOpen: true }),
    );

    act(() => result.current.setQuery('App'));

    const count = result.current.results.length;
    expect(count).toBeGreaterThan(0);

    // Move past the end
    for (let i = 0; i < count; i++) {
      act(() => result.current.moveDown());
    }
    expect(result.current.selectedIndex).toBe(0);
  });

  it('moveUp wraps around to the end', () => {
    const { result } = renderHook(() =>
      useCommandPalette({ projectId: 'proj-1', isOpen: true }),
    );

    act(() => result.current.setQuery('App'));

    const count = result.current.results.length;
    expect(count).toBeGreaterThan(0);

    // Move up from index 0 → wraps to last
    act(() => result.current.moveUp());
    expect(result.current.selectedIndex).toBe(count - 1);
  });

  it('selectCurrent calls action of the selected item', () => {
    const { result } = renderHook(() =>
      useCommandPalette({ projectId: 'proj-1', isOpen: true }),
    );

    act(() => result.current.setQuery('App'));

    act(() => result.current.selectCurrent());

    expect(mockNavigate).toHaveBeenCalled();
  });

  it('reports loading state from sub-hooks', () => {
    setupDefaultMocks({ isLoading: true });

    const { result } = renderHook(() =>
      useCommandPalette({ projectId: 'proj-1', isOpen: true }),
    );

    expect(result.current.isLoading).toBe(true);
  });

  it('reports not loading when all sub-hooks are done', () => {
    setupDefaultMocks({ isLoading: false });

    const { result } = renderHook(() =>
      useCommandPalette({ projectId: 'proj-1', isOpen: true }),
    );

    expect(result.current.isLoading).toBe(false);
  });

  it('includes quick actions in search results', () => {
    const { result } = renderHook(() =>
      useCommandPalette({ projectId: 'proj-1', isOpen: true }),
    );

    act(() => result.current.setQuery('theme'));

    const labels = result.current.results.map((r) => r.label);
    expect(labels).toContain('Toggle Theme');
  });

  it('selectCurrent calls toggleTheme for the theme action', () => {
    const { result } = renderHook(() =>
      useCommandPalette({ projectId: 'proj-1', isOpen: true }),
    );

    act(() => result.current.setQuery('Toggle Theme'));

    const themeIdx = result.current.results.findIndex((r) => r.label === 'Toggle Theme');
    expect(themeIdx).toBeGreaterThanOrEqual(0);

    // Navigate to the theme action
    for (let i = 0; i < themeIdx; i++) {
      act(() => result.current.moveDown());
    }

    act(() => result.current.selectCurrent());
    expect(mockToggleTheme).toHaveBeenCalled();
  });
});
