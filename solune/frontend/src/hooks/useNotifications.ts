/**
 * useNotifications — surfaces high-signal activity events as notifications.
 * Uses localStorage for read/unread state persistence.
 * Queries the activity feed for pipeline completions/failures, chore triggers, and agent executions.
 */

import { useState, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { activityApi } from '@/services/api';
import { useAuth } from '@/hooks/useAuth';
import type { Notification, ActivityEvent } from '@/types';

const STORAGE_KEY = 'solune-read-notifications';
const HIGH_SIGNAL_TYPES = 'pipeline_run,chore_trigger,agent_execution';

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

function mapEventToNotification(event: ActivityEvent, readIds: Set<string>): Notification {
  let type: Notification['type'] = 'agent';
  if (event.event_type.startsWith('pipeline')) {
    type = 'pipeline';
  } else if (event.event_type.startsWith('chore')) {
    type = 'chore';
  }
  return {
    id: event.id,
    type,
    title: event.summary,
    timestamp: event.created_at,
    read: readIds.has(event.id),
    source: event.entity_type,
  };
}

interface UseNotificationsReturn {
  notifications: Notification[];
  unreadCount: number;
  markAllRead: () => void;
}

export function useNotifications(): UseNotificationsReturn {
  const [readIds, setReadIds] = useState<Set<string>>(() => getReadIds());
  const { user } = useAuth();
  const projectId = user?.selected_project_id;

  const { data } = useQuery({
    queryKey: ['notifications', projectId],
    queryFn: () =>
      activityApi.feed(projectId!, {
        limit: 20,
        event_type: HIGH_SIGNAL_TYPES,
      }),
    enabled: !!projectId,
    staleTime: 30_000,
  });

  const items = data?.items;

  const notifications: Notification[] = useMemo(() => {
    if (!items) return [];
    return items.map((event) => mapEventToNotification(event, readIds));
  }, [items, readIds]);

  const unreadCount = useMemo(
    () => notifications.filter((n) => !n.read).length,
    [notifications],
  );

  const markAllRead = useCallback(() => {
    const allIds = new Set(notifications.map((n) => n.id));
    setReadIds(allIds);
    saveReadIds(allIds);
  }, [notifications]);

  return { notifications, unreadCount, markAllRead };
}
