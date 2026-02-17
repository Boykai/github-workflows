/**
 * Color mapping utilities for StatusColor enum to CSS values.
 */

import type { StatusColor } from '@/types';

/** Map GitHub StatusColor enum values to CSS hex colors */
const STATUS_COLOR_MAP: Record<StatusColor, string> = {
  GRAY: '#6e7781',
  BLUE: '#0969da',
  GREEN: '#1a7f37',
  YELLOW: '#bf8700',
  ORANGE: '#bc4c00',
  RED: '#cf222e',
  PINK: '#bf3989',
  PURPLE: '#8250df',
};

/** Map StatusColor to background with low opacity for badges */
const STATUS_COLOR_BG_MAP: Record<StatusColor, string> = {
  GRAY: 'rgba(110, 119, 129, 0.15)',
  BLUE: 'rgba(9, 105, 218, 0.15)',
  GREEN: 'rgba(26, 127, 55, 0.15)',
  YELLOW: 'rgba(191, 135, 0, 0.15)',
  ORANGE: 'rgba(188, 76, 0, 0.15)',
  RED: 'rgba(207, 34, 46, 0.15)',
  PINK: 'rgba(191, 57, 137, 0.15)',
  PURPLE: 'rgba(130, 80, 223, 0.15)',
};

/**
 * Convert a StatusColor enum value to a CSS hex color string.
 */
export function statusColorToCSS(color: StatusColor): string {
  return STATUS_COLOR_MAP[color] || STATUS_COLOR_MAP.GRAY;
}

/**
 * Convert a StatusColor enum value to a semi-transparent background color.
 */
export function statusColorToBg(color: StatusColor): string {
  return STATUS_COLOR_BG_MAP[color] || STATUS_COLOR_BG_MAP.GRAY;
}
