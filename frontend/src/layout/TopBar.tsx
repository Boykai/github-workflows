/**
 * TopBar — horizontal bar with breadcrumb, theme toggle, notification bell, and user avatar.
 */

import { Sun, Moon } from 'lucide-react';
import { Breadcrumb } from './Breadcrumb';
import { NotificationBell } from './NotificationBell';
import { LoginButton } from '@/components/auth/LoginButton';
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
  isDarkMode,
  onToggleTheme,
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
        <div className="hidden items-center gap-2 rounded-full border border-border/70 bg-background/45 px-3 py-1.5 md:flex">
          <span className="h-2 w-2 rounded-full bg-primary shadow-sm" />
          <span className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">Solar focus</span>
        </div>

        {/* Theme toggle */}
        <button
          onClick={onToggleTheme}
          className="flex h-10 w-10 items-center justify-center rounded-full border border-border/70 bg-background/50 text-muted-foreground transition-all hover:border-primary/30 hover:bg-accent/60 hover:text-foreground"
          aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

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
