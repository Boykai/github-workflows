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

export function NotificationBell({ notifications, unreadCount, onMarkAllRead }: NotificationBellProps) {
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
        className="relative p-2 rounded-md hover:bg-muted transition-colors text-muted-foreground"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-primary text-primary-foreground text-[10px] font-bold flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-1 w-80 bg-card border border-border rounded-lg shadow-lg z-50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-border">
            <span className="text-sm font-semibold">Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={onMarkAllRead}
                className="text-xs text-primary hover:text-primary/80 transition-colors"
              >
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-[320px] overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="py-8 text-center">
                <Bell className="w-8 h-8 mx-auto text-muted-foreground/30 mb-2" />
                <p className="text-sm text-muted-foreground">No notifications yet</p>
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`flex items-start gap-3 px-4 py-3 border-b border-border last:border-0 text-sm ${
                    n.read ? 'opacity-60' : ''
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${n.read ? 'bg-transparent' : 'bg-primary'}`} />
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
