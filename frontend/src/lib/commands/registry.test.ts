/**
 * Unit tests for command registry and parseCommand function.
 */
import { describe, it, expect, afterAll } from 'vitest';

// Import from registry (which registers built-in commands on load)
import {
  getCommand,
  getAllCommands,
  filterCommands,
  parseCommand,
  registerCommand,
  unregisterCommand,
} from './registry';

describe('CommandRegistry', () => {
  it('returns command definition for registered command name', () => {
    const cmd = getCommand('help');
    expect(cmd).toBeDefined();
    expect(cmd!.name).toBe('help');
  });

  it('returns undefined for unregistered command name', () => {
    expect(getCommand('nonexistent')).toBeUndefined();
  });

  it('performs case-insensitive lookup', () => {
    expect(getCommand('HELP')).toBeDefined();
    expect(getCommand('Help')).toBeDefined();
    expect(getCommand('THEME')).toBeDefined();
  });

  it('getAllCommands returns sorted list of all registered commands', () => {
    const commands = getAllCommands();
    expect(commands.length).toBeGreaterThanOrEqual(6);
    // Check sorted order
    for (let i = 1; i < commands.length; i++) {
      expect(commands[i - 1].name.localeCompare(commands[i].name)).toBeLessThanOrEqual(0);
    }
  });

  it('getAllCommands includes help, theme, language, notifications, view, agent', () => {
    const names = getAllCommands().map((c) => c.name);
    expect(names).toContain('help');
    expect(names).toContain('theme');
    expect(names).toContain('language');
    expect(names).toContain('notifications');
    expect(names).toContain('view');
    expect(names).toContain('agent');
  });

  it('filterCommands returns matching commands by prefix', () => {
    const filtered = filterCommands('th');
    expect(filtered.length).toBe(1);
    expect(filtered[0].name).toBe('theme');
  });

  it('filterCommands is case-insensitive', () => {
    const filtered = filterCommands('TH');
    expect(filtered.length).toBe(1);
    expect(filtered[0].name).toBe('theme');
  });

  it('filterCommands returns all commands for empty prefix', () => {
    const filtered = filterCommands('');
    expect(filtered.length).toBe(getAllCommands().length);
  });

  it('filterCommands returns empty array for no matches', () => {
    const filtered = filterCommands('xyz');
    expect(filtered.length).toBe(0);
  });

  it('each command has required fields', () => {
    const commands = getAllCommands();
    for (const cmd of commands) {
      expect(cmd.name).toBeTruthy();
      expect(cmd.description).toBeTruthy();
      expect(cmd.syntax).toBeTruthy();
      expect(typeof cmd.handler).toBe('function');
    }
  });

  it('agent command is registered with passthrough flag', () => {
    const cmd = getCommand('agent');
    expect(cmd).toBeDefined();
    expect(cmd!.passthrough).toBe(true);
    expect(cmd!.name).toBe('agent');
  });

  it('filterCommands includes agent when prefix matches', () => {
    const filtered = filterCommands('ag');
    expect(filtered.length).toBeGreaterThanOrEqual(1);
    expect(filtered.find((c) => c.name === 'agent')).toBeDefined();
  });
});

describe('parseCommand', () => {
  it('parses /help as command with name "help" and no args', () => {
    const result = parseCommand('/help');
    expect(result.isCommand).toBe(true);
    expect(result.name).toBe('help');
    expect(result.args).toBe('');
  });

  it('parses /theme dark as command with name "theme" and args "dark"', () => {
    const result = parseCommand('/theme dark');
    expect(result.isCommand).toBe(true);
    expect(result.name).toBe('theme');
    expect(result.args).toBe('dark');
  });

  it('handles bare / as incomplete command', () => {
    const result = parseCommand('/');
    expect(result.isCommand).toBe(true);
    expect(result.name).toBeNull();
  });

  it('treats "help" keyword (exact, case-insensitive) as help alias', () => {
    expect(parseCommand('help').isCommand).toBe(true);
    expect(parseCommand('help').name).toBe('help');
    expect(parseCommand('HELP').name).toBe('help');
    expect(parseCommand('Help').name).toBe('help');
  });

  it('treats non-/ non-help input as non-command', () => {
    const result = parseCommand('hello world');
    expect(result.isCommand).toBe(false);
    expect(result.name).toBeNull();
  });

  it('is case-insensitive for command names', () => {
    expect(parseCommand('/THEME dark').name).toBe('theme');
    expect(parseCommand('/Theme Dark').name).toBe('theme');
    expect(parseCommand('/Theme Dark').args).toBe('Dark');
  });

  it('normalizes whitespace in arguments', () => {
    const result = parseCommand('/theme   dark');
    expect(result.args).toBe('dark');
  });

  it('trims leading/trailing whitespace', () => {
    const result = parseCommand('  /help  ');
    expect(result.isCommand).toBe(true);
    expect(result.name).toBe('help');
  });

  it('preserves raw input', () => {
    const input = '  /theme   dark  ';
    const result = parseCommand(input);
    expect(result.raw).toBe(input);
  });

  // Edge cases — Markdown characters are NOT commands
  it('# (Markdown header) is NOT a command', () => {
    const result = parseCommand('# Heading');
    expect(result.isCommand).toBe(false);
  });

  it('## (Markdown header) is NOT a command', () => {
    const result = parseCommand('## Sub-heading');
    expect(result.isCommand).toBe(false);
  });

  it('* (Markdown bold/list) is NOT a command', () => {
    const result = parseCommand('**bold text**');
    expect(result.isCommand).toBe(false);
  });

  it('- (Markdown list) is NOT a command', () => {
    const result = parseCommand('- list item');
    expect(result.isCommand).toBe(false);
  });

  it('> (Markdown blockquote) is NOT a command', () => {
    const result = parseCommand('> blockquote');
    expect(result.isCommand).toBe(false);
  });

  it('` (Markdown code) is NOT a command', () => {
    const result = parseCommand('`code`');
    expect(result.isCommand).toBe(false);
  });

  it('/ mid-sentence is NOT a command', () => {
    const result = parseCommand('change /theme dark');
    expect(result.isCommand).toBe(false);
  });

  it('empty string is not a command', () => {
    const result = parseCommand('');
    expect(result.isCommand).toBe(false);
  });

  it('whitespace-only string is not a command', () => {
    const result = parseCommand('   ');
    expect(result.isCommand).toBe(false);
  });

  it('extra whitespace between / and command is handled', () => {
    // '/  theme dark' — after '/', trim, first word is 'theme'
    const result = parseCommand('/  theme dark');
    expect(result.isCommand).toBe(true);
    expect(result.name).toBe('theme');
    expect(result.args).toBe('dark');
  });

  it('mixed case /Theme Dark normalizes name but preserves args case', () => {
    const result = parseCommand('/Theme Dark');
    expect(result.name).toBe('theme');
    expect(result.args).toBe('Dark');
  });
});

describe('Single Source of Truth (US5)', () => {
  // Clean up the test command after this suite to prevent state leakage
  // across test files running in the same Vitest worker.
  afterAll(() => {
    unregisterCommand('_test_ssot');
  });

  it('newly registered command appears in getAllCommands', () => {
    const before = getAllCommands().length;
    registerCommand({
      name: '_test_ssot',
      description: 'Test SSOT command',
      syntax: '/_test_ssot',
      handler: () => ({ success: true, message: 'ok', clearInput: true }),
    });
    const after = getAllCommands().length;
    expect(after).toBe(before + 1);
    expect(getAllCommands().find((c) => c.name === '_test_ssot')).toBeDefined();
  });

  it('newly registered command is findable by getCommand', () => {
    expect(getCommand('_test_ssot')).toBeDefined();
  });

  it('newly registered command appears in filterCommands', () => {
    const filtered = filterCommands('_test_');
    expect(filtered.length).toBeGreaterThanOrEqual(1);
    expect(filtered[0].name).toBe('_test_ssot');
  });
});
