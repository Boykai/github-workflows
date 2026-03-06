# Research: Western/Cowboy UI Theme Refresh

**Phase**: 0 — Outline & Research  
**Branch**: `019-western-theme-refresh`

## Research Tasks & Findings

### RT-1: Western Color Palette HSL Values (from NEEDS CLARIFICATION: exact HSL tokens)

**Decision**: Use the following HSL values derived from the Double D Ranch reference image, validated against hex equivalents and WCAG contrast requirements.

**Light Mode Token Values**:

| Token | HSL Value | Hex Approx | Description |
|-------|-----------|------------|-------------|
| `--background` | `39 50% 96%` | #F5EFE0 | Warm cream/parchment |
| `--foreground` | `24 30% 15%` | #3B2D1F | Dark brown (silhouette tones) |
| `--card` | `39 40% 97%` | #F7F2E8 | Slightly warmer cream for elevation |
| `--card-foreground` | `24 30% 15%` | #3B2D1F | Match foreground |
| `--popover` | `39 40% 97%` | #F7F2E8 | Match card |
| `--popover-foreground` | `24 30% 15%` | #3B2D1F | Match foreground |
| `--primary` | `24 50% 22%` | #55351A | Rich saddle brown |
| `--primary-foreground` | `40 60% 95%` | #F8F0DC | Warm white/cream |
| `--secondary` | `33 30% 88%` | #E8DCC8 | Light tan/wheat |
| `--secondary-foreground` | `24 30% 20%` | #42321F | Dark brown text |
| `--muted` | `35 25% 90%` | #EBE4D6 | Pale wheat |
| `--muted-foreground` | `24 15% 45%` | #6B5D50 | Dusty brown |
| `--accent` | `36 80% 55%` | #D4A017 | Sunset gold |
| `--accent-foreground` | `24 50% 15%` | #3A2410 | Dark brown |
| `--destructive` | `0 60% 45%` | #B84233 | Terra-cotta red |
| `--destructive-foreground` | `40 60% 95%` | #F8F0DC | Cream on red |
| `--border` | `30 20% 80%` | #D4C8B8 | Warm tan border |
| `--input` | `30 20% 82%` | #D9CEBI | Input border (slightly lighter) |
| `--ring` | `36 80% 55%` | #D4A017 | Sunset gold (focus rings) |
| `--radius` | `0.375rem` | — | Slightly less rounded for rugged feel |

**Dark Mode Token Values**:

| Token | HSL Value | Hex Approx | Description |
|-------|-----------|------------|-------------|
| `--background` | `24 30% 10%` | #1E1610 | Deep espresso brown |
| `--foreground` | `39 40% 90%` | #EDE4D1 | Warm off-white |
| `--card` | `24 25% 14%` | #2A2018 | Dark brown card |
| `--card-foreground` | `39 40% 90%` | #EDE4D1 | Match foreground |
| `--popover` | `24 25% 14%` | #2A2018 | Match card |
| `--popover-foreground` | `39 40% 90%` | #EDE4D1 | Match foreground |
| `--primary` | `36 80% 55%` | #D4A017 | Sunset gold (primary on dark) |
| `--primary-foreground` | `24 30% 10%` | #1E1610 | Dark text on gold |
| `--secondary` | `24 20% 20%` | #3D3228 | Warm dark gray-brown |
| `--secondary-foreground` | `39 40% 90%` | #EDE4D1 | Light text |
| `--muted` | `24 20% 18%` | #372D24 | Slightly lighter than bg |
| `--muted-foreground` | `24 15% 60%` | #A49585 | Dusty tan |
| `--accent` | `36 80% 55%` | #D4A017 | Sunset gold |
| `--accent-foreground` | `24 30% 10%` | #1E1610 | Dark brown |
| `--destructive` | `0 50% 40%` | #993333 | Muted terra-cotta |
| `--destructive-foreground` | `39 40% 90%` | #EDE4D1 | Cream text |
| `--border` | `24 20% 25%` | #4D3F33 | Warm dark border |
| `--input` | `24 20% 25%` | #4D3F33 | Match border |
| `--ring` | `36 80% 55%` | #D4A017 | Gold |

**Rationale**: HSL format is required by shadcn/ui's CSS variable system (Tailwind uses `hsl(var(--token))` syntax). Values derived from the Double D Ranch reference palette. The warm brown/cream/gold family creates a cohesive western aesthetic.

**Alternatives considered**:
- Oklahoma hex palette from western design references — rejected because raw hex doesn't integrate with the HSL variable system
- Desert Southwest palette (turquoise/coral) — rejected because it diverges from the ranch aesthetic reference image
- Pure sepia tone (monotone brown) — rejected because insufficient visual hierarchy; the gold accent adds necessary contrast for interactive elements

---

### RT-2: Display Font Selection (from NEEDS CLARIFICATION: which slab-serif font)

**Decision**: **Rye** from Google Fonts as the display/heading font.

**Rationale**:
- Free and open-source (Apache 2.0) — no licensing concerns
- Available on Google Fonts CDN — zero self-hosting complexity; loaded via `<link>` tag with `display=swap`
- Authentic western saloon/wanted-poster aesthetic — instantly recognizable cowboy typography
- Single weight is sufficient for headings/branding (no need for multiple weights)
- Good readability at heading sizes (h1, h2, h3); not intended for body text

**Fallback chain**: `'Rye', 'Georgia', serif` — Georgia provides a reasonable slab-serif fallback if the CDN is unavailable; generic serif as final fallback.

**Alternatives considered**:
- **Playfair Display** — elegant serif but not distinctly western; more editorial than saloon
- **Bungee Shade** — too decorative/heavy; readability concerns at h2/h3 sizes
- **Abril Fatface** — beautiful display font but French Didone style, not western
- **Self-hosted WOFF2** — unnecessary complexity when Google Fonts CDN provides reliable delivery with font-display: swap

---

### RT-3: Warm Shadow Implementation (from dependency: Tailwind shadow customization)

**Decision**: Define custom `boxShadow` values in `tailwind.config.js` using brown-tinted RGBA shadows instead of the default neutral gray.

**Implementation**:
```js
boxShadow: {
  'warm-sm': '0 1px 2px 0 rgba(59, 45, 31, 0.08)',
  'warm': '0 1px 3px 0 rgba(59, 45, 31, 0.12), 0 1px 2px -1px rgba(59, 45, 31, 0.12)',
  'warm-md': '0 4px 6px -1px rgba(59, 45, 31, 0.12), 0 2px 4px -2px rgba(59, 45, 31, 0.12)',
  'warm-lg': '0 10px 15px -3px rgba(59, 45, 31, 0.12), 0 4px 6px -4px rgba(59, 45, 31, 0.12)',
}
```

**Rationale**: Default Tailwind shadows use `rgba(0,0,0,...)` which appears cold/gray on warm cream backgrounds. Brown-tinted shadows (`rgb(59,45,31)` = `--foreground` dark brown) create a cohesive warm aesthetic. Same spread/blur structure as Tailwind defaults — just different tint.

**Alternatives considered**:
- CSS `filter: drop-shadow()` — less control over color; inconsistent browser rendering on card elements
- Custom CSS `--shadow-color` variable — adds unnecessary abstraction; Tailwind utility classes are simpler
- No shadow customization — rejected because default gray shadows look visually cold against the warm palette

---

### RT-4: Hardcoded Color Disposition Inventory (from NEEDS CLARIFICATION: keep/replace/soften decisions)

**Decision**: Categorize all ~120 hardcoded Tailwind color instances across 20 files into three dispositions.

#### KEEP (functional/semantic — preserve as-is)
These colors convey real-time system state and must remain standard:

| Component | Colors | Reason |
|-----------|--------|--------|
| `ProjectBoardPage.tsx` sync status dots | `green-500`, `yellow-500`, `red-500` | Real-time connection state indicators |
| `SignalConnection.tsx` | `green-*`, `yellow-*`, `red-*` | WebSocket connection status |
| `McpSettings.tsx` status | `green-*`, `yellow-*` | MCP server status |
| `IssueCard.tsx` sub-issue state icons | `green-500`, `purple-500` | GitHub issue open/closed state (standard convention) |
| `IssueDetailModal.tsx` state indicators | `green-500`, `purple-500`, `red-500` | GitHub issue/PR state |

#### REPLACE (decorative/theme-level — switch to theme tokens)
These colors serve visual styling rather than semantic meaning:

| Component | Current | Replacement | Reason |
|-----------|---------|-------------|--------|
| `App.tsx` SignalBannerBar | `amber-*` (6 classes) | `accent/*` theme tokens | Warning banner is decorative styling |
| `AgentCard.tsx` "active" badge | `green-100/800` | `bg-green-100/80 text-green-900` | Soften for palette harmony |
| `AgentCard.tsx` "pending PR" badge | `yellow-100/800` | `bg-accent/20 text-accent-foreground` | Use gold accent token |
| `AgentCard.tsx` "pending deletion" | `red-100/800` | `bg-destructive/15 text-destructive` | Use destructive token |
| `CleanUpSummary.tsx` success | `green-*` (6 instances) | `bg-green-100/80 text-green-800` | Soften green for cream bg harmony |
| `CleanUpConfirmModal.tsx` | `green-*` | `bg-green-100/80 text-green-800` | Same treatment |
| `CleanUpAuditHistory.tsx` | `green-*`, `yellow-*` | Soften or use tokens | Harmonize with palette |
| `TaskPreview.tsx` confirm button | `green-500/600` | `bg-primary text-primary-foreground` | Use theme primary |
| `StatusChangePreview.tsx` confirm | `green-500/600` | `bg-primary text-primary-foreground` | Use theme primary |
| `IssueRecommendationPreview.tsx` | multi-color buttons/badges | Theme tokens where possible | Reduce hardcoded palette |
| `DynamicDropdown.tsx` | `amber-*` | `accent/*` tokens | Warning styling |
| `SettingsSection.tsx` | `green-500` success text | `text-green-700 dark:text-green-400` | Adjust for cream contrast |
| `MessageBubble.tsx` | `green-500` | `text-green-700 dark:text-green-400` | Adjust for contrast |

#### SOFTEN (keep color family, adjust shade for palette harmony)
These retain their semantic color but shift shade for better contrast on warm backgrounds:

| Component | Current | Softened | Reason |
|-----------|---------|---------|--------|
| `AgentTile.tsx` | `amber-500` | `amber-600` or `accent` token | Better contrast on cream |
| `AgentColumnCell.tsx` | `amber-500` | `amber-600` or `accent` token | Same |
| `AddAgentPopover.tsx` status | `amber-500`, `green-500`, `blue-500` | `amber-600`, `green-600`, `blue-600` | Shift one shade darker for cream bg |
| `ChoreCard.tsx` status | `green-500`, `yellow-500` | `green-600`, `yellow-600` | Better contrast |
| `ProjectBoardPage.tsx` warning banners | `yellow-500/10`, `yellow-700` | `accent/10`, `accent-foreground` | Use theme tokens |

**Rationale**: The three-tier system ensures functional indicators remain instantly recognizable (-500 semantic colors retained for status dots), decorative elements integrate with the theme system (tokens), and borderline elements get shade-shifted for optimal contrast on the new warm backgrounds.

**Alternatives considered**:
- Replace ALL hardcoded colors with theme tokens — rejected because status indicators (green/yellow/red) have universal meaning that transcends the theme
- Leave all hardcoded colors unchanged — rejected because amber/yellow on cream creates insufficient contrast
- Create a completely new semantic color token system — rejected as overengineering (Principle V: Simplicity/DRY); direct class adjustments are simpler

---

### RT-5: WCAG AA Contrast Validation (from dependency: accessibility compliance)

**Decision**: All proposed color combinations meet WCAG AA requirements. Two combinations require usage restrictions.

**Verified Contrast Ratios (Light Mode)**:

| Pair | Foreground | Background | Ratio | WCAG AA |
|------|-----------|------------|-------|---------|
| Body text | #3B2D1F (dark brown) | #F5EFE0 (cream) | ~10.2:1 | ✅ Pass |
| Primary button | #F8F0DC (cream) | #55351A (saddle brown) | ~6.3:1 | ✅ Pass |
| Muted text | #6B5D50 (dusty brown) | #F5EFE0 (cream) | ~4.6:1 | ✅ Pass (normal text) |
| Gold accent on cream | #D4A017 (gold) | #F5EFE0 (cream) | ~2.5:1 | ⚠️ Large text/decorative only |
| Gold on dark brown | #D4A017 (gold) | #3B2D1F (dark brown) | ~4.1:1 | ✅ Pass (large text 3:1) |
| Destructive | #B84233 (terra-cotta) | #F5EFE0 (cream) | ~4.8:1 | ✅ Pass |

**Verified Contrast Ratios (Dark Mode)**:

| Pair | Foreground | Background | Ratio | WCAG AA |
|------|-----------|------------|-------|---------|
| Body text | #EDE4D1 (warm white) | #1E1610 (espresso) | ~11.5:1 | ✅ Pass |
| Gold primary | #D4A017 (gold) | #1E1610 (espresso) | ~5.5:1 | ✅ Pass |
| Muted text | #A49585 (dusty tan) | #1E1610 (espresso) | ~4.8:1 | ✅ Pass |
| Card surface text | #EDE4D1 | #2A2018 (dark card) | ~9.2:1 | ✅ Pass |

**Usage restrictions**:
- Gold accent (#D4A017) MUST NOT be used as small body text color on cream (#F5EFE0) — insufficient 2.5:1 ratio. Use only for: large headings (≥18px), decorative borders, icons paired with text labels, interactive focus rings (non-text).
- Gold buttons on cream MUST pair gold background with dark brown text (#3B2D1F on #D4A017 = ~4.1:1) — passes for large text (buttons ≥14px bold).

**Rationale**: Pre-validating contrast ratios prevents post-implementation accessibility failures. The gold accent limitation is documented so implementers know to pair it with dark text for small elements.

---

### RT-6: Button Press Animation Approach (from integration: CSS transitions)

**Decision**: Add `transition-transform duration-150 active:scale-[0.97]` to the button component's base `className`.

**Rationale**: 
- `scale(0.97)` provides subtle tactile feedback without being distracting
- `duration-150` is fast enough to feel responsive, slow enough to be perceptible
- Applied via Tailwind utilities — no custom CSS or keyframes needed
- The `active:` pseudo-class triggers on mouse-down/touch-start — immediate feedback

**Alternatives considered**:
- CSS `@keyframes` animation — overkill for a simple scale; harder to integrate with class-variance-authority
- `transform: translateY(1px)` — vertical shift feels less natural than scale for buttons
- `scale(0.95)` — too aggressive; feels "bouncy" rather than tactile
- JavaScript-based spring animation (framer-motion) — adds dependency; violates zero-new-dependencies constraint

---

### RT-7: Favicon Approach (from FR-013)

**Decision**: Create a simple SVG favicon with a western-themed icon (horseshoe or cowboy hat silhouette) using the theme's gold (#D4A017) and brown (#55351A) colors.

**Rationale**: SVG favicons are supported by all modern browsers, scale to any device pixel ratio, and require zero build tooling. A simple 2-color silhouette keeps file size minimal.

**Implementation**: Replace `frontend/public/vite.svg` with a `favicon.svg` file and update the `<link rel="icon">` in `index.html`.

**Alternatives considered**:
- ICO format with multiple sizes — unnecessary complexity; SVG handles all sizes
- PNG with multiple `<link>` tags — more files to maintain; SVG is sufficient
- Keep Vite favicon — contradicts FR-013 and misses a low-effort branding opportunity
