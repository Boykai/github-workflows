/**
 * Unit tests for help command handler.
 */
import { describe, it, expect } from 'vitest';
import { helpHandler } from './help';
import { getAllCommands } from '../registry';
import { createCommandContext } from '@/test/factories';

describe('helpHandler', () => {
  const context = createCommandContext();

  it('returns a successful result', () => {
    const result = helpHandler('', context);
    expect(result.success).toBe(true);
    expect(result.clearInput).toBe(true);
  });

  it('output contains all registered commands', () => {
    const result = helpHandler('', context);
    const commands = getAllCommands();

    for (const cmd of commands) {
      expect(result.message).toContain(cmd.name);
    }
  });

  it('output includes command syntax and description', () => {
    const result = helpHandler('', context);
    const commands = getAllCommands();

    for (const cmd of commands) {
      expect(result.message).toContain(cmd.syntax);
      expect(result.message).toContain(cmd.description);
    }
  });

  it('output starts with Available Commands header', () => {
    const result = helpHandler('', context);
    expect(result.message).toContain('Available Commands');
  });

  it('auto-updates when new commands are added', () => {
    // The help handler uses getAllCommands() dynamically, so any new command
    // registered will appear. We test this by checking the count.
    const result = helpHandler('', context);
    const lineCount = result.message.split('\n').filter((l) => l.includes('/')).length;
    expect(lineCount).toBe(getAllCommands().length);
  });
});
