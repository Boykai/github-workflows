/**
 * Tests for useCommands hook.
 */
import { describe, it, expect, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@/components/ThemeProvider';
import { useCommands } from './useCommands';
import type { ReactNode } from 'react';

// Mock settings API
vi.mock('@/services/api', () => ({
  settingsApi: {
    getUserSettings: vi.fn().mockResolvedValue({
      ai: { provider: 'copilot', model: 'gpt-4o', temperature: 0.7 },
      display: { theme: 'dark', default_view: 'board', sidebar_collapsed: false },
      workflow: { default_repository: null, default_assignee: null, copilot_polling_interval: 15 },
      notifications: {
        task_status_change: true,
        agent_completion: true,
        new_recommendation: true,
        chat_mention: true,
      },
    }),
    updateUserSettings: vi.fn().mockResolvedValue({}),
  },
}));

vi.mock('@/constants', () => ({
  STALE_TIME_LONG: 0,
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <ThemeProvider defaultTheme="dark" storageKey="test-theme">
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      </ThemeProvider>
    );
  };
}

describe('useCommands', () => {
  describe('isCommand', () => {
    it('identifies / commands', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      expect(result.current.isCommand('/help')).toBe(true);
      expect(result.current.isCommand('/theme dark')).toBe(true);
    });

    it('identifies help keyword as command', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      expect(result.current.isCommand('help')).toBe(true);
      expect(result.current.isCommand('HELP')).toBe(true);
    });

    it('identifies regular messages as non-commands', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      expect(result.current.isCommand('hello world')).toBe(false);
      expect(result.current.isCommand('create a task')).toBe(false);
    });

    it('does not treat Markdown characters as commands', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      expect(result.current.isCommand('# Heading')).toBe(false);
      expect(result.current.isCommand('**bold**')).toBe(false);
      expect(result.current.isCommand('- list item')).toBe(false);
      expect(result.current.isCommand('> blockquote')).toBe(false);
    });
  });

  describe('parseInput', () => {
    it('returns correct ParsedCommand for /help', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      const parsed = result.current.parseInput('/help');
      expect(parsed.isCommand).toBe(true);
      expect(parsed.name).toBe('help');
      expect(parsed.args).toBe('');
    });

    it('returns correct ParsedCommand for /theme dark', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      const parsed = result.current.parseInput('/theme dark');
      expect(parsed.isCommand).toBe(true);
      expect(parsed.name).toBe('theme');
      expect(parsed.args).toBe('dark');
    });
  });

  describe('executeCommand', () => {
    it('for /help returns formatted help output', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      const cmdResult = result.current.executeCommand('/help');
      // executeCommand may return a Promise, so handle both cases
      if (cmdResult instanceof Promise) {
        return cmdResult.then((r) => {
          expect(r.success).toBe(true);
          expect(r.message).toContain('Available Commands');
        });
      }
      expect(cmdResult.success).toBe(true);
      expect(cmdResult.message).toContain('Available Commands');
    });

    it('for unknown command returns error', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      const cmdResult = result.current.executeCommand('/foobar');
      if (cmdResult instanceof Promise) {
        return cmdResult.then((r) => {
          expect(r.success).toBe(false);
          expect(r.message).toContain('Unknown command');
        });
      }
      expect(cmdResult.success).toBe(false);
      expect(cmdResult.message).toContain('Unknown command');
    });

    it('for passthrough command /agent returns passthrough flag', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      const cmdResult = result.current.executeCommand('/agent Build a reviewer');
      if (cmdResult instanceof Promise) {
        return cmdResult.then((r) => {
          expect(r.success).toBe(true);
          expect(r.passthrough).toBe(true);
        });
      }
      expect(cmdResult.success).toBe(true);
      expect(cmdResult.passthrough).toBe(true);
    });

    it('for bare / returns helpful message', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      const cmdResult = result.current.executeCommand('/');
      if (cmdResult instanceof Promise) {
        return cmdResult.then((r) => {
          expect(r.success).toBe(false);
          expect(r.message).toContain('/help');
        });
      }
      expect(cmdResult.success).toBe(false);
      expect(cmdResult.message).toContain('/help');
    });
  });

  describe('getFilteredCommands', () => {
    it('returns all commands for empty prefix', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      const filtered = result.current.getFilteredCommands('');
      expect(filtered.length).toBeGreaterThanOrEqual(6);
    });

    it('filters by prefix', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      const filtered = result.current.getFilteredCommands('th');
      expect(filtered.length).toBe(1);
      expect(filtered[0].name).toBe('theme');
    });

    it('case-insensitive filtering', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      expect(result.current.getFilteredCommands('TH').length).toBe(1);
    });

    it('returns empty array for no matches', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      expect(result.current.getFilteredCommands('xyz').length).toBe(0);
    });
  });

  describe('getAllCommands', () => {
    it('returns all registered commands', () => {
      const { result } = renderHook(() => useCommands(), { wrapper: createWrapper() });
      const commands = result.current.getAllCommands();
      expect(commands.length).toBeGreaterThanOrEqual(6);
      const names = commands.map((c) => c.name);
      expect(names).toContain('help');
      expect(names).toContain('theme');
      expect(names).toContain('agent');
    });
  });
});
