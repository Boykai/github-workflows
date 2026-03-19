import * as React from 'react';
import { cn } from '@/lib/utils';

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'pulse' | 'shimmer';
}

function Skeleton({ className, variant = 'pulse', ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        'rounded bg-muted',
        variant === 'pulse' && 'animate-pulse',
        variant === 'shimmer' && 'celestial-shimmer',
        className
      )}
      role="presentation"
      aria-hidden="true"
      {...props}
    />
  );
}

export { Skeleton };
