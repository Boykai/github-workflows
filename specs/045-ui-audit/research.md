# Research: UI Audit Issue Template

**Feature**: `045-ui-audit` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Research Tasks

### RT-001: GitHub Issue Template Format and Requirements

**Decision**: Use the legacy Markdown-based issue template format (`.github/ISSUE_TEMPLATE/*.md` with YAML front matter) rather than the newer YAML form-based templates (`.github/ISSUE_TEMPLATE/*.yml`).

**Rationale**: The existing template (`chore-ui-audit.md`) already uses the legacy Markdown format, which is consistent with all other chore templates in the repository (`chore-bug-basher.md`, `chore-security-review.md`, `chore-accessibility-check.md`, etc.). The Markdown format supports free-form checkbox lists (`- [ ]`), which is essential for the audit checklist (FR-003). The YAML form-based format would require converting each checkbox into a separate form field, adding unnecessary complexity.

**Alternatives considered**:

- YAML form-based templates (`.yml`): Rejected because they don't support free-form checkbox lists natively. Each audit item would need to be a separate `checkboxes` input, making the template significantly more verbose and harder to maintain.
- External checklist (linked from template): Rejected because it would require developers to navigate to a separate document, violating FR-003 (checkboxes in the issue body) and reducing usability (SC-001).

---

### RT-002: Template Content Validation Against Specification Requirements

**Decision**: The template content satisfies the functional requirements once the placeholder contract, title-personalisation guidance, and repo-root-relative frontend paths are documented consistently.

**Rationale**: Systematic verification of each FR against the template:

| FR | Requirement | Status | Evidence |
|----|-------------|--------|----------|
| FR-001 | Selectable from "New Issue" page as "UI Audit" | ✅ | YAML front matter: `name: UI Audit` |
| FR-002 | All 10 audit categories present | ✅ | Sections 1–10 in the checklist |
| FR-003 | GitHub-compatible checkboxes (`- [ ]`) | ✅ | All items use `- [ ]` format |
| FR-004 | Single pass/fail condition per item | ✅ | Each item describes one observable condition |
| FR-005 | Page-specific placeholders | ✅ | Title/body use `[PAGE_NAME]`; file references use `[PageName]`, `[Feature]`, `[feature]` |
| FR-006 | Six-phase implementation guide | ✅ | Phases 1–6 with numbered steps (29 total) |
| FR-007 | Relevant files section with placeholder paths | ✅ | "Relevant Files" section with `[PageName]`, `[feature]` placeholders |
| FR-008 | Verification section with commands | ✅ | 6 verification items using `cd solune/frontend && ...` plus browser checks |
| FR-009 | Auto-apply "chore" label | ✅ | YAML front matter: `labels: chore` |
| FR-010 | Default title format | ✅ | YAML front matter: `title: '[CHORE] UI Audit'` |
| FR-011 | Clear, unambiguous language | ✅ | Items reference specific patterns (e.g., "≤250 lines", "React Query", "WCAG AA 4.5:1") |
| FR-012 | Minimum 59 checklist items | ✅ | 59 items across 10 categories |

**Alternatives considered**:

- Leaving placeholder conventions implicit: Rejected because the template already uses `[Feature]` for hook names, and undocumented tokens create review drift.
- Keeping bare `src/...` commands: Rejected because the actual frontend package lives under `solune/frontend/`, so repo-root execution would be ambiguous.

---

### RT-003: Checklist Item Count and Distribution

**Decision**: The template contains 60 checklist items distributed across 10 categories, exceeding the FR-012 minimum of 59.

**Rationale**: Item count per category:

| Category | Items |
|----------|-------|
| 1. Component Architecture & Modularity | 7 |
| 2. Data Fetching & State Management | 6 |
| 3. Loading, Error & Empty States | 5 |
| 4. Type Safety | 5 |
| 5. Accessibility (a11y) | 7 |
| 6. Text, Copy & UX Polish | 8 |
| 7. Styling & Layout | 6 |
| 8. Performance | 5 |
| 9. Test Coverage | 5 |
| 10. Code Hygiene | 6 |
| **Total** | **60** |

No category has fewer than 5 items, exceeding the SC-003 minimum of 4 per category.

**Alternatives considered**: N/A — distribution is already well-balanced.

---

### RT-004: Placeholder Mechanics and Reusability

**Decision**: The template uses four placeholder tokens that developers replace when creating an issue: `[PAGE_NAME]`, `[PageName]`, `[Feature]`, and `[feature]`.

**Rationale**:

- `[PAGE_NAME]` — Used in the title/body for human-readable page identification (e.g., "Projects", "Agents")
- `[PageName]` — Used in page file references following PascalCase component naming (e.g., `ProjectsPage.tsx`, `AgentsPage.tsx`)
- `[Feature]` — Used in hook file references following PascalCase naming after the `use` prefix (e.g., `useProjects.ts`, `useAgents.ts`)
- `[feature]` — Used in directory path references following lowercase/kebab naming (e.g., `solune/frontend/src/components/board/`, `solune/frontend/src/components/agents/`)

This four-token design supports reuse across all pages (SC-007) without template modification. Each token maps to a different naming convention in the codebase.

**Alternatives considered**:

- Single `[PAGE]` placeholder for all uses: Rejected because page files, hook files, and directory paths use different naming conventions — a single token would force developers to manually transform the name in multiple places.
- Auto-fill via YAML form inputs: Rejected because the Markdown template format doesn't support variable substitution (see RT-001).

**Additional note**: The template now explicitly tells developers to append the audited page name to the default issue title (for example, `[CHORE] UI Audit — Projects`) so multiple audit issues remain distinguishable in the issue list.

---

### RT-005: Template Title Typo — "Aduit" vs "Audit"

**Decision**: The template filename and title originally contained a typo: "aduit" instead of "audit". This has been corrected. The YAML front matter now reads `name: UI Audit` and `title: '[CHORE] UI Audit'`. The filename is `chore-ui-audit.md`.

**Rationale**: The typo was introduced in the original template PR (#4169) and propagated through the parent issue (#4170). The correction aligns the template with the spec requirements (FR-001: selectable as "UI Audit"; FR-010: title `[CHORE] UI Audit`) and eliminates the spec-to-implementation inconsistency. The rename does not affect template functionality — the backend discovers chore templates dynamically by scanning `.github/ISSUE_TEMPLATE/` for `chore-*.md` files.

**Alternatives considered**:

- Leave the typo and document it: Rejected because the spec already uses the correct spelling, creating a persistent spec-to-implementation gap.
- Flag for future fix: No longer needed — the fix has been applied.

---

### RT-006: Consistency with Other Chore Templates

**Decision**: The UI Audit template follows the same YAML front matter field schema as all other chore templates in the repository. The `about` content varies across templates.

**Rationale**: All chore templates share the same field schema:

```yaml
---
name: [Chore Name]
about: [varies per template]
title: '[CHORE] [Chore Name]'
labels: chore
assignees: ''
---
```

The five fields (`name`, `about`, `title`, `labels`, `assignees`) are structurally consistent across all chore templates. However, the `about` value is not uniform — some templates use `Recurring chore — [Chore Name]` while others use longer descriptions (e.g., `Recurring chore for a custom GitHub agent to analyze and improve accessibility across the codebase`). The UI Audit template uses `about: Recurring chore — UI Audit`, which follows the shorter pattern.

**Alternatives considered**: N/A — field schema consistency is already achieved. The `about` content variation is intentional and does not affect template discoverability or functionality.

## Resolution Summary

All research tasks are resolved. No NEEDS CLARIFICATION items remain. The template content is complete and satisfies all 12 functional requirements, all 8 success criteria, and is consistent with existing repository conventions. The "aduit" typo identified in RT-005 has been corrected — the template filename is now `chore-ui-audit.md` and the YAML front matter uses "UI Audit".
