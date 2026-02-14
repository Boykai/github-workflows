# TypeScript Contracts: Application Title

**Feature**: 001-app-title-update  
**Phase**: 1 - Contracts  
**Date**: 2026-02-14

## Overview

This document defines TypeScript interfaces and type contracts for the application title feature. Given the simplicity of this feature (static string replacement), the contracts are minimal and mostly documentary.

## Type Definitions

### AppTitle Type

```typescript
/**
 * The application's display title
 * Used in browser tabs, bookmarks, and UI headers
 */
type AppTitle = string;

/**
 * Constant application title
 * DO NOT change at runtime
 */
const APP_TITLE: AppTitle = "GitHub Workflows";
```

**Constraints**:
- Must be non-empty string
- Should be human-readable
- Recommended max length: 60 characters (for browser tab visibility)
- Current length: 17 characters ✅

---

## Component Interface

### App Component (Modified)

The App component will be modified to set the document title on mount.

```typescript
/**
 * No props changes needed for App component
 * Internal implementation adds useEffect for document.title
 */
interface AppComponentBehavior {
  /**
   * Sets browser document title on component mount
   * @effect document.title = "GitHub Workflows"
   */
  setDocumentTitle(): void;
  
  /**
   * Renders header with application title
   * @returns JSX element with <h1>GitHub Workflows</h1>
   */
  renderHeader(): JSX.Element;
  
  /**
   * Renders login screen with application title
   * @returns JSX element with <h1>GitHub Workflows</h1>
   */
  renderLoginScreen(): JSX.Element;
}
```

**Implementation Notes**:
- No new props required
- No new state variables needed
- useEffect has empty dependency array (runs once)

---

## HTML Contract

### index.html Structure

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <!-- CONTRACT: Title must be "GitHub Workflows" -->
    <title>GitHub Workflows</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**Contract Guarantees**:
- `<title>` tag exists in `<head>`
- Title text is exactly "GitHub Workflows"
- No dynamic title generation at build time

---

## Browser API Contract

### Document.title Property

```typescript
/**
 * Browser DOM API for document title
 * Guaranteed to be available in all supported browsers
 */
interface Document {
  /**
   * Gets or sets the title of the current document
   * @property title - The document title shown in browser tabs
   */
  title: string;
}

/**
 * Usage in React component
 * @example
 * useEffect(() => {
 *   document.title = "GitHub Workflows";
 * }, []);
 */
```

**Browser Compatibility**:
- ✅ Chrome (all versions)
- ✅ Firefox (all versions)
- ✅ Safari (all versions)
- ✅ Edge (all versions)

---

## React Hook Contract

### useEffect for Document Title

```typescript
/**
 * React hook to set document title on component mount
 * @hook useEffect
 * @deps [] - Empty array ensures single execution
 */
const documentTitleEffect: React.EffectCallback = () => {
  document.title = "GitHub Workflows";
  
  // No cleanup needed (title persists)
  return undefined;
};

/**
 * Usage
 * @example
 * useEffect(() => {
 *   document.title = "GitHub Workflows";
 * }, []);
 */
```

**Contract Guarantees**:
- Runs after first render (after HTML title already visible)
- Runs only once (empty dependency array)
- No cleanup function needed
- Side effect is safe (DOM manipulation in effect)

---

## JSX Contract

### Header Text Contract

```typescript
/**
 * JSX elements for application title display
 */
interface TitleJSX {
  /**
   * Login screen title
   * @location App.tsx line ~69
   */
  loginTitle: JSX.Element; // <h1>GitHub Workflows</h1>
  
  /**
   * Main header title
   * @location App.tsx line ~85
   */
  headerTitle: JSX.Element; // <h1>GitHub Workflows</h1>
}
```

**Contract Guarantees**:
- Both titles are `<h1>` semantic elements
- Both contain exact text "GitHub Workflows"
- No additional props or classes added
- Existing styling preserved

---

## Consistency Contract

### Cross-Location Title Consistency

```typescript
/**
 * Ensures all title locations use the same value
 */
interface TitleConsistency {
  /**
   * HTML initial title
   */
  htmlTitle: "GitHub Workflows";
  
  /**
   * React-set document title
   */
  documentTitle: "GitHub Workflows";
  
  /**
   * Login screen UI title
   */
  loginUITitle: "GitHub Workflows";
  
  /**
   * Main header UI title
   */
  headerUITitle: "GitHub Workflows";
}

/**
 * Validation function (for testing purposes)
 */
function validateTitleConsistency(): boolean {
  const htmlTitle = document.querySelector('title')?.textContent;
  const documentTitle = document.title;
  const loginTitle = document.querySelector('.app-login h1')?.textContent;
  const headerTitle = document.querySelector('.app-header h1')?.textContent;
  
  return (
    htmlTitle === "GitHub Workflows" &&
    documentTitle === "GitHub Workflows" &&
    loginTitle === "GitHub Workflows" &&
    headerTitle === "GitHub Workflows"
  );
}
```

**Validation Points**:
- All four locations must match exactly
- Case-sensitive comparison ("GitHub Workflows" not "github workflows")
- No leading/trailing whitespace

---

## File Change Contract

### Modified Files

```typescript
/**
 * Contract for files modified by this feature
 */
interface FileChanges {
  "frontend/index.html": {
    line: 7;
    before: "<title>Welcome to Tech Connect 2026!</title>";
    after: "<title>GitHub Workflows</title>";
  };
  
  "frontend/src/App.tsx": {
    changes: [
      {
        line: 69;
        before: "<h1>Welcome to Tech Connect 2026!</h1>";
        after: "<h1>GitHub Workflows</h1>";
      },
      {
        line: 85;
        before: "<h1>Welcome to Tech Connect 2026!</h1>";
        after: "<h1>GitHub Workflows</h1>";
      },
      {
        location: "After App component start";
        addition: "useEffect(() => { document.title = 'GitHub Workflows'; }, []);";
      }
    ];
  };
}
```

**Change Guarantees**:
- Exactly 3 text replacements
- 1 useEffect addition
- No other files modified
- No new dependencies added

---

## Constitution Compliance

✅ **Specification-First**: Contracts derived from spec requirements  
✅ **Template-Driven**: Following contracts structure conventions  
✅ **Agent-Orchestrated**: Single-purpose contract definition phase  
✅ **Test Optionality**: Manual testing contract only (no automated tests)  
✅ **Simplicity/DRY**: Minimal types, no unnecessary abstractions
