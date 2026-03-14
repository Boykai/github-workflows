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
    expect(mockChatApi.sendMessage.mock.calls[0][0]).toEqual({
      content: 'Test message',
      ai_enhance: true,
      file_urls: [],
    });
  });

  it('should remove a pending proposal after confirmProposal succeeds', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: 'msg_task',
      session_id: 's1',
      sender_type: 'assistant',
      content: 'Task proposal ready',
      timestamp: '2024-01-01T00:00:02Z',
      action_type: 'task_create',
      action_data: {
        proposal_id: 'proposal-1',
        proposed_title: 'Add task confirmation feedback',
        proposed_description: 'Show an error in chat when task creation fails.',
        status: 'pending',
      },
    });
    mockChatApi.confirmProposal.mockResolvedValue({
      proposal_id: 'proposal-1',
      session_id: 's1',
      original_input: 'Create a task',
      proposed_title: 'Add task confirmation feedback',
      proposed_description: 'Show an error in chat when task creation fails.',
      status: 'confirmed',
      created_at: '2024-01-01T00:00:00Z',
      expires_at: '2024-01-01T00:05:00Z',
    });

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('Create a task');
    });

    await waitFor(() => {
      expect(result.current.pendingProposals.has('proposal-1')).toBe(true);
    });

    await act(async () => {
      await result.current.confirmProposal('proposal-1');
    });

    await waitFor(() => {
      expect(result.current.pendingProposals.has('proposal-1')).toBe(false);
    });
  });

  it('should append a system error message when confirmProposal fails', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: 'msg_task',
      session_id: 's1',
      sender_type: 'assistant',
      content: 'Task proposal ready',
      timestamp: '2024-01-01T00:00:02Z',
      action_type: 'task_create',
      action_data: {
        proposal_id: 'proposal-2',
        proposed_title: 'Add task confirmation feedback',
        proposed_description: 'Show an error in chat when task creation fails.',
        status: 'pending',
      },
    });
    mockChatApi.confirmProposal.mockRejectedValue(new Error('Failed to create issue'));

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('Create a task');
    });

    await waitFor(() => {
      expect(result.current.pendingProposals.has('proposal-2')).toBe(true);
    });

    await act(async () => {
      await result.current.confirmProposal('proposal-2');
    });

    expect(mockChatApi.confirmProposal).toHaveBeenCalledWith('proposal-2', undefined);
    expect(result.current.pendingProposals.has('proposal-2')).toBe(true);
    expect(
      result.current.messages.some(
        (message) =>
          message.sender_type === 'system' &&
          message.content === 'Task creation failed: Failed to create issue'
      )
    ).toBe(true);
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

    // With optimistic rendering, errors are caught internally and the
    // optimistic message is marked as 'failed' instead of the promise rejecting.
    await act(async () => {
      await result.current.sendMessage('Bad message');
    });

    expect(mockChatApi.sendMessage).toHaveBeenCalled();
    // The optimistic message should remain with 'failed' status
    const failedMsg = result.current.messages.find(
      (m) => m.content === 'Bad message' && m.status === 'failed'
    );
    expect(failedMsg).toBeDefined();
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
      await result.current.sendMessage('/help');
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
      await result.current.sendMessage('/help', { isCommand: true });
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

    // Send a bare '/' which doesn't map to any command but IS a command input —
    // the registry returns a failure result for unknown commands.
    await act(async () => {
      await result.current.sendMessage('/');
    });

    expect(mockChatApi.sendMessage).not.toHaveBeenCalled();
    const systemMsg = result.current.messages.find((m) => m.sender_type === 'system');
    expect(systemMsg).toBeDefined();
    // The message should indicate help is available
    expect(systemMsg!.content).toContain('/help');
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
    expect(mockChatApi.sendMessage.mock.calls[0][0]).toEqual({
      content: 'Hello world',
      ai_enhance: true,
      file_urls: [],
    });
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
      await result.current.sendMessage('/agent Build a code reviewer');
    });

    // Passthrough command SHOULD reach the backend
    expect(mockChatApi.sendMessage).toHaveBeenCalled();
    expect(mockChatApi.sendMessage.mock.calls[0][0]).toEqual({
      content: '/agent Build a code reviewer',
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
      await result.current.sendMessage('/agent Create a tester', { isCommand: true });
    });

    expect(mockChatApi.sendMessage).toHaveBeenCalled();
    expect(mockChatApi.sendMessage.mock.calls[0][0]).toEqual({ content: '/agent Create a tester' });
    // Should NOT produce local system messages
    const systemMsgs = result.current.messages.filter((m) => m.sender_type === 'system');
    expect(systemMsgs).toHaveLength(0);
  });

  // ── Regression tests: command state isolation (T021–T023) ────────────────

  it('should not auto-repeat #help on subsequent normal messages', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: 'msg_after_help',
      session_id: 's1',
      sender_type: 'assistant',
      content: 'Normal response',
      timestamp: '2024-01-01T00:00:05Z',
    });

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Step 1: Send #help command
    await act(async () => {
      await result.current.sendMessage('/help');
    });

    expect(mockChatApi.sendMessage).not.toHaveBeenCalled();

    // Step 2: Send a normal follow-up message
    await act(async () => {
      await result.current.sendMessage('Hello after help');
    });

    // The normal message should reach the backend with NO command references
    expect(mockChatApi.sendMessage).toHaveBeenCalledTimes(1);
    expect(mockChatApi.sendMessage.mock.calls[0][0]).toEqual({
      content: 'Hello after help',
      ai_enhance: true,
      file_urls: [],
    });
  });

  it('should dispatch multiple different commands independently without cross-contamination', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Send /help
    await act(async () => {
      await result.current.sendMessage('/help');
    });

    const helpMsgs = result.current.messages.filter((m) => m.sender_type === 'system');
    expect(helpMsgs).toHaveLength(1);
    expect(helpMsgs[0].content).toContain('Available Commands');

    // Send /status (unknown command — should produce error/help text)
    await act(async () => {
      await result.current.sendMessage('/status');
    });

    const allSystemMsgs = result.current.messages.filter((m) => m.sender_type === 'system');
    expect(allSystemMsgs).toHaveLength(2);

    // No backend calls should have been made for local commands
    expect(mockChatApi.sendMessage).not.toHaveBeenCalled();
  });

  it('should fully clear localMessages command entries after command dispatch', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('/help');
    });

    // localMessages should only contain the user message + system response
    const msgs = result.current.messages;
    const userMsgs = msgs.filter((m) => m.sender_type === 'user');
    const systemMsgs = msgs.filter((m) => m.sender_type === 'system');
    expect(userMsgs).toHaveLength(1);
    expect(userMsgs[0].content).toBe('/help');
    expect(systemMsgs).toHaveLength(1);
    // No pending/failed messages should exist
    const pendingOrFailed = msgs.filter((m) => m.status === 'pending' || m.status === 'failed');
    expect(pendingOrFailed).toHaveLength(0);
  });

  // ── Optimistic message rendering tests (T024) ───────────────────────────

  it('should show optimistic message with pending status before mutation resolves', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });

    // Create a deferred promise so we control when the mutation resolves
    let resolveSend!: (value: unknown) => void;
    mockChatApi.sendMessage.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveSend = resolve;
        })
    );

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Start sending — don't await so we can inspect intermediate state
    let sendPromise: Promise<void>;
    act(() => {
      sendPromise = result.current.sendMessage('Optimistic test');
    });

    // The optimistic message should appear immediately with 'pending' status
    await waitFor(() => {
      const pending = result.current.messages.find(
        (m) => m.content === 'Optimistic test' && m.status === 'pending'
      );
      expect(pending).toBeDefined();
    });

    // Resolve the mutation
    await act(async () => {
      resolveSend({
        message_id: 'msg_server',
        session_id: 's1',
        sender_type: 'assistant',
        content: 'Server response',
        timestamp: '2024-01-01T00:00:06Z',
      });
      await sendPromise!;
    });

    // After resolution, the optimistic message should be removed
    const stillPending = result.current.messages.find(
      (m) => m.content === 'Optimistic test' && m.status === 'pending'
    );
    expect(stillPending).toBeUndefined();
  });

  // ── Failed message retry test (T025) ────────────────────────────────────

  it('should mark message as failed on error and allow retry', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Send a message that will fail
    await act(async () => {
      await result.current.sendMessage('Will fail');
    });

    // Should have a failed message
    const failedMsg = result.current.messages.find(
      (m) => m.content === 'Will fail' && m.status === 'failed'
    );
    expect(failedMsg).toBeDefined();

    // Now retry — mock a successful response this time
    mockChatApi.sendMessage.mockResolvedValueOnce({
      message_id: 'msg_retried',
      session_id: 's1',
      sender_type: 'assistant',
      content: 'Retry success',
      timestamp: '2024-01-01T00:00:07Z',
    });

    await act(async () => {
      await result.current.retryMessage(failedMsg!.message_id);
    });

    // The failed message should be removed after successful retry
    const stillFailed = result.current.messages.find(
      (m) => m.content === 'Will fail' && m.status === 'failed'
    );
    expect(stillFailed).toBeUndefined();
  });
});
