/**
 * DateTimeDisplay component
 * Displays current date and time that updates every second
 */
import { useEffect, useState } from 'react';

export function DateTimeDisplay() {
  const [dateTime, setDateTime] = useState(new Date());

  useEffect(() => {
    // Update time every second
    const intervalId = setInterval(() => {
      setDateTime(new Date());
    }, 1000);

    // Cleanup interval on unmount
    return () => clearInterval(intervalId);
  }, []);

  // Format date as YYYY-MM-DD
  const formatDate = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Format time as HH:mm:ss
  const formatTime = (date: Date): string => {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  };

  const formattedDate = formatDate(dateTime);
  const formattedTime = formatTime(dateTime);

  return (
    <div className="datetime-display" aria-live="polite">
      <time 
        dateTime={dateTime.toISOString()}
        aria-label={`Current date: ${formattedDate}, Current time: ${formattedTime}`}
      >
        <span className="datetime-date" aria-label="Date">
          {formattedDate}
        </span>
        <span className="datetime-separator" aria-hidden="true"> | </span>
        <span className="datetime-time" aria-label="Time">
          {formattedTime}
        </span>
      </time>
    </div>
  );
}
