import { useState, useEffect, useId } from 'react';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { cn } from '@/lib/utils';

/**
 * A single loading phase with a human-readable label and completion status.
 */
export interface LoadingPhase {
  label: string;
  complete: boolean;
}

export interface CelestialLoadingProgressProps {
  phases: LoadingPhase[];
  className?: string;
}

const RADIUS = 52;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

/**
 * CelestialLoadingProgress — A cosmic-themed circular SVG progress ring with
 * phased status labels. Embeds the existing CelestialLoader centered inside the
 * ring. Progress is computed as max(minProgress, completedPhases / totalPhases).
 */
export function CelestialLoadingProgress({ phases, className }: CelestialLoadingProgressProps) {
  const [minProgress, setMinProgress] = useState(0);
  const gradientId = useId();

  // Time-based minimum progress: 0→15% over 3s, then slowly toward 30% cap
  useEffect(() => {
    const start = Date.now();
    const id = setInterval(() => {
      const elapsed = Date.now() - start;
      if (elapsed <= 3000) {
        setMinProgress(Math.min(0.15, (elapsed / 3000) * 0.15));
      } else {
        setMinProgress((prev) => {
          const next = Math.min(0.3, prev + 0.001);
          if (next >= 0.3) {
            clearInterval(id);
          }
          return next;
        });
      }
    }, 100);
    return () => clearInterval(id);
  }, []);

  const completedCount = phases.filter((p) => p.complete).length;
  const realProgress = phases.length > 0 ? completedCount / phases.length : 1;
  const displayProgress = Math.max(minProgress, realProgress);

  const offset = CIRCUMFERENCE * (1 - displayProgress);

  const currentPhaseLabel =
    phases.find((p) => !p.complete)?.label ?? phases[phases.length - 1]?.label ?? '';

  return (
    <div className={cn('flex flex-col items-center gap-4', className)}>
      <div className="relative">
        <svg
          role="progressbar"
          aria-valuenow={Math.round(displayProgress * 100)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Loading progress"
          className="celestial-ring-glow"
          viewBox="0 0 120 120"
          width={120}
          height={120}
        >
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="hsl(var(--gold))" />
              <stop offset="100%" stopColor="hsl(var(--primary))" />
            </linearGradient>
          </defs>
          {/* Background track */}
          <circle
            cx="60"
            cy="60"
            r={RADIUS}
            stroke="hsl(var(--muted) / 0.2)"
            strokeWidth="4"
            fill="none"
          />
          {/* Progress arc */}
          <circle
            cx="60"
            cy="60"
            r={RADIUS}
            stroke={`url(#${gradientId})`}
            strokeWidth="4"
            fill="none"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.6s ease' }}
            transform="rotate(-90 60 60)"
          />
        </svg>
        {/* CelestialLoader centered inside the ring */}
        <div className="absolute inset-0 flex items-center justify-center">
          <CelestialLoader size="lg" />
        </div>
        {/* Twinkling star decorations */}
        <span
          className="celestial-twinkle absolute -top-1 -right-1 text-[10px] text-gold/70"
          aria-hidden="true"
        >
          ✦
        </span>
        <span
          className="celestial-twinkle-delayed absolute -bottom-1 -left-1 text-[8px] text-gold/50"
          aria-hidden="true"
        >
          ✦
        </span>
        <span
          className="celestial-twinkle-slow absolute top-1/2 -right-3 text-[7px] text-gold/40"
          aria-hidden="true"
        >
          ✦
        </span>
      </div>

      {/* Phase label */}
      <p key={currentPhaseLabel} className="celestial-fade-in text-sm text-muted-foreground">
        {currentPhaseLabel}
      </p>
    </div>
  );
}
