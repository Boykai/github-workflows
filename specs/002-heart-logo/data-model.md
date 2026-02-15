# Data Model: Heart Logo on Homepage

**Feature**: 002-heart-logo | **Date**: 2026-02-15 | **Spec**: [spec.md](./spec.md)

## Phase 1: Entities & Relationships

This document defines entities and their relationships for the heart logo feature.

---

## Entity Overview

This feature involves a single visual entity (Heart Logo) with no data persistence, no API contracts, and no database schema changes. It is a pure frontend presentation layer addition.

---

## Entity 1: Heart Logo (Visual Asset)

**Type**: Static Asset (SVG File)  
**Storage**: Filesystem (`frontend/public/heart-logo.svg`)  
**Lifecycle**: Created once during implementation, persists as static file  
**Ownership**: Frontend presentation layer

### Attributes

| Attribute | Type | Description | Validation | Source |
|-----------|------|-------------|------------|--------|
| **File Name** | string | `heart-logo.svg` | Must be valid filename | Implementation |
| **Format** | SVG | Scalable vector graphic | Must be valid SVG XML | Design/Implementation |
| **Size** | File size | Recommended < 10KB | Should be optimized | Implementation |
| **Dimensions** | Viewbox | Intrinsic aspect ratio | Should be square or 16:9 | Design |
| **Color** | CSS/SVG fill | Brand colors | Must use CSS variables or brand hex codes | Design |

### Validation Rules

1. **File existence**: Logo file must exist at `/frontend/public/heart-logo.svg`
2. **SVG validity**: Must be well-formed XML and valid SVG
3. **File size**: Should be < 10KB for fast loading (SC-001: load within 1 second)
4. **Scalability**: Must not have fixed width/height attributes (use viewBox instead)
5. **Accessibility**: SVG should have `<title>` element inside for enhanced accessibility

### Relationships

- **Referenced by**: React component (App.tsx) via `<img src="/heart-logo.svg" />`
- **Styled by**: CSS class in App.css (`.logo`)
- **No database relationship**: This is a static asset, not a database entity

---

## Entity 2: Logo Component (React JSX)

**Type**: UI Component (inline JSX element)  
**Storage**: Component code (`frontend/src/App.tsx`)  
**Lifecycle**: Rendered when login page is displayed  
**Ownership**: App component

### Attributes

| Attribute | Type | Description | Validation | Source |
|-----------|------|-------------|------------|--------|
| **src** | string | `/heart-logo.svg` | Must be valid path | Implementation (fixed value) |
| **alt** | string | Descriptive alt text | Must not be empty (FR-005) | Implementation (fixed value) |
| **className** | string | `logo` | Must match CSS class | Implementation (fixed value) |

### Validation Rules

1. **src attribute**: Must reference valid file path (`/heart-logo.svg`)
2. **alt attribute**: Must be descriptive (e.g., "Heart logo - Tech Connect 2026") for FR-005
3. **className**: Must reference existing CSS class for styling
4. **Tag type**: Must be `<img>` (not `<div>` with background, for semantic HTML)
5. **No event handlers**: Must not have onClick or other interaction handlers (FR-007)

### Relationships

- **References**: Heart Logo asset (`/heart-logo.svg`)
- **Styled by**: CSS class (`.logo` in App.css)
- **Contained by**: Login section JSX (App.tsx lines 68-71)
- **No state relationship**: Static element, no React state or props

---

## Entity 3: Logo Styling (CSS Rules)

**Type**: CSS Class  
**Storage**: Stylesheet (`frontend/src/App.css`)  
**Lifecycle**: Loaded with component styles  
**Ownership**: App component styles

### Attributes

| Attribute | Type | Description | Validation | Source |
|-----------|------|-------------|------------|--------|
| **Class name** | string | `.logo` | Must be valid CSS selector | Implementation (fixed value) |
| **width** | CSS value | e.g., `clamp(60px, 10vw, 120px)` | Must be responsive | Research Decision 5 |
| **height** | CSS value | `auto` | Must maintain aspect ratio | Implementation |
| **display** | CSS value | `block` | Standard display | Implementation |
| **margin** | CSS value | e.g., `0 auto 1rem auto` | Center horizontally + bottom spacing | Implementation |
| **fill** (optional) | CSS value | `var(--color-primary)` | For SVG color | Research Decision 9 |

### Validation Rules

1. **Responsive sizing**: Must use clamp() or media queries (FR-003)
2. **Aspect ratio**: height must be `auto` to maintain proportions (FR-004)
3. **Centering**: Must use margin auto or flexbox for horizontal centering (FR-001)
4. **Brand colors**: Should reference CSS variables if coloring SVG (FR-006)
5. **No pointer cursor**: Must not use `cursor: pointer` (FR-007: non-interactive)

### Relationships

- **Applied to**: Logo component (`<img className="logo" />`)
- **References**: CSS variables from index.css (optional, for colors)
- **Scoped to**: App component (App.css)

---

## Non-Entities (Explicitly Excluded)

The following are **NOT** part of this feature's data model:

1. **Database Table**: No database entity; logo is a static file
2. **API Endpoint**: No API calls required; logo served as static asset by Vite
3. **User Preferences**: Logo is not customizable per-user
4. **Theme Variants**: No dark/light mode specific logos (out of scope per spec)
5. **State Management**: No React state, Redux, or context required
6. **Logo Metadata**: No tracking, analytics, or metadata beyond file attributes

---

## Relationship Diagram

```text
[Heart Logo SVG File]
   │
   │ (referenced by src attribute)
   │
   ▼
[Logo Component JSX] ◄──────────── (styled by) ──────────── [Logo CSS Class]
   │                                                               │
   │ (rendered in)                                                 │
   │                                                               │
   ▼                                                               ▼
[App.tsx Login Section]                                  [App.css Stylesheet]
```

**Data Flow**:
1. Browser requests `/heart-logo.svg` → Vite serves static file
2. App.tsx renders `<img src="/heart-logo.svg" className="logo" />`
3. Browser applies CSS from `.logo` class
4. Logo displays at top center of login page

**No Network Requests** (beyond initial file fetch):
- Logo is a static asset (not dynamically generated)
- No API calls
- No database queries
- No WebSocket connections

---

## Validation Summary

### Frontend Validation (Implementation Time)

- [ ] SVG file exists at `frontend/public/heart-logo.svg`
- [ ] SVG is valid XML and well-formed
- [ ] SVG uses viewBox (not fixed width/height)
- [ ] SVG file size < 10KB
- [ ] img element has non-empty alt text
- [ ] img element has className="logo"
- [ ] img element has no click handlers
- [ ] CSS class `.logo` exists in App.css
- [ ] CSS includes responsive sizing (clamp or media queries)
- [ ] CSS maintains aspect ratio (height: auto)

### Runtime Validation (Manual Testing)

- [ ] Logo displays at top center of login page
- [ ] Logo loads within 1 second (SC-001)
- [ ] Logo scales on window resize (SC-002)
- [ ] Logo visible on mobile/tablet/desktop (SC-002, SC-003)
- [ ] Screen reader announces alt text (SC-004)
- [ ] Alt text displays if image fails to load (FR-008)
- [ ] Logo non-interactive (clicking does nothing) (FR-007)

---

## Notes

- **Simplicity**: This data model reflects the minimal nature of the feature - a single static asset with no business logic, no persistence, and no API integration
- **No Migration**: No database migration files needed
- **No Schema**: No GraphQL, OpenAPI, or database schema changes
- **No Serialization**: No JSON/XML data structures beyond SVG file format
- **Constitution Alignment**: Adheres to principle V (Simplicity & DRY) by avoiding unnecessary abstractions
