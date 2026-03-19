# Contract: Quick Wins (Phase 6)

**Feature**: 050-frontend-ux-improvements  
**Requirements**: FR-028 through FR-033

## Component Contracts

### 6a: Board Filtering by Priority (FR-028)

**Location**: `solune/frontend/src/components/board/BoardToolbar.tsx`, `solune/frontend/src/hooks/useBoardControls.ts`  
**Action**: Add priority to the existing filter panel.

```tsx
// In BoardToolbar.tsx Filter Panel, add a priority section:
<fieldset>
  <legend className="text-xs font-medium text-muted-foreground mb-1">Priority</legend>
  {['P0', 'P1', 'P2', 'P3'].map(priority => (
    <label key={priority} className="flex items-center gap-2">
      <input
        type="checkbox"
        checked={filters.priority?.includes(priority)}
        onChange={() => togglePriorityFilter(priority)}
      />
      <span className={priorityColorClass(priority)}>{priority}</span>
    </label>
  ))}
</fieldset>

// In useBoardControls.ts, extend filter state:
interface BoardFilters {
  labels: string[];
  assignees: string[];
  milestones: string[];
  pipelineConfig: string | null;
  priority: string[];          // NEW
}
```

**Edge Case**: When filtering returns zero results, display a friendly empty state with a "Clear filters" button.

---

### 6b: Onboarding Tour Progress Indicator (FR-029)

**Location**: `solune/frontend/src/components/onboarding/SpotlightTooltip.tsx`  
**Action**: Add "Step X of N" text next to existing progress bar.

```tsx
// In SpotlightTooltip, near the navigation buttons:
<span className="text-xs text-muted-foreground">
  Step {currentStep + 1} of {totalSteps}
</span>
```

**Notes**: `SpotlightTour.tsx` already passes `currentStep` and `totalSteps` (derived from `TOUR_STEPS.length = 9`) to `SpotlightTooltip`. The tooltip already renders a progress bar — this adds a text label alongside it.

---

### 6c: Chat Date Separators (FR-030)

**Location**: `solune/frontend/src/components/chat/ChatInterface.tsx`  
**Action**: Insert date separator elements between messages from different calendar days.

```tsx
// Helper function:
function formatDateSeparator(date: Date): string {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (isSameDay(date, today)) return 'Today';
  if (isSameDay(date, yesterday)) return 'Yesterday';
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// In message rendering loop:
{messages.map((message, index) => {
  const prevMessage = messages[index - 1];
  const showDateSeparator = !prevMessage ||
    !isSameDay(new Date(message.timestamp), new Date(prevMessage.timestamp));

  return (
    <React.Fragment key={message.id}>
      {showDateSeparator && (
        <div className="flex items-center gap-3 py-2">
          <div className="flex-1 h-px bg-border" />
          <span className="text-xs text-muted-foreground font-medium">
            {formatDateSeparator(new Date(message.timestamp))}
          </span>
          <div className="flex-1 h-px bg-border" />
        </div>
      )}
      <MessageBubble message={message} ... />
    </React.Fragment>
  );
})}
```

---

### 6d: Notification Bell Pulse Animation (FR-031)

**Location**: `solune/frontend/src/layout/NotificationBell.tsx`  
**Action**: Add/verify the pulse animation on the unread badge.

**Current state**: The NotificationBell already applies `celestial-pulse-glow` to the badge when `unreadCount > 0`. This requirement may already be satisfied. Verify and adjust if the animation is not visible or not tied to the `unreadCount > 0` condition.

```tsx
// Existing badge (verify this condition exists):
{unreadCount > 0 && (
  <span className="... celestial-pulse-glow">
    {unreadCount > 9 ? '9+' : unreadCount}
  </span>
)}
```

---

### 6e: Empty State Enrichment (FR-032)

**Location**: `solune/frontend/src/components/board/BoardColumn.tsx`, `solune/frontend/src/components/board/ProjectBoardContent.tsx`  
**Action**: Replace the plain "No items" text with a themed illustration and suggested next step.

```tsx
// In BoardColumn.tsx empty state:
{items.length === 0 && (
  <div className="flex flex-col items-center justify-center py-8 text-center">
    {/* Celestial-themed SVG illustration (star/constellation) */}
    <StarChartIcon className="h-12 w-12 text-muted-foreground/30 mb-3" />
    <p className="text-sm text-muted-foreground">No items yet</p>
    <p className="text-xs text-muted-foreground/70 mt-1">
      Create your first issue to get started
    </p>
  </div>
)}
```

---

### 6f: Ctrl+Enter to Send in Chat (FR-033)

**Location**: `solune/frontend/src/components/chat/ChatInterface.tsx`  
**Action**: Add `Ctrl+Enter` keyboard handler to the chat input.

```tsx
// In the chat input's onKeyDown handler:
const handleKeyDown = (event: React.KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault();
    handleSend();
    return;
  }
  // ... existing key handlers
};
```

## Notes

- All Phase 6 items are independent and can be implemented in any order.
- No new dependencies required.
- Each item is small (< 30 lines of code change).
