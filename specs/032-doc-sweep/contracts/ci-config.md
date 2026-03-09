# Contract: CI Configuration — Documentation Linting and Link Checking

**Feature**: 032-doc-sweep | **Date**: 2026-03-09
**Requirements**: FR-014, FR-015, FR-016 | **Success Criteria**: SC-006, SC-007

## Overview

The CI pipeline enforces documentation formatting standards and validates links. This contract defines the required CI configuration and validates the existing setup against 032-doc-sweep requirements.

## CI Workflow: `docs` Job (`.github/workflows/ci.yml`)

### Required Steps

### Step 1 — Markdown Formatting Lint (FR-015)

```yaml
- name: Lint markdown formatting
  run: markdownlint "docs/**/*.md" "*.md" --config .markdownlint.json
```

**Scope**: All markdown files in `docs/` directory (recursive) + all markdown files at repository root.
**Tool**: markdownlint-cli 0.48.0
**Config**: `.markdownlint.json`

### Step 2 — Link Validation (FR-016)

```yaml
- name: Check documentation links
  run: |
    find docs -name "*.md" -print0 | xargs -0 -I {} \
      markdown-link-check {} \
        --config .markdown-link-check.json \
        --quiet
    markdown-link-check README.md \
      --config .markdown-link-check.json \
      --quiet
```

**Scope**: All markdown files in `docs/` directory (recursive) + `README.md`.
**Tool**: markdown-link-check 3.14.2
**Config**: `.markdown-link-check.json`

## Formatting Standards Config (`.markdownlint.json`)

### Required Rules (FR-014)

| Rule | Setting | Purpose |
|------|---------|---------|
| MD003 | `style: "consistent"` (default via `"default": true`) | Enforce consistent heading style (ATX in practice) |
| MD004 | `style: "dash"` | Enforce dash-style unordered lists |
| MD013 | `false` (disabled) | No line length limit (project convention) |
| MD032 | `true` (default) | Require blank lines around lists |
| MD033 | `false` (allow inline HTML) | Permit HTML in markdown (project convention) |
| MD040 | `true` (default) | Enforce language specification on fenced code blocks |
| MD041 | `false` (disabled) | Don't require heading on first line (project convention) |

### Current Config

```json
{
  "default": true,
  "MD004": { "style": "dash" },
  "MD006": true,
  "MD013": false,
  "MD032": true,
  "MD033": false,
  "MD034": true,
  "MD041": false,
  "MD060": false
}
```

### Assessment

The current config enforces key formatting standards via `"default": true`. Consistent heading style is enforced by default (MD003 — ATX in practice since all docs use ATX). Code block language tags are enforced by default (MD040). The config is permissive where appropriate (no line length, allow inline HTML).

## Link Check Config (`.markdown-link-check.json`)

### Required Behavior (FR-016)

- MUST check all internal links within `docs/`
- MUST check external links (GitHub docs, library docs)
- MUST handle rate limiting gracefully (retry on 429)
- MUST distinguish permanent failures (404) from transient failures (5xx, timeout)
- MUST ignore known-false-positive URLs (Codespaces links, localhost)

### Current Link Check Config

The existing `.markdown-link-check.json` includes:

- ✅ Ignore patterns for Codespaces and localhost URLs
- ✅ Retry configuration (2 retries, 30s delay for 429)
- ✅ Timeout of 20 seconds
- ✅ Accept 200 and 206 status codes

## Pre-Commit Hooks (`.pre-commit-config.yaml`)

### Existing Markdown Hook

```yaml
- repo: https://github.com/igorshubovych/markdownlint-cli
  rev: v0.48.0
  hooks:
    - id: markdownlint
      name: Lint Markdown (markdownlint)
      args: [--config, .markdownlint.json]
      files: (^docs/.*\.md$|^[^/]*\.md$)
```

**Scope**: `docs/**/*.md` + root-level `*.md` files. Matches CI scope.

## Compliance Assessment

| Requirement | Current State | Status |
|-------------|--------------|--------|
| FR-014: Formatting standards | `.markdownlint.json` enforces consistent headings (ATX in practice), dash lists, code block formatting | ✅ Compliant |
| FR-015: CI formatting enforcement | `ci.yml` runs markdownlint on `docs/**/*.md` + `*.md` | ✅ Compliant |
| FR-016: CI link checking | `ci.yml` runs markdown-link-check on `docs/**/*.md` + `README.md` | ✅ Compliant |
| SC-006: Formatting violations caught | markdownlint runs on every push/PR to main | ✅ Compliant |
| SC-007: Broken links caught | markdown-link-check runs on every push/PR to main | ✅ Compliant |

## Changes Required

**None.** The existing CI configuration, markdownlint config, link-check config, and pre-commit hooks are fully compliant with FR-014–FR-016 and SC-006–SC-007.
