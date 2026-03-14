/**
 * Tooltip — reusable wrapper component built on @radix-ui/react-tooltip.
 *
 * Primary usage:  <Tooltip contentKey="agents.card.deleteButton">…</Tooltip>
 * Escape-hatch:   <Tooltip content="Dynamic text">…</Tooltip>
 *
 * If the resolved content includes a `title` it is rendered as a bold
 * heading above the summary (progressive disclosure tier 1).
 * If a `learnMoreUrl` is present a "Learn more →" link is appended.
 */

import * as React from 'react';
import * as RadixTooltip from '@radix-ui/react-tooltip';
import { cn } from '@/lib/utils';
import { tooltipContent, type TooltipEntry } from '@/constants/tooltip-content';

// ---------------------------------------------------------------------------
// Re-export the provider for App.tsx
// ---------------------------------------------------------------------------
export const TooltipProvider = RadixTooltip.Provider;

// ---------------------------------------------------------------------------
// Component props
// ---------------------------------------------------------------------------
export interface TooltipProps {
  /** Registry key to look up tooltip content (primary usage). */
  contentKey?: string;
  /** Direct tooltip text (escape-hatch for dynamic content). */
  content?: string;
  /** Direct title (used together with `content`). */
  title?: string;
  /** Direct learnMoreUrl (used together with `content`). */
  learnMoreUrl?: string;
  /** Preferred placement (default: "top"). */
  side?: 'top' | 'right' | 'bottom' | 'left';
  /** Alignment relative to the trigger. */
  align?: 'start' | 'center' | 'end';
  /** Override the default hover delay (ms). */
  delayDuration?: number;
  /** The element that triggers the tooltip. */
  children: React.ReactNode;
}

// ---------------------------------------------------------------------------
// Internal: resolve the tooltip entry from props
// ---------------------------------------------------------------------------
function resolveEntry(props: TooltipProps): TooltipEntry | null {
  if (props.contentKey) {
    const entry = tooltipContent[props.contentKey];
    if (!entry) {
      if (import.meta.env.DEV) {
        console.warn(`[Tooltip] No registry entry for key "${props.contentKey}"`);
      }
      return null;
    }
    return entry;
  }

  if (props.content) {
    return {
      summary: props.content,
      title: props.title,
      learnMoreUrl: props.learnMoreUrl,
    };
  }

  return null;
}

// ---------------------------------------------------------------------------
// Tooltip component
// ---------------------------------------------------------------------------
export function Tooltip({
  children,
  side = 'top',
  align = 'center',
  delayDuration,
  ...rest
}: TooltipProps) {
  const entry = resolveEntry({ children, side, align, delayDuration, ...rest });

  // FR-012: gracefully skip rendering when no content is found
  if (!entry) {
    return <>{children}</>;
  }

  return (
    <RadixTooltip.Root delayDuration={delayDuration}>
      <RadixTooltip.Trigger asChild>{children}</RadixTooltip.Trigger>
      <RadixTooltip.Portal>
        <RadixTooltip.Content
          side={side}
          align={align}
          sideOffset={6}
          collisionPadding={8}
          className={cn(
            'z-50 max-w-[280px] rounded-lg border border-border/60',
            'bg-popover px-3 py-2 text-popover-foreground shadow-md',
            'animate-in fade-in-0 zoom-in-95',
            'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95',
            'data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2',
            'data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
            'motion-reduce:animate-none'
          )}
          style={{ fontSize: '13px' }}
        >
          {entry.title && <p className="font-semibold leading-snug mb-1">{entry.title}</p>}
          <p className="leading-snug">{entry.summary}</p>
          {entry.learnMoreUrl && (
            <a
              href={entry.learnMoreUrl}
              className="mt-1 inline-block text-xs text-primary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
            >
              Learn more →
            </a>
          )}
          <RadixTooltip.Arrow className="fill-popover" />
        </RadixTooltip.Content>
      </RadixTooltip.Portal>
    </RadixTooltip.Root>
  );
}
