/**
 * TopBar — horizontal bar with breadcrumb, notification bell, and user avatar.
 */

import { HelpCircle, Search } from '@/lib/icons';
import { NavLink } from 'react-router-dom';
import { Breadcrumb } from './Breadcrumb';
import { NotificationBell } from './NotificationBell';
import { LoginButton } from '@/components/auth/LoginButton';
import { RateLimitBar } from './RateLimitBar';
import { cn } from '@/lib/utils';
import type { Notification } from '@/types';

interface TopBarProps {
  isDarkMode: boolean;
  onToggleTheme: () => void;
  user?: { login: string; avatar_url?: string };
  notifications: Notification[];
  unreadCount: number;
  onMarkAllRead: () => void;
}

const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform);

function SearchTrigger() {
  return (
    <button
      type="button"
      aria-label="Open command palette"
      title={`Search (${isMac ? '⌘' : 'Ctrl+'}K)`}
      className="celestial-focus flex h-9 items-center gap-2 rounded-full border border-transparent px-3 text-muted-foreground transition-colors hover:border-border hover:bg-primary/10 hover:text-foreground"
      onClick={() => window.dispatchEvent(new CustomEvent('solune:open-command-palette'))}
    >
      <Search className="h-4 w-4" />
      <span className="hidden text-xs md:inline">Search</span>
      <kbd className="hidden sm:inline-flex min-w-[1.25rem] items-center justify-center rounded border border-border bg-muted px-1 py-0.5 text-[10px] font-medium text-muted-foreground">
        {isMac ? '⌘' : '⌃'}K
      </kbd>
    </button>
  );
}

function HelpButton() {
  return (
    <NavLink
      to="/help"
      data-tour-step="help-link"
      aria-label="Help"
      className={({ isActive }) =>
        cn(
          'celestial-focus flex h-9 w-9 items-center justify-center rounded-full border transition-colors',
          isActive
            ? 'border-primary/30 bg-primary/14 text-primary'
            : 'border-transparent text-muted-foreground hover:border-border hover:bg-primary/10 hover:text-foreground',
        )
      }
    >
      <HelpCircle className="h-5 w-5" />
    </NavLink>
  );
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
      <div className="flex items-center gap-2">
        <Breadcrumb />
      </div>

      <div className="flex items-center gap-3">
        <RateLimitBar />

        {/* Search / Command Palette trigger */}
        <SearchTrigger />

        {/* Help */}
        <HelpButton />

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
