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

/**
 * Convert a StatusColor enum value to a CSS hex color string.
 */
export function statusColorToCSS(color: StatusColor): string {
  return STATUS_COLOR_MAP[color] || STATUS_COLOR_MAP.GRAY;
}
