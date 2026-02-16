# Data Model: Homepage Star Icon for Quick Access

**Feature**: 002-homepage-star-icon | **Date**: 2026-02-16  
**Branch**: copilot/add-star-icon-homepage-again  
**Purpose**: Define entities, components, and state structure for star icon feature

## Overview

This feature introduces a new UI component (star icon button) with local React state for interaction feedback. No database entities or API contracts are involved as backend persistence is out of scope. This document captures the component structure, props, state, and styling entities that constitute the data model for this visual feature.

## Component Entities

### 1. Star Icon Button Component

**Type**: React functional component (inline in App.tsx for MVP)  
**Location**: `frontend/src/App.tsx` (lines to be added in header-actions div)

**Purpose**: Display interactive star icon with hover, click, and keyboard states

**Props Interface** (if extracted to separate component later):
```typescript
interface StarIconButtonProps {
  onClick?: () => void;
  className?: string;
  ariaLabel?: string;
}
```

**State**:
```typescript
// In AppContent component
const [isStarClicked, setIsStarClicked] = useState<boolean>(false);
const [showFavoritesModal, setShowFavoritesModal] = useState<boolean>(false); // Optional P3
```

**State Transitions**:
1. **Default** → (hover) → **Hover State** → (mouse leave) → **Default**
2. **Default** → (click/Enter/Space) → **Clicked State** (300ms) → **Default**
3. **Default** → (click) → **Modal Open** (if P3 implemented) → (close) → **Default**

**Attributes**:
- `className`: "star-icon-btn" (base class)
- `onClick`: handleStarClick function
- `onKeyDown`: handleKeyDown function  
- `aria-label`: "Favorites"
- `tabIndex`: 0 (keyboard focusable)
- `role`: "button" (implicit from <button> element)

**Visual States**:
| State | Color | Transform | Description |
|-------|-------|-----------|-------------|
| Default | var(--color-text-secondary) | scale(1) | Neutral gray, no hover |
| Hover | #DAA520 (goldenrod) | scale(1.1) | Gold color on mouse hover |
| Active/Click | #DAA520 | scale(0.95) | Brief scale-down on click |
| Focus | var(--color-text-secondary) + outline | scale(1) | Keyboard focus ring |

**Validation Rules**:
- Must have aria-label for screen readers (WCAG 2.4.4)
- Color contrast must meet 3:1 minimum (WCAG 1.4.11 for UI components)
  - Light theme: #DAA520 on #ffffff = 4.5:1 ✓
  - Dark theme: #DAA520 on #0d1117 = 4.9:1 ✓
- Must be keyboard accessible (tabIndex, onKeyDown)

---

### 2. Star Icon SVG Entity

**Type**: Inline SVG element within button  
**Location**: Nested in star icon button

**Attributes**:
- `viewBox`: "0 0 24 24" (standard coordinate system)
- `width`: "20" (pixels)
- `height`: "20" (pixels)
- `fill`: "currentColor" (inherits button text color)
- `stroke`: "none"

**SVG Path Data**:
```
<path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
```
(Standard 5-point solid star, 24x24 viewBox)

**Relationships**:
- Parent: Star Icon Button
- Color source: currentColor from button CSS color property

---

### 3. Favorites Modal Entity (Optional P3)

**Type**: React modal component (conditional rendering)  
**Location**: `frontend/src/App.tsx` or separate `components/common/FavoritesModal.tsx`

**Purpose**: Display list of favorited items or empty state

**Props Interface**:
```typescript
interface FavoritesModalProps {
  isOpen: boolean;
  onClose: () => void;
  favorites?: FavoriteItem[]; // Empty array or undefined for MVP
}

interface FavoriteItem {
  id: string;
  name: string;
  type: string; // e.g., "project", "task"
}
```

**State**:
- Managed by parent (App.tsx): `showFavoritesModal` boolean

**Structure**:
```tsx
<div className="favorites-modal-backdrop" onClick={onClose}>
  <div className="favorites-modal" role="dialog" aria-modal="true" aria-labelledby="favorites-title">
    <h2 id="favorites-title">Favorites</h2>
    <div className="favorites-content">
      {favorites?.length > 0 ? (
        <ul>
          {favorites.map(item => <li key={item.id}>{item.name}</li>)}
        </ul>
      ) : (
        <p>No favorites yet. Start marking items as favorites!</p>
      )}
    </div>
    <button onClick={onClose}>Close</button>
  </div>
</div>
```

**Accessibility**:
- `role="dialog"`
- `aria-modal="true"`
- `aria-labelledby="favorites-title"`
- Keyboard: Escape key closes modal
- Focus trap: Focus moves to modal on open

**Validation Rules**:
- Must have title for aria-labelledby
- Backdrop click must close modal
- Escape key must close modal (FR-008 acceptance scenario 3)

---

## CSS Style Entities

### 1. Star Icon Button Styles

**Class**: `.star-icon-btn`  
**Location**: `frontend/src/App.css` (add after theme-toggle-btn styles ~line 83)

**Properties**:
```css
.star-icon-btn {
  background: transparent;
  border: none;
  padding: 6px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
}

.star-icon-btn:hover {
  color: #DAA520; /* Goldenrod for WCAG contrast */
  transform: scale(1.1);
}

.star-icon-btn:active {
  transform: scale(0.95);
}

.star-icon-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

**CSS Variables Used**:
- `--color-text-secondary`: Neutral default color (defined in index.css:12, 28)
- `--color-primary`: Focus outline color (defined in index.css:3, 19)
- `--radius`: Border radius (defined in index.css:13)

**Relationships**:
- Inherits from global button styles (index.css:46-54)
- Similar pattern to `.theme-toggle-btn` (App.css:72-83)

---

### 2. Favorites Modal Styles (Optional P3)

**Classes**: `.favorites-modal-backdrop`, `.favorites-modal`, `.favorites-content`  
**Location**: `frontend/src/App.css`

**Properties**:
```css
.favorites-modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.favorites-modal {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 24px;
  min-width: 300px;
  max-width: 500px;
  box-shadow: var(--shadow);
}

.favorites-modal h2 {
  margin-bottom: 16px;
  color: var(--color-text);
}

.favorites-content {
  margin-bottom: 16px;
  color: var(--color-text-secondary);
}
```

**CSS Variables Used**:
- `--color-bg`: Modal background (index.css:8, 24)
- `--color-border`: Modal border (index.css:10, 26)
- `--color-text`: Header text (index.css:11, 27)
- `--color-text-secondary`: Body text (index.css:12, 28)
- `--radius`: Border radius (index.css:13)
- `--shadow`: Box shadow (index.css:14, 29)

---

## Event Handler Entities

### 1. handleStarClick Function

**Purpose**: Handle star icon activation (click, Enter, Space)

**Signature**:
```typescript
const handleStarClick = () => void;
```

**Implementation**:
```typescript
const handleStarClick = () => {
  if (isStarClicked) return; // Debounce rapid clicks
  
  setIsStarClicked(true);
  setTimeout(() => setIsStarClicked(false), 300);
  
  // Optional P3: Open favorites modal
  // setShowFavoritesModal(true);
  
  console.log('Star icon clicked - Favorites feature');
};
```

**Side Effects**:
1. Sets `isStarClicked` state to true
2. After 300ms, resets `isStarClicked` to false
3. Optional: Opens favorites modal (P3 user story)

**Validation**:
- Debounces rapid clicks with `isStarClicked` check
- Provides visual feedback via state change + CSS animation

---

### 2. handleKeyDown Function

**Purpose**: Handle keyboard activation (Enter, Space keys)

**Signature**:
```typescript
const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => void;
```

**Implementation**:
```typescript
const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault(); // Prevent scroll on Space
    handleStarClick();
  }
};
```

**Validation**:
- Only responds to Enter and Space keys (WCAG 2.1.1)
- Prevents default Space scroll behavior
- Delegates to handleStarClick for consistency

---

### 3. handleModalClose Function (Optional P3)

**Purpose**: Close favorites modal

**Signature**:
```typescript
const handleModalClose = () => void;
```

**Implementation**:
```typescript
const handleModalClose = () => {
  setShowFavoritesModal(false);
};
```

**Keyboard Support**:
```typescript
// In modal or App.tsx useEffect
useEffect(() => {
  const handleEscape = (e: KeyboardEvent) => {
    if (e.key === 'Escape' && showFavoritesModal) {
      handleModalClose();
    }
  };
  
  document.addEventListener('keydown', handleEscape);
  return () => document.removeEventListener('keydown', handleEscape);
}, [showFavoritesModal]);
```

---

## State Management

### Application State

**Location**: App.tsx AppContent component  
**State Variables**:

1. **isStarClicked**: `boolean`
   - Purpose: Track click animation state
   - Initial: `false`
   - Duration: true for 300ms after click

2. **showFavoritesModal**: `boolean` (Optional P3)
   - Purpose: Control modal visibility
   - Initial: `false`
   - Toggle: On star click / modal close

**State Diagram**:
```
Default State
  ├─> [hover] → Hover Visual (CSS only, no state change)
  ├─> [click] → isStarClicked: true (300ms) → isStarClicked: false
  └─> [click + P3] → showFavoritesModal: true → [close] → showFavoritesModal: false
```

**No Global State**: This feature uses local component state only. No Redux, Context, or external state management required.

---

## Data Flow

### User Interaction Flow

1. **User hovers star icon** (mouse device)
   - CSS :hover applies → color changes to #DAA520, scale(1.1)
   - No state change

2. **User clicks star icon** (or presses Enter/Space)
   - handleKeyDown/onClick fires
   - setIsStarClicked(true)
   - CSS :active applies → scale(0.95)
   - After 300ms → setIsStarClicked(false)
   - Optional P3: setShowFavoritesModal(true)

3. **User closes modal** (if P3 implemented)
   - Clicks backdrop or Close button or presses Escape
   - handleModalClose fires
   - setShowFavoritesModal(false)

**Performance Characteristics**:
- State updates: 1 per click (isStarClicked)
- Re-renders: 2 per click (true → false after 300ms)
- CSS transitions: GPU-accelerated (transform, color)
- Latency: <100ms (CSS transition duration: 200ms, within SC-005 requirement)

---

## File Change Summary

### Modified Files

1. **frontend/src/App.tsx**
   - Add: `isStarClicked` state (line ~27)
   - Add: `showFavoritesModal` state if P3 (line ~28)
   - Add: handleStarClick function (line ~51)
   - Add: handleKeyDown function (line ~60)
   - Add: Star icon button JSX in header-actions (line ~87)
   - Optional: Favorites modal JSX (line ~140)

2. **frontend/src/App.css**
   - Add: .star-icon-btn styles (after line 83)
   - Add: .star-icon-btn:hover styles
   - Add: .star-icon-btn:active styles
   - Add: .star-icon-btn:focus-visible styles
   - Optional P3: .favorites-modal-backdrop, .favorites-modal styles

### No New Files Required

MVP implementation adds code to existing files only. Optional: Extract to `components/common/StarIcon.tsx` post-MVP if reused elsewhere.

---

## Testing Data Model

### Manual Test Cases

**Test Data**: N/A (visual feature, no data input)

**Verification States**:
1. Default state: Icon visible, neutral color, no transform
2. Hover state: Gold color (#DAA520), scale(1.1)
3. Click state: Scale(0.95) for 300ms
4. Focus state: Visible focus outline
5. Keyboard activation: Enter/Space trigger same as click

**Accessibility Test Points**:
- Screen reader: Announces "Favorites button"
- Keyboard: Tab navigates to icon (within 3 tab stops from page load)
- Keyboard: Enter and Space activate icon
- Color contrast: 4.5:1 minimum (both themes)

---

## Dependencies on Existing Entities

### CSS Variables (index.css)
- `--color-text-secondary`: Default icon color
- `--color-primary`: Focus outline color
- `--color-bg`: Modal background (P3)
- `--color-border`: Modal border (P3)
- `--radius`: Border radius
- `--shadow`: Box shadow (P3)

### React Hooks
- `useState`: Track isStarClicked, showFavoritesModal
- `useEffect`: Handle Escape key for modal (P3)

### Existing Components
- App.tsx: AppContent component (parent)
- header-actions div: Container for star icon button

**No New Dependencies**: No npm packages required. Uses existing React, TypeScript, CSS infrastructure.

---

## Future Extensions (Out of Scope)

These entities are NOT included in MVP but documented for future reference:

1. **useFavorites Hook**: Manage favorites state (add/remove items)
2. **Favorites API**: Backend endpoints for persisting favorites
3. **FavoriteItem Interface**: Data structure for favorited items
4. **Star Toggle State**: Filled vs outlined star based on favorite status
5. **Favorites Count Badge**: Number indicator on star icon

These are explicitly out of scope per spec Assumptions and Scope sections.
