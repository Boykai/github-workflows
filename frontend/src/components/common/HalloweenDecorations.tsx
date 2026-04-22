/**
 * Halloween decorations overlay component.
 * Renders animated floating bats across the screen when the Halloween theme is active.
 */

import { useMemo } from 'react';

interface BatConfig {
  id: number;
  top: string;
  delay: string;
  duration: string;
  size: string;
}

const BAT_COUNT = 8;

export function HalloweenDecorations() {
  const bats = useMemo<BatConfig[]>(() => {
    return Array.from({ length: BAT_COUNT }, (_, i) => ({
      id: i,
      top: `${10 + Math.floor((i / BAT_COUNT) * 75)}%`,
      delay: `${(i * 3.7).toFixed(1)}s`,
      duration: `${12 + (i % 4) * 3}s`,
      size: i % 3 === 0 ? '24px' : i % 3 === 1 ? '18px' : '14px',
    }));
  }, []);

  return (
    <div className="halloween-decorations" aria-hidden="true">
      {bats.map((bat) => (
        <span
          key={bat.id}
          className="bat"
          style={{
            top: bat.top,
            left: '-40px',
            animationDelay: bat.delay,
            animationDuration: bat.duration,
            fontSize: bat.size,
          }}
        >
          🦇
        </span>
      ))}
    </div>
  );
}
