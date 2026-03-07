/**
 * NotificationBell — bell icon with count badge and dropdown listing recent notifications.
 */

import { useState, useRef, useEffect } from 'react';
import { Bell } from 'lucide-react';
import type { Notification } from '@/types';

interface NotificationBellProps {
  notifications: Notification[];
  unreadCount: number;
  onMarkAllRead: () => void;
}

export function NotificationBell({
  notifications,
  unreadCount,
  onMarkAllRead,
}: NotificationBellProps) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [isOpen]);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative rounded-full border border-transparent p-2 text-muted-foreground transition-all hover:border-border hover:bg-accent/70 hover:text-foreground"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground shadow-sm">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="celestial-panel absolute right-0 top-full z-50 mt-2 w-80 overflow-hidden rounded-[1.25rem] border border-border/80 shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-border/70 px-4 py-3">
            <span className="text-sm font-semibold">Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={onMarkAllRead}
                className="text-xs text-primary transition-colors hover:text-foreground"
              >
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-[320px] overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="py-10 text-center">
                <Bell className="mx-auto mb-3 h-8 w-8 text-primary/35" />
                <p className="text-sm text-muted-foreground">No notifications yet</p>
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`flex items-start gap-3 border-b border-border/60 px-4 py-3 text-sm last:border-0 ${
                    n.read ? 'opacity-60' : ''
                  }`}
                >
                  <span
                    className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${n.read ? 'bg-transparent' : 'bg-primary'}`}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-foreground truncate">{n.title}</p>
                    {n.source && <p className="text-xs text-muted-foreground mt-0.5">{n.source}</p>}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
