# Component Contracts: Help Page

**Feature**: `042-onboarding-help-faq` | **Date**: 2026-03-15

## HelpPage

**File**: `solune/frontend/src/pages/HelpPage.tsx`  
**Route**: `/help` (lazy-loaded, protected by AuthGate)  
**Export**: `export function HelpPage()`

**Sections** (rendered top to bottom):
1. `CelestialCatalogHero` — eyebrow, title, description, "Replay Tour" button
2. Getting Started — 3 cards linking to first actions
3. `FaqAccordion` — 12 FAQ entries in 4 categories
4. Feature Guide Grid — 8 `FeatureGuideCard` instances
5. Slash Commands Table — rendered from `getAllCommands()`

**Dependencies**: `useOnboarding` (for `restart`), `getAllCommands()`, `CelestialCatalogHero`, `FaqAccordion`, `FeatureGuideCard`, `Button`

---

## FaqAccordion

**File**: `solune/frontend/src/components/help/FaqAccordion.tsx`

```typescript
interface FaqEntry {
  id: string;
  question: string;
  answer: string;
  category: 'getting-started' | 'agents-pipelines' | 'chat-voice' | 'settings-integration';
}

interface FaqAccordionProps {
  /** FAQ entries to render, grouped by category */
  entries: FaqEntry[];
}
```

**Behavior**:
- Groups entries by category with section headings
- One item open at a time (exclusive toggle)
- Animated expand/collapse via `grid-template-rows: 0fr → 1fr`
- Gold chevron indicator rotates on expand
- Keyboard: Enter/Space toggles, Tab navigates

**Styling**: `.celestial-panel` per item, `.celestial-fade-in` on expanded content

---

## FeatureGuideCard

**File**: `solune/frontend/src/components/help/FeatureGuideCard.tsx`

```typescript
interface FeatureGuideCardProps {
  /** Feature title */
  title: string;
  /** Brief description */
  description: string;
  /** Lucide icon component */
  icon: React.ComponentType<{ className?: string }>;
  /** Route path to navigate to */
  href: string;
}
```

**Renders**: Clickable card with icon, title, description. Navigates to `href` on click.  
**Styling**: `.moonwell` background, `-translate-y-0.5` hover lift, `rounded-[1.25rem]`

---

## Modified Contracts

### NAV_ROUTES (constants.ts)

Add entry after Apps, before Settings:

```typescript
{ path: '/help', label: 'Help', icon: HelpCircle }
```

**Note**: `HelpCircle` is already available in `lucide-react ^0.577.0`.

### App.tsx Route Addition

```typescript
const HelpPage = lazy(() =>
  import('@/pages/HelpPage').then((module) => ({ default: module.HelpPage }))
);

// Inside route tree, within the AppLayout parent:
<Route path="help" element={withSuspense(<HelpPage />)} />
```

### AppLayout.tsx Addition

```typescript
// After ChatPopup, add:
<SpotlightTour
  isSidebarCollapsed={isCollapsed}
  onToggleSidebar={toggleSidebar}
/>
```
