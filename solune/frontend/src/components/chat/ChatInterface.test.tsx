import { describe, expect, it, vi } from 'vitest';
import { fireEvent } from '@testing-library/react';
import { render, screen } from '@/test/test-utils';
import { ChatInterface } from './ChatInterface';
import type { ChatMessage } from '@/types';

// ── Mock sub-components ──

vi.mock('./MessageBubble', () => ({
  MessageBubble: ({ message }: { message: ChatMessage }) => (
    <div data-testid="message-bubble">{message.content}</div>
  ),
}));

vi.mock('./SystemMessage', () => ({
  SystemMessage: ({ message }: { message: ChatMessage }) => (
    <div data-testid="system-message">{message.content}</div>
  ),
}));

vi.mock('./CommandAutocomplete', () => ({
  CommandAutocomplete: () => <div data-testid="command-autocomplete" />,
}));

vi.mock('./MentionAutocomplete', () => ({
  MentionAutocomplete: () => <div data-testid="mention-autocomplete" />,
}));

vi.mock('./MentionInput', () => ({
  MentionInput: vi.fn().mockImplementation(
    ({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) => (
      <input
        data-testid="mention-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    )
  ),
}));

vi.mock('./PipelineIndicator', () => ({
  PipelineIndicator: () => <div data-testid="pipeline-indicator" />,
}));

vi.mock('./TaskPreview', () => ({
  TaskPreview: () => <div data-testid="task-preview" />,
}));

vi.mock('./StatusChangePreview', () => ({
  StatusChangePreview: () => <div data-testid="status-change-preview" />,
}));

vi.mock('./IssueRecommendationPreview', () => ({
  IssueRecommendationPreview: () => <div data-testid="issue-recommendation-preview" />,
}));

vi.mock('./ChatToolbar', () => ({
  ChatToolbar: () => <div data-testid="chat-toolbar" />,
}));

vi.mock('./FilePreviewChips', () => ({
  FilePreviewChips: () => <div data-testid="file-preview-chips" />,
}));

vi.mock('./PipelineWarningBanner', () => ({
  PipelineWarningBanner: () => <div data-testid="pipeline-warning-banner" />,
}));

vi.mock('@/components/ui/tooltip', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/components/ui/tooltip')>();
  return {
    ...actual,
    Tooltip: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  };
});

// ── Mock hooks ──

vi.mock('@/hooks/useCommands', () => ({
  useCommands: () => ({
    isCommand: vi.fn(() => false),
    getFilteredCommands: vi.fn(() => []),
  }),
}));

vi.mock('@/hooks/useChatHistory', () => ({
  useChatHistory: () => ({
    addToHistory: vi.fn(),
    navigateUp: vi.fn(() => null),
    navigateDown: vi.fn(() => null),
    isNavigating: false,
    resetNavigation: vi.fn(),
    history: [],
    selectFromHistory: vi.fn(),
  }),
}));

vi.mock('@/hooks/useCyclingPlaceholder', () => ({
  useCyclingPlaceholder: vi.fn(() => 'Ask me anything…'),
}));

vi.mock('@/hooks/useFileUpload', () => ({
  useFileUpload: () => ({
    files: [],
    errors: [],
    addFiles: vi.fn(),
    removeFile: vi.fn(),
    uploadAll: vi.fn(async () => []),
    clearAll: vi.fn(),
  }),
}));

vi.mock('@/hooks/useVoiceInput', () => ({
  useVoiceInput: () => ({
    isRecording: false,
    isSupported: false,
    startRecording: vi.fn(),
    stopRecording: vi.fn(),
  }),
}));

vi.mock('@/hooks/useMentionAutocomplete', () => ({
  useMentionAutocomplete: () => ({
    isAutocompleteOpen: false,
    clearTokens: vi.fn(),
    handleMentionDismiss: vi.fn(),
    handleMentionTrigger: vi.fn(),
    suggestions: [],
    selectedIndex: 0,
    selectSuggestion: vi.fn(),
    activePipelineId: undefined,
  }),
}));

// ── Helpers ──

function createMessage(overrides: Partial<ChatMessage> = {}): ChatMessage {
  return {
    message_id: 'msg-1',
    session_id: 'session-1',
    sender_type: 'user',
    content: 'Hello world',
    timestamp: new Date().toISOString(),
    ...overrides,
  };
}

function renderChat(overrides: Partial<React.ComponentProps<typeof ChatInterface>> = {}) {
  const defaultProps: React.ComponentProps<typeof ChatInterface> = {
    messages: [],
    pendingProposals: new Map(),
    pendingStatusChanges: new Map(),
    pendingRecommendations: new Map(),
    isSending: false,
    onSendMessage: vi.fn(),
    onRetryMessage: vi.fn(),
    onConfirmProposal: vi.fn(),
    onConfirmStatusChange: vi.fn(),
    onConfirmRecommendation: vi.fn(),
    onRejectProposal: vi.fn(),
    onRejectRecommendation: vi.fn(),
    onNewChat: vi.fn(),
    ...overrides,
  };

  return render(<ChatInterface {...defaultProps} />);
}

// ── Tests ──

describe('ChatInterface', () => {
  it('renders the New Chat button when messages exist', () => {
    renderChat({ messages: [createMessage()] });

    expect(screen.getByText('New Chat')).toBeInTheDocument();
  });

  it('renders messages in the message list', () => {
    const messages = [
      createMessage({ message_id: 'msg-1', content: 'First message' }),
      createMessage({ message_id: 'msg-2', content: 'Second message', sender_type: 'assistant' }),
    ];

    renderChat({ messages });

    expect(screen.getByText('First message')).toBeInTheDocument();
    expect(screen.getByText('Second message')).toBeInTheDocument();
  });

  it('shows the empty state when no messages are present', () => {
    renderChat();

    expect(screen.getByText('Start a conversation')).toBeInTheDocument();
  });

  it('calls onNewChat when the New Chat button is clicked', () => {
    const onNewChat = vi.fn();
    renderChat({ onNewChat, messages: [createMessage()] });

    fireEvent.click(screen.getByText('New Chat'));

    expect(onNewChat).toHaveBeenCalledOnce();
  });
});
