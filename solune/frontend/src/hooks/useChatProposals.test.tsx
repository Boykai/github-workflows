import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

vi.mock('@/services/api', () => ({
  chatApi: {
    confirmProposal: vi.fn(),
    cancelProposal: vi.fn(),
  },
  tasksApi: {
    updateStatus: vi.fn(),
  },
}));

vi.mock('@/constants', () => ({
  PROPOSAL_EXPIRY_MS: 600_000,
}));

import * as api from '@/services/api';
import { useChatProposals } from './useChatProposals';
import type { ChatMessage } from '@/types';

const mockChatApi = api.chatApi as unknown as {
  confirmProposal: ReturnType<typeof vi.fn>;
  cancelProposal: ReturnType<typeof vi.fn>;
};
const mockTasksApi = api.tasksApi as unknown as {
  updateStatus: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('useChatProposals', () => {
  beforeEach(() => vi.clearAllMocks());

  it('starts with empty proposals', () => {
    const { result } = renderHook(() => useChatProposals(), {
      wrapper: createWrapper(),
    });

    expect(result.current.pendingProposals.size).toBe(0);
    expect(result.current.pendingStatusChanges.size).toBe(0);
    expect(result.current.pendingRecommendations.size).toBe(0);
  });

  it('handleActionResponse adds a task_create proposal', () => {
    const { result } = renderHook(() => useChatProposals(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.handleActionResponse({
        session_id: 'sess-1',
        action_type: 'task_create',
        action_data: {
          proposal_id: 'prop-1',
          status: 'pending',
          proposed_title: 'New Task',
          proposed_description: 'A description',
        },
      } as ChatMessage);
    });

    expect(result.current.pendingProposals.size).toBe(1);
    expect(result.current.pendingProposals.get('prop-1')?.proposed_title).toBe('New Task');
  });

  it('handleActionResponse adds a status_update proposal', () => {
    const { result } = renderHook(() => useChatProposals(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.handleActionResponse({
        session_id: 'sess-1',
        action_type: 'status_update',
        action_data: {
          proposal_id: 'sp-1',
          task_id: 'task-1',
          status: 'pending',
          task_title: 'Task',
          current_status: 'Todo',
          target_status: 'Done',
          status_option_id: 'opt-1',
          status_field_id: 'field-1',
        },
      } as ChatMessage);
    });

    expect(result.current.pendingStatusChanges.size).toBe(1);
    expect(result.current.pendingStatusChanges.get('sp-1')?.target_status).toBe('Done');
  });

  it('handleActionResponse adds an issue_create recommendation', () => {
    const { result } = renderHook(() => useChatProposals(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.handleActionResponse({
        session_id: 'sess-1',
        action_type: 'issue_create',
        action_data: {
          recommendation_id: 'rec-1',
          status: 'pending',
          title: 'New Issue',
        },
      } as ChatMessage);
    });

    expect(result.current.pendingRecommendations.size).toBe(1);
    expect(result.current.pendingRecommendations.get('rec-1')?.status).toBe('pending');
  });

  it('confirmProposal calls API and removes proposal', async () => {
    mockChatApi.confirmProposal.mockResolvedValue({ success: true });

    const { result } = renderHook(() => useChatProposals(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.handleActionResponse({
        session_id: 'sess-1',
        action_type: 'task_create',
        action_data: { proposal_id: 'prop-1', status: 'pending', proposed_title: 'Task' },
      } as ChatMessage);
    });
    expect(result.current.pendingProposals.size).toBe(1);

    await act(async () => {
      await result.current.confirmProposal('prop-1');
    });

    expect(mockChatApi.confirmProposal).toHaveBeenCalledWith('prop-1', undefined);
    expect(result.current.pendingProposals.size).toBe(0);
  });

  it('rejectProposal calls cancel API and removes proposal', async () => {
    mockChatApi.cancelProposal.mockResolvedValue({ success: true });

    const { result } = renderHook(() => useChatProposals(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.handleActionResponse({
        session_id: 'sess-1',
        action_type: 'task_create',
        action_data: { proposal_id: 'prop-1', status: 'pending', proposed_title: 'Task' },
      } as ChatMessage);
    });

    await act(async () => {
      await result.current.rejectProposal('prop-1');
    });

    expect(mockChatApi.cancelProposal).toHaveBeenCalled();
    expect(mockChatApi.cancelProposal.mock.calls[0][0]).toBe('prop-1');
    expect(result.current.pendingProposals.size).toBe(0);
  });

  it('confirmStatusChange calls updateStatus API', async () => {
    mockTasksApi.updateStatus.mockResolvedValue({ success: true });

    const { result } = renderHook(() => useChatProposals(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.handleActionResponse({
        session_id: 'sess-1',
        action_type: 'status_update',
        action_data: {
          proposal_id: 'sp-1',
          task_id: 'task-1',
          status: 'pending',
          target_status: 'Done',
        },
      } as ChatMessage);
    });

    await act(async () => {
      await result.current.confirmStatusChange('sp-1');
    });

    expect(mockTasksApi.updateStatus).toHaveBeenCalledWith('task-1', 'Done');
    expect(result.current.pendingStatusChanges.size).toBe(0);
  });

  it('clearProposals clears all pending state', () => {
    const { result } = renderHook(() => useChatProposals(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.handleActionResponse({
        session_id: 'sess-1',
        action_type: 'task_create',
        action_data: { proposal_id: 'prop-1', status: 'pending', proposed_title: 'Task' },
      } as ChatMessage);
    });
    expect(result.current.pendingProposals.size).toBe(1);

    act(() => {
      result.current.clearProposals();
    });

    expect(result.current.pendingProposals.size).toBe(0);
    expect(result.current.pendingStatusChanges.size).toBe(0);
    expect(result.current.pendingRecommendations.size).toBe(0);
  });

  it('removePendingRecommendation removes a specific recommendation', () => {
    const { result } = renderHook(() => useChatProposals(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.handleActionResponse({
        session_id: 'sess-1',
        action_type: 'issue_create',
        action_data: { recommendation_id: 'rec-1', status: 'pending' },
      } as ChatMessage);
      result.current.handleActionResponse({
        session_id: 'sess-1',
        action_type: 'issue_create',
        action_data: { recommendation_id: 'rec-2', status: 'pending' },
      } as ChatMessage);
    });
    expect(result.current.pendingRecommendations.size).toBe(2);

    act(() => {
      result.current.removePendingRecommendation('rec-1');
    });

    expect(result.current.pendingRecommendations.size).toBe(1);
    expect(result.current.pendingRecommendations.has('rec-2')).toBe(true);
  });
});
