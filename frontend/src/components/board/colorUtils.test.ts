/**
 * Unit tests for color utility functions
 */
import { describe, it, expect } from 'vitest';
import { statusColorToCSS, statusColorToBg } from './colorUtils';
import type { StatusColor } from '@/types';

describe('statusColorToCSS', () => {
  const expected: Record<StatusColor, string> = {
    GRAY: '#6e7781',
    BLUE: '#0969da',
    GREEN: '#1a7f37',
    YELLOW: '#bf8700',
    ORANGE: '#bc4c00',
    RED: '#cf222e',
    PINK: '#bf3989',
    PURPLE: '#8250df',
  };

  it.each(Object.entries(expected))('maps %s to %s', (color, hex) => {
    expect(statusColorToCSS(color as StatusColor)).toBe(hex);
  });

  it('falls back to GRAY for unknown color', () => {
    expect(statusColorToCSS('UNKNOWN' as StatusColor)).toBe('#6e7781');
  });
});

describe('statusColorToBg', () => {
  const expected: Record<StatusColor, string> = {
    GRAY: 'rgba(110, 119, 129, 0.15)',
    BLUE: 'rgba(9, 105, 218, 0.15)',
    GREEN: 'rgba(26, 127, 55, 0.15)',
    YELLOW: 'rgba(191, 135, 0, 0.15)',
    ORANGE: 'rgba(188, 76, 0, 0.15)',
    RED: 'rgba(207, 34, 46, 0.15)',
    PINK: 'rgba(191, 57, 137, 0.15)',
    PURPLE: 'rgba(130, 80, 223, 0.15)',
  };

  it.each(Object.entries(expected))('maps %s to %s', (color, bg) => {
    expect(statusColorToBg(color as StatusColor)).toBe(bg);
  });

  it('falls back to GRAY for unknown color', () => {
    expect(statusColorToBg('INVALID' as StatusColor)).toBe('rgba(110, 119, 129, 0.15)');
  });
});
