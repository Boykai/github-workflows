/**
 * Unit tests for useChat hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useChat } from './useChat';
import * as api from '@/services/api';
import type { ReactNode } from 'react';

// Mock the API module
vi.mock('@/services/api', () => ({
  chatApi: {
    getMessages: vi.fn(),
    sendMessage: vi.fn(),
    confirmProposal: vi.fn(),
    cancelProposal: vi.fn(),
    clearMessages: vi.fn(),
  },
  tasksApi: {
    updateStatus: vi.fn(),
  },
}));

const mockChatApi = api.chatApi as unknown as {
  getMessages: ReturnType<typeof vi.fn>;
  sendMessage: ReturnType<typeof vi.fn>;
  confirmProposal: ReturnType<typeof vi.fn>;
  cancelProposal: ReturnType<typeof vi.fn>;
  clearMessages: ReturnType<typeof vi.fn>;
};

const mockTasksApi = api.tasksApi as unknown as {
  updateStatus: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
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

  it('should return messages from query', async () => {
    const messages = [
      { message_id: '1', content: 'Hello', sender_type: 'user', session_id: 's1', timestamp: new Date().toISOString() },
      { message_id: '2', content: 'Hi there', sender_type: 'assistant', session_id: 's1', timestamp: new Date().toISOString() },
    ];
    mockChatApi.getMessages.mockResolvedValue({ messages });

    const { result } = renderHook(() => useChat(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.messages).toEqual(messages);
  });

  it('should return empty messages when query returns no data', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });

    const { result } = renderHook(() => useChat(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.messages).toEqual([]);
  });

  it('sendMessage triggers mutation', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: '3',
      content: 'Response',
      sender_type: 'assistant',
      session_id: 's1',
      timestamp: new Date().toISOString(),
    });

    const { result } = renderHook(() => useChat(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('Test message');
    });

    expect(mockChatApi.sendMessage).toHaveBeenCalledWith(
      { content: 'Test message' },
      expect.anything()
    );
  });

  it('handles task_create proposals', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: '4',
      content: 'I can create a task for you',
      sender_type: 'assistant',
      session_id: 's1',
      action_type: 'task_create',
      action_data: {
        proposal_id: 'prop-1',
        proposed_title: 'New Task',
        proposed_description: 'Task description',
        status: 'pending',
      },
      timestamp: new Date().toISOString(),
    });

    const { result } = renderHook(() => useChat(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('Create a task');
    });

    expect(result.current.pendingProposals.size).toBe(1);
    expect(result.current.pendingProposals.has('prop-1')).toBe(true);
    const proposal = result.current.pendingProposals.get('prop-1');
    expect(proposal?.proposed_title).toBe('New Task');
  });

  it('handles status_update proposals', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: '5',
      content: 'Update status?',
      sender_type: 'assistant',
      session_id: 's1',
      action_type: 'status_update',
      action_data: {
        proposal_id: 'sp-1',
        task_id: 'T1',
        task_title: 'My Task',
        current_status: 'Todo',
        target_status: 'In Progress',
        status_option_id: 'opt-1',
        status_field_id: 'field-1',
        status: 'pending',
      },
      timestamp: new Date().toISOString(),
    });

    const { result } = renderHook(() => useChat(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('Move task to in progress');
    });

    expect(result.current.pendingStatusChanges.size).toBe(1);
    expect(result.current.pendingStatusChanges.has('sp-1')).toBe(true);
  });

  it('handles issue_create recommendations', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: '6',
      content: 'Recommend an issue',
      sender_type: 'assistant',
      session_id: 's1',
      action_type: 'issue_create',
      action_data: {
        recommendation_id: 'rec-1',
        proposed_title: 'New Feature',
        user_story: 'As a user...',
        ui_ux_description: 'A button...',
        functional_requirements: ['req1'],
        status: 'pending',
      },
      timestamp: new Date().toISOString(),
    });

    const { result } = renderHook(() => useChat(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('Suggest an issue');
    });

    expect(result.current.pendingRecommendations.size).toBe(1);
    expect(result.current.pendingRecommendations.has('rec-1')).toBe(true);
  });

  it('confirmProposal removes from pending', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: '7',
      content: 'Create task?',
      sender_type: 'assistant',
      session_id: 's1',
      action_type: 'task_create',
      action_data: {
        proposal_id: 'prop-2',
        proposed_title: 'Task',
        proposed_description: 'Desc',
        status: 'pending',
      },
      timestamp: new Date().toISOString(),
    });
    mockChatApi.confirmProposal.mockResolvedValue({
      proposal_id: 'prop-2',
      status: 'confirmed',
    });

    const { result } = renderHook(() => useChat(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('Create task');
    });

    expect(result.current.pendingProposals.size).toBe(1);

    await act(async () => {
      await result.current.confirmProposal('prop-2');
    });

    expect(result.current.pendingProposals.size).toBe(0);
  });

  it('confirmStatusChange works', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: '8',
      content: 'Update status?',
      sender_type: 'assistant',
      session_id: 's1',
      action_type: 'status_update',
      action_data: {
        proposal_id: 'sp-2',
        task_id: 'T1',
        task_title: 'My Task',
        current_status: 'Todo',
        target_status: 'Done',
        status_option_id: 'opt-1',
        status_field_id: 'field-1',
        status: 'pending',
      },
      timestamp: new Date().toISOString(),
    });
    mockTasksApi.updateStatus.mockResolvedValue({
      task_id: 'T1',
      status: 'Done',
    });

    const { result } = renderHook(() => useChat(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('Mark done');
    });

    expect(result.current.pendingStatusChanges.size).toBe(1);

    await act(async () => {
      await result.current.confirmStatusChange('sp-2');
    });

    expect(result.current.pendingStatusChanges.size).toBe(0);
    expect(mockTasksApi.updateStatus).toHaveBeenCalledWith('T1', 'Done');
  });

  it('rejectProposal works', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: '9',
      content: 'Create task?',
      sender_type: 'assistant',
      session_id: 's1',
      action_type: 'task_create',
      action_data: {
        proposal_id: 'prop-3',
        proposed_title: 'Task',
        proposed_description: 'Desc',
        status: 'pending',
      },
      timestamp: new Date().toISOString(),
    });
    mockChatApi.cancelProposal.mockResolvedValue(undefined);

    const { result } = renderHook(() => useChat(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('Create task');
    });

    expect(result.current.pendingProposals.size).toBe(1);

    await act(async () => {
      await result.current.rejectProposal('prop-3');
    });

    expect(result.current.pendingProposals.size).toBe(0);
    expect(mockChatApi.cancelProposal).toHaveBeenCalledWith('prop-3', expect.anything());
  });

  it('removePendingRecommendation works', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.sendMessage.mockResolvedValue({
      message_id: '10',
      content: 'Issue',
      sender_type: 'assistant',
      session_id: 's1',
      action_type: 'issue_create',
      action_data: {
        recommendation_id: 'rec-2',
        proposed_title: 'Feature',
        user_story: 'Story',
        ui_ux_description: 'UI',
        functional_requirements: [],
        status: 'pending',
      },
      timestamp: new Date().toISOString(),
    });

    const { result } = renderHook(() => useChat(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('Recommend');
    });

    expect(result.current.pendingRecommendations.size).toBe(1);

    act(() => {
      result.current.removePendingRecommendation('rec-2');
    });

    expect(result.current.pendingRecommendations.size).toBe(0);
  });

  it('clearChat works', async () => {
    mockChatApi.getMessages.mockResolvedValue({ messages: [] });
    mockChatApi.clearMessages.mockResolvedValue({ message: 'Cleared' });

    const { result } = renderHook(() => useChat(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.clearChat();
    });

    expect(mockChatApi.clearMessages).toHaveBeenCalled();
  });
});
