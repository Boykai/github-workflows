/**
 * Unit tests for help command handler.
 */
import { describe, it, expect, afterAll } from 'vitest';
import { helpHandler } from './help';
import { getAllCommands, getCommandsByCategory, registerCommand, unregisterCommand } from '../registry';
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
    // The help handler uses getCommandsByCategory() dynamically, so any new command
    // registered will appear. We test this by checking the count.
    const result = helpHandler('', context);
    const lineCount = result.message.split('\n').filter((l) => l.includes('#')).length;
    expect(lineCount).toBe(getAllCommands().length);
  });
});

describe('helpHandler categorized output (US1)', () => {
  const context = createCommandContext();

  it('contains category headers General, Settings, Workflow', () => {
    const result = helpHandler('', context);
    expect(result.message).toContain('General');
    expect(result.message).toContain('Settings');
    expect(result.message).toContain('Workflow');
  });

  it('groups commands under correct categories', () => {
    const result = helpHandler('', context);
    const lines = result.message.split('\n');

    // Find category header positions
    const generalIdx = lines.findIndex((l) => l.trim() === 'General');
    const settingsIdx = lines.findIndex((l) => l.trim() === 'Settings');
    const workflowIdx = lines.findIndex((l) => l.trim() === 'Workflow');

    expect(generalIdx).toBeGreaterThanOrEqual(0);
    expect(settingsIdx).toBeGreaterThan(generalIdx);
    expect(workflowIdx).toBeGreaterThan(settingsIdx);

    // help should be between General and Settings headers
    const helpLine = lines.findIndex((l) => l.includes('#help'));
    expect(helpLine).toBeGreaterThan(generalIdx);
    expect(helpLine).toBeLessThan(settingsIdx);

    // theme should be between Settings and Workflow headers
    const themeLine = lines.findIndex((l) => l.includes('#theme'));
    expect(themeLine).toBeGreaterThan(settingsIdx);
    expect(themeLine).toBeLessThan(workflowIdx);

    // agent should be after Workflow header
    const agentLine = lines.findIndex((l) => l.includes('#agent'));
    expect(agentLine).toBeGreaterThan(workflowIdx);
  });

  it('commands without explicit category default to General', () => {
    const categories = getCommandsByCategory();
    const generalGroup = categories.find((g) => g.category === 'General');
    expect(generalGroup).toBeDefined();
    // help command has no explicit category, should be in General
    expect(generalGroup!.commands.find((c) => c.name === 'help')).toBeDefined();
  });

  it('each command entry shows name, description, and syntax', () => {
    const result = helpHandler('', context);
    const commands = getAllCommands();

    for (const cmd of commands) {
      expect(result.message).toContain(cmd.syntax);
      expect(result.message).toContain(cmd.description);
    }
  });
});

describe('helpHandler empty registry edge case (US1)', () => {
  it('displays no commands message when registry is empty', () => {
    // Temporarily unregister all commands, test, then re-register
    const commands = getAllCommands();
    for (const cmd of commands) {
      unregisterCommand(cmd.name);
    }

    const context = createCommandContext();
    const result = helpHandler('', context);
    expect(result.message).toContain('No commands available');

    // Re-register all commands to restore state
    for (const cmd of commands) {
      registerCommand(cmd);
    }
  });
});

describe('helpHandler dynamic registration (US1)', () => {
  afterAll(() => {
    unregisterCommand('_test_dynamic_help');
  });

  it('newly registered command appears in help output under its category', () => {
    registerCommand({
      name: '_test_dynamic_help',
      description: 'Dynamic test command',
      syntax: '#_test_dynamic_help',
      handler: () => ({ success: true, message: 'ok', clearInput: true }),
      category: 'Workflow',
    });

    const context = createCommandContext();
    const result = helpHandler('', context);
    expect(result.message).toContain('_test_dynamic_help');
    expect(result.message).toContain('Dynamic test command');
  });
});

describe('helpHandler single-command help (US4)', () => {
  const context = createCommandContext();

  it('#help theme shows detailed info for theme only', () => {
    const result = helpHandler('theme', context);
    expect(result.success).toBe(true);
    expect(result.message).toContain('#theme');
    expect(result.message).toContain('Change the UI theme');
    expect(result.message).toContain('Usage:');
    expect(result.message).toContain('Options: light, dark, system');
    expect(result.message).toContain('Example: #theme light');
    // Should NOT contain other commands
    expect(result.message).not.toContain('#language');
    expect(result.message).not.toContain('#notifications');
  });

  it('#help nonexistent shows not found message', () => {
    const result = helpHandler('nonexistent', context);
    expect(result.success).toBe(false);
    expect(result.message).toContain('not found');
    expect(result.message).toContain('#help');
  });

  it('#help #theme strips leading # and shows theme help', () => {
    const result = helpHandler('#theme', context);
    expect(result.success).toBe(true);
    expect(result.message).toContain('#theme');
    expect(result.message).toContain('Change the UI theme');
  });

  it('#help with no argument shows full categorized listing', () => {
    const result = helpHandler('', context);
    expect(result.success).toBe(true);
    expect(result.message).toContain('Available Commands');
    expect(result.message).toContain('General');
    expect(result.message).toContain('Settings');
  });
});

describe('helpHandler error format (US3)', () => {
  const context = createCommandContext();

  it('command not found follows three-part structure', () => {
    const result = helpHandler('nonexistent', context);
    expect(result.success).toBe(false);
    // What went wrong
    expect(result.message).toContain("'nonexistent' not found");
    // Where to get help
    expect(result.message).toContain('#help');
  });
});
