/**
 * Integration tests for MessageBubble user/assistant rendering.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { MessageBubble } from './MessageBubble';
import type { ChatMessage } from '@/types';

function createMessage(overrides: Partial<ChatMessage> = {}): ChatMessage {
  return {
    message_id: 'msg-1',
    session_id: 'session-1',
    sender_type: 'user',
    content: 'Hello world',
    timestamp: '2025-01-15T10:30:00Z',
    ...overrides,
  };
}

describe('MessageBubble', () => {
  it('renders user message content', () => {
    render(<MessageBubble message={createMessage({ content: 'User says hi' })} />);
    expect(screen.getByText('User says hi')).toBeInTheDocument();
  });

  it('renders assistant message content', () => {
    render(
      <MessageBubble message={createMessage({ sender_type: 'assistant', content: 'Bot reply' })} />
    );
    expect(screen.getByText('Bot reply')).toBeInTheDocument();
  });

  it('renders system message content', () => {
    render(
      <MessageBubble message={createMessage({ sender_type: 'system', content: 'System notice' })} />
    );
    expect(screen.getByText('System notice')).toBeInTheDocument();
  });

  it('applies right-aligned styling for user messages', () => {
    const { container } = render(<MessageBubble message={createMessage()} />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain('self-end');
  });

  it('applies left-aligned styling for assistant messages', () => {
    const { container } = render(
      <MessageBubble message={createMessage({ sender_type: 'assistant' })} />
    );
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain('self-start');
  });

  it('shows avatar icon for assistant messages but not user messages', () => {
    const { container: assistantContainer } = render(
      <MessageBubble message={createMessage({ sender_type: 'assistant' })} />
    );
    expect(assistantContainer.querySelector('svg')).toBeInTheDocument();

    const { container: userContainer } = render(
      <MessageBubble message={createMessage({ sender_type: 'user' })} />
    );
    expect(userContainer.querySelector('svg')).not.toBeInTheDocument();
  });

  it('displays formatted timestamp', () => {
    render(<MessageBubble message={createMessage({ timestamp: '2025-01-15T10:30:00Z' })} />);
    // getByRole('time') is invalid — <time> has no implicit ARIA role; query by text instead
    const timeEl = screen.getByText(/\d{1,2}:\d{2}/);
    expect(timeEl).toBeInTheDocument();
  });

  it('applies user bubble styling (bg-primary)', () => {
    const { container } = render(<MessageBubble message={createMessage()} />);
    const bubble = container.querySelector('.bg-primary');
    expect(bubble).toBeInTheDocument();
  });

  it('applies assistant bubble styling (bg-muted)', () => {
    const { container } = render(<MessageBubble message={createMessage({ sender_type: 'assistant' })} />);
    const bubble = container.querySelector('.bg-background\\/62');
    expect(bubble).toBeInTheDocument();
    expect(bubble?.className).toContain('border');
  });

  it('applies system message styling (text-muted-foreground)', () => {
    const { container } = render(
      <MessageBubble message={createMessage({ sender_type: 'system' })} />
    );
    const systemEl = container.querySelector('.text-muted-foreground');
    expect(systemEl).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<MessageBubble message={createMessage()} />);
    await expectNoA11yViolations(container);
  });
});
