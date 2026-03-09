/**
 * Viewport preset constants for Playwright E2E tests.
 *
 * Defines standard breakpoints for responsive layout testing.
 */

export const VIEWPORTS = {
  mobileSmall: { width: 320, height: 568 },
  mobile: { width: 375, height: 667 },
  mobileLarge: { width: 390, height: 844 },
  tablet: { width: 768, height: 1024 },
  desktopSmall: { width: 1024, height: 768 },
  desktop: { width: 1280, height: 800 },
  desktopLarge: { width: 1440, height: 900 },
} as const;

export type ViewportName = keyof typeof VIEWPORTS;
