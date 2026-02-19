/**
 * Unit tests for ChatInterface component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInterface } from './ChatInterface';
import type { ChatMessage, AITaskProposal, IssueCreateActionData } from '@/types';

vi.mock('./ChatInterface.css', () => ({}));

// jsdom does not implement scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

vi.mock('./MessageBubble', () => ({
  MessageBubble: ({ message }: { message: ChatMessage }) => (
    <div data-testid="message-bubble">{message.content}</div>
  ),
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

interface StatusChangeProposal {
  proposal_id: string;
  task_id: string;
  task_title: string;
  current_status: string;
  target_status: string;
  status_option_id: string;
  status_field_id: string;
  status: string;
}

function createDefaultProps(overrides: Partial<{
  messages: ChatMessage[];
  pendingProposals: Map<string, AITaskProposal>;
  pendingStatusChanges: Map<string, StatusChangeProposal>;
  pendingRecommendations: Map<string, IssueCreateActionData>;
  isSending: boolean;
  onSendMessage: (content: string) => void;
  onConfirmProposal: (id: string) => void;
  onConfirmStatusChange: (id: string) => void;
  onConfirmRecommendation: (id: string) => Promise<{ success: boolean; message: string }>;
  onRejectProposal: (id: string) => void;
  onRejectRecommendation: (id: string) => Promise<void>;
  onNewChat: () => void;
}> = {}) {
  return {
    messages: [] as ChatMessage[],
    pendingProposals: new Map<string, AITaskProposal>(),
    pendingStatusChanges: new Map<string, StatusChangeProposal>(),
    pendingRecommendations: new Map<string, IssueCreateActionData>(),
    isSending: false,
    onSendMessage: vi.fn(),
    onConfirmProposal: vi.fn(),
    onConfirmStatusChange: vi.fn(),
    onConfirmRecommendation: vi.fn().mockResolvedValue({ success: true, message: 'ok' }),
    onRejectProposal: vi.fn(),
    onRejectRecommendation: vi.fn().mockResolvedValue(undefined),
    onNewChat: vi.fn(),
    ...overrides,
  };
}

function createMessage(overrides: Partial<ChatMessage> = {}): ChatMessage {
  return {
    message_id: 'msg-1',
    session_id: 'session-1',
    sender_type: 'user',
    content: 'Hello',
    timestamp: '2024-01-15T10:00:00Z',
    ...overrides,
  };
}

describe('ChatInterface', () => {
  it('shows empty state when no messages', () => {
    render(<ChatInterface {...createDefaultProps()} />);
    expect(screen.getByText('Start a conversation')).toBeDefined();
  });

  it('renders messages when provided', () => {
    const messages = [
      createMessage({ message_id: 'msg-1', content: 'Hello' }),
      createMessage({ message_id: 'msg-2', content: 'World', sender_type: 'assistant' }),
    ];
    render(<ChatInterface {...createDefaultProps({ messages })} />);
    expect(screen.getAllByTestId('message-bubble')).toHaveLength(2);
  });

  it('shows loading indicator when isSending', () => {
    const messages = [createMessage()];
    const { container } = render(
      <ChatInterface {...createDefaultProps({ messages, isSending: true })} />
    );
    expect(container.querySelector('.typing-indicator')).not.toBeNull();
  });

  it('send button is disabled when input is empty', () => {
    render(<ChatInterface {...createDefaultProps()} />);
    const button = screen.getByRole('button', { name: '' });
    // The submit button should be disabled when input is empty
    expect((button as HTMLButtonElement).disabled).toBe(true);
  });

  it('send button is disabled when isSending', () => {
    render(<ChatInterface {...createDefaultProps({ isSending: true })} />);
    const textarea = screen.getByPlaceholderText(/Describe a feature/);
    expect((textarea as HTMLTextAreaElement).disabled).toBe(true);
  });

  it('typing text and submitting calls onSendMessage', () => {
    const onSendMessage = vi.fn();
    render(<ChatInterface {...createDefaultProps({ onSendMessage })} />);
    const textarea = screen.getByPlaceholderText(/Describe a feature/);
    fireEvent.change(textarea, { target: { value: 'Create a login page' } });
    fireEvent.submit(textarea.closest('form')!);
    expect(onSendMessage).toHaveBeenCalledWith('Create a login page');
  });

  it('New Chat button calls onNewChat', () => {
    const onNewChat = vi.fn();
    const messages = [createMessage()];
    render(<ChatInterface {...createDefaultProps({ messages, onNewChat })} />);
    fireEvent.click(screen.getByText('New Chat'));
    expect(onNewChat).toHaveBeenCalledOnce();
  });

  it('renders TaskPreview for task_create proposals', () => {
    const proposal: AITaskProposal = {
      proposal_id: 'prop-1',
      session_id: 'session-1',
      original_input: 'Create login',
      proposed_title: 'Login page',
      proposed_description: 'Build login',
      status: 'pending',
      created_at: '2024-01-15T10:00:00Z',
      expires_at: '2024-01-15T11:00:00Z',
    };
    const pendingProposals = new Map([['prop-1', proposal]]);
    const messages = [
      createMessage({
        message_id: 'msg-1',
        sender_type: 'assistant',
        action_type: 'task_create',
        action_data: { proposal_id: 'prop-1', status: 'pending' } as never,
      }),
    ];
    render(<ChatInterface {...createDefaultProps({ messages, pendingProposals })} />);
    expect(screen.getByTestId('task-preview')).toBeDefined();
  });

  it('renders StatusChangePreview for status_update proposals', () => {
    const statusChange: StatusChangeProposal = {
      proposal_id: 'sc-1',
      task_id: 'task-1',
      task_title: 'Fix bug',
      current_status: 'Todo',
      target_status: 'In Progress',
      status_option_id: 'opt-1',
      status_field_id: 'field-1',
      status: 'pending',
    };
    const pendingStatusChanges = new Map([['sc-1', statusChange]]);
    const messages = [
      createMessage({
        message_id: 'msg-1',
        sender_type: 'assistant',
        action_type: 'status_update',
        action_data: { proposal_id: 'sc-1' } as never,
      }),
    ];
    render(<ChatInterface {...createDefaultProps({ messages, pendingStatusChanges })} />);
    expect(screen.getByTestId('status-change-preview')).toBeDefined();
  });
});
