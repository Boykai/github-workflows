/**
 * EmptyState — reusable empty state component for catalog pages.
 * Displays an icon, title, description, and an optional CTA button
 * using the celestial design tokens.
 */

import type { LucideIcon } from '@/lib/icons';
import { Lightbulb } from '@/lib/icons';
import { Button } from '@/components/ui/button';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  hint?: string;
}

export function EmptyState({ icon: Icon, title, description, actionLabel, onAction, hint }: EmptyStateProps) {
  return (
    <div className="flex min-h-[30vh] flex-col items-center justify-center rounded-[1.35rem] border border-dashed border-border/80 bg-background/42 p-8 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
        <Icon className="h-7 w-7 text-primary" />
      </div>
      <h3 className="mb-2 text-lg font-semibold text-foreground">{title}</h3>
      <p className="mb-6 max-w-sm text-sm text-muted-foreground">{description}</p>
      {hint && (
        <p className="mb-6 flex items-start gap-1.5 max-w-sm text-xs text-muted-foreground/80">
          <Lightbulb className="h-3.5 w-3.5 shrink-0 mt-0.5" />
          <span>{hint}</span>
        </p>
      )}
      {actionLabel && onAction && (
        <Button variant="default" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
