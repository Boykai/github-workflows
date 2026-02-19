/**
 * Unit tests for MessageBubble component
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MessageBubble } from './MessageBubble';
import type { ChatMessage } from '@/types';

function createMessage(overrides: Partial<ChatMessage> = {}): ChatMessage {
  return {
    message_id: 'msg-1',
    session_id: 'session-1',
    sender_type: 'user',
    content: 'Hello world',
    timestamp: '2024-01-15T10:30:00Z',
    ...overrides,
  };
}

describe('MessageBubble', () => {
  it('renders user message with correct class', () => {
    const { container } = render(<MessageBubble message={createMessage({ sender_type: 'user' })} />);
    const bubble = container.querySelector('.message-bubble');
    expect(bubble?.className).toContain('user');
  });

  it('renders assistant message with avatar icon', () => {
    const { container } = render(
      <MessageBubble message={createMessage({ sender_type: 'assistant' })} />
    );
    const avatar = container.querySelector('.message-avatar');
    expect(avatar).not.toBeNull();
    expect(avatar?.querySelector('svg')).not.toBeNull();
  });

  it('does not render avatar for user messages', () => {
    const { container } = render(<MessageBubble message={createMessage({ sender_type: 'user' })} />);
    expect(container.querySelector('.message-avatar')).toBeNull();
  });

  it('renders system message with system class', () => {
    const { container } = render(
      <MessageBubble message={createMessage({ sender_type: 'system', content: 'System notice' })} />
    );
    expect(container.querySelector('.system-message')).not.toBeNull();
    expect(screen.getByText('System notice')).toBeDefined();
  });

  it('shows formatted timestamp', () => {
    render(<MessageBubble message={createMessage()} />);
    const timeEl = document.querySelector('.message-time');
    expect(timeEl).not.toBeNull();
    expect(timeEl?.textContent).toBeTruthy();
  });

  it('renders message content', () => {
    render(<MessageBubble message={createMessage({ content: 'Test content' })} />);
    expect(screen.getByText('Test content')).toBeDefined();
  });
});
