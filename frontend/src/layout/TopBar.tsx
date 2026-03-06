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
    <header className="flex items-center justify-between h-14 px-6 bg-card border-b border-border shrink-0">
      <Breadcrumb />

      <div className="flex items-center gap-3">
        {/* Theme toggle */}
        <button
          onClick={onToggleTheme}
          className="p-2 rounded-md hover:bg-muted transition-colors text-muted-foreground"
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
          <div className="flex items-center gap-2">
            {user.avatar_url && (
              <img
                src={user.avatar_url}
                alt={user.login}
                className="w-7 h-7 rounded-full border border-border"
                width={28}
                height={28}
              />
            )}
          </div>
        )}
        <LoginButton />
      </div>
    </header>
  );
}
