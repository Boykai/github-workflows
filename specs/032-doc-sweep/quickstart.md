# Quickstart: Recurring Documentation Update Process

**Feature**: 032-doc-sweep | **Date**: 2026-03-09

## Prerequisites

- Git and a clone of the repository
- Node.js 20+ (for running markdown linting locally)
- Familiarity with the project's `docs/` directory structure

## What This Feature Delivers

This feature establishes a comprehensive, recurring documentation maintenance process. It does **not** change application code. The deliverables are:

1. **PR template** (`.github/pull_request_template.md`) — documentation checklist for every pull request
2. **Review checklists** (`docs/checklists/`) — structured checklists for weekly, monthly, and quarterly reviews
3. **CI enforcement** (`.github/workflows/ci.yml`) — automated markdown linting and link validation
4. **Documentation ownership** (`docs/OWNERS.md`) — clear file-to-owner mappings with review cadence
5. **Architecture Decision Records** (`docs/decisions/`) — template and index for capturing architectural decisions
6. **Good documentation definition** — formalized acceptance bar applied across all review phases (FR-021)

## Quick Verification

### 1. Verify PR Template

Create a new pull request. The PR description automatically populates with the documentation checklist section, including 6 documentation items and a rationale field.

### 2. Verify CI Linting

Run markdown linting locally to confirm the CI checks pass:

```bash
# Install tools (same versions as CI)
npm install -g markdownlint-cli@0.48.0 markdown-link-check@3.14.2

# Lint docs and root-level markdown files
markdownlint "docs/**/*.md" "*.md" --config .markdownlint.json

# Check links in documentation and README
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
cat docs/checklists/weekly-sweep.md
cat docs/checklists/monthly-review.md
cat docs/checklists/quarterly-audit.md
```

### 4. Verify Documentation Ownership

Confirm `docs/OWNERS.md` includes entries for all documentation files:

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
   - File issues for any discrepancies found
4. If all items pass, the sweep is complete
5. If significant issues are found (>30 min to fix), file tracking issues and escalate

### Monthly Review (~2–3 hours)

1. Open `docs/checklists/monthly-review.md`
2. Walk through every file in `docs/`:
   - Verify accuracy against current code behavior
   - Verify completeness (no undocumented features)
   - Verify consistency (terminology, naming, formatting)
3. Perform the cross-reference check:
   - Validate all internal links resolve to existing headings
   - Verify code snippets against current codebase
   - Check external links still resolve
4. Assess readability standards:
   - Purpose statements, numbered lists, table formats
   - Troubleshooting entries follow Symptom → Cause → Fix format
5. Apply the "good documentation" acceptance bar to all files:
   - Accurate, minimal, actionable, discoverable, maintained
6. File issues for any gaps; aim for zero unresolved issues per cycle

### Quarterly Architecture Audit (~half day)

1. Open `docs/checklists/quarterly-audit.md`
2. Verify `docs/architecture.md` against current Docker Compose topology
3. Review `docs/decisions/` for ADR completeness:
   - Ensure all significant decisions from the quarter are captured
   - Verify ADR format: Context → Decision → Consequences
4. Conduct developer experience test:
   - Have a team member follow `docs/setup.md` from scratch
   - Document friction points and update troubleshooting guide
5. Perform docs gaps analysis:
   - List features shipped this quarter
   - Confirm each has adequate documentation

## Roles Quick Reference

| Role | What to Do |
|------|-----------|
| **PR author** | Complete the documentation checklist in every PR |
| **PR reviewer** | Reject PRs that change behavior without updating relevant docs |
| **Dev (rotation)** | Perform weekly staleness sweep (~30 min) |
| **Tech lead** | Sign off on monthly review; lead quarterly architecture audit |
| **All contributors** | Follow formatting standards; flag stale docs when encountered |

## Definition of Good Documentation

A doc is considered current and complete when it meets all five criteria:

1. **Accurate** — Every step, command, variable, and path matches the current codebase
2. **Minimal** — No redundant content; each fact appears in exactly one place
3. **Actionable** — Readers can accomplish the documented task without needing to read source code
4. **Discoverable** — The correct doc is easy to find from the README or table of contents
5. **Maintained** — Last-reviewed date is within the current quarter

## Formatting Standards

When writing or updating documentation, follow these standards:

- Use ATX-style headings (`#`, `##`, `###`)
- Specify language on code blocks (` ```python `, ` ```bash `, ` ```typescript `)
- Use tables for: env vars, API endpoints, config options
- Use numbered lists for sequential steps; bullet lists for non-ordered items
- Use inline code formatting for filenames (e.g., `config.py`)

The CI pipeline enforces these standards automatically via `markdownlint`.
