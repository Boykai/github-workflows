# Research: Audit Pipelines Page for UI Consistency, Quality & UX

**Feature**: 033-audit-pipelines-ux | **Date**: 2026-03-10

## R1: Audit Methodology — Manual Review vs Automated Tooling vs Hybrid

**Task**: Determine the optimal approach for auditing the Pipelines page across all five categories (visual consistency, functional bugs, accessibility, UX quality, code quality).

**Decision**: Hybrid approach combining automated tooling with manual expert review. Automated tools handle the objective, measurable checks (color contrast, ARIA compliance, console errors, lint rules), while manual review covers subjective quality assessments (visual cohesion, UX clarity, information hierarchy). The initial designer audit (`audit-report.md`) has already been conducted as the manual pass, identifying 6 findings with 3 fixed in-PR. The remaining work focuses on resolving open findings and systematically verifying all spec requirements.

**Rationale**: Automated tools alone cannot assess visual cohesion or UX quality — these require human judgment. However, relying solely on manual review for accessibility and code quality is error-prone and incomplete. The hybrid approach leverages existing tooling in the project (jest-axe for automated a11y testing, ESLint with jsx-a11y plugin for static analysis, Vitest for regression testing) alongside structured manual review against the design token system documented in `index.css`. The initial designer audit provides a high-quality manual baseline that the automated pass can verify and extend.

**Alternatives Considered**:

- **Fully automated audit (Lighthouse, axe-core CLI)**: Rejected as the sole approach — these tools measure contrast, ARIA, and performance but cannot evaluate visual consistency against the Solune design system or assess UX quality. Used as a supplement, not a replacement.
- **Fully manual audit**: Rejected — too slow and error-prone for accessibility compliance checks. Manual review misses subtle ARIA issues that automated tools catch reliably.
- **Third-party audit service**: Rejected — scope is limited to this single page, and the project already has in-house tooling. External services add cost and latency without proportional benefit.

---

## R2: Accessibility Standard — WCAG 2.1 AA Compliance Approach

**Task**: Determine how to systematically verify WCAG 2.1 Level AA compliance for the Pipelines page, particularly for complex interactive patterns like drag-and-drop and inline editing.

**Decision**: Apply WCAG 2.1 Level AA as the target standard, focusing on the success criteria most relevant to the Pipelines page's interactive patterns. Key criteria: SC 1.3.1 (Info and Relationships), SC 1.4.3 (Contrast), SC 2.1.1 (Keyboard), SC 2.4.7 (Focus Visible), SC 3.3.1 (Error Identification), SC 4.1.2 (Name, Role, Value). For drag-and-drop specifically, provide a keyboard-accessible alternative using dnd-kit's built-in `KeyboardSensor` (already configured in `StageCard.tsx` with `sortableKeyboardCoordinates`). For form validation, wire `aria-invalid` and `aria-describedby` to error messages.

**Rationale**: WCAG 2.1 AA is the de facto standard for web accessibility and is assumed by the spec (Assumption section). The Pipelines page already has partial keyboard support via dnd-kit's `KeyboardSensor`, but the validation feedback in `PipelineBoard.tsx` is visual-only — the pipeline name input lacks `aria-invalid` and `aria-describedby` attributes (finding PIPE-004). The existing `jsx-a11y` ESLint plugin catches some issues statically, and `jest-axe` is available for runtime checks. The remediation is targeted and minimal: add standard HTML attributes to the name input, not a new accessibility framework.

**Alternatives Considered**:

- **WCAG 2.1 AAA**: Rejected — AAA requirements (e.g., 7:1 contrast ratio, sign language interpretation) go beyond what the spec requires and what the application's design system supports. AA is the appropriate target.
- **Custom accessibility testing framework**: Rejected — the project already has `jest-axe` and `@testing-library/react` which together cover the needed automated checks. No new tooling is required.
- **Deferred accessibility remediation**: Rejected — the spec explicitly includes accessibility as a P2 audit category (User Story 3). PIPE-004 is a Medium severity finding that should be resolved in this audit cycle.

---

## R3: Visual Consistency Baseline — Design Token Verification Approach

**Task**: Determine how to systematically compare the Pipelines page against the application's design token system and cross-page visual patterns.

**Decision**: Use the design tokens defined in `frontend/src/index.css` as the authoritative baseline for visual properties (colors, typography, spacing, shadows, border radii, animations). Compare each Pipelines page component against the tokens and against equivalent patterns on the Dashboard (`ProjectsPage`), Agents (`AgentsPage`), and Settings pages. Document deviations as findings with expected (token value) vs actual (component value) comparisons. The initial designer audit already verified the major elements; the remaining work focuses on the open findings (PIPE-005 skeleton styling, PIPE-006 activity capping).

**Rationale**: The design token system in `index.css` defines semantic colors (`--primary`, `--destructive`, `--muted`), celestial theme colors (`--glow`, `--gold`, `--night`, `--star`), typography (`--font-display`, `--font-sans`), shadows (`--shadow-sm` through `--shadow-lg`), border radii (`--radius-sm/md/lg`), and animation timings (`--transition-cosmic-fast/base/slow/drift`). These tokens are used consistently across other pages via utility classes (`.celestial-panel`, `.solar-action`, `.celestial-fade-in`). Any Pipelines page component that uses raw values instead of tokens, or different token values than equivalent components on other pages, is a visual consistency deviation.

**Alternatives Considered**:

- **Visual regression testing (Percy, Chromatic)**: Rejected — these tools compare against stored snapshots but the project doesn't have existing snapshots, and setting them up is out of scope for an audit. Manual side-by-side comparison with documented deviations is sufficient for this one-time audit.
- **CSS linting for token compliance**: Considered as a future enforcement mechanism, but rejected for this audit — the goal is to identify deviations, not to build an automated enforcement pipeline. A CSS linting rule could be recommended as a remediation action.
- **Design review with stakeholders**: Valuable but not a replacement for systematic component-by-component comparison. The designer audit has already provided expert-level visual review.

---

## R4: Skeleton Loading Pattern — Upgrade Strategy for PIPE-005

**Task**: Determine the correct loading skeleton pattern for `SavedWorkflowsList` that aligns with the application's established celestial panel style.

**Decision**: Upgrade the `SavedWorkflowsList` loading skeleton from generic `animate-pulse` blocks to structured placeholders that mirror the saved workflow card layout, using `celestial-panel` class styling with `rounded-[1.3rem]` border radius and `border-border/50` border treatment. The skeleton cards should include placeholder shapes for the pipeline name, description line, flow graph area, and stats row — matching the actual card structure so the transition from loading to loaded feels seamless.

**Rationale**: The current skeleton (3 × `h-32 rounded-xl border-border/50 bg-muted/20 animate-pulse` blocks) is functional but visually flat compared to the rest of the Solune UI. Other pages use `celestial-panel` class for content areas, which includes the radial gradient glow background, theme-aware borders, and hover transitions. The `AgentsPage` loading state wraps `CelestialLoader` inside a `celestial-panel` container. While `SavedWorkflowsList` doesn't need a centered spinner (cards are the better skeleton shape for a list), the card skeleton should use the same border radius, border opacity, and background treatment as the loaded cards. This is finding PIPE-005 (Low severity).

**Alternatives Considered**:

- **Replace skeleton with `CelestialLoader` spinner**: Rejected — a single spinner doesn't communicate the card-list layout that will appear when loading completes. Skeleton cards are better for spatial prediction.
- **Keep generic pulse blocks**: Rejected — this is the documented finding. The spec requires visual consistency across the application.
- **Full `celestial-shimmer` animation**: Considered but rejected — the shimmer animation is used for decorative elements, not loading states. `animate-pulse` remains the standard loading animation, but the skeleton shape and styling should match the target card layout.

---

## R5: Recent Activity Capping — UX Improvement Strategy for PIPE-006

**Task**: Determine the appropriate UX improvement for the Recent Activity section which hard-caps at 3 pipelines without any disclosure or navigation affordance.

**Decision**: Add a subtle text label below the 3 most recent pipelines indicating how many total pipelines exist when the count exceeds 3, with a reference to the Saved Pipelines section. The format: "Showing 3 of {total} — see all in Saved Pipelines" with "Saved Pipelines" as an anchor link to `#saved-pipelines`. This provides context without adding navigation complexity.

**Rationale**: The current implementation shows the 3 most recently updated pipelines in the "Recent Activity" section (via `recentPipelines` computed from `pipelineConfig.pipelines`). When more than 3 pipelines exist, users have no indication that older pipelines are hidden. The fix is minimal — a conditional text line that appears only when the pipeline count exceeds 3. The anchor link to `#saved-pipelines` reuses the section ID that was added as part of the PIPE-002 fix, creating a natural navigation path. This is finding PIPE-006 (Low severity).

**Alternatives Considered**:

- **"Show all" expansion button**: Rejected — the Recent Activity section is intentionally compact (showing recent context, not a full list). Expanding it would duplicate the Saved Pipelines section. The purpose of Recent Activity is at-a-glance recent context, not browsing.
- **Pagination**: Rejected — overkill for a 3-item summary section. Pagination adds interaction cost for minimal benefit.
- **Remove the cap entirely**: Rejected — showing all pipelines would make the section unbounded and defeat its purpose as a quick-glance summary.
