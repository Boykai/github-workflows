/**
 * useNotifications — aggregates agent workflow events and chore completion with read tracking.
 * Uses localStorage for read/unread state persistence.
 */

import { useState, useCallback, useMemo } from 'react';
import type { Notification } from '@/types';

const STORAGE_KEY = 'solune-read-notifications';

function getReadIds(): Set<string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? new Set(JSON.parse(raw)) : new Set();
  } catch {
    return new Set();
  }
}

function saveReadIds(ids: Set<string>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...ids]));
}

interface UseNotificationsReturn {
  notifications: Notification[];
  unreadCount: number;
  markAllRead: () => void;
}

export function useNotifications(): UseNotificationsReturn {
  const [readIds, setReadIds] = useState<Set<string>>(() => getReadIds());

  // Placeholder notifications — in full implementation these would come from
  // useWorkflow events and useChoresList completion events
  const notifications: Notification[] = useMemo(() => [], []);

  const unreadCount = useMemo(
    () => notifications.filter((n) => !readIds.has(n.id)).length,
    [notifications, readIds]
  );

  const markAllRead = useCallback(() => {
    const allIds = new Set(notifications.map((n) => n.id));
    setReadIds(allIds);
    saveReadIds(allIds);
  }, [notifications]);

  return { notifications, unreadCount, markAllRead };
}
