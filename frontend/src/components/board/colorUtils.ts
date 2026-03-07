/**
 * Color mapping utilities for StatusColor enum to CSS values.
 */

import type { StatusColor } from '@/types';

/** Map GitHub StatusColor enum values to CSS hex colors */
const STATUS_COLOR_MAP: Record<StatusColor, string> = {
  GRAY: '#9b9389',
  BLUE: '#5a74d6',
  GREEN: '#4e9e74',
  YELLOW: '#d7ab46',
  ORANGE: '#d88947',
  RED: '#d45f67',
  PINK: '#cb7eb3',
  PURPLE: '#8f78d8',
};

/** Map StatusColor to background with low opacity for badges */
const STATUS_COLOR_BG_MAP: Record<StatusColor, string> = {
  GRAY: 'rgba(155, 147, 137, 0.18)',
  BLUE: 'rgba(90, 116, 214, 0.18)',
  GREEN: 'rgba(78, 158, 116, 0.18)',
  YELLOW: 'rgba(215, 171, 70, 0.2)',
  ORANGE: 'rgba(216, 137, 71, 0.18)',
  RED: 'rgba(212, 95, 103, 0.18)',
  PINK: 'rgba(203, 126, 179, 0.18)',
  PURPLE: 'rgba(143, 120, 216, 0.18)',
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
