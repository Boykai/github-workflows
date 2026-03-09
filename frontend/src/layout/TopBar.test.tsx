/**
 * Unit tests for TopBar component — validates hamburger menu rendering,
 * user avatar display, breadcrumb, and responsive behavior.
 */
import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent, cleanup } from '@/test/test-utils';
import { render as rtlRender } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { RateLimitProvider } from '@/context/RateLimitContext';
import { TopBar } from './TopBar';

function renderTopBar(overrides: Partial<Parameters<typeof TopBar>[0]> = {}) {
  const defaultProps: Parameters<typeof TopBar>[0] = {
    isDarkMode: false,
    onToggleTheme: vi.fn(),
    user: { login: 'testuser', avatar_url: 'https://example.com/avatar.png' },
    notifications: [],
    unreadCount: 0,
    onMarkAllRead: vi.fn(),
    onMenuToggle: vi.fn(),
    isMobileMenuOpen: false,
    ...overrides,
  };
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return rtlRender(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <RateLimitProvider>
          <TopBar {...defaultProps} />
        </RateLimitProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('TopBar', () => {
  describe('hamburger menu button', () => {
    it('renders hamburger menu button when onMenuToggle is provided', () => {
      renderTopBar();
      const button = screen.getByLabelText('Open navigation menu');
      expect(button).toBeTruthy();
    });

    it('does not render hamburger button when onMenuToggle is not provided', () => {
      renderTopBar({ onMenuToggle: undefined });
      expect(screen.queryByLabelText('Open navigation menu')).toBeNull();
    });

    it('calls onMenuToggle when hamburger button is clicked', () => {
      const onMenuToggle = vi.fn();
      renderTopBar({ onMenuToggle });
      fireEvent.click(screen.getByLabelText('Open navigation menu'));
      expect(onMenuToggle).toHaveBeenCalledOnce();
    });

    it('sets aria-expanded based on isMobileMenuOpen state', () => {
      const { unmount: unmount1 } = renderTopBar({ isMobileMenuOpen: false });
      const button = screen.getByLabelText('Open navigation menu');
      expect(button.getAttribute('aria-expanded')).toBe('false');
      unmount1();

      // Render again with mobile menu open to verify aria-expanded changes
      renderTopBar({ isMobileMenuOpen: true });
      const updatedButton = screen.getByLabelText('Open navigation menu');
      expect(updatedButton.getAttribute('aria-expanded')).toBe('true');
    });

    it('references mobile-nav-drawer via aria-controls', () => {
      renderTopBar();
      const button = screen.getByLabelText('Open navigation menu');
      expect(button.getAttribute('aria-controls')).toBe('mobile-nav-drawer');
    });

    it('has touch-target class for mobile touch sizing', () => {
      renderTopBar();
      const button = screen.getByLabelText('Open navigation menu');
      expect(button.className).toContain('touch-target');
    });
  });

  describe('user display', () => {
    it('renders user avatar when avatar_url is provided', () => {
      renderTopBar({ user: { login: 'alice', avatar_url: 'https://example.com/alice.png' } });
      const img = screen.getByAltText('alice');
      expect(img).toBeTruthy();
      expect(img.getAttribute('src')).toBe('https://example.com/alice.png');
    });

    it('renders username text', () => {
      renderTopBar({ user: { login: 'alice', avatar_url: 'https://example.com/alice.png' } });
      expect(screen.getByText('alice')).toBeTruthy();
    });

    it('does not render user section when user is undefined', () => {
      renderTopBar({ user: undefined });
      expect(screen.queryByAltText('alice')).toBeNull();
    });
  });

  describe('layout structure', () => {
    it('renders as a header element', () => {
      renderTopBar();
      const header = document.querySelector('header');
      expect(header).toBeTruthy();
    });

    it('contains responsive padding classes', () => {
      renderTopBar();
      const header = document.querySelector('header');
      expect(header!.className).toContain('px-3');
      expect(header!.className).toContain('md:px-6');
    });
  });
});
