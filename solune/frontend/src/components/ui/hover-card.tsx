/**
 * HoverCard — reusable wrapper component built on @radix-ui/react-hover-card.
 *
 * Displays rich content previews (agent details, issue summaries, etc.) when
 * hovering over a trigger element. Modeled on the existing `tooltip.tsx`.
 *
 * Usage:
 *   <HoverCard openDelay={300} closeDelay={150}>
 *     <HoverCardTrigger asChild>
 *       <button>Hover me</button>
 *     </HoverCardTrigger>
 *     <HoverCardContent side="right">
 *       <p>Rich preview content</p>
 *     </HoverCardContent>
 *   </HoverCard>
 */

import * as React from 'react';
import * as HoverCardPrimitive from '@radix-ui/react-hover-card';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Re-export root and trigger for composition
// ---------------------------------------------------------------------------
export const HoverCard = HoverCardPrimitive.Root;
export const HoverCardTrigger = HoverCardPrimitive.Trigger;

// ---------------------------------------------------------------------------
// Styled content wrapper
// ---------------------------------------------------------------------------
export const HoverCardContent = React.forwardRef<
  React.ComponentRef<typeof HoverCardPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof HoverCardPrimitive.Content>
>(({ className, side = 'bottom', align = 'center', sideOffset = 4, ...props }, ref) => (
  <HoverCardPrimitive.Portal>
    <HoverCardPrimitive.Content
      ref={ref}
      side={side}
      align={align}
      sideOffset={sideOffset}
      collisionPadding={8}
      className={cn(
        'z-50 w-80 rounded-lg border border-border/60 bg-popover p-4 text-popover-foreground shadow-md outline-none',
        'motion-safe:animate-in motion-safe:fade-in-0 motion-safe:zoom-in-95',
        'motion-safe:data-[state=closed]:animate-out motion-safe:data-[state=closed]:fade-out-0 motion-safe:data-[state=closed]:zoom-out-95',
        'motion-safe:data-[side=bottom]:slide-in-from-top-2 motion-safe:data-[side=left]:slide-in-from-right-2',
        'motion-safe:data-[side=right]:slide-in-from-left-2 motion-safe:data-[side=top]:slide-in-from-bottom-2',
        className
      )}
      {...props}
    />
  </HoverCardPrimitive.Portal>
));
HoverCardContent.displayName = 'HoverCardContent';
