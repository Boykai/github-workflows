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
    clearMessages: vi.fn(),
    confirmProposal: vi.fn(),
    cancelProposal: vi.fn(),
  },
  tasksApi: {
    updateStatus: vi.fn(),
  },
}));

// Mock constants
vi.mock('@/constants', () => ({
  STALE_TIME_MEDIUM: 0,
  PROPOSAL_EXPIRY_MS: 300000,
}));

const mockChatApi = api.chatApi as unknown as {
  getMessages: ReturnType<typeof vi.fn>;
  sendMessage: ReturnType<typeof vi.fn>;
  clearMessages: ReturnType<typeof vi.fn>;
  confirmProposal: ReturnType<typeof vi.fn>;
  cancelProposal: ReturnType<typeof vi.fn>;
};

// Create wrapper with QueryClientProvider
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
        { message_id: 'msg_1', session_id: 's1', sender_type: 'user', content: 'Hello', timestamp: '2024-01-01T00:00:00Z' },
        { message_id: 'msg_2', session_id: 's1', sender_type: 'assistant', content: 'Hi there!', timestamp: '2024-01-01T00:00:01Z' },
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
      }),
    ).rejects.toThrow('Send failed');

    expect(mockChatApi.sendMessage).toHaveBeenCalled();
  });
});
