import { describe, it, expect } from 'vitest';
import {
  parseHsl,
  hslToRgb,
  relativeLuminance,
  contrastRatio,
  checkContrastFromHsl,
} from './themeAudit';

describe('themeAudit', () => {
  describe('parseHsl', () => {
    it('parses a space-separated HSL string with percentage signs', () => {
      expect(parseHsl('41 82% 95%')).toEqual([41, 82, 95]);
    });

    it('parses a string without percentage signs', () => {
      expect(parseHsl('0 0 100')).toEqual([0, 0, 100]);
    });

    it('throws on malformed input', () => {
      expect(() => parseHsl('red')).toThrow();
    });
  });

  describe('hslToRgb', () => {
    it('converts pure white (0, 0, 100) → [255, 255, 255]', () => {
      expect(hslToRgb(0, 0, 100)).toEqual([255, 255, 255]);
    });

    it('converts pure black (0, 0, 0) → [0, 0, 0]', () => {
      expect(hslToRgb(0, 0, 0)).toEqual([0, 0, 0]);
    });

    it('converts a warm gold HSL value', () => {
      const [r, , b] = hslToRgb(42, 90, 48);
      // Gold-like colour — mostly in the warm range
      expect(r).toBeGreaterThan(200);
      expect(b).toBeLessThan(50);
    });
  });

  describe('relativeLuminance', () => {
    it('returns ~1 for white', () => {
      expect(relativeLuminance(255, 255, 255)).toBeCloseTo(1, 2);
    });

    it('returns ~0 for black', () => {
      expect(relativeLuminance(0, 0, 0)).toBeCloseTo(0, 2);
    });
  });

  describe('contrastRatio', () => {
    it('returns 21:1 for black-on-white', () => {
      const l1 = relativeLuminance(255, 255, 255);
      const l2 = relativeLuminance(0, 0, 0);
      expect(contrastRatio(l1, l2)).toBeCloseTo(21, 0);
    });

    it('returns 1:1 for same colour', () => {
      const l = relativeLuminance(128, 128, 128);
      expect(contrastRatio(l, l)).toBeCloseTo(1, 2);
    });
  });

  describe('checkContrastFromHsl', () => {
    it('passes for high-contrast pair (foreground on background)', () => {
      const result = checkContrastFromHsl('228 24% 16%', '41 82% 95%', 4.5);
      expect(result.passes).toBe(true);
      expect(result.ratio).toBeGreaterThan(10);
    });

    it('fails for low-contrast pair', () => {
      // Two very light colours
      const result = checkContrastFromHsl('40 80% 90%', '41 82% 95%', 4.5);
      expect(result.passes).toBe(false);
    });

    it('detects primary-on-background passes 3:1 after audit fix', () => {
      // Updated primary (42 90% 38%) on background (41 82% 95%)
      const result = checkContrastFromHsl('42 90% 38%', '41 82% 95%', 3.0);
      expect(result.passes).toBe(true);
    });

    it('detects border-on-card passes 3:1 after audit fix', () => {
      // Updated border (37 36% 49%) on card (40 88% 97%)
      const result = checkContrastFromHsl('37 36% 49%', '40 88% 97%', 3.0);
      expect(result.passes).toBe(true);
    });
  });
});
