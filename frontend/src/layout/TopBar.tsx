/**
 * TopBar — horizontal bar with breadcrumb, notification bell, and user avatar.
 */

import { Breadcrumb } from './Breadcrumb';
import { NotificationBell } from './NotificationBell';
import { LoginButton } from '@/components/auth/LoginButton';
import { RateLimitBar } from './RateLimitBar';
import type { Notification } from '@/types';

interface TopBarProps {
  isDarkMode: boolean;
  onToggleTheme: () => void;
  user?: { login: string; avatar_url?: string };
  notifications: Notification[];
  unreadCount: number;
  onMarkAllRead: () => void;
}

export function TopBar({
  isDarkMode: _isDarkMode,
  onToggleTheme: _onToggleTheme,
  user,
  notifications,
  unreadCount,
  onMarkAllRead,
}: TopBarProps) {
  return (
    <header className="celestial-panel flex h-16 items-center justify-between border-b border-border/70 px-6 backdrop-blur-sm shrink-0">
      <div className="flex items-center gap-3">
        <span className="celestial-sigil hidden h-8 w-8 rounded-full border border-primary/20 text-[10px] text-primary/80 md:inline-flex">
          <span className="relative z-10">✦</span>
        </span>
        <span className="hidden h-8 w-px bg-border/70 md:block" />
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
