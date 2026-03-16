# Quickstart: UI Audit Issue Template

**Feature**: `045-ui-audit` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Overview

This feature delivers a GitHub issue template for standardised UI page audits. The template is a static Markdown file — there is no build step, no runtime component, and no automated tests. Validation is manual: create an issue from the template and verify the output.

## Prerequisites

- Access to the GitHub repository with write permissions
- The branch `045-ui-audit` or `copilot/speckit-specify-ui-audit` checked out

## Template Location

```text
.github/ISSUE_TEMPLATE/chore-ui-aduit.md
```

## Quick Verification

### 1. Verify Template Structure

```bash
# Check the template file exists
ls -la .github/ISSUE_TEMPLATE/chore-ui-aduit.md

# Verify YAML front matter
head -7 .github/ISSUE_TEMPLATE/chore-ui-aduit.md
# Expected:
# ---
# name: UI Aduit
# about: Recurring chore — UI Aduit
# title: '[CHORE] UI Aduit'
# labels: chore
# assignees: ''
# ---
```

### 2. Verify Checklist Item Count

```bash
# Count total checklist items (lines starting with "- [ ]")
grep -c '^\- \[ \]' .github/ISSUE_TEMPLATE/chore-ui-aduit.md
# Expected: 60 (minimum 59 per FR-012)
```

### 3. Verify All 10 Audit Categories Present

```bash
# List all category headings
grep '^### [0-9]' .github/ISSUE_TEMPLATE/chore-ui-aduit.md
# Expected output:
# ### 1. Component Architecture & Modularity
# ### 2. Data Fetching & State Management
# ### 3. Loading, Error & Empty States
# ### 4. Type Safety
# ### 5. Accessibility (a11y)
# ### 6. Text, Copy & UX Polish
# ### 7. Styling & Layout
# ### 8. Performance
# ### 9. Test Coverage
# ### 10. Code Hygiene
```

### 4. Verify Six Implementation Phases

```bash
# List all phase headings
grep '^### Phase' .github/ISSUE_TEMPLATE/chore-ui-aduit.md
# Expected output:
# ### Phase 1: Discovery & Assessment
# ### Phase 2: Structural Fixes (if needed)
# ### Phase 3: States & Error Handling
# ### Phase 4: a11y & UX Polish
# ### Phase 5: Testing
# ### Phase 6: Validation
```

### 5. Verify Placeholder Tokens

```bash
# Check for [PAGE_NAME] placeholder
grep -c '\[PAGE_NAME\]' .github/ISSUE_TEMPLATE/chore-ui-aduit.md
# Expected: ≥2 (title heading and TL;DR)

# Check for [PageName] placeholder (PascalCase file references)
grep -c '\[PageName\]' .github/ISSUE_TEMPLATE/chore-ui-aduit.md
# Expected: ≥3 (file paths in multiple sections)

# Check for [feature] placeholder (directory references)
grep -c '\[feature\]' .github/ISSUE_TEMPLATE/chore-ui-aduit.md
# Expected: ≥5 (component paths, test paths, etc.)
```

### 6. Verify Label Assignment

```bash
# Check labels in front matter
grep '^labels:' .github/ISSUE_TEMPLATE/chore-ui-aduit.md
# Expected: labels: chore
```

## Manual Browser Verification

After the branch is merged, verify the template works end-to-end:

1. **Navigate** to the repository's "New Issue" page on GitHub
2. **Select** the "UI Aduit" template from the template picker
3. **Verify** the issue body contains all 10 audit category sections with checkbox items
4. **Replace** all `[PAGE_NAME]` placeholders with a real page name (e.g., "Projects")
5. **Replace** all `[PageName]` placeholders with the PascalCase name (e.g., "ProjectsPage")
6. **Replace** all `[feature]` placeholders with the feature directory (e.g., "board")
7. **Submit** the issue
8. **Verify** the "chore" label is automatically applied
9. **Verify** the issue title shows `[CHORE] UI Aduit`
10. **Verify** checkbox counters display correctly (e.g., "0/7" per section)
11. **Check** one checkbox item and verify the counter updates (e.g., "1/7")

## Using the Template for a Page Audit

```bash
# Example: Audit the Projects page
# 1. Create a new issue from the template
# 2. Replace placeholders:
#    [PAGE_NAME] → Projects
#    [PageName] → ProjectsPage
#    [feature]  → board
# 3. Work through Phase 1 (Discovery) to understand the page
# 4. Score each checklist item (Pass/Fail/N/A)
# 5. Fix issues in Phase 2–5 order
# 6. Run Phase 6 verification commands
# 7. Close the issue when all items are checked
```

## Key Constraints

- **No code changes**: This is a static Markdown template — no build or deploy step
- **No automated tests**: Validation is manual (create issue, verify output)
- **No new dependencies**: The template uses only GitHub's built-in issue template feature
- **Reusable**: The same template applies to any page via placeholder substitution (SC-007)
