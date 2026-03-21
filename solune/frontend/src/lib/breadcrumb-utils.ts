/**
 * Breadcrumb utility functions — pure functions for breadcrumb segment building.
 * No React dependencies; suitable for unit testing.
 */

export interface BreadcrumbSegment {
  label: string;
  path: string;
}

/**
 * Convert a URL slug to title case.
 * Splits on hyphens and underscores, capitalizes each word, joins with spaces.
 *
 * @example toTitleCase('my-cool-app')  → 'My Cool App'
 * @example toTitleCase('user_profile') → 'User Profile'
 */
export function toTitleCase(slug: string): string {
  if (!slug) return '';
  return slug
    .split(/[-_]/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Build breadcrumb segments from a pathname.
 *
 * Always starts with "Home" (path `/`). Splits the pathname into segments
 * and resolves each label via three-tier resolution:
 *   1. Context overrides (`labelOverrides` Map)
 *   2. NAV_ROUTES exact match
 *   3. Title-case fallback
 *
 * Trailing slashes are normalized so `/apps/` and `/apps` produce identical output.
 */
export function buildBreadcrumbSegments(
  pathname: string,
  navRoutes: ReadonlyArray<{ path: string; label: string }>,
  labelOverrides: ReadonlyMap<string, string>,
): BreadcrumbSegment[] {
  const segments: BreadcrumbSegment[] = [{ label: 'Home', path: '/' }];

  // Normalize: strip trailing slashes
  const normalized = pathname.replace(/\/+$/, '') || '/';
  if (normalized === '/') return segments;

  const parts = normalized.split('/').filter(Boolean);

  for (let i = 0; i < parts.length; i++) {
    const cumulativePath = '/' + parts.slice(0, i + 1).join('/');

    // 1. Check context overrides
    const override = labelOverrides.get(cumulativePath);
    if (override !== undefined) {
      segments.push({ label: override, path: cumulativePath });
      continue;
    }

    // 2. Check NAV_ROUTES (exact path match)
    const route = navRoutes.find((r) => r.path === cumulativePath);
    if (route) {
      segments.push({ label: route.label, path: cumulativePath });
      continue;
    }

    // 3. Title-case fallback (decode URI-encoded segments first)
    let decodedSegment = parts[i];
    try {
      decodedSegment = decodeURIComponent(parts[i]);
    } catch {
      // If decoding fails (malformed URI component), fall back to the raw segment.
    }
    segments.push({ label: toTitleCase(decodedSegment), path: cumulativePath });
  }

  return segments;
}
