# Component Contracts: Frontend Style Audit & Celestial/Cosmic Theme Animation Enhancement

**Feature**: 031-celestial-theme-animations | **Date**: 2026-03-09

## New Components

### CelestialLoader

**File**: `frontend/src/components/common/CelestialLoader.tsx`
**Type**: Presentational component (no state, no side effects)

#### Props

```typescript
interface CelestialLoaderProps {
  size?: 'sm' | 'md' | 'lg';  // Default: 'md'
  label?: string;               // Default: 'Loading…'
  className?: string;           // Additional CSS classes on wrapper
}
```

#### Rendered Structure

```html
<div role="status" aria-label="{label}" class="flex flex-col items-center gap-2 {className}">
  <!-- Orbital container -->
  <div class="relative {sizeClasses.orbit}">
    <!-- Central sun -->
    <div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary celestial-pulse-glow {sizeClasses.sun}" />
    <!-- Orbit ring -->
    <div class="absolute inset-0 rounded-full border border-primary/30 celestial-orbit-spin-fast" />
    <!-- Planet dot -->
    <div class="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-gold {sizeClasses.planet}" />
  </div>
  <!-- Screen reader label -->
  <span class="sr-only">{label}</span>
</div>
```

#### Behavior

- Renders a pure CSS animated loading indicator with celestial theme
- No JavaScript animations — relies on existing `celestial-pulse-glow` and `celestial-orbit-spin-fast` CSS classes
- Automatically respects `prefers-reduced-motion` via existing CSS rules (orbit stops, glow stops)
- Accessible: `role="status"` + `aria-label` for screen readers

#### Size Variants

| Size | Orbit | Sun | Planet |
|------|-------|-----|--------|
| `sm` | `h-8 w-8` | `h-2 w-2` | `h-1.5 w-1.5` |
| `md` | `h-12 w-12` | `h-3 w-3` | `h-2 w-2` |
| `lg` | `h-16 w-16` | `h-4 w-4` | `h-2.5 w-2.5` |

---

## Modified Components

### index.css (Design Token System)

**File**: `frontend/src/index.css`
**Changes**: Extend existing `@theme` block and `@layer base` rules

#### New Additions to @theme Block

```css
/* Theme transition token */
--transition-theme-shift: 600ms ease-in-out;

/* Loader animation token */
--animate-celestial-loader: orbit-spin 1.8s linear infinite;

/* Theme shift keyframe */
@keyframes theme-shift {
  0% { opacity: 0; }
  50% { opacity: 0.3; }
  100% { opacity: 0; }
}
```

#### New Utility Class in @layer base

```css
/* Theme transition overlay */
.theme-transitioning {
  transition:
    background-color var(--transition-theme-shift),
    color var(--transition-theme-shift);
}
.theme-transitioning::after {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 9999;
  background: linear-gradient(
    135deg,
    hsl(var(--gold) / 0.08) 0%,
    hsl(var(--night) / 0.12) 50%,
    hsl(var(--glow) / 0.06) 100%
  );
  animation: theme-shift var(--transition-theme-shift) ease-in-out both;
}
```

#### Updated prefers-reduced-motion Block

```css
/* Add to existing reduced-motion block: */
.theme-transitioning,
.theme-transitioning::after {
  animation: none !important;
  transition: none !important;
}
```

---

### ThemeProvider.tsx

**File**: `frontend/src/components/ThemeProvider.tsx`
**Changes**: Add theme-transitioning class during theme toggle

#### Current Behavior
```typescript
// Current: directly sets class on root element
const root = window.document.documentElement;
root.classList.remove('light', 'dark');
root.classList.add(resolvedTheme);
```

#### New Behavior
```typescript
// New: add transition class, toggle theme, remove after timeout
const root = window.document.documentElement;
root.classList.add('theme-transitioning');
root.classList.remove('light', 'dark');
root.classList.add(resolvedTheme);
setTimeout(() => {
  root.classList.remove('theme-transitioning');
}, 600);
```

**Impact**: Purely additive. No prop changes, no API changes. The `useTheme()` hook return value is unchanged.

---

### UI Components (components/ui/)

#### button.tsx
- **Add**: `celestial-focus` class to all button variants for themed focus ring
- **Add**: `solar-action` class to default/primary variants for hover lift effect
- **Audit**: Verify all color values reference design tokens

#### card.tsx
- **Add**: `celestial-panel` class for hover glow lift effect
- **Add**: `celestial-fade-in` class for entry animation
- **Audit**: Verify border, shadow, radius use design tokens

#### input.tsx
- **Add**: `celestial-focus` class for themed focus ring
- **Audit**: Verify border, background, text colors reference tokens

#### tooltip.tsx
- **Audit**: Verify styling uses `--popover`, `--foreground`, `--border` tokens
- **No animation changes** — tooltip enter/exit already handled by Radix

#### confirmation-dialog.tsx
- **Add**: `celestial-fade-in` class on dialog content
- **Audit**: Backdrop overlay alignment with celestial theme
- **Text casing**: Verify button labels follow convention

---

### Agent Components (components/agents/)

| Component | Token Audit | Text Casing | Animation |
|-----------|------------|-------------|-----------|
| AgentCard.tsx | Verify card colors, shadows | Title Case for agent names | `celestial-panel` hover |
| AgentsPanel.tsx | Verify panel styling | Title Case for heading | `celestial-fade-in` on panel |
| AddAgentModal.tsx | Verify modal styling | Sentence case for descriptions | `celestial-fade-in` on modal |
| AgentIconCatalog.tsx | Verify grid styling | Title Case for heading | Hover glow on icon items |
| AgentIconPickerModal.tsx | Verify modal styling | Title Case for modal title | `celestial-fade-in` |
| AgentInlineEditor.tsx | Verify input styling | Sentence case for labels | `celestial-focus` on inputs |
| AgentChatFlow.tsx | Verify chat styling | Sentence case for messages | N/A (inherits from chat) |
| BulkModelUpdateDialog.tsx | Verify dialog styling | Title Case for dialog title | `celestial-fade-in` |
| ToolsEditor.tsx | Verify form styling | Sentence case for form labels | `celestial-focus` on inputs |
| AgentAvatar.tsx | Verify image/icon styling | N/A | Subtle glow on hover |

---

### Board Components (components/board/)

| Component | Token Audit | Text Casing | Animation |
|-----------|------------|-------------|-----------|
| ProjectBoard.tsx | Verify layout styling | Title Case for board title | `celestial-fade-in` |
| BoardColumn.tsx | Verify column styling | Title Case for column headers | N/A (container) |
| BoardToolbar.tsx | Verify toolbar styling | Title Case for toolbar labels | `solar-action` on buttons |
| IssueCard.tsx | Verify card styling | Title Case for issue title | `celestial-panel` hover |
| IssueDetailModal.tsx | Verify modal styling | Title Case for modal heading | `celestial-fade-in` |
| RefreshButton.tsx | Verify button styling | N/A (icon only) | `solar-action` hover |
| CleanUpButton.tsx | Verify button styling | Title Case for label | `solar-action` hover |
| AgentTile.tsx | Verify tile styling | Title Case for agent name | Subtle hover glow |
| BlockingChainPanel.tsx | Verify panel styling | Title Case for heading | `celestial-fade-in` |

---

### Chat Components (components/chat/)

| Component | Token Audit | Text Casing | Animation |
|-----------|------------|-------------|-----------|
| ChatInterface.tsx | Verify layout styling | Sentence case for placeholder | N/A (container) |
| ChatPopup.tsx | Verify popup styling | Title Case for header | `celestial-fade-in` on open |
| MessageBubble.tsx | Verify bubble styling | N/A (user content) | `celestial-fade-in` for messages |
| ChatToolbar.tsx | Verify toolbar styling | Sentence case for tooltips | `solar-action` on buttons |
| MentionInput.tsx | Verify input styling | Sentence case for placeholder | `celestial-focus` |
| VoiceInputButton.tsx | Verify button styling | N/A (icon only) | `solar-action` hover |

---

### Chores Components (components/chores/)

| Component | Token Audit | Text Casing | Animation |
|-----------|------------|-------------|-----------|
| ChoresPanel.tsx | Verify panel styling | Title Case for heading | `celestial-fade-in` |
| ChoreCard.tsx | Verify card styling | Title Case for chore name | `celestial-panel` hover |
| AddChoreModal.tsx | Verify modal styling | Title Case for modal title | `celestial-fade-in` |
| ChoreChatFlow.tsx | Verify chat styling | Sentence case | N/A |
| ChoreScheduleConfig.tsx | Verify form styling | Sentence case for labels | `celestial-focus` on inputs |
| FeaturedRitualsPanel.tsx | Verify panel styling | Title Case for heading | `celestial-fade-in` |

---

### Pipeline Components (components/pipeline/)

| Component | Token Audit | Text Casing | Animation |
|-----------|------------|-------------|-----------|
| PipelineBoard.tsx | Verify board styling | Title Case for board title | `celestial-fade-in` |
| PipelineFlowGraph.tsx | Verify graph styling | N/A (data-driven) | Subtle glow on connections |
| StageCard.tsx | Verify card styling | Title Case for stage name | `celestial-panel` hover |
| AgentNode.tsx | Verify node styling | Title Case for agent name | Hover glow |
| ModelSelector.tsx | Verify dropdown styling | Sentence case for options | `celestial-focus` |
| SavedWorkflowsList.tsx | Verify list styling | Title Case for heading | `celestial-fade-in` |

---

### Settings Components (components/settings/)

| Component | Token Audit | Text Casing | Animation |
|-----------|------------|-------------|-----------|
| GlobalSettings.tsx | Verify layout styling | Title Case for headings | `celestial-fade-in` |
| SettingsSection.tsx | Verify section styling | Title Case for section title | N/A (container) |
| DisplayPreferences.tsx | Verify form styling | Sentence case for labels | `celestial-focus` on inputs |
| AIPreferences.tsx | Verify form styling | Sentence case for labels | `celestial-focus` on inputs |
| NotificationPreferences.tsx | Verify form styling | Sentence case for labels | `celestial-focus` on inputs |
| AdvancedSettings.tsx | Verify form styling | Sentence case for labels | `celestial-focus` on inputs |

---

### Tools Components (components/tools/)

| Component | Token Audit | Text Casing | Animation |
|-----------|------------|-------------|-----------|
| ToolsPanel.tsx | Verify panel styling | Title Case for heading | `celestial-fade-in` |
| ToolCard.tsx | Verify card styling | Title Case for tool name | `celestial-panel` hover |
| ToolSelectorModal.tsx | Verify modal styling | Title Case for modal title | `celestial-fade-in` |
| McpPresetsGallery.tsx | Verify gallery styling | Title Case for heading | `celestial-fade-in` |

---

### Layout Components (layout/)

| Component | Token Audit | Text Casing | Animation |
|-----------|------------|-------------|-----------|
| AppLayout.tsx | Already themed ✅ | Verify any text labels | Already has starfield + orbits ✅ |
| Sidebar.tsx | Verify nav styling | Title Case for nav items | Hover glow on nav items |
| TopBar.tsx | Verify bar styling | Title Case for app name | `solar-action` on buttons |
| Breadcrumb.tsx | Verify breadcrumb styling | Title Case for segments | N/A |
| ProjectSelector.tsx | Verify dropdown styling | Title Case for project names | `celestial-focus` |
| NotificationBell.tsx | Verify bell styling | N/A (icon) | Subtle glow on notification dot |

---

### Page Components (pages/)

| Component | Token Audit | Text Casing | Animation |
|-----------|------------|-------------|-----------|
| AppPage.tsx | Verify dashboard styling | Title Case for headings | `celestial-fade-in` on load |
| LoginPage.tsx | Verify login styling | Title Case for heading | Celestial background, `celestial-fade-in` |
| ProjectsPage.tsx | Verify list styling | Title Case for heading | `celestial-fade-in` |
| AgentsPage.tsx | Verify page styling | Title Case for heading | `celestial-fade-in` |
| AgentsPipelinePage.tsx | Verify page styling | Title Case for heading | `celestial-fade-in` |
| ToolsPage.tsx | Verify page styling | Title Case for heading | `celestial-fade-in` |
| ChoresPage.tsx | Verify page styling | Title Case for heading | `celestial-fade-in` |
| SettingsPage.tsx | Verify page styling | Title Case for heading | `celestial-fade-in` |
| NotFoundPage.tsx | Verify error styling | Title Case for heading | Celestial styling |

---

## API Contracts

No API contracts. This feature has zero backend changes — no new endpoints, no modified endpoints, no new request/response schemas.

## Integration Patterns

### Applying Celestial Animation Classes

**Standard pattern** (for any card/panel component):
```tsx
<div className="celestial-panel celestial-fade-in rounded-lg border border-border bg-card p-4 shadow-sm">
  {/* component content */}
</div>
```

**Button hover enhancement** (for primary action buttons):
```tsx
<button className="solar-action celestial-focus rounded-md bg-primary px-4 py-2 text-primary-foreground">
  Save Changes
</button>
```

**Interactive element focus** (for inputs, selects):
```tsx
<input className="celestial-focus rounded-md border border-input bg-background px-3 py-2" />
```

**Loading state replacement**:
```tsx
// Before
<div>Loading...</div>

// After
<CelestialLoader size="md" label="Loading agents…" />
```

### Theme Transition Integration

The theme transition is automatic — no component changes needed beyond `ThemeProvider.tsx`. When `setTheme()` is called, the `theme-transitioning` class is added and removed automatically.
