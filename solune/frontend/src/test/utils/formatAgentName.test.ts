import { describe, it, expect } from 'vitest';
import { formatAgentName } from '@/utils/formatAgentName';

describe('formatAgentName', () => {
  it('title-cases single-word slug', () => {
    expect(formatAgentName('linter')).toBe('Linter');
  });

  it('formats dot-separated slug with title-case segments', () => {
    expect(formatAgentName('speckit.tasks')).toBe('Spec Kit - Tasks');
  });

  it('formats speckit.implement', () => {
    expect(formatAgentName('speckit.implement')).toBe('Spec Kit - Implement');
  });

  it('formats multi-segment slug', () => {
    expect(formatAgentName('agent.v2.runner')).toBe('Agent - V2 - Runner');
  });

  it('filters empty segments from double dots', () => {
    expect(formatAgentName('speckit..tasks')).toBe('Spec Kit - Tasks');
  });

  it('returns empty string for empty slug', () => {
    expect(formatAgentName('')).toBe('');
  });

  it('returns displayName when provided', () => {
    expect(formatAgentName('linter', 'My Custom Linter')).toBe('My Custom Linter');
  });

  it('formats raw slug displayName (single word) like a slug', () => {
    expect(formatAgentName('tester', 'tester')).toBe('Tester');
  });

  it('formats raw slug displayName (hyphenated) like a slug', () => {
    expect(formatAgentName('quality-assurance', 'quality-assurance')).toBe('Quality Assurance');
  });

  it('formats raw slug displayName (underscored) like a slug', () => {
    expect(formatAgentName('quality_assurance', 'quality_assurance')).toBe('Quality Assurance');
  });

  it('lowercases all-caps slug before title-casing', () => {
    expect(formatAgentName('LINTER')).toBe('Linter');
  });

  it('falls back to slug formatting when displayName is empty string', () => {
    expect(formatAgentName('speckit.analyze', '')).toBe('Spec Kit - Analyze');
  });

  it('falls back to slug formatting when displayName is null', () => {
    expect(formatAgentName('speckit.analyze', null)).toBe('Spec Kit - Analyze');
  });

  it('returns displayName when displayName is provided even for empty slug', () => {
    expect(formatAgentName('', 'Custom Name')).toBe('Custom Name');
  });

  it('formats spec kit agents with suffix style when requested', () => {
    expect(formatAgentName('speckit.clarify', 'Speckit.Clarify', { specKitStyle: 'suffix' })).toBe(
      'Clarify (Spec Kit)'
    );
  });

  it('formats hyphenated spec kit agents with suffix style when requested', () => {
    expect(formatAgentName('speckit-taskstoissues', undefined, { specKitStyle: 'suffix' })).toBe(
      'Tasks To Issues (Spec Kit)'
    );
  });
});
