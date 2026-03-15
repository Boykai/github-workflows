# Data Model: Frontend Theme Audit — Light/Dark Mode Contrast & Style Consistency

**Feature**: `037-theme-contrast-audit` | **Date**: 2026-03-12 | **Phase**: 1

## Entities

### Theme Token

A named CSS custom property that maps to different color values in Light and Dark modes.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `token_name` | string | CSS custom property name (e.g., `--background`) | Must start with `--`; unique within scope |
| `light_value` | string | HSL value in Light mode (e.g., `41 82% 95%`) | Valid HSL triplet |
| `dark_value` | string | HSL value in Dark mode (e.g., `236 28% 7%`) | Valid HSL triplet |
| `category` | enum | Usage category | One of: `background`, `text`, `border`, `shadow`, `accent`, `status`, `interactive` |
| `tailwind_alias` | string | Tailwind @theme mapping (e.g., `--color-background`) | Optional; maps via `hsl(var(--token))` |

**Current Token Inventory** (34 tokens):

| Token | Category | Light HSL | Dark HSL |
|-------|----------|-----------|----------|
| `--background` | background | `41 82% 95%` | `236 28% 7%` |
| `--foreground` | text | `228 24% 16%` | `38 45% 89%` |
| `--card` | background | `40 88% 97%` | `238 22% 11%` |
| `--card-foreground` | text | `228 24% 16%` | `38 45% 89%` |
| `--popover` | background | `39 82% 96%` | `238 23% 9%` |
| `--popover-foreground` | text | `228 24% 16%` | `38 45% 89%` |
| `--primary` | accent | `42 90% 48%` | `45 90% 68%` |
| `--primary-foreground` | text | `32 36% 12%` | `236 28% 9%` |
| `--secondary` | background | `38 52% 89%` | `237 14% 17%` |
| `--secondary-foreground` | text | `228 16% 24%` | `38 45% 89%` |
| `--muted` | background | `39 44% 90%` | `237 16% 13%` |
| `--muted-foreground` | text | `228 10% 40%` | `35 24% 72%` |
| `--accent` | accent | `230 34% 40%` | `242 28% 25%` |
| `--accent-foreground` | text | `40 90% 97%` | `38 45% 89%` |
| `--destructive` | status | `0 72% 51%` | `0 65% 53%` |
| `--destructive-foreground` | text | `0 0% 100%` | `240 10% 92%` |
| `--border` | border | `37 34% 78%` | `239 16% 24%` |
| `--input` | background | `39 50% 93%` | `238 18% 15%` |
| `--ring` | interactive | `42 90% 48%` | `45 90% 68%` |
| `--panel` | background | `40 78% 95%` | `238 19% 11%` |
| `--panel-foreground` | text | `228 24% 16%` | `38 45% 89%` |
| `--glow` | accent | `47 100% 79%` | `45 82% 72%` |
| `--gold` | accent | `42 92% 52%` | `45 92% 67%` |
| `--night` | background | `226 28% 19%` | `235 34% 5%` |
| `--star` | accent | `38 72% 42%` | `43 76% 92%` |
| `--star-soft` | accent | `43 84% 62%` | `44 86% 74%` |
| `--priority-p0` | status | `0 72% 51%` | `0 72% 51%` |
| `--priority-p1` | status | `25 95% 53%` | `25 95% 53%` |
| `--priority-p2` | status | `217 91% 60%` | `217 91% 60%` |
| `--priority-p3` | status | `142 71% 45%` | `142 71% 45%` |
| `--sync-connected` | status | `160 84% 39%` | `160 84% 47%` |
| `--sync-polling` | status | `38 92% 50%` | `38 92% 56%` |
| `--sync-connecting` | status | `199 89% 48%` | `199 89% 56%` |
| `--sync-disconnected` | status | `0 84% 60%` | `0 84% 65%` |

### Component Variant

A distinct visual configuration of a UI component with theme-specific styling.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `component_name` | string | Base component name (e.g., `Button`) | Must match a file in `frontend/src/components/` |
| `variant_name` | string | Variant identifier (e.g., `primary`, `destructive`) | Unique per component |
| `states` | list[enum] | Applicable interactive states | Subset of: `default`, `hover`, `focus`, `active`, `disabled` |
| `token_assignments` | map | Token-to-property mappings | Maps CSS properties to token names |
| `light_compliant` | boolean | Passes WCAG AA in Light mode | Verified by contrast check |
| `dark_compliant` | boolean | Passes WCAG AA in Dark mode | Verified by contrast check |

**Component Variant Registry** (files with CVA variants):

| Component | File | Variants | States |
|-----------|------|----------|--------|
| Button | `ui/button.tsx` | default, destructive, outline, secondary, ghost, link | default, hover, focus, active, disabled |
| Card | `ui/card.tsx` | default | default, hover |
| Input | `ui/input.tsx` | default | default, focus, disabled |
| Tooltip | `ui/tooltip.tsx` | default | default (visible) |
| ConfirmationDialog | `ui/confirmation-dialog.tsx` | default | default |
| Solar Chip | `index.css` | base, soft, neutral, success, warning, danger, violet | default |
| Solar Action | `index.css` | base, danger | default, hover, active |
| Solar Halo | `index.css` | base | default, hover, pulse |

### Contrast Pair

A measurable relationship between a foreground element and its background surface.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `foreground_token` | string | Token used for foreground (text, icon, border) | Must reference a Theme Token |
| `background_token` | string | Token used for background surface | Must reference a Theme Token |
| `context` | string | Where this pair appears (e.g., `card body text`) | Descriptive |
| `light_ratio` | float | Computed contrast ratio in Light mode | Must be calculated via WCAG formula |
| `dark_ratio` | float | Computed contrast ratio in Dark mode | Must be calculated via WCAG formula |
| `threshold` | float | Required minimum ratio | 4.5 for normal text, 3.0 for large text/UI |
| `light_pass` | boolean | Light mode meets threshold | `light_ratio >= threshold` |
| `dark_pass` | boolean | Dark mode meets threshold | `dark_ratio >= threshold` |

**Critical Contrast Pairs to Verify**:

| Foreground | Background | Context | Threshold |
|------------|------------|---------|-----------|
| `--foreground` | `--background` | Page body text | 4.5:1 |
| `--card-foreground` | `--card` | Card body text | 4.5:1 |
| `--popover-foreground` | `--popover` | Popover/dropdown text | 4.5:1 |
| `--primary-foreground` | `--primary` | Primary button text | 4.5:1 |
| `--secondary-foreground` | `--secondary` | Secondary button text | 4.5:1 |
| `--muted-foreground` | `--muted` | Muted/placeholder text | 4.5:1 |
| `--accent-foreground` | `--accent` | Accent element text | 4.5:1 |
| `--destructive-foreground` | `--destructive` | Destructive button text | 4.5:1 |
| `--panel-foreground` | `--panel` | Panel body text | 4.5:1 |
| `--muted-foreground` | `--background` | Subtle text on page | 4.5:1 |
| `--primary` | `--background` | Primary links/headings | 3.0:1 |
| `--border` | `--background` | Input/card borders | 3.0:1 |
| `--border` | `--card` | Card borders | 3.0:1 |
| `--ring` | `--background` | Focus ring indicator | 3.0:1 |
| `--destructive` | `--background` | Error text | 3.0:1 |
| `--priority-p0` | `--card` | P0 badge on card | 3.0:1 |
| `--priority-p1` | `--card` | P1 badge on card | 3.0:1 |
| `--priority-p2` | `--card` | P2 badge on card | 3.0:1 |
| `--priority-p3` | `--card` | P3 badge on card | 3.0:1 |
| `--sync-connected` | `--background` | Sync status indicator | 3.0:1 |

### Theme Context Scope

The boundary within the component tree where a specific theme applies.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `root_selector` | string | CSS selector that activates the theme | `.dark` on `<html>` element |
| `inheritance_chain` | string | How theme propagates through DOM | `html.dark → body → #root → App → …` |
| `portal_targets` | list[string] | Portal mount points | All mount to `document.body` (inherits from `<html>`) |
| `isolated_subtrees` | list[string] | Subtrees that escape theme control | None detected |
| `transition_mechanism` | string | How theme transitions are handled | `theme-transitioning` class with 600ms duration |

**Portal-Rendered Components** (9 identified):

| Component | Portal Target | Theme Inherits |
|-----------|--------------|----------------|
| `ChoreCard` tooltip | `document.body` | ✅ Yes |
| `ModelSelector` dropdown | `document.body` | ✅ Yes |
| `StageCard` dropdown | `document.body` | ✅ Yes |
| `NotificationBell` dropdown | `document.body` | ✅ Yes |
| `CleanUpSummary` modal | `document.body` | ✅ Yes |
| `CleanUpAuditHistory` modal | `document.body` | ✅ Yes |
| `CleanUpConfirmModal` modal | `document.body` | ✅ Yes |
| `AgentIconPickerModal` modal | `document.body` | ✅ Yes |
| `AddAgentPopover` popover | `document.body` | ✅ Yes |

## Relationships

```
Theme Token ──(defines colors for)──→ Component Variant
Theme Token ──(participates in)──→ Contrast Pair (as foreground or background)
Component Variant ──(has multiple)──→ Contrast Pair (per state)
Theme Context Scope ──(provides tokens to)──→ Component Variant
Theme Context Scope ──(propagates to)──→ Portal-Rendered Components
```

## Validation Rules

1. Every `Component Variant` must have all `Contrast Pair` entries passing (both `light_pass` and `dark_pass` = true).
2. No `Theme Token` with category `background` may use pure `#000000` (Dark) or pure `#FFFFFF` (Light).
3. Every `Theme Token` must have both `light_value` and `dark_value` defined.
4. All `Portal-Rendered Components` must have `theme_inherits` = true.
5. No `isolated_subtrees` are permitted in the `Theme Context Scope`.

## State Transitions

```
Theme Toggle Flow:
  [Light Active] ──(user clicks toggle)──→ [Transitioning] ──(600ms)──→ [Dark Active]
  [Dark Active]  ──(user clicks toggle)──→ [Transitioning] ──(600ms)──→ [Light Active]
  [System Mode]  ──(OS preference changes)──→ [Resolve to Light or Dark]

  Transitioning state:
    1. Add 'theme-transitioning' class to <html>
    2. Remove current theme class ('light' or 'dark')
    3. Add new theme class
    4. After 600ms, remove 'theme-transitioning' class
```
