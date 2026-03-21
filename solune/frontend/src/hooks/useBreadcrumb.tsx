/**
 * BreadcrumbContext — React Context for dynamic breadcrumb labels.
 *
 * Holds a Map<string, string> of path→label overrides that page components
 * can set/remove. The Breadcrumb component reads these labels to display
 * human-readable names instead of raw URL slugs.
 */

import { createContext, useContext, useCallback, useState, type ReactNode } from 'react';

interface BreadcrumbContextValue {
  labels: Map<string, string>;
  setLabel: (path: string, label: string) => void;
  removeLabel: (path: string) => void;
}

const BreadcrumbContext = createContext<BreadcrumbContextValue | null>(null);

export function BreadcrumbProvider({ children }: { children: ReactNode }) {
  const [labels, setLabels] = useState<Map<string, string>>(() => new Map());

  const setLabel = useCallback((path: string, label: string) => {
    setLabels((prev) => {
      const next = new Map(prev);
      next.set(path, label);
      return next;
    });
  }, []);

  const removeLabel = useCallback((path: string) => {
    setLabels((prev) => {
      const next = new Map(prev);
      next.delete(path);
      return next;
    });
  }, []);

  return (
    <BreadcrumbContext.Provider value={{ labels, setLabel, removeLabel }}>
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
export function useBreadcrumbLabels(): Map<string, string> {
  const ctx = useContext(BreadcrumbContext);
  if (!ctx) throw new Error('useBreadcrumbLabels must be used within BreadcrumbProvider');
  return ctx.labels;
}
