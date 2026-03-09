/**
 * TopBar — horizontal bar with breadcrumb, notification bell, and user avatar.
 */

import { Breadcrumb } from './Breadcrumb';
import { NotificationBell } from './NotificationBell';
import { LoginButton } from '@/components/auth/LoginButton';
import { RateLimitBar } from './RateLimitBar';
import { Menu } from 'lucide-react';
import type { Notification } from '@/types';

interface TopBarProps {
  isDarkMode: boolean;
  onToggleTheme: () => void;
  user?: { login: string; avatar_url?: string };
  notifications: Notification[];
  unreadCount: number;
  onMarkAllRead: () => void;
  onMenuToggle?: () => void;
  isMobileMenuOpen?: boolean;
}

export function TopBar({
  isDarkMode: _isDarkMode,
  onToggleTheme: _onToggleTheme,
  user,
  notifications,
  unreadCount,
  onMarkAllRead,
  onMenuToggle,
  isMobileMenuOpen,
}: TopBarProps) {
  return (
    <header className="celestial-panel flex h-16 items-center justify-between border-b border-border/70 px-3 md:px-6 backdrop-blur-sm shrink-0">
      <div className="flex items-center gap-2">
        {onMenuToggle && (
          <button
            type="button"
            onClick={onMenuToggle}
            className="touch-target inline-flex items-center justify-center rounded-full p-2 text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground md:hidden"
            aria-label={isMobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={isMobileMenuOpen ?? false}
            aria-controls="mobile-nav-drawer"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}
        <Breadcrumb />
      </div>

      <div className="flex items-center gap-3">
        <RateLimitBar />

        {/* Notification Bell */}
        <NotificationBell
          notifications={notifications}
          unreadCount={unreadCount}
          onMarkAllRead={onMarkAllRead}
        />

        {/* User avatar & logout */}
        {user && (
          <div className="flex items-center gap-2 rounded-full border border-border/70 bg-background/50 px-2 py-1">
            {user.avatar_url && (
              <img
                src={user.avatar_url}
                alt={user.login}
                className="h-7 w-7 rounded-full border border-primary/20"
                width={28}
                height={28}
              />
            )}
            <span className="hidden pr-1 text-xs uppercase tracking-[0.18em] text-muted-foreground md:block">
              {user.login}
            </span>
          </div>
        )}
        <LoginButton authenticatedDisplay="action-only" />
      </div>
    </header>
  );
}
