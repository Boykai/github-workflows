/**
 * useSidebarState — manages sidebar collapse state with localStorage persistence
 * and mobile drawer open/close state.
 */

import { useState, useCallback, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const STORAGE_KEY = 'sidebar-collapsed';

function loadCollapsed(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'true';
  } catch {
    return false;
  }
}

export function useSidebarState() {
  const [isCollapsed, setIsCollapsed] = useState(loadCollapsed);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const location = useLocation();

  const toggle = useCallback(() => {
    setIsCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(STORAGE_KEY, String(next));
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  const openMobile = useCallback(() => setIsMobileOpen(true), []);
  const closeMobile = useCallback(() => setIsMobileOpen(false), []);

  // Auto-close mobile drawer on route change
  useEffect(() => {
    setIsMobileOpen(false);
  }, [location.pathname]);

  return { isCollapsed, toggle, isMobileOpen, openMobile, closeMobile };
}
