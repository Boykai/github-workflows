/**
 * TourProgress — dot-based step indicator for the spotlight tour.
 * Active dot gets celestial-pulse-glow. Completed dots solid gold. Upcoming muted.
 */

import { cn } from '@/lib/utils';

interface TourProgressProps {
  currentStep: number;
  totalSteps: number;
}

export function TourProgress({ currentStep, totalSteps }: TourProgressProps) {
  return (
    <div className="flex items-center gap-1.5" role="group" aria-label={`Step ${currentStep + 1} of ${totalSteps}`}>
      {Array.from({ length: totalSteps }, (_, i) => (
        <span
          key={i}
          className={cn(
            'h-2 w-2 rounded-full transition-all duration-300',
            i === currentStep && 'bg-primary celestial-pulse-glow scale-125',
            i < currentStep && 'bg-primary/80',
            i > currentStep && 'border border-muted-foreground/40 bg-transparent',
          )}
          aria-hidden="true"
        />
      ))}
    </div>
  );
}
