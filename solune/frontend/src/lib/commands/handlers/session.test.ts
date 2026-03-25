/**
 * Unit tests for session command handlers (/clear, /compact, /context).
 */
import { describe, it, expect, vi } from 'vitest';
import { clearHandler, compactHandler, contextHandler } from './session';
import { createCommandContext, createMockChatMessage } from '@/test/factories';

describe('clearHandler', () => {
  it('clears chat and returns confirmation when messages exist', async () => {
    const clearChat = vi.fn().mockResolvedValue(undefined);
    const messages = [createMockChatMessage()];
    const context = createCommandContext({ clearChat, messages });
    const result = await clearHandler('', context);

    expect(result.success).toBe(true);
    expect(result.clearInput).toBe(true);
    expect(result.message).toContain('Chat cleared');
    expect(clearChat).toHaveBeenCalledOnce();
  });

  it('returns "no messages" when conversation is empty', async () => {
    const clearChat = vi.fn();
    const context = createCommandContext({ clearChat, messages: [] });
    const result = await clearHandler('', context);

    expect(result.success).toBe(true);
    expect(result.message).toContain('No messages to clear');
    expect(clearChat).not.toHaveBeenCalled();
  });

  it('returns failure when clearChat rejects', async () => {
    const clearChat = vi.fn().mockRejectedValue(new Error('Network error'));
    const messages = [createMockChatMessage()];
    const context = createCommandContext({ clearChat, messages });
    const result = await clearHandler('', context);

    expect(result.success).toBe(false);
    expect(result.message).toContain('Failed to clear');
  });
});

describe('compactHandler', () => {
  it('returns passthrough result', () => {
    const result = compactHandler();

    expect(result.success).toBe(true);
    expect(result.passthrough).toBe(true);
    expect(result.clearInput).toBe(true);
    expect(result.message).toBe('');
  });
});

describe('contextHandler', () => {
  it('returns passthrough result', () => {
    const result = contextHandler();

    expect(result.success).toBe(true);
    expect(result.passthrough).toBe(true);
    expect(result.clearInput).toBe(true);
    expect(result.message).toBe('');
  });
});
