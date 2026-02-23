/**
 * Tests for the copper background theme design tokens.
 *
 * Validates that the copper color palette is defined as CSS custom properties
 * and that key text-on-background combinations meet WCAG 2.1 AA contrast (≥ 4.5:1).
 */

import { describe, it, expect, beforeAll } from 'vitest';
import fs from 'fs';
import path from 'path';

/* ── helpers ─────────────────────────────────────────────────────────── */

/** Convert a single sRGB channel (0-255) to linear light. */
function sRGBToLinear(c: number): number {
  const s = c / 255;
  return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
}

/** Relative luminance per WCAG 2.1 definition. */
function luminance(hex: string): number {
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return 0.2126 * sRGBToLinear(r) + 0.7152 * sRGBToLinear(g) + 0.0722 * sRGBToLinear(b);
}

/** WCAG contrast ratio between two hex colors. */
function contrastRatio(c1: string, c2: string): number {
  let l1 = luminance(c1);
  let l2 = luminance(c2);
  if (l1 < l2) [l1, l2] = [l2, l1];
  return (l1 + 0.05) / (l2 + 0.05);
}

/* ── CSS parsing ─────────────────────────────────────────────────────── */

let cssContent: string;

beforeAll(() => {
  cssContent = fs.readFileSync(path.resolve(__dirname, 'index.css'), 'utf-8');
});

/** Extract a CSS variable value from a given block of text. */
function extractVar(block: string, varName: string): string | null {
  const re = new RegExp(`${varName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}:\\s*(#[0-9a-fA-F]{3,8})`, 'm');
  const m = block.match(re);
  return m ? m[1] : null;
}

function getRootBlock(): string {
  const m = cssContent.match(/:root\s*\{([^}]+)\}/);
  return m ? m[1] : '';
}

function getDarkBlock(): string {
  const m = cssContent.match(/html\.dark-mode-active\s*\{([^}]+)\}/);
  return m ? m[1] : '';
}

/* ── tests ───────────────────────────────────────────────────────────── */

describe('Copper theme design tokens', () => {
  describe('light mode (:root)', () => {
    it('defines --color-bg-copper as the single source of truth copper token', () => {
      const root = getRootBlock();
      const copper = extractVar(root, '--color-bg-copper');
      expect(copper).toBeTruthy();
    });

    it('sets --color-bg to copper', () => {
      const root = getRootBlock();
      const bg = extractVar(root, '--color-bg');
      expect(bg).toBe('#B87333');
    });

    it('sets --color-bg-secondary to a copper shade', () => {
      const root = getRootBlock();
      const bg2 = extractVar(root, '--color-bg-secondary');
      expect(bg2).toBeTruthy();
      // Should not be white/light gray
      expect(bg2).not.toBe('#ffffff');
      expect(bg2).not.toBe('#f6f8fa');
    });

    it('text on --color-bg meets WCAG AA (≥ 4.5:1)', () => {
      const root = getRootBlock();
      const bg = extractVar(root, '--color-bg')!;
      const text = extractVar(root, '--color-text')!;
      expect(contrastRatio(bg, text)).toBeGreaterThanOrEqual(4.5);
    });

    it('text on --color-bg-secondary meets WCAG AA (≥ 4.5:1)', () => {
      const root = getRootBlock();
      const bg2 = extractVar(root, '--color-bg-secondary')!;
      const text = extractVar(root, '--color-text')!;
      expect(contrastRatio(bg2, text)).toBeGreaterThanOrEqual(4.5);
    });

    it('secondary text on --color-bg meets WCAG AA (≥ 4.5:1)', () => {
      const root = getRootBlock();
      const bg = extractVar(root, '--color-bg')!;
      const text2 = extractVar(root, '--color-text-secondary')!;
      expect(contrastRatio(bg, text2)).toBeGreaterThanOrEqual(4.5);
    });
  });

  describe('dark mode (html.dark-mode-active)', () => {
    it('defines --color-bg-copper dark variant', () => {
      const dark = getDarkBlock();
      const copper = extractVar(dark, '--color-bg-copper');
      expect(copper).toBeTruthy();
    });

    it('sets --color-bg to a dark copper shade', () => {
      const dark = getDarkBlock();
      const bg = extractVar(dark, '--color-bg');
      expect(bg).toBeTruthy();
      // Dark mode background should be darker than light mode copper
      expect(luminance(bg!)).toBeLessThan(luminance('#B87333'));
    });

    it('text on dark --color-bg meets WCAG AA (≥ 4.5:1)', () => {
      const dark = getDarkBlock();
      const bg = extractVar(dark, '--color-bg')!;
      const text = extractVar(dark, '--color-text')!;
      expect(contrastRatio(bg, text)).toBeGreaterThanOrEqual(4.5);
    });

    it('text on dark --color-bg-secondary meets WCAG AA (≥ 4.5:1)', () => {
      const dark = getDarkBlock();
      const bg2 = extractVar(dark, '--color-bg-secondary')!;
      const text = extractVar(dark, '--color-text')!;
      expect(contrastRatio(bg2, text)).toBeGreaterThanOrEqual(4.5);
    });

    it('secondary text on dark --color-bg meets WCAG AA (≥ 4.5:1)', () => {
      const dark = getDarkBlock();
      const bg = extractVar(dark, '--color-bg')!;
      const text2 = extractVar(dark, '--color-text-secondary')!;
      expect(contrastRatio(bg, text2)).toBeGreaterThanOrEqual(4.5);
    });
  });
});
