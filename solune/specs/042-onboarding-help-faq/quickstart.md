# Quickstart: Onboarding Spotlight Tour & Help/FAQ Page

**Feature**: `042-onboarding-help-faq` | **Date**: 2026-03-15

## Overview

This feature adds two capabilities:
1. **Spotlight Tour** — A 9-step guided walkthrough that auto-launches on first login
2. **Help Page** — A `/help` route with FAQ, feature guides, and tour replay

All changes are frontend-only. No backend modifications. No new npm dependencies.

## Development Setup

```bash
cd solune/frontend
npm install          # no new deps, just ensure existing ones are installed
npm run dev          # starts Vite dev server on :5173
```

## Key Files to Know

| File | Purpose |
|------|---------|
| `src/hooks/useOnboarding.ts` | Tour state management (localStorage + React state) |
| `src/components/onboarding/SpotlightTour.tsx` | Tour orchestrator — all 9 step definitions live here |
| `src/components/onboarding/SpotlightOverlay.tsx` | Viewport overlay with CSS clip-path cutout |
| `src/components/onboarding/SpotlightTooltip.tsx` | Positioned/bottom-sheet tooltip |
| `src/pages/HelpPage.tsx` | Help Center page with FAQ + guides |
| `src/components/help/FaqAccordion.tsx` | Collapsible Q&A component |
| `src/constants.ts` | NAV_ROUTES — Help entry added here |

## Adding a New Tour Step

1. Add `data-tour-step="your-id"` attribute to the target element in the layout
2. Add a TSX icon component in `src/assets/onboarding/icons.tsx` (inline SVG using `currentColor`, exported as a named React component)
3. Add a step object to the `TOUR_STEPS` array in `SpotlightTour.tsx`:

```typescript
{
  id: 10,
  targetSelector: 'your-id',
  title: 'Your Step Title',
  description: 'Explanation of this feature.',
  icon: YourIcon,
  placement: 'bottom',
}
```

4. Update `TOTAL_STEPS` constant in `useOnboarding.ts`

## Adding a New FAQ Entry

Add an object to the `FAQ_ENTRIES` array in `HelpPage.tsx`:

```typescript
{
  id: 'category-n',
  question: 'Your question here?',
  answer: 'Your answer here.',
  category: 'getting-started', // or 'agents-pipelines', 'chat-voice', 'settings-integration'
}
```

## Testing the Tour

1. Open browser DevTools → Application → Local Storage
2. Delete the `solune-onboarding-completed` key
3. Refresh the page — tour should auto-launch
4. Or navigate to `/help` and click "Replay Tour"

## Running Tests

```bash
npm run test              # vitest unit tests
npm run test:e2e          # playwright e2e tests  
npm run type-check        # TypeScript compilation check
npm run lint              # ESLint
```

## CSS Classes Used

All new components reuse existing celestial design system classes:
- `.celestial-panel` — gradient panel background
- `.golden-ring` — glow border effect
- `.celestial-fade-in` — entry animation
- `.celestial-pulse-glow` — pulsing glow (active progress dot)
- `.celestial-twinkle` — star sparkle decoration
- `.moonwell` — frosted glass card background
- `.solar-action` — interactive button styling
- `.starfield` — cosmic background pattern
