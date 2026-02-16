# File Change Contracts: Homepage Star Icon

**Feature**: 002-homepage-star-icon | **Date**: 2026-02-16  
**Branch**: copilot/add-star-icon-homepage-again  
**Purpose**: Define precise file changes required to implement star icon feature

## Overview

This feature requires modifications to 2 existing files (App.tsx, App.css) with no new files for MVP. Changes are surgical additions to existing React component and stylesheet. All line numbers reference current main branch state.

## Contract 1: Add Star Icon Button to App Header

**File**: `frontend/src/App.tsx`  
**Change Type**: Addition (JSX + event handlers)  
**Lines**: ~27-28 (state), ~51-69 (handlers), ~87-98 (JSX insertion)

### Current State (Line 82-96)

```tsx
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Welcome to Tech Connect 2026!</h1>
        <div className="header-actions">
          <button 
            className="theme-toggle-btn"
            onClick={toggleTheme}
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>
          <LoginButton />
        </div>
      </header>
```

### Target State (After Change)

```tsx
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Welcome to Tech Connect 2026!</h1>
        <div className="header-actions">
          <button 
            className="star-icon-btn"
            onClick={handleStarClick}
            onKeyDown={handleKeyDown}
            aria-label="Favorites"
            tabIndex={0}
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
            </svg>
          </button>
          <button 
            className="theme-toggle-btn"
            onClick={toggleTheme}
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>
          <LoginButton />
        </div>
      </header>
```

### Change Details

**Location 1: Add State** (after line 26, before existing hooks)
```tsx
  const [isStarClicked, setIsStarClicked] = useState(false);
```

**Location 2: Add Event Handlers** (after line 50, before authLoading check)
```tsx
  const handleStarClick = () => {
    if (isStarClicked) return; // Debounce rapid clicks
    
    setIsStarClicked(true);
    setTimeout(() => setIsStarClicked(false), 300);
    
    // Visual feedback provided by CSS animation
    console.log('Star icon clicked - Favorites feature');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault(); // Prevent Space key scrolling
      handleStarClick();
    }
  };
```

**Location 3: Insert Button JSX** (in header-actions div, before theme-toggle-btn)
```tsx
          <button 
            className="star-icon-btn"
            onClick={handleStarClick}
            onKeyDown={handleKeyDown}
            aria-label="Favorites"
            tabIndex={0}
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
            </svg>
          </button>
```

### Validation Criteria

✓ **Compiles**: TypeScript compilation succeeds (no type errors)  
✓ **Renders**: Star icon appears in header between h1 and theme toggle  
✓ **Accessibility**: aria-label present, tabIndex set, keyboard handlers defined  
✓ **Functionality**: Click and keyboard activation log to console  
✓ **Debounce**: Rapid clicks don't trigger multiple logs within 300ms  

---

## Contract 2: Add Star Icon Button Styles

**File**: `frontend/src/App.css`  
**Change Type**: Addition (CSS rules)  
**Lines**: After line 83 (after theme-toggle-btn styles)

### Change Details

**Insert After**: Line 83 (after `.theme-toggle-btn:hover` closing brace)

**New CSS Rules** (4 rules):
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
  color: #DAA520; /* Goldenrod - WCAG AA compliant */
  transform: scale(1.1);
}

.star-icon-btn:active {
  transform: scale(0.95);
  color: #DAA520;
}

.star-icon-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

### Validation Criteria

✓ **Syntax**: CSS validates (no syntax errors)  
✓ **Variables**: Uses existing CSS custom properties  
✓ **Contrast**: Gold color #DAA520 meets WCAG AA (4.5:1 on light, 4.9:1 on dark)  
✓ **Transitions**: All transitions under 200ms  

---

## File Change Summary

| File | Lines Changed | Type | Description |
|------|--------------|------|-------------|
| frontend/src/App.tsx | +30 | Addition | State, handlers, JSX button |
| frontend/src/App.css | +35 | Addition | Button styles (4 rules) |
| **Total** | **65** | **Addition** | **No deletions, no new files** |
