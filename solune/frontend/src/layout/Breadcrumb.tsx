/**
 * Breadcrumb — derives breadcrumb segments from the current pathname and NAV_ROUTES.
 */

import { useLocation, Link } from 'react-router-dom';
import { NAV_ROUTES } from '@/constants';
import { ChevronRight } from 'lucide-react';

export function Breadcrumb() {
  const { pathname } = useLocation();

  // Find matching route for the current path
  const matchedRoute = NAV_ROUTES.find((r) =>
    r.path === '/' ? pathname === '/' : pathname.startsWith(r.path)
  );

  // Build breadcrumb segments
  const segments: Array<{ label: string; path: string }> = [{ label: 'Home', path: '/' }];

  if (matchedRoute && matchedRoute.path !== '/') {
    segments.push({ label: matchedRoute.label, path: matchedRoute.path });
  }

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
