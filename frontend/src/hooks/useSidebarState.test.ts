/**
 * Unit tests for useSidebarState hook — validates sidebar collapse persistence,
 * mobile drawer open/close, and auto-close on route change.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

// Track location fields so we can simulate route changes.
const mockLocation = { pathname: '/', search: '', hash: '', key: 'initial' };

vi.mock('react-router-dom', () => ({
  useLocation: () => mockLocation,
}));

import { useSidebarState } from './useSidebarState';

describe('useSidebarState', () => {
  beforeEach(() => {
    localStorage.clear();
    mockLocation.pathname = '/';
    mockLocation.search = '';
    mockLocation.hash = '';
    mockLocation.key = 'initial';
  });

  describe('isCollapsed', () => {
    it('defaults to false when localStorage is empty', () => {
      const { result } = renderHook(() => useSidebarState());
      expect(result.current.isCollapsed).toBe(false);
    });

    it('reads initial collapsed state from localStorage', () => {
      localStorage.setItem('sidebar-collapsed', 'true');
      const { result } = renderHook(() => useSidebarState());
      expect(result.current.isCollapsed).toBe(true);
    });

    it('toggles collapsed state and persists to localStorage', () => {
      const { result } = renderHook(() => useSidebarState());
      expect(result.current.isCollapsed).toBe(false);

      act(() => {
        result.current.toggle();
      });
      expect(result.current.isCollapsed).toBe(true);
      expect(localStorage.getItem('sidebar-collapsed')).toBe('true');

      act(() => {
        result.current.toggle();
      });
      expect(result.current.isCollapsed).toBe(false);
      expect(localStorage.getItem('sidebar-collapsed')).toBe('false');
    });
  });

  describe('mobile drawer', () => {
    it('starts with mobile drawer closed', () => {
      const { result } = renderHook(() => useSidebarState());
      expect(result.current.isMobileOpen).toBe(false);
    });

    it('opens mobile drawer via openMobile', () => {
      const { result } = renderHook(() => useSidebarState());

      act(() => {
        result.current.openMobile();
      });
      expect(result.current.isMobileOpen).toBe(true);
    });

    it('closes mobile drawer via closeMobile', () => {
      const { result } = renderHook(() => useSidebarState());

      act(() => {
        result.current.openMobile();
      });
      expect(result.current.isMobileOpen).toBe(true);

      act(() => {
        result.current.closeMobile();
      });
      expect(result.current.isMobileOpen).toBe(false);
    });

    it('auto-closes mobile drawer when route changes', () => {
      const { result, rerender } = renderHook(() => useSidebarState());

      act(() => {
        result.current.openMobile();
      });
      expect(result.current.isMobileOpen).toBe(true);

      // Simulate route change
      mockLocation.pathname = '/settings';
      mockLocation.key = 'route-settings';
      rerender();
      expect(result.current.isMobileOpen).toBe(false);
    });

    it('auto-closes mobile drawer when only search or hash changes', () => {
      const { result, rerender } = renderHook(() => useSidebarState());

      act(() => {
        result.current.openMobile();
      });
      expect(result.current.isMobileOpen).toBe(true);

      mockLocation.search = '?tab=advanced';
      mockLocation.hash = '#models';
      mockLocation.key = 'route-settings-query';
      rerender();

      expect(result.current.isMobileOpen).toBe(false);
    });
  });

  describe('callback stability', () => {
    it('returns stable callback references across renders', () => {
      const { result, rerender } = renderHook(() => useSidebarState());
      const firstToggle = result.current.toggle;
      const firstOpenMobile = result.current.openMobile;
      const firstCloseMobile = result.current.closeMobile;

      rerender();

      expect(result.current.toggle).toBe(firstToggle);
      expect(result.current.openMobile).toBe(firstOpenMobile);
      expect(result.current.closeMobile).toBe(firstCloseMobile);
    });
  });
});
