# Data Model: Green Theme Option

**Feature**: Green Theme Option  
**Branch**: `002-green-theme`  
**Date**: 2026-02-14  
**Phase**: 1 - Design

## Overview

This document defines the data structures, entities, and relationships for the green theme feature. The data model focuses on theme preference representation and theme definition structures.

---

## Core Entities

### 1. ThemeMode (Type Alias)

**Description**: Represents the available theme options in the application.

**Definition**:
```typescript
type ThemeMode = 'light' | 'dark' | 'green' | 'green-dark';
```

**Attributes**:
- `'light'`: Default light theme with standard colors
- `'dark'`: Dark theme with inverted colors
- `'green'`: Light theme with green accent colors
- `'green-dark'`: Dark theme with green accent colors

**Validation Rules**:
- MUST be one of the four literal string values
- NOT nullable (always has a valid default)
- Case-sensitive (lowercase only)

**Usage Context**:
- Component state in `useAppTheme` hook
- localStorage persistence value
- CSS class name generation
- Theme selector UI options

**Relationships**:
- Maps to CSS class names via transformation (e.g., `'green-dark'` → `'green-dark-mode-active'`)
- Corresponds to ThemeDefinition entries

---

### 2. ThemePreference (Interface)

**Description**: Represents a user's stored theme preference with metadata.

**Definition**:
```typescript
interface ThemePreference {
  /** Selected theme mode */
  mode: ThemeMode;
  
  /** Timestamp when preference was last updated (ISO 8601) */
  updatedAt: string;
  
  /** Optional: Browser/device identifier for cross-device disambiguation */
  deviceId?: string;
}
```

**Attributes**:

| Attribute | Type | Required | Validation | Description |
|-----------|------|----------|------------|-------------|
| `mode` | ThemeMode | Yes | Must be valid ThemeMode | Current selected theme |
| `updatedAt` | string | Yes | ISO 8601 format | Last modification timestamp |
| `deviceId` | string | No | Non-empty string | Device identifier (optional) |

**Validation Rules**:
- `mode`: Must be one of `'light'`, `'dark'`, `'green'`, `'green-dark'`
- `updatedAt`: Must be valid ISO 8601 timestamp
- `deviceId`: If present, must be non-empty string

**Default Values**:
```typescript
const DEFAULT_PREFERENCE: ThemePreference = {
  mode: 'light',
  updatedAt: new Date().toISOString(),
};
```

**Storage Format** (localStorage):
```json
{
  "mode": "green",
  "updatedAt": "2026-02-14T00:00:00.000Z"
}
```

**Legacy Compatibility**: For backward compatibility with existing `'dark'` / `'light'` string values in localStorage, the system should:
1. Detect simple string values
2. Migrate to full ThemePreference object
3. Preserve the user's existing choice

**State Transitions**:
```
light → dark → green → green-dark → light (cycle pattern)
     ↓         ↓        ↓            ↓
   [User selects specific theme from UI]
```

---

### 3. ThemeDefinition (Interface)

**Description**: Defines the complete visual styling specifications for a single theme.

**Definition**:
```typescript
interface ThemeDefinition {
  /** Unique theme identifier matching ThemeMode */
  id: ThemeMode;
  
  /** Human-readable theme name for UI display */
  name: string;
  
  /** CSS class name applied to document root */
  className: string;
  
  /** Color palette for this theme */
  colors: ThemeColors;
  
  /** Accessibility metadata */
  accessibility: ThemeAccessibility;
}
```

**Sub-Structure: ThemeColors**:
```typescript
interface ThemeColors {
  primary: string;        // Primary accent color (CSS hex)
  secondary: string;      // Secondary accent color
  success: string;        // Success state color
  warning: string;        // Warning state color
  danger: string;         // Error/danger color
  background: string;     // Main background color
  backgroundSecondary: string; // Secondary background (cards, panels)
  border: string;         // Border color
  text: string;           // Primary text color
  textSecondary: string;  // Secondary text color (descriptions, hints)
}
```

**Sub-Structure: ThemeAccessibility**:
```typescript
interface ThemeAccessibility {
  /** Minimum contrast ratio for normal text (target: 4.5:1) */
  normalTextContrast: number;
  
  /** Minimum contrast ratio for large text (target: 3:1) */
  largeTextContrast: number;
  
  /** WCAG compliance level ('AA' or 'AAA') */
  wcagLevel: 'AA' | 'AAA';
  
  /** Notes about color blindness considerations */
  colorBlindSafe: boolean;
}
```

**Example Instances**:

```typescript
const GREEN_LIGHT_THEME: ThemeDefinition = {
  id: 'green',
  name: 'Green',
  className: 'green-mode-active',
  colors: {
    primary: '#2da44e',
    secondary: '#6e7781',
    success: '#1a7f37',
    warning: '#9a6700',
    danger: '#cf222e',
    background: '#ffffff',
    backgroundSecondary: '#f6fff8',  // Subtle green tint
    border: '#d0d7de',
    text: '#24292f',
    textSecondary: '#57606a',
  },
  accessibility: {
    normalTextContrast: 4.8,  // Exceeds 4.5:1 requirement
    largeTextContrast: 3.2,   // Exceeds 3:1 requirement
    wcagLevel: 'AA',
    colorBlindSafe: true,
  },
};

const GREEN_DARK_THEME: ThemeDefinition = {
  id: 'green-dark',
  name: 'Green Dark',
  className: 'green-dark-mode-active',
  colors: {
    primary: '#3fb950',
    secondary: '#8b949e',
    success: '#56d364',
    warning: '#d29922',
    danger: '#f85149',
    background: '#0d1117',
    backgroundSecondary: '#0d1a12',  // Subtle green tint
    border: '#30363d',
    text: '#e6edf3',
    textSecondary: '#8b949e',
  },
  accessibility: {
    normalTextContrast: 4.9,
    largeTextContrast: 3.3,
    wcagLevel: 'AA',
    colorBlindSafe: true,
  },
};
```

**Validation Rules**:
- `id`: Must match one of the ThemeMode values
- `name`: Non-empty string, user-facing label
- `className`: Valid CSS class name (no spaces, starts with letter)
- `colors`: All properties must be valid CSS color values (hex, rgb, etc.)
- `accessibility.normalTextContrast`: Must be >= 4.5 for AA compliance
- `accessibility.largeTextContrast`: Must be >= 3.0 for AA compliance

**Usage Context**:
- Defines CSS custom property values
- Provides metadata for theme selector UI
- Documents accessibility compliance
- Enables programmatic theme generation

---

## Entity Relationships

```
ThemeMode (type alias)
    ↓ (referenced by)
ThemePreference.mode
    ↓ (stored in)
localStorage['tech-connect-theme-mode']
    ↓ (loaded into)
useAppTheme hook state
    ↓ (applied as)
CSS class on document.documentElement
    ↓ (selects)
CSS custom property overrides
    ↓ (defined by)
ThemeDefinition.colors
```

**Flow Diagram**:
```
User Selection
    ↓
UI Component (ThemeSelector)
    ↓
useAppTheme.setTheme(mode)
    ↓
Update State + localStorage
    ↓
useEffect triggers
    ↓
Apply CSS class to DOM
    ↓
Browser applies CSS overrides
    ↓
Visual theme change (instant)
```

---

## Storage Schema

### localStorage Entry

**Key**: `'tech-connect-theme-mode'`

**Value Format** (Current):
```json
{
  "mode": "green",
  "updatedAt": "2026-02-14T12:00:00.000Z"
}
```

**Value Format** (Legacy - backward compatible):
```
"dark"
```
or
```
"light"
```

**Migration Logic**:
```typescript
function migrateThemePreference(stored: string | null): ThemePreference {
  if (!stored) {
    return { mode: 'light', updatedAt: new Date().toISOString() };
  }
  
  // Try parsing as JSON (new format)
  try {
    const parsed = JSON.parse(stored);
    if (parsed.mode && VALID_THEMES.includes(parsed.mode)) {
      return parsed;
    }
  } catch {
    // Not JSON, might be legacy string
  }
  
  // Handle legacy string format
  if (stored === 'dark' || stored === 'light') {
    return { mode: stored, updatedAt: new Date().toISOString() };
  }
  
  // Invalid data, use default
  return { mode: 'light', updatedAt: new Date().toISOString() };
}
```

**Storage Size**: ~100 bytes per preference (well within localStorage limits)

---

## Validation & Constraints

### Type Guards

```typescript
const VALID_THEMES: readonly ThemeMode[] = ['light', 'dark', 'green', 'green-dark'];

function isValidThemeMode(value: unknown): value is ThemeMode {
  return typeof value === 'string' && VALID_THEMES.includes(value as ThemeMode);
}

function isThemePreference(value: unknown): value is ThemePreference {
  return (
    typeof value === 'object' &&
    value !== null &&
    'mode' in value &&
    isValidThemeMode(value.mode) &&
    'updatedAt' in value &&
    typeof value.updatedAt === 'string'
  );
}
```

### Business Rules

1. **Single Active Theme**: Only one theme can be active at a time
2. **Graceful Degradation**: Invalid theme values fall back to 'light'
3. **Persistence Guarantee**: Theme changes MUST be persisted immediately to localStorage
4. **Instant Application**: Theme changes MUST apply within the same render cycle
5. **Accessibility Enforcement**: All themes MUST meet WCAG 2.1 Level AA contrast requirements

### Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| localStorage unavailable | Use 'light' theme, show warning, don't crash |
| Corrupted JSON in localStorage | Fall back to 'light', clear invalid data |
| Unknown theme mode string | Fall back to 'light', log warning |
| Rapid theme switching | Debounce is NOT required (CSS handles instantly) |
| Missing CSS class definition | Theme applies but may show default colors |
| User clears localStorage | Next load uses 'light' default |

---

## Data Flow Diagrams

### Initial Load Flow

```
Application Start
    ↓
useAppTheme() hook initializes
    ↓
Read localStorage['tech-connect-theme-mode']
    ↓
Validate & migrate if needed
    ↓
Set initial state: theme = validatedMode
    ↓
useEffect: Apply CSS class to document.documentElement
    ↓
User sees themed UI
```

### Theme Change Flow

```
User clicks theme option in UI
    ↓
ThemeSelector calls setTheme('green')
    ↓
useAppTheme updates state: setTheme('green')
    ↓
Update localStorage with new preference
    ↓
React re-renders (synchronous)
    ↓
useEffect runs: Apply 'green-mode-active' class
    ↓
Browser applies CSS overrides (instant)
    ↓
User sees green theme (<1 second total)
```

### Persistence Flow

```
Theme Change Event
    ↓
Create ThemePreference object
    ↓
Serialize to JSON
    ↓
localStorage.setItem('tech-connect-theme-mode', json)
    ↓
Preference persisted
    ↓
[Later: Browser close/reopen]
    ↓
App loads, reads from localStorage
    ↓
Theme restored automatically
```

---

## Security Considerations

1. **XSS Prevention**: Theme values are validated before use; no user input directly becomes CSS
2. **localStorage Safety**: JSON parsing wrapped in try-catch to prevent crashes
3. **CSS Injection**: Theme class names are hardcoded constants, not user-supplied
4. **Privacy**: Theme preference is client-side only, not transmitted to servers

---

## Performance Considerations

1. **Load Time**: localStorage read is synchronous (~1ms), CSS class change is instant
2. **Memory**: Four theme definitions (~2KB total), minimal memory footprint
3. **Rendering**: CSS custom properties are hardware-accelerated by browsers
4. **Storage**: localStorage entry is ~100 bytes, negligible storage impact

---

## Future Extensions

Possible future enhancements (out of current scope):
- Server-side theme sync across devices (requires authentication)
- User-customizable color values (requires color picker UI)
- Automatic theme switching based on time of day (requires scheduler)
- Theme preview before selection (requires modal or inline preview)

---

## Summary

The data model defines three primary structures:
1. **ThemeMode**: Type alias for available theme options
2. **ThemePreference**: User preference with metadata for persistence
3. **ThemeDefinition**: Complete theme specification with colors and accessibility data

All entities are designed for:
- Type safety (TypeScript)
- Backward compatibility (legacy string values)
- Accessibility compliance (WCAG 2.1 AA)
- Performance (minimal overhead)
- Extensibility (easy to add more themes)

**Next Phase**: Create contracts/ directory with TypeScript interfaces and API specifications.
