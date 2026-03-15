/**
 * Popover — reusable wrapper component built on @radix-ui/react-popover.
 *
 * Click-triggered overlay for menus, selectors, and interactive content.
 * Focus-trapped, closes on outside click/Escape, returns focus to trigger.
 *
 * Usage:
 *   <Popover>
 *     <PopoverTrigger asChild>
 *       <button>Open menu</button>
 *     </PopoverTrigger>
 *     <PopoverContent side="bottom" align="start">
 *       <p>Interactive content</p>
 *     </PopoverContent>
 *   </Popover>
 */

import * as React from 'react';
import * as PopoverPrimitive from '@radix-ui/react-popover';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Re-export primitives for composition
// ---------------------------------------------------------------------------

/**
 * Popover root — defaults to `modal` mode for focus trapping.
 * Pass `modal={false}` to opt out when focus trapping is undesirable
 * (e.g., inline search dropdowns that need typing in other fields).
 */
export function Popover({ modal = true, ...props }: React.ComponentPropsWithoutRef<typeof PopoverPrimitive.Root> & { modal?: boolean }) {
  return <PopoverPrimitive.Root modal={modal} {...props} />;
}

export const PopoverTrigger = PopoverPrimitive.Trigger;
export const PopoverAnchor = PopoverPrimitive.Anchor;
export const PopoverClose = PopoverPrimitive.Close;

// ---------------------------------------------------------------------------
// Styled arrow
// ---------------------------------------------------------------------------
export const PopoverArrow = React.forwardRef<
  React.ComponentRef<typeof PopoverPrimitive.Arrow>,
  React.ComponentPropsWithoutRef<typeof PopoverPrimitive.Arrow>
>(({ className, ...props }, ref) => (
  <PopoverPrimitive.Arrow ref={ref} className={cn('fill-popover', className)} {...props} />
));
PopoverArrow.displayName = 'PopoverArrow';

// ---------------------------------------------------------------------------
// Styled content wrapper
// ---------------------------------------------------------------------------
export const PopoverContent = React.forwardRef<
  React.ComponentRef<typeof PopoverPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof PopoverPrimitive.Content>
>(
  (
    { className, side = 'bottom', align = 'center', sideOffset = 4, collisionPadding = 8, ...props },
    ref
  ) => (
    <PopoverPrimitive.Portal>
      <PopoverPrimitive.Content
        ref={ref}
        side={side}
        align={align}
        sideOffset={sideOffset}
        collisionPadding={collisionPadding}
        className={cn(
          'z-50 w-72 rounded-lg border border-border/60 bg-popover p-4 text-popover-foreground shadow-md outline-none',
          'motion-safe:animate-in motion-safe:fade-in-0 motion-safe:zoom-in-95',
          'motion-safe:data-[state=closed]:animate-out motion-safe:data-[state=closed]:fade-out-0 motion-safe:data-[state=closed]:zoom-out-95',
          'motion-safe:data-[side=bottom]:slide-in-from-top-2 motion-safe:data-[side=left]:slide-in-from-right-2',
          'motion-safe:data-[side=right]:slide-in-from-left-2 motion-safe:data-[side=top]:slide-in-from-bottom-2',
          className
        )}
        {...props}
      />
    </PopoverPrimitive.Portal>
  )
);
PopoverContent.displayName = 'PopoverContent';
