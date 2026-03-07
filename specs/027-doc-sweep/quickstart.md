# Quickstart: Recurring Documentation Update Process

**Feature**: 027-doc-sweep | **Date**: 2026-03-07

## Prerequisites

- Git and a clone of the repository
- Node.js 20+ (for running markdown linting locally)
- Familiarity with the project's `docs/` directory structure

After this feature is merged, all deliverables below are available on the `main` branch.

## What This Feature Delivers

This feature establishes a recurring documentation maintenance process. It does **not** change application code. The deliverables are:

1. **PR template** (`.github/pull_request_template.md`) — documentation checklist for every pull request
2. **Review checklists** (`docs/checklists/`) — structured checklists for weekly, monthly, and quarterly reviews
3. **CI configuration updates** (`.github/workflows/ci.yml`) — expanded markdown linting scope

## Quick Verification

### 1. Verify PR Template

After the feature branch is merged, create a new pull request. The PR description should automatically populate with the documentation checklist section.

### 2. Verify CI Linting

Run markdown linting locally to confirm the expanded scope works:

```bash
# Install tools (same versions as CI)
npm install -g markdownlint-cli@0.48.0 markdown-link-check@3.14.2

# Lint docs and root-level markdown files
markdownlint "docs/**/*.md" "*.md" --config .markdownlint.json

# Check links in documentation and README (matches CI)
find docs -name "*.md" -print0 | xargs -0 -I {} \
  markdown-link-check {} \
    --config .markdown-link-check.json \
    --quiet

markdown-link-check README.md \
  --config .markdown-link-check.json \
  --quiet
```

### 3. Verify Checklists

Open each checklist and confirm it matches the expected structure:

```bash
# Weekly sweep checklist
cat docs/checklists/weekly-sweep.md

# Monthly review checklist
cat docs/checklists/monthly-review.md

# Quarterly audit checklist
cat docs/checklists/quarterly-audit.md
```

### 4. Verify Documentation Ownership

Confirm `docs/OWNERS.md` includes entries for the new `docs/checklists/` files:

```bash
cat docs/OWNERS.md
```

## Using the Review Checklists

### Weekly Sweep (~30 minutes)

1. Open `docs/checklists/weekly-sweep.md`
2. Copy the checklist into a new issue or work through it directly
3. For each section (API Reference, Configuration, Setup Guide):
   - Compare the documentation against the current codebase
   - Check off items that are accurate
   - File issues for discrepancies that need more than a quick fix
4. Record completion at the bottom of the checklist

### Monthly Review (~2–3 hours)

1. Open `docs/checklists/monthly-review.md`
2. Work through each section: Coverage Audit, Cross-Reference Check, Readability Assessment
3. Use the per-file verification table to check each doc systematically
4. File issues for any problems found; link them in the completion record

### Quarterly Audit (~half day)

1. Open `docs/checklists/quarterly-audit.md`
2. Work through: Architecture Review, ADR Check, Developer Experience Audit, Gaps Analysis
3. Have a team member follow `docs/setup.md` from scratch as part of the DX audit
4. Create ADRs for any significant architectural decisions from the quarter

## Roles Quick Reference

| Role | Responsibility | Cadence |
|------|---------------|---------|
| PR author | Fill out documentation checklist in PR template | Every PR |
| PR reviewer | Verify documentation checklist before approving | Every PR |
| Dev (rotation) | Complete weekly staleness sweep | Weekly |
| Tech lead | Lead monthly review and quarterly audit | Monthly / Quarterly |
