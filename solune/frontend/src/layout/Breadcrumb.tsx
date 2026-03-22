/**
 * Breadcrumb — derives breadcrumb segments from the current pathname, NAV_ROUTES,
 * and dynamic label overrides provided via BreadcrumbContext.
 */

import { useLocation, Link } from 'react-router-dom';
import { NAV_ROUTES } from '@/constants';
import { ChevronRight } from '@/lib/icons';
import { useBreadcrumbLabels } from '@/hooks/useBreadcrumb';
import { buildBreadcrumbSegments } from '@/lib/breadcrumb-utils';

export function Breadcrumb() {
  const { pathname } = useLocation();
  const labelOverrides = useBreadcrumbLabels();
  const segments = buildBreadcrumbSegments(pathname, NAV_ROUTES, labelOverrides);

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm text-muted-foreground">
      {segments.map((segment, i) => (
        <span key={segment.path} className="flex items-center gap-1">
          {i > 0 && <ChevronRight className="w-3.5 h-3.5 text-primary/60" />}
          {i < segments.length - 1 ? (
            <Link to={segment.path} className="transition-colors hover:text-primary">
              {segment.label}
            </Link>
          ) : (
            <span className="font-medium tracking-wide text-foreground">{segment.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
