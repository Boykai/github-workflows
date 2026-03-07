# Contract: CI Configuration for Documentation Linting

**Feature**: 027-doc-sweep | **Date**: 2026-03-07
**Requirements**: FR-010, FR-011, FR-012

## Current State

The CI workflow (`.github/workflows/ci.yml`) already includes a `docs` job that:
- Runs `markdownlint` on `docs/**/*.md` and `README.md`
- Runs `markdown-link-check` on all `docs/**/*.md` files
- Uses `markdownlint-cli@0.48.0` and `markdown-link-check@3.14.2`
- Triggers on push to `main` and on PRs to `main`

## Required Changes

### Markdown Linting Scope (FR-010)

**Current**:

```yaml
- name: Lint markdown formatting
  run: markdownlint "docs/**/*.md" "README.md" --config .markdownlint.json
```

**Required**: Expand to cover all `*.md` files at the repository root (FR-010: "all `*.md` files in the repository").

```yaml
- name: Lint markdown formatting
  run: markdownlint "docs/**/*.md" "*.md" --config .markdownlint.json
```

**Rationale**: `"*.md"` covers `README.md` plus any future root-level markdown files (`CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`). The `specs/` directory is intentionally excluded — spec planning artifacts have different formatting conventions (templates, placeholders) that would fail documentation linting rules.

### Link Checking Scope (FR-011)

**Current**: Checks only `docs/**/*.md` files.

**Required**: No change needed. Link checking is most valuable for documentation files that contain cross-references and external links. Root-level `*.md` files (README) should also be checked.

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

### Error Message Clarity (FR-012)

**Current**: Both `markdownlint` and `markdown-link-check` already produce clear, file-and-line-specific error messages by default.

**Required**: No change needed. `markdownlint` outputs format: `filename:line:column rule description`. `markdown-link-check` outputs format: `[✖] url - STATUS_CODE`.

**Validation**: FR-012 is satisfied by the default output behavior of both tools.

## Markdownlint Configuration

**File**: `.markdownlint.json`

**Current configuration** (no changes needed):

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

**Notes**:
- `MD013: false` (line length) is appropriate — documentation tables and URLs frequently exceed 80 characters
- `MD033: false` (inline HTML) is appropriate — some docs use HTML for badges and images
- `MD041: false` (first-line heading) is appropriate — some docs start with metadata or badges

## Link Check Configuration

**File**: `.markdown-link-check.json`

**Current configuration** (no changes needed):

```json
{
  "ignorePatterns": [
    { "pattern": "^https://codespaces\\.new/" },
    { "pattern": "^https://github\\.com/codespaces/badge\\.svg" },
    { "pattern": "^https?://localhost" }
  ],
  "aliveStatusCodes": [200, 206],
  "retryOn429": true,
  "retryCount": 2,
  "fallbackRetryDelay": "30s",
  "timeout": "20s"
}
```

**Edge Case Handling** (from spec): The link checker distinguishes between permanent failures (404) and temporary failures (timeout, 5xx). The `retryOn429`, `retryCount`, and `timeout` settings handle transient failures. Permanent 404s will fail the build as expected.

## Acceptance Criteria Mapping

| FR | Current Status | Change Needed |
|----|---------------|---------------|
| FR-010: Markdown formatting validation | ✅ Partially met (docs + README) | Minor: expand glob to `"*.md"` |
| FR-011: Link validation | ✅ Met for docs | Minor: add README to link check |
| FR-012: Clear error messages | ✅ Met (default tool behavior) | None |
