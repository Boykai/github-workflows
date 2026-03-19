/**
 * SpotlightTooltip — positioned tooltip for the spotlight tour.
 * Desktop: positioned popover near target element with viewport-aware algorithm.
 * Mobile (<768px): fixed bottom sheet.
 * Includes focus trap (Phase 6 enhancement) and accessibility attributes.
 */

import { useRef, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { TourProgress } from './TourProgress';
import type { TourStep, TourStepPlacement } from '@/types';
import { cn } from '@/lib/utils';

interface SpotlightTooltipProps {
  step: TourStep;
  targetRect: DOMRect | null;
  currentStep: number;
  totalSteps: number;
  onNext: () => void;
  onBack: () => void;
  onSkip: () => void;
}

const MARGIN = 16;
const TOOLTIP_WIDTH = 340;
const TOOLTIP_HEIGHT_EST = 260;

function computePosition(
  targetRect: DOMRect | null,
  placement: TourStepPlacement,
): { top: number; left: number } {
  if (!targetRect) {
    // Center in viewport for welcome step
    return {
      top: Math.max(MARGIN, (window.innerHeight - TOOLTIP_HEIGHT_EST) / 2),
      left: Math.max(MARGIN, (window.innerWidth - TOOLTIP_WIDTH) / 2),
    };
  }

  const vw = window.innerWidth;
  const vh = window.innerHeight;

  const positions: Record<TourStepPlacement, { top: number; left: number }> = {
    right: {
      top: targetRect.top + (targetRect.height - TOOLTIP_HEIGHT_EST) / 2,
      left: targetRect.right + MARGIN,
    },
    left: {
      top: targetRect.top + (targetRect.height - TOOLTIP_HEIGHT_EST) / 2,
      left: targetRect.left - TOOLTIP_WIDTH - MARGIN,
    },
    bottom: {
      top: targetRect.bottom + MARGIN,
      left: targetRect.left + (targetRect.width - TOOLTIP_WIDTH) / 2,
    },
    top: {
      top: targetRect.top - TOOLTIP_HEIGHT_EST - MARGIN,
      left: targetRect.left + (targetRect.width - TOOLTIP_WIDTH) / 2,
    },
  };

  const preferred = positions[placement];

  // Check if preferred fits
  if (
    preferred.top >= MARGIN &&
    preferred.top + TOOLTIP_HEIGHT_EST <= vh - MARGIN &&
    preferred.left >= MARGIN &&
    preferred.left + TOOLTIP_WIDTH <= vw - MARGIN
  ) {
    return preferred;
  }

  // Flip to opposite
  const opposites: Record<TourStepPlacement, TourStepPlacement> = {
    top: 'bottom',
    bottom: 'top',
    left: 'right',
    right: 'left',
  };
  const flipped = positions[opposites[placement]];
  if (
    flipped.top >= MARGIN &&
    flipped.top + TOOLTIP_HEIGHT_EST <= vh - MARGIN &&
    flipped.left >= MARGIN &&
    flipped.left + TOOLTIP_WIDTH <= vw - MARGIN
  ) {
    return flipped;
  }

  // Fallback: bottom, clamped
  return {
    top: Math.min(Math.max(MARGIN, positions.bottom.top), vh - TOOLTIP_HEIGHT_EST - MARGIN),
    left: Math.min(Math.max(MARGIN, positions.bottom.left), vw - TOOLTIP_WIDTH - MARGIN),
  };
}

export function SpotlightTooltip({
  step,
  targetRect,
  currentStep,
  totalSteps,
  onNext,
  onBack,
  onSkip,
}: SpotlightTooltipProps) {
  const tooltipRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const [isMobile, setIsMobile] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(max-width: 767px)').matches
  );

  // Track mobile viewport
  useEffect(() => {
    const mq = window.matchMedia('(max-width: 767px)');
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  // Focus trap via document keydown
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      const container = tooltipRef.current;
      if (!container) return;

      const focusable = container.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      );
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []);

  // Capture pre-tour focus on mount, restore on unmount
  useEffect(() => {
    previousFocusRef.current = document.activeElement as HTMLElement;
    return () => {
      previousFocusRef.current?.focus();
    };
  }, []);

  // Focus first button on each step change
  useEffect(() => {
    const timer = requestAnimationFrame(() => {
      const firstBtn = tooltipRef.current?.querySelector<HTMLElement>('button');
      firstBtn?.focus();
    });
    return () => cancelAnimationFrame(timer);
  }, [currentStep]);

  const Icon = step.icon;
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === totalSteps - 1;

  if (isMobile) {
    return (
      <div
        ref={tooltipRef}
        role="dialog"
        aria-modal="true"
        aria-label={`Tour step ${currentStep + 1}: ${step.title}`}
        tabIndex={-1}
        className="celestial-panel golden-ring celestial-fade-in fixed bottom-0 left-0 right-0 z-[101] rounded-t-2xl border-t border-border/70 p-6"
      >
        {/* Drag handle indicator */}
        <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-muted-foreground/30" />
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full bg-primary/15 text-primary">
            <Icon className="h-5 w-5 shrink-0" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs text-muted-foreground">
              Step {currentStep + 1} of {totalSteps}
            </p>
            <h3 className="text-base font-semibold text-foreground">{step.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{step.description}</p>
          </div>
        </div>
        <div className="mt-4 flex flex-col gap-3">
          <TourProgress currentStep={currentStep} totalSteps={totalSteps} />
          <div className="flex flex-wrap items-center justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={onSkip}>
              Skip Tour
            </Button>
            {!isFirstStep && (
              <Button variant="outline" size="sm" onClick={onBack}>
                Back
              </Button>
            )}
            <Button size="sm" onClick={onNext}>
              {isLastStep ? 'Done' : 'Next'}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const position = computePosition(targetRect, step.placement);

  return (
    <div
      ref={tooltipRef}
      role="dialog"
      aria-modal="true"
      aria-label={`Tour step ${currentStep + 1}: ${step.title}`}
      tabIndex={-1}
      className={cn(
        'celestial-panel golden-ring celestial-fade-in fixed z-[101] w-[340px] rounded-2xl border border-border/70 p-5',
      )}
      style={{
        top: position.top,
        left: position.left,
      }}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full bg-primary/15 text-primary">
          <Icon className="h-5 w-5 shrink-0" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs text-muted-foreground">
            Step {currentStep + 1} of {totalSteps}
          </p>
          <h3 className="text-base font-semibold text-foreground">{step.title}</h3>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{step.description}</p>
        </div>
      </div>
      <div className="mt-4 flex flex-col gap-3">
        <TourProgress currentStep={currentStep} totalSteps={totalSteps} />
        <div className="flex flex-wrap items-center justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={onSkip}>
            Skip Tour
          </Button>
          {!isFirstStep && (
            <Button variant="outline" size="sm" onClick={onBack}>
              Back
            </Button>
          )}
          <Button size="sm" onClick={onNext}>
            {isLastStep ? 'Done' : 'Next'}
          </Button>
        </div>
      </div>
    </div>
  );
}
