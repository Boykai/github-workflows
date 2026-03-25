/**
 * Unit tests for monitoring command handlers (/diff, /usage, /share, /feedback).
 */
import { describe, it, expect, vi } from 'vitest';
import { diffHandler, usageHandler, shareHandler, feedbackHandler } from './monitoring';
import { createCommandContext, createMockChatMessage } from '@/test/factories';

describe('diffHandler', () => {
  it('returns passthrough result', () => {
    const result = diffHandler();

    expect(result.success).toBe(true);
    expect(result.passthrough).toBe(true);
    expect(result.clearInput).toBe(true);
    expect(result.message).toBe('');
  });
});

describe('usageHandler', () => {
  it('returns passthrough result', () => {
    const result = usageHandler();

    expect(result.success).toBe(true);
    expect(result.passthrough).toBe(true);
    expect(result.clearInput).toBe(true);
    expect(result.message).toBe('');
  });
});

describe('shareHandler', () => {
  it('returns "no messages" when conversation is empty', () => {
    const context = createCommandContext({ messages: [] });
    const result = shareHandler('', context);

    expect(result.success).toBe(true);
    expect(result.message).toContain('No messages to export');
  });

  it('exports messages as Markdown and triggers download', () => {
    const createObjectURL = vi.fn(() => 'blob:test');
    const revokeObjectURL = vi.fn();
    const click = vi.fn();
    const createElement = vi.spyOn(document, 'createElement').mockReturnValue({
      href: '',
      download: '',
      click,
    } as unknown as HTMLAnchorElement);

    globalThis.URL.createObjectURL = createObjectURL;
    globalThis.URL.revokeObjectURL = revokeObjectURL;

    const messages = [
      createMockChatMessage({ sender_type: 'user', content: 'Hello' }),
      createMockChatMessage({ sender_type: 'assistant', content: 'Hi there!' }),
    ];
    const context = createCommandContext({ messages });
    const result = shareHandler('', context);

    expect(result.success).toBe(true);
    expect(result.message).toContain('Chat exported');
    expect(result.message).toContain('2 messages');
    expect(createObjectURL).toHaveBeenCalledOnce();
    expect(click).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledOnce();

    createElement.mockRestore();
  });
});

describe('feedbackHandler', () => {
  it('returns feedback link message', () => {
    const result = feedbackHandler();

    expect(result.success).toBe(true);
    expect(result.clearInput).toBe(true);
    expect(result.message).toContain('https://github.com/Boykai/github-workflows/discussions');
    expect(result.message).toContain('feedback');
  });
});
