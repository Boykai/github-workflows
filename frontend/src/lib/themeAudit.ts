/**
 * Theme audit helpers — WCAG 2.1 AA contrast-ratio utilities
 * and HSL/RGB conversion functions for the Celestial design system.
 *
 * Note: The audit scripts under frontend/scripts/ embed equivalent logic
 * directly because they run as plain ESM and cannot import this TypeScript
 * helper. Keep those inline copies in sync manually if this module changes.
 */

/* ── Colour-space conversions ── */

/** Parse an HSL triplet string like "41 82% 95%" → [41, 82, 95] */
export function parseHsl(raw: string): [number, number, number] {
  const parts = raw
    .replace(/%/g, '')
    .trim()
    .split(/\s+/)
    .map(Number);
  if (parts.length !== 3 || parts.some(Number.isNaN)) {
    throw new Error(`Invalid HSL triplet: "${raw}"`);
  }
  return [parts[0], parts[1], parts[2]];
}

/** Convert HSL (h 0-360, s 0-100, l 0-100) → sRGB [r, g, b] each 0-255. */
export function hslToRgb(
  h: number,
  s: number,
  l: number,
): [number, number, number] {
  const sN = s / 100;
  const lN = l / 100;
  const c = (1 - Math.abs(2 * lN - 1)) * sN;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = lN - c / 2;

  let r1: number, g1: number, b1: number;
  if (h < 60) [r1, g1, b1] = [c, x, 0];
  else if (h < 120) [r1, g1, b1] = [x, c, 0];
  else if (h < 180) [r1, g1, b1] = [0, c, x];
  else if (h < 240) [r1, g1, b1] = [0, x, c];
  else if (h < 300) [r1, g1, b1] = [x, 0, c];
  else [r1, g1, b1] = [c, 0, x];

  return [
    Math.round((r1 + m) * 255),
    Math.round((g1 + m) * 255),
    Math.round((b1 + m) * 255),
  ];
}

/* ── WCAG 2.1 relative luminance & contrast ratio ── */

/** sRGB channel (0-255) → linear-light value (IEC 61966-2-1). */
function linearize(channel: number): number {
  const c = channel / 255;
  return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

/** Relative luminance of an sRGB colour (WCAG definition). */
export function relativeLuminance(r: number, g: number, b: number): number {
  return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b);
}

/** WCAG contrast ratio between two relative-luminance values. */
export function contrastRatio(l1: number, l2: number): number {
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

/* ── High-level helpers ── */

/**
 * Given two HSL triplet strings, compute the WCAG contrast ratio
 * and return whether it passes the supplied threshold.
 */
export function checkContrastFromHsl(
  fgHsl: string,
  bgHsl: string,
  threshold: number,
): { ratio: number; passes: boolean } {
  const [fh, fs, fl] = parseHsl(fgHsl);
  const [bh, bs, bl] = parseHsl(bgHsl);
  const fgRgb = hslToRgb(fh, fs, fl);
  const bgRgb = hslToRgb(bh, bs, bl);
  const fgL = relativeLuminance(...fgRgb);
  const bgL = relativeLuminance(...bgRgb);
  const ratio = contrastRatio(fgL, bgL);
  return { ratio: Math.round(ratio * 100) / 100, passes: ratio >= threshold };
}
