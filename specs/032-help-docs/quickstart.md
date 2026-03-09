# Quickstart: Add Help Documentation or Support Resource

**Feature**: 032-help-docs | **Date**: 2026-03-09 | **Plan**: [plan.md](plan.md)

## Overview

This guide explains how to validate, refine, and maintain the help documentation for Agent Projects. The help infrastructure already exists — this feature focuses on ensuring all spec requirements are fully met and content is accurate.

## Prerequisites

- Git repository cloned locally
- Text editor with Markdown preview (VS Code recommended)
- Node.js 22+ (for frontend development, if modifying HelpPage.tsx)

## Step 1: Review the Help Document

Open `docs/help.md` and verify each section against the functional requirements:

| Section | Requirement | What to Check |
|---------|------------|---------------|
| Getting Started | FR-002 | Prerequisites listed, setup steps link to Setup Guide |
| FAQ | FR-003 | ≥ 8 questions across ≥ 3 categories (Setup, Usage, Pipeline, Contributing) |
| Support Channels | FR-004 | Lists GitHub Issues + at least one other support channel |
| Pipeline Overview | FR-005 | Describes each pipeline stage with corresponding command |
| Further Reading | FR-007 | All FAQ answers with advanced topics link to relevant docs |
| Header | FR-008 | "Last Updated" date is current; contribution note present |
| Overall | FR-009 | Clear, plain language; no unnecessary jargon |

## Step 2: Validate Internal Links

Check that all relative links in `docs/help.md` resolve to existing files:

```bash
# List all markdown links in the help document
grep -oP '\[.*?\]\((.*?)\)' docs/help.md

# Verify each linked file exists
for link in setup.md configuration.md troubleshooting.md testing.md \
            custom-agents-best-practices.md agent-pipeline.md architecture.md \
            api-reference.md; do
  [ -f "docs/$link" ] && echo "✅ $link" || echo "❌ $link MISSING"
done
```

## Step 3: Verify README Integration

Confirm the README documentation table includes a link to the help document:

```bash
grep -n "help.md" README.md
```

Expected output should show a row in the documentation table: `| [Help & Support](docs/help.md) | ... |`

## Step 4: Verify Frontend Help Page (if modifying UI)

If making changes to the frontend HelpPage:

```bash
cd frontend
npm install
npm run type-check   # Verify TypeScript compiles
npm test             # Run existing tests
npm run build        # Verify production build
```

Open the application and navigate to `/help` to verify:
- Getting Started section renders correctly
- FAQ accordion expands/collapses with category filtering
- Support channel links work
- Pipeline overview is visible
- Responsive layout works on narrow viewports (≥320px)

## Step 5: Update the "Last Updated" Date

After making any content changes to `docs/help.md`, update the date in the header:

```markdown
**Last updated:** YYYY-MM-DD · Contributions welcome — open a PR to improve this guide.
```

## Verification Checklist

- [ ] All functional requirements (FR-001 through FR-010) are addressed
- [ ] FAQ has ≥ 8 questions across ≥ 3 categories
- [ ] All internal links resolve to existing documentation files
- [ ] README documentation table links to `docs/help.md`
- [ ] "Last Updated" date is current
- [ ] Content uses plain language suitable for beginners
- [ ] Document renders correctly on GitHub
- [ ] Frontend HelpPage mirrors documentation content (if applicable)
- [ ] Sidebar help link navigates to `/help` route (if applicable)

## Spec Traceability

| Requirement | Artifact | Status |
|-------------|----------|--------|
| FR-001 | `docs/help.md` | Existing — validate |
| FR-002 | `docs/help.md` → Getting Started | Existing — validate |
| FR-003 | `docs/help.md` → FAQ | Existing — validate (10 items, 4 categories) |
| FR-004 | `docs/help.md` → Support Channels | Existing — validate |
| FR-005 | `docs/help.md` → Pipeline Overview | Existing — validate |
| FR-006 | `README.md` → Documentation table | Existing — validate |
| FR-007 | `docs/help.md` → FAQ detail links | Existing — validate |
| FR-008 | `docs/help.md` → Header date + note | Existing — validate |
| FR-009 | `docs/help.md` → All sections | Existing — validate readability |
| FR-010 | `HelpPage.tsx` + Sidebar.tsx | Existing — validate |
