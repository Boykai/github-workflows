# Contracts: Add Help Documentation or Support Resource

**Feature**: 032-help-docs | **Date**: 2026-03-09 | **Plan**: [plan.md](plan.md)

## Documentation Contracts

### docs/help.md — Structure Contract

The help document MUST follow this section structure to satisfy all functional requirements:

```markdown
# Help & Support

> [Tagline describing the guide's purpose]

**Last updated:** [ISO date] · Contributions welcome — open a PR to improve this guide.

---

## Getting Started                    ← FR-002
### 1. Clone and configure            ← Prerequisites + setup steps
### 2. Start the application          ← Docker / Codespaces / Local options
### 3. Open the app                   ← Access URL
### 4. Create a project               ← Project board setup
### 5. Start building                 ← First interaction guidance
→ Link to Setup Guide (setup.md)

---

## Frequently Asked Questions         ← FR-003
### Setup                             ← Category 1 (≥2 questions)
### Usage                             ← Category 2 (≥2 questions)
### Agent Pipeline                    ← Category 3 (≥2 questions)
### Contributing                      ← Category 4 (≥2 questions)
→ Each answer with advanced topics links to relevant docs (FR-007)

---

## Support Channels                   ← FR-004
- GitHub Issues                       ← Primary support channel
- GitHub Discussions                  ← Secondary support channel
- Documentation                       ← Link back to README docs table

---

## Agent Pipeline Overview            ← FR-005
[ASCII diagram of pipeline stages]
→ Link to Agent Pipeline docs (agent-pipeline.md)

---

## Further Reading                    ← FR-007 (comprehensive link table)
| Document | Description |
|----------|-------------|
[Links to all major documentation files]
```

### README.md — Integration Contract (FR-006)

The README documentation table MUST include a row linking to the help document:

```markdown
| [Help & Support](docs/help.md) | Beginner guide, FAQ, support channels, and pipeline overview |
```

## Frontend Component Contracts

### HelpPage.tsx — Interface Contract (FR-010)

**Location**: `frontend/src/pages/HelpPage.tsx`

The HelpPage component MUST render the following sections to mirror `docs/help.md`:

```typescript
// FAQ data structure
interface FaqItem {
  question: string;
  answer: string;
  category: 'Setup' | 'Usage' | 'Pipeline' | 'Contributing';
}

// Page sections (in render order)
// 1. Hero section with title and description
// 2. Getting Started guide (5 steps)
// 3. FAQ accordion with category filter tabs
// 4. Support Channels with external links
// 5. Agent Pipeline overview
// 6. Further Reading documentation table
```

**Behavioral requirements**:
- FAQ accordion items expand/collapse on click
- Category filter tabs filter FAQ items by category
- All external links open in new tab (`target="_blank"`)
- Responsive layout renders without horizontal scrolling on viewports ≥320px (SC-004)
- Celestial theme styling applied consistently

### Sidebar.tsx — Navigation Contract (FR-010)

**Location**: `frontend/src/layout/Sidebar.tsx`

The sidebar navigation MUST include a help link:

```typescript
// In NAV_ROUTES constant (from constants.ts)
{ path: '/help', label: 'Help', icon: HelpCircle }
```

## Validation Rules

| Rule | Source | Check |
|------|--------|-------|
| FAQ count ≥ 8 | SC-002 | Count `###` headings with `?` in FAQ section |
| FAQ categories ≥ 3 | SC-002 | Count unique `### [Category]` headings in FAQ |
| Detail links valid | SC-003 | All `[text](file.md)` links resolve to existing `docs/` files |
| Viewport ≥ 320px | SC-004 | No horizontal scroll on narrow viewport |
| Readability ≤ Grade 8 | SC-007 | Flesch-Kincaid Grade Level check on prose content |
| Last Updated accurate | SC-006 | Date within one release cycle |

## No New Dependencies

This feature requires zero new npm packages, Python packages, or external services. All functionality is achieved with existing project dependencies and standard Markdown.
