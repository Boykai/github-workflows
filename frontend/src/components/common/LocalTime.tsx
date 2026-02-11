/**
 * Local time display component that shows the user's current local time.
 */

import { useState, useEffect } from 'react';
import './LocalTime.css';

export function LocalTime() {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    // Calculate milliseconds until the next minute boundary
    const now = new Date();
    const msUntilNextMinute = (60 - now.getSeconds()) * 1000 - now.getMilliseconds();

    let intervalId: ReturnType<typeof setInterval> | null = null;

    // Set initial timeout to align with minute boundary
    const initialTimeout = setTimeout(() => {
      setCurrentTime(new Date());

      // After aligning to minute boundary, update every 60 seconds
      intervalId = setInterval(() => {
        setCurrentTime(new Date());
      }, 60000);
    }, msUntilNextMinute);

    // Cleanup timeout and interval on unmount
    return () => {
      clearTimeout(initialTimeout);
      if (intervalId) clearInterval(intervalId);
    };
  }, []);

  // Format time as HH:mm
  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  };

  // Format full date and timezone for tooltip
  const formatFullDateTime = (date: Date): string => {
    const dateStr = date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return `${dateStr} (${timeZone})`;
  };

  return (
    <div className="local-time" title={formatFullDateTime(currentTime)}>
      <span className="time-icon">🕐</span>
      <span className="time-display">{formatTime(currentTime)}</span>
    </div>
  );
}
