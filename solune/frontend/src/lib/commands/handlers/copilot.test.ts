/**
 * Unit tests for Copilot passthrough commands.
 */
import { describe, it, expect } from 'vitest';
import { copilotPassthroughHandler } from './copilot';
import { getCommand, getAllCommands, parseCommand } from '../registry';

const COPILOT_COMMANDS = [
  'explain',
  'fix',
  'doc',
  'tests',
  'setuptests',
  'new',
  'newnotebook',
  'search',
  'startdebugging',
] as const;

describe('copilotPassthroughHandler', () => {
  it('returns passthrough result with clearInput', () => {
    const result = copilotPassthroughHandler();
    expect(result).toEqual({
      success: true,
      message: '',
      clearInput: true,
      passthrough: true,
    });
  });
});

describe('Copilot command registration', () => {
  it('all 9 Copilot commands are registered in the registry', () => {
    for (const name of COPILOT_COMMANDS) {
      const cmd = getCommand(name);
      expect(cmd, `command /${name} should be registered`).toBeDefined();
    }
  });

  it('all Copilot commands have passthrough: true', () => {
    for (const name of COPILOT_COMMANDS) {
      const cmd = getCommand(name)!;
      expect(cmd.passthrough, `/${name} should be passthrough`).toBe(true);
    }
  });

  it('all Copilot commands have category: copilot', () => {
    for (const name of COPILOT_COMMANDS) {
      const cmd = getCommand(name)!;
      expect(cmd.category, `/${name} should have copilot category`).toBe('copilot');
    }
  });

  it('all Copilot commands appear in getAllCommands()', () => {
    const allNames = getAllCommands().map((c) => c.name);
    for (const name of COPILOT_COMMANDS) {
      expect(allNames, `/${name} should be in getAllCommands()`).toContain(name);
    }
  });

  it('existing Solune commands retain category: solune', () => {
    const soluneCommands = ['help', 'agent', 'plan', 'clear'];
    for (const name of soluneCommands) {
      const cmd = getCommand(name)!;
      expect(cmd.category, `/${name} should have solune category`).toBe('solune');
    }
  });
});

describe('parseCommand for Copilot commands', () => {
  it('parses /explain with arguments', () => {
    const result = parseCommand('/explain What is a closure?');
    expect(result.isCommand).toBe(true);
    expect(result.name).toBe('explain');
    expect(result.args).toBe('What is a closure?');
  });

  it('parses /fix without arguments', () => {
    const result = parseCommand('/fix');
    expect(result.isCommand).toBe(true);
    expect(result.name).toBe('fix');
    expect(result.args).toBe('');
  });

  it('parses /setupTests case-insensitively', () => {
    const result = parseCommand('/setupTests React project');
    expect(result.isCommand).toBe(true);
    expect(result.name).toBe('setuptests');
    expect(result.args).toBe('React project');
  });

  it('parses /newNotebook case-insensitively', () => {
    const result = parseCommand('/newNotebook data analysis');
    expect(result.isCommand).toBe(true);
    expect(result.name).toBe('newnotebook');
    expect(result.args).toBe('data analysis');
  });

  it('parses /startDebugging case-insensitively', () => {
    const result = parseCommand('/startDebugging Node.js app');
    expect(result.isCommand).toBe(true);
    expect(result.name).toBe('startdebugging');
    expect(result.args).toBe('Node.js app');
  });
});
