import { cn } from '@/lib/utils';

interface CelestialLoaderProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  className?: string;
}

const sizeMap = {
  sm: { orbit: 'h-8 w-8', sun: 'h-2 w-2', planet: 'h-1.5 w-1.5' },
  md: { orbit: 'h-12 w-12', sun: 'h-3 w-3', planet: 'h-2 w-2' },
  lg: { orbit: 'h-16 w-16', sun: 'h-4 w-4', planet: 'h-2.5 w-2.5' },
} as const;

export function CelestialLoader({
  size = 'md',
  label = 'Loading…',
  className,
}: CelestialLoaderProps) {
  const s = sizeMap[size];

  return (
    <div role="status" className={cn('flex flex-col items-center gap-2', className)}>
      <div className={cn('relative', s.orbit)}>
        {/* Central sun */}
        <div
          className={cn(
            'absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary celestial-pulse-glow',
            s.sun
          )}
        />
        {/* Orbit ring with planet — planet must be a child so it orbits with the spin */}
        <div className="absolute inset-0 rounded-full border border-primary/30 celestial-orbit-spin-fast">
          <div
            className={cn(
              'absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-gold',
              s.planet
            )}
          />
        </div>
      </div>
      <span className="sr-only">{label}</span>
    </div>
  );
}
