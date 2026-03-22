/**
 * NotificationBell — bell icon with count badge and dropdown listing recent notifications.
 */

import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Bell } from '@/lib/icons';
import { useNavigate } from 'react-router-dom';
import type { Notification } from '@/types';
import { cn } from '@/lib/utils';

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
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);

  const [prevIsOpen, setPrevIsOpen] = useState(isOpen);
  if (isOpen !== prevIsOpen) {
    setPrevIsOpen(isOpen);
    if (!isOpen) setPosition(null);
  }

  useEffect(() => {
    if (!isOpen) return;

    const updatePosition = () => {
      if (!buttonRef.current) return;
      const rect = buttonRef.current.getBoundingClientRect();
      const panelWidth = 320;
      const margin = 12;
      const maxLeft = Math.max(window.innerWidth - panelWidth - margin, margin);

      setPosition({
        top: rect.bottom + 8,
        left: Math.min(Math.max(rect.right - panelWidth, margin), maxLeft),
      });
    };

    updatePosition();

    // Throttle scroll/resize recalculations to once per animation frame to
    // prevent layout thrashing from repeated getBoundingClientRect calls.
    let rafId = 0;
    const scheduleUpdate = () => {
      if (rafId) return;
      rafId = requestAnimationFrame(() => {
        rafId = 0;
        updatePosition();
      });
    };

    window.addEventListener('resize', scheduleUpdate);
    window.addEventListener('scroll', scheduleUpdate, { capture: true, passive: true });
    return () => {
      window.removeEventListener('resize', scheduleUpdate);
      window.removeEventListener('scroll', scheduleUpdate, { capture: true });
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, [isOpen]);

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

  useEffect(() => {
    if (!isOpen) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setIsOpen(false);
        buttonRef.current?.focus();
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  const dropdown =
    isOpen && position
      ? createPortal(
          <div
            className="celestial-panel fixed z-[10000] w-80 overflow-hidden rounded-[1.25rem] border border-border/80 shadow-lg backdrop-blur-md"
            style={{ top: position.top, left: position.left }}
          >
            <div className="flex items-center justify-between border-b border-border/70 bg-background/25 px-4 py-3">
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
                    className={cn(
                      'flex items-start gap-3 border-b border-border/60 px-4 py-3 text-sm transition-colors last:border-0 hover:bg-background/20',
                      n.read ? 'opacity-60' : ''
                    )}
                  >
                    <span
                      className={cn(
                        'w-2 h-2 rounded-full mt-1.5 shrink-0',
                        n.read ? 'bg-transparent' : 'bg-primary'
                      )}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-foreground truncate">{n.title}</p>
                      {n.source && (
                        <p className="text-xs text-muted-foreground mt-0.5">{n.source}</p>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="border-t border-border/70 px-4 py-2 text-center">
              <button
                type="button"
                className="text-xs font-medium text-primary hover:text-foreground transition-colors"
                onClick={() => {
                  setIsOpen(false);
                  navigate('/activity');
                }}
              >
                View all activity
              </button>
            </div>
          </div>,
          document.body
        )
      : null;

  return (
    <div ref={ref} className="relative">
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className="celestial-focus relative rounded-full border border-transparent p-2 text-muted-foreground transition-all hover:border-border hover:bg-primary/10 hover:text-foreground focus-visible:outline-none"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground shadow-sm celestial-pulse-glow">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {dropdown}
    </div>
  );
}
