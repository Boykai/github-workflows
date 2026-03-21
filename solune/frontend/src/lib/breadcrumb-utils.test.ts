import { describe, it, expect } from 'vitest';
import { toTitleCase, buildBreadcrumbSegments, type BreadcrumbSegment } from './breadcrumb-utils';

describe('toTitleCase', () => {
  it('converts hyphenated slugs to title case', () => {
    expect(toTitleCase('my-cool-app')).toBe('My Cool App');
  });

  it('converts underscored slugs to title case', () => {
    expect(toTitleCase('user_profile')).toBe('User Profile');
  });

  it('capitalizes single words', () => {
    expect(toTitleCase('settings')).toBe('Settings');
  });

  it('handles mixed hyphens and underscores', () => {
    expect(toTitleCase('my-cool_app')).toBe('My Cool App');
  });

  it('returns empty string for empty input', () => {
    expect(toTitleCase('')).toBe('');
  });
});

describe('buildBreadcrumbSegments', () => {
  const navRoutes = [
    { path: '/', label: 'App' },
    { path: '/projects', label: 'Projects' },
    { path: '/apps', label: 'Apps' },
    { path: '/settings', label: 'Settings' },
    { path: '/tools', label: 'Tools' },
  ];

  it('returns only Home for root path', () => {
    const result = buildBreadcrumbSegments('/', navRoutes, new Map());
    expect(result).toEqual<BreadcrumbSegment[]>([{ label: 'Home', path: '/' }]);
  });

  it('returns Home + route label for a single-segment known route', () => {
    const result = buildBreadcrumbSegments('/apps', navRoutes, new Map());
    expect(result).toEqual<BreadcrumbSegment[]>([
      { label: 'Home', path: '/' },
      { label: 'Apps', path: '/apps' },
    ]);
  });

  it('returns Home + route label + title-cased slug for a two-segment path', () => {
    const result = buildBreadcrumbSegments('/apps/my-cool-app', navRoutes, new Map());
    expect(result).toEqual<BreadcrumbSegment[]>([
      { label: 'Home', path: '/' },
      { label: 'Apps', path: '/apps' },
      { label: 'My Cool App', path: '/apps/my-cool-app' },
    ]);
  });

  it('uses context overrides over NAV_ROUTES and title-case', () => {
    const overrides = new Map([
      ['/apps', 'Applications'],
      ['/apps/my-cool-app', 'My Awesome App'],
    ]);
    const result = buildBreadcrumbSegments('/apps/my-cool-app', navRoutes, overrides);
    expect(result).toEqual<BreadcrumbSegment[]>([
      { label: 'Home', path: '/' },
      { label: 'Applications', path: '/apps' },
      { label: 'My Awesome App', path: '/apps/my-cool-app' },
    ]);
  });

  it('handles three-segment paths', () => {
    const result = buildBreadcrumbSegments('/apps/my-app/settings', navRoutes, new Map());
    expect(result).toEqual<BreadcrumbSegment[]>([
      { label: 'Home', path: '/' },
      { label: 'Apps', path: '/apps' },
      { label: 'My App', path: '/apps/my-app' },
      { label: 'Settings', path: '/apps/my-app/settings' },
    ]);
  });

  it('handles four-segment paths', () => {
    const result = buildBreadcrumbSegments(
      '/apps/my-app/settings/notifications',
      navRoutes,
      new Map(),
    );
    expect(result).toHaveLength(5);
    expect(result[4]).toEqual({ label: 'Notifications', path: '/apps/my-app/settings/notifications' });
  });

  it('normalizes trailing slashes', () => {
    const withSlash = buildBreadcrumbSegments('/apps/', navRoutes, new Map());
    const withoutSlash = buildBreadcrumbSegments('/apps', navRoutes, new Map());
    expect(withSlash).toEqual(withoutSlash);
  });

  it('normalizes multiple trailing slashes', () => {
    const result = buildBreadcrumbSegments('/apps///', navRoutes, new Map());
    const expected = buildBreadcrumbSegments('/apps', navRoutes, new Map());
    expect(result).toEqual(expected);
  });

  it('handles unknown single-segment routes with title-case fallback', () => {
    const result = buildBreadcrumbSegments('/unknown-page', navRoutes, new Map());
    expect(result).toEqual<BreadcrumbSegment[]>([
      { label: 'Home', path: '/' },
      { label: 'Unknown Page', path: '/unknown-page' },
    ]);
  });

  it('resolves all 9 NAV_ROUTES entries by exact path match', () => {
    const fullNavRoutes = [
      { path: '/', label: 'App' },
      { path: '/projects', label: 'Projects' },
      { path: '/pipeline', label: 'Agents Pipelines' },
      { path: '/agents', label: 'Agents' },
      { path: '/tools', label: 'Tools' },
      { path: '/chores', label: 'Chores' },
      { path: '/apps', label: 'Apps' },
      { path: '/activity', label: 'Activity' },
      { path: '/settings', label: 'Settings' },
    ];

    for (const route of fullNavRoutes) {
      if (route.path === '/') continue;
      const result = buildBreadcrumbSegments(route.path, fullNavRoutes, new Map());
      expect(result[1]).toEqual({ label: route.label, path: route.path });
    }
  });

  it('accepts empty-string overrides without falling through', () => {
    const overrides = new Map([['/apps', '']]);
    const result = buildBreadcrumbSegments('/apps', navRoutes, overrides);
    expect(result).toEqual<BreadcrumbSegment[]>([
      { label: 'Home', path: '/' },
      { label: '', path: '/apps' },
    ]);
  });

  it('decodes URI-encoded segments in the title-case fallback', () => {
    const result = buildBreadcrumbSegments('/apps/my%20cool%20app', navRoutes, new Map());
    // decodeURIComponent turns 'my%20cool%20app' into 'my cool app';
    // toTitleCase splits on hyphens/underscores only, so the label is 'My cool app'
    expect(result[2]).toEqual({ label: 'My cool app', path: '/apps/my%20cool%20app' });
  });
});
