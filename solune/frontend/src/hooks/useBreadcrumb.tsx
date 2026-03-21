/**
 * BreadcrumbContext — React Context for dynamic breadcrumb labels.
 *
 * Holds a Map<string, string> of path→label overrides that page components
 * can set/remove. The Breadcrumb component reads these labels to display
 * human-readable names instead of raw URL slugs.
 */

import { createContext, useContext, useCallback, useState, useMemo, type ReactNode } from 'react';

interface BreadcrumbContextValue {
  labels: ReadonlyMap<string, string>;
  setLabel: (path: string, label: string) => void;
  removeLabel: (path: string) => void;
}

const BreadcrumbContext = createContext<BreadcrumbContextValue | null>(null);

/** Strip trailing slashes to match buildBreadcrumbSegments normalization. */
function normalizePath(path: string): string {
  return path.replace(/\/+$/, '') || '/';
}

export function BreadcrumbProvider({ children }: { children: ReactNode }) {
  const [labels, setLabels] = useState<Map<string, string>>(() => new Map());

  const setLabel = useCallback((path: string, label: string) => {
    const normalized = normalizePath(path);
    setLabels((prev) => {
      const next = new Map(prev);
      next.set(normalized, label);
      return next;
    });
  }, []);

  const removeLabel = useCallback((path: string) => {
    const normalized = normalizePath(path);
    setLabels((prev) => {
      const next = new Map(prev);
      next.delete(normalized);
      return next;
    });
  }, []);

  const value = useMemo(
    () => ({ labels, setLabel, removeLabel }),
    [labels, setLabel, removeLabel],
  );

  return (
    <BreadcrumbContext.Provider value={value}>
      {children}
    </BreadcrumbContext.Provider>
  );
}

/** Hook for page components to register/unregister breadcrumb labels. */
export function useBreadcrumb() {
  const ctx = useContext(BreadcrumbContext);
  if (!ctx) throw new Error('useBreadcrumb must be used within BreadcrumbProvider');
  return { setLabel: ctx.setLabel, removeLabel: ctx.removeLabel };
}

/** Hook for the Breadcrumb component to read label overrides. */
export function useBreadcrumbLabels(): ReadonlyMap<string, string> {
  const ctx = useContext(BreadcrumbContext);
  if (!ctx) throw new Error('useBreadcrumbLabels must be used within BreadcrumbProvider');
  return ctx.labels;
}
