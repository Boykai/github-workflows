/**
 * Unit tests for useChat hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useChat } from './useChat';
import * as api from '@/services/api';
import type { ReactNode } from 'react';
import { ThemeProvider } from '@/components/ThemeProvider';

// Mock the API module
vi.mock('@/services/api', () => ({
  chatApi: {
    getMessages: vi.fn(),
    sendMessage: vi.fn(),
    clearMessages: vi.fn(),
    confirmProposal: vi.fn(),
    cancelProposal: vi.fn(),
  },
  tasksApi: {
    updateStatus: vi.fn(),
  },
  settingsApi: {
    getUserSettings: vi.fn().mockResolvedValue({
      ai: { provider: 'copilot', model: 'gpt-4o', temperature: 0.7 },
      display: { theme: 'dark', default_view: 'board', sidebar_collapsed: false },
      workflow: { auto_assign: true, default_status: 'Todo', polling_interval: 15 },
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

// Mock constants
vi.mock('@/constants', () => ({
  STALE_TIME_MEDIUM: 0,
  STALE_TIME_LONG: 0,
  PROPOSAL_EXPIRY_MS: 300000,
}));

const mockChatApi = api.chatApi as unknown as {
  getMessages: ReturnType<typeof vi.fn>;
  sendMessage: ReturnType<typeof vi.fn>;
  clearMessages: ReturnType<typeof vi.fn>;
  confirmProposal: ReturnType<typeof vi.fn>;
  cancelProposal: ReturnType<typeof vi.fn>;
};

// Create wrapper with QueryClientProvider and ThemeProvider
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <ThemeProvider defaultTheme="dark" storageKey="test-theme">
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      </ThemeProvider>
    );
  };
}

describe('useChat', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should return empty messages initially while loading', () => {
    mockChatApi.getMessages.mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoading).toBe(true);
  });

  it('should return messages after loading', async () => {
    const mockMessages = {
      messages: [
        {
          message_id: 'msg_1',
          session_id: 's1',
          sender_type: 'user',
          content: 'Hello',
          timestamp: '2024-01-01T00:00:00Z',
        },
        {
          message_id: 'msg_2',
          session_id: 's1',
          sender_type: 'assistant',
          content: 'Hi there!',
          timestamp: '2024-01-01T00:00:01Z',
        },
      ],
    };

    mockChatApi.getMessages.mockResolvedValue(mockMessages);

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].content).toBe('Hello');
    expect(result.current.messages[1].sender_type).toBe('assistant');
  });

  it('sendMessage should trigger mutation', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: 'msg_3',
      session_id: 's1',
      sender_type: 'assistant',
      content: 'Response',
      timestamp: '2024-01-01T00:00:02Z',
    });

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('Test message');
    });

    expect(mockChatApi.sendMessage).toHaveBeenCalled();
    expect(mockChatApi.sendMessage.mock.calls[0][0]).toEqual({ content: 'Test message' });
  });

  it('should handle sendMessage error gracefully', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockRejectedValue(new Error('Send failed'));

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await expect(
      act(async () => {
        await result.current.sendMessage('Bad message');
      })
    ).rejects.toThrow('Send failed');

    expect(mockChatApi.sendMessage).toHaveBeenCalled();
  });

  // ── Command interception tests (AI review recommendation) ────────────────
  // Verifies that # commands are intercepted client-side and never sent
  // to the backend API, producing local system messages instead.

  it('should intercept #help command and not call chatApi.sendMessage', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('#help');
    });

    // The command should NOT reach the backend
    expect(mockChatApi.sendMessage).not.toHaveBeenCalled();
    // Should produce local user + system messages
    expect(result.current.messages.length).toBeGreaterThanOrEqual(2);
    const systemMsg = result.current.messages.find((m) => m.sender_type === 'system');
    expect(systemMsg).toBeDefined();
    expect(systemMsg!.content).toContain('Available Commands');
  });

  it('should intercept #help when passed via isCommand option', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('#help', { isCommand: true });
    });

    expect(mockChatApi.sendMessage).not.toHaveBeenCalled();
    const systemMsg = result.current.messages.find((m) => m.sender_type === 'system');
    expect(systemMsg).toBeDefined();
  });

  it('should append a system error message when command execution throws', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Send a bare '#' which doesn't map to any command but IS a command input —
    // the registry returns a failure result for unknown commands.
    await act(async () => {
      await result.current.sendMessage('#');
    });

    expect(mockChatApi.sendMessage).not.toHaveBeenCalled();
    const systemMsg = result.current.messages.find((m) => m.sender_type === 'system');
    expect(systemMsg).toBeDefined();
    // The message should indicate help is available
    expect(systemMsg!.content).toContain('#help');
  });

  it('should NOT intercept regular chat messages as commands', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: 'msg_resp',
      session_id: 's1',
      sender_type: 'assistant',
      content: 'Hello!',
      timestamp: '2024-01-01T00:00:02Z',
    });

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('Hello world');
    });

    // Regular message should reach the backend (React Query's mutateAsync
    // passes additional internal args, so verify just the first argument).
    expect(mockChatApi.sendMessage).toHaveBeenCalled();
    expect(mockChatApi.sendMessage.mock.calls[0][0]).toEqual({ content: 'Hello world' });
  });

  // ── Passthrough command tests ────────────────────────────────────────────
  // Verifies that passthrough commands (e.g. #agent) are forwarded to the
  // backend API instead of being handled locally.

  it('should forward #agent command to backend (passthrough)', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: 'msg_agent',
      session_id: 's1',
      sender_type: 'assistant',
      content: 'Agent creation started',
      timestamp: '2024-01-01T00:00:03Z',
    });

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('#agent Build a code reviewer');
    });

    // Passthrough command SHOULD reach the backend
    expect(mockChatApi.sendMessage).toHaveBeenCalled();
    expect(mockChatApi.sendMessage.mock.calls[0][0]).toEqual({
      content: '#agent Build a code reviewer',
    });
  });

  it('should forward #agent via isCommand option to backend (passthrough)', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: 'msg_agent2',
      session_id: 's1',
      sender_type: 'assistant',
      content: 'Agent preview ready',
      timestamp: '2024-01-01T00:00:04Z',
    });

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('#agent Create a tester', { isCommand: true });
    });

    expect(mockChatApi.sendMessage).toHaveBeenCalled();
    expect(mockChatApi.sendMessage.mock.calls[0][0]).toEqual({ content: '#agent Create a tester' });
    // Should NOT produce local system messages
    const systemMsgs = result.current.messages.filter((m) => m.sender_type === 'system');
    expect(systemMsgs).toHaveLength(0);
  });
});
