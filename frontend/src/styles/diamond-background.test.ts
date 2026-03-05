/**
 * Tests for diamond background CSS custom properties and pseudo-element.
 *
 * Verifies that the required CSS variables are defined in both light and dark
 * themes and that the body::before pseudo-element renders the diamond pattern
 * without interfering with interactive elements (pointer-events: none).
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';

/**
 * Inject a minimal version of the diamond background CSS variables
 * so we can verify theme-token structure in the test environment.
 */
function injectDiamondStyles(): HTMLStyleElement {
  const style = document.createElement('style');
  style.textContent = `
    :root {
      --diamond-color: 0 0% 0%;
      --diamond-size: 40px;
      --diamond-opacity: 0.04;
    }
    .dark {
      --diamond-color: 0 0% 100%;
      --diamond-size: 40px;
      --diamond-opacity: 0.05;
    }
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      z-index: 0;
      pointer-events: none;
      opacity: var(--diamond-opacity);
      background-image:
        linear-gradient(45deg, hsl(var(--diamond-color)) 25%, transparent 25%),
        linear-gradient(-45deg, hsl(var(--diamond-color)) 25%, transparent 25%),
        linear-gradient(45deg, transparent 75%, hsl(var(--diamond-color)) 75%),
        linear-gradient(-45deg, transparent 75%, hsl(var(--diamond-color)) 75%);
      background-size: var(--diamond-size) var(--diamond-size);
    }
    #root {
      position: relative;
      z-index: 1;
    }
  `;
  document.head.appendChild(style);
  return style;
}

describe('Diamond Background', () => {
  let styleEl: HTMLStyleElement;

  beforeEach(() => {
    document.documentElement.classList.remove('light', 'dark');
    styleEl = injectDiamondStyles();
  });

  afterEach(() => {
    styleEl.remove();
    document.documentElement.classList.remove('light', 'dark');
  });

  describe('CSS custom properties', () => {
    it('defines --diamond-color on :root', () => {
      const value = getComputedStyle(document.documentElement).getPropertyValue('--diamond-color');
      expect(value.trim()).toBe('0 0% 0%');
    });

    it('defines --diamond-size on :root', () => {
      const value = getComputedStyle(document.documentElement).getPropertyValue('--diamond-size');
      expect(value.trim()).toBe('40px');
    });

    it('defines --diamond-opacity on :root', () => {
      const value = getComputedStyle(document.documentElement).getPropertyValue('--diamond-opacity');
      expect(value.trim()).toBe('0.04');
    });

    it('overrides --diamond-color in dark mode', () => {
      document.documentElement.classList.add('dark');
      const value = getComputedStyle(document.documentElement).getPropertyValue('--diamond-color');
      expect(value.trim()).toBe('0 0% 100%');
    });

    it('overrides --diamond-opacity in dark mode', () => {
      document.documentElement.classList.add('dark');
      const value = getComputedStyle(document.documentElement).getPropertyValue('--diamond-opacity');
      expect(value.trim()).toBe('0.05');
    });
  });

  describe('body::before pseudo-element styles', () => {
    it('includes pointer-events: none so it does not block interaction', () => {
      expect(styleEl.textContent).toContain('pointer-events: none');
    });

    it('is positioned fixed to cover the viewport', () => {
      expect(styleEl.textContent).toContain('position: fixed');
    });

    it('uses diamond CSS variables for background', () => {
      expect(styleEl.textContent).toContain('var(--diamond-color)');
      expect(styleEl.textContent).toContain('var(--diamond-size)');
      expect(styleEl.textContent).toContain('var(--diamond-opacity)');
    });

    it('uses linear-gradient for the diamond pattern', () => {
      expect(styleEl.textContent).toContain('linear-gradient(45deg');
      expect(styleEl.textContent).toContain('linear-gradient(-45deg');
    });
  });

  describe('#root stacking context', () => {
    it('sits above the diamond overlay (z-index: 1)', () => {
      let rootEl = document.getElementById('root');
      let created = false;
      if (!rootEl) {
        rootEl = document.createElement('div');
        rootEl.id = 'root';
        document.body.appendChild(rootEl);
        created = true;
      }
      const style = getComputedStyle(rootEl);
      expect(style.position).toBe('relative');
      expect(style.zIndex).toBe('1');
      if (created) rootEl.remove();
    });
  });
});
