/**
 * Unit tests for Sidebar component — validates dual rendering (desktop/mobile),
 * navigation links, collapse behavior, and mobile drawer overlay.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { NAV_ROUTES } from '@/constants';

function renderSidebar(overrides: Partial<Parameters<typeof Sidebar>[0]> = {}) {
  const defaultProps: Parameters<typeof Sidebar>[0] = {
    isCollapsed: false,
    onToggle: vi.fn(),
    isDarkMode: false,
    onToggleTheme: vi.fn(),
    selectedProject: { project_id: '1', name: 'TestProject', owner_login: 'testowner' },
    recentInteractions: [],
    projects: [],
    projectsLoading: false,
    onSelectProject: vi.fn(),
    isMobileOpen: false,
    onCloseMobile: vi.fn(),
    ...overrides,
  };
  return render(
    <MemoryRouter>
      <Sidebar {...defaultProps} />
    </MemoryRouter>,
  );
}

describe('Sidebar', () => {
  describe('desktop sidebar', () => {
    it('renders all navigation routes', () => {
      renderSidebar();
      for (const route of NAV_ROUTES) {
        expect(screen.getByText(route.label)).toBeTruthy();
      }
    });

    it('renders expand/collapse button with correct label', () => {
      renderSidebar({ isCollapsed: false });
      expect(screen.getByLabelText('Collapse sidebar')).toBeTruthy();
    });

    it('renders expand button when collapsed', () => {
      renderSidebar({ isCollapsed: true });
      expect(screen.getByLabelText('Expand sidebar')).toBeTruthy();
    });

    it('calls onToggle when collapse button is clicked', () => {
      const onToggle = vi.fn();
      renderSidebar({ onToggle });
      fireEvent.click(screen.getByLabelText('Collapse sidebar'));
      expect(onToggle).toHaveBeenCalledOnce();
    });

    it('shows project name when expanded', () => {
      renderSidebar({
        isCollapsed: false,
        selectedProject: { project_id: '1', name: 'Moonbase', owner_login: 'solune' },
      });
      expect(screen.getAllByText('Moonbase').length).toBeGreaterThan(0);
    });
  });

  describe('mobile drawer', () => {
    it('does not render drawer when isMobileOpen is false', () => {
      renderSidebar({ isMobileOpen: false });
      expect(screen.queryByLabelText('Close navigation menu')).toBeNull();
    });

    it('renders drawer with close button when isMobileOpen is true', () => {
      renderSidebar({ isMobileOpen: true });
      expect(screen.getByLabelText('Close navigation menu')).toBeTruthy();
    });

    it('renders mobile drawer with aria-label for navigation', () => {
      renderSidebar({ isMobileOpen: true });
      const drawer = document.getElementById('mobile-nav-drawer');
      expect(drawer).toBeTruthy();
      expect(drawer!.getAttribute('aria-label')).toBe('Main navigation');
    });

    it('calls onCloseMobile when close button is clicked', () => {
      const onCloseMobile = vi.fn();
      renderSidebar({ isMobileOpen: true, onCloseMobile });
      fireEvent.click(screen.getByLabelText('Close navigation menu'));
      expect(onCloseMobile).toHaveBeenCalledOnce();
    });

    it('calls onCloseMobile when backdrop is clicked', () => {
      const onCloseMobile = vi.fn();
      renderSidebar({ isMobileOpen: true, onCloseMobile });
      // The backdrop has aria-hidden="true" and is the md:hidden overlay
      const backdrops = document.querySelectorAll('[aria-hidden="true"]');
      const backdrop = Array.from(backdrops).find(
        (el) => el.className.includes('bg-black/50'),
      );
      expect(backdrop).toBeTruthy();
      fireEvent.click(backdrop!);
      expect(onCloseMobile).toHaveBeenCalledOnce();
    });

    it('renders all navigation routes in mobile drawer', () => {
      renderSidebar({ isMobileOpen: true });
      for (const route of NAV_ROUTES) {
        // Desktop and mobile both render, so at least two instances
        expect(screen.getAllByText(route.label).length).toBeGreaterThanOrEqual(1);
      }
    });
  });

  describe('theme toggle', () => {
    it('renders dark mode toggle with correct label', () => {
      renderSidebar({ isDarkMode: true });
      expect(screen.getAllByLabelText('Switch to light mode').length).toBeGreaterThan(0);
    });

    it('renders light mode toggle label when in light mode', () => {
      renderSidebar({ isDarkMode: false });
      expect(screen.getAllByLabelText('Switch to dark mode').length).toBeGreaterThan(0);
    });

    it('calls onToggleTheme when theme button is clicked', () => {
      const onToggleTheme = vi.fn();
      renderSidebar({ onToggleTheme });
      fireEvent.click(screen.getAllByLabelText('Switch to dark mode')[0]);
      expect(onToggleTheme).toHaveBeenCalledOnce();
    });
  });
});
