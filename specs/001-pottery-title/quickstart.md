# Quickstart Guide: Update Project Title to 'pottery'

**Branch**: `copilot/update-project-title-to-pottery-again` | **Date**: 2026-02-16 | **Spec**: [spec.md](./spec.md)

## Overview

This guide provides step-by-step instructions for implementing the pottery title update feature. Follow these steps in order to ensure all functional requirements are met.

## Prerequisites

- ✅ Git repository cloned
- ✅ Branch `copilot/update-project-title-to-pottery-again` checked out
- ✅ Text editor or IDE available
- ✅ Node.js 18+ installed (for frontend testing)
- ✅ Python 3.11+ installed (for backend verification)

## Quick Reference

| File | Line(s) | Change Type | Priority |
|------|---------|-------------|----------|
| frontend/index.html | 7 | REPLACE | P1 |
| frontend/e2e/ui.spec.ts | 15 | REPLACE | P1 |
| README.md | 1, 3 | REPLACE | P2 |
| frontend/package.json | 4 (new) | ADD | P3 |
| backend/pyproject.toml | 4 | UPDATE | P3 |

## Implementation Steps

### Step 1: Update HTML Page Title (P1)

**Goal**: Change browser tab title to "pottery"

**File**: `frontend/index.html`

**Action**:
```bash
# Navigate to repository root
cd /home/runner/work/github-workflows/github-workflows

# Edit the file
```

**Change line 7 from**:
```html
    <title>Welcome to Tech Connect 2026!</title>
```

**To**:
```html
    <title>pottery</title>
```

**Verification**:
```bash
grep -n "<title>" frontend/index.html
# Expected: 7:    <title>pottery</title>
```

**✅ Acceptance Criteria**:
- [ ] Line 7 contains `<title>pottery</title>`
- [ ] Lowercase "pottery" used
- [ ] HTML structure unchanged

---

### Step 2: Update E2E Test Assertion (P1)

**Goal**: Align test with new page title

**File**: `frontend/e2e/ui.spec.ts`

**Action**:
```bash
# Edit the test file
```

**Change line 15 from**:
```typescript
  await expect(page).toHaveTitle('Welcome to Tech Connect 2026!');
```

**To**:
```typescript
  await expect(page).toHaveTitle('pottery');
```

**Verification**:
```bash
grep "toHaveTitle" frontend/e2e/ui.spec.ts
# Expected: Line containing .toHaveTitle('pottery')
```

**✅ Acceptance Criteria**:
- [ ] Test assertion updated to expect "pottery"
- [ ] TypeScript syntax valid

---

### Step 3: Verify P1 Changes (Browser Title)

**Goal**: Ensure browser displays "pottery" and tests pass

**Actions**:

1. **Install dependencies** (if not already done):
```bash
cd frontend
npm install
cd ..
```

2. **Run TypeScript check**:
```bash
cd frontend
npm run type-check
# Expected: No errors
```

3. **Start frontend dev server** (Terminal 1):
```bash
cd frontend
npm run dev
# Server will start on http://localhost:5173
```

4. **Run E2E test** (Terminal 2):
```bash
cd frontend
npm run test:e2e
# Expected: Test passes
```

5. **Manual verification**:
   - Open browser to http://localhost:5173
   - Check browser tab displays "pottery"
   - Take screenshot if needed

6. **Stop dev server**:
```bash
# Press Ctrl+C in Terminal 1
```

**✅ Acceptance Criteria**:
- [ ] Browser tab shows "pottery"
- [ ] E2E test passes
- [ ] No console errors

---

### Step 4: Update README Title (P2)

**Goal**: Update documentation to reference "pottery"

**File**: `README.md`

**Action 1 - Update main heading (line 1)**:

**Change from**:
```markdown
# GitHub Projects Chat Interface
```

**To**:
```markdown
# pottery
```

**Action 2 - Update subtitle (line 3)**:

**Change from**:
```markdown
> **A new way of working with DevOps** — leveraging AI in a conversational web app to create, manage, and execute GitHub Issues on a GitHub Project Board.
```

**To**:
```markdown
> **pottery: A new way of working with DevOps** — leveraging AI in a conversational web app to create, manage, and execute GitHub Issues on a GitHub Project Board.
```

**Verification**:
```bash
head -5 README.md
# Expected: Line 1 shows "# pottery"
# Expected: Line 3 shows "pottery:" prefix
```

**✅ Acceptance Criteria**:
- [ ] Line 1 is `# pottery`
- [ ] Line 3 includes "pottery:" prefix
- [ ] Markdown syntax valid
- [ ] No trailing whitespace

---

### Step 5: Verify P2 Changes (Documentation)

**Goal**: Ensure README renders correctly

**Actions**:

1. **Check markdown syntax**:
```bash
# Visual inspection - open README.md in editor
# or use markdown preview if available
```

2. **Verify links** (optional but recommended):
```bash
# If markdown-link-check is installed:
npx markdown-link-check README.md

# Otherwise, manually click a few links in GitHub preview
```

3. **Search for old title references**:
```bash
grep -i "github projects chat interface" README.md
# Expected: No matches in title (line 1)
# May appear in body text describing functionality - that's OK
```

**✅ Acceptance Criteria**:
- [ ] README title displays "pottery"
- [ ] Subtitle includes "pottery:"
- [ ] All links work (spot check)
- [ ] Markdown renders correctly in GitHub

---

### Step 6: Add Frontend Package Description (P3)

**Goal**: Add human-readable description to package.json

**File**: `frontend/package.json`

**Action**:

**Change from**:
```json
{
  "name": "github-projects-chat-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
```

**To**:
```json
{
  "name": "github-projects-chat-frontend",
  "private": true,
  "version": "0.1.0",
  "description": "pottery - A conversational DevOps interface for GitHub Projects",
  "type": "module",
```

**⚠️ Important Notes**:
- Add comma after `"version": "0.1.0",` if not present
- Maintain 2-space indentation
- Package name MUST stay `github-projects-chat-frontend` (backward compatibility)

**Verification**:
```bash
jq '.name, .description' frontend/package.json
# Expected output:
# "github-projects-chat-frontend"
# "pottery - A conversational DevOps interface for GitHub Projects"
```

**✅ Acceptance Criteria**:
- [ ] `name` field unchanged
- [ ] `description` field added with "pottery"
- [ ] JSON is valid (jq parses without errors)

---

### Step 7: Update Backend Package Description (P3)

**Goal**: Update pyproject.toml description field

**File**: `backend/pyproject.toml`

**Action**:

**Change line 4 from**:
```toml
description = "FastAPI backend for GitHub Projects Chat Interface"
```

**To**:
```toml
description = "pottery - FastAPI backend for conversational DevOps"
```

**⚠️ Important Notes**:
- Package name on line 2 MUST stay `github-projects-chat-backend` (backward compatibility)
- Maintain TOML syntax (quotes, equal sign)

**Verification**:
```bash
grep -E "^(name|description) = " backend/pyproject.toml
# Expected output:
# name = "github-projects-chat-backend"
# description = "pottery - FastAPI backend for conversational DevOps"
```

**✅ Acceptance Criteria**:
- [ ] `name` field unchanged
- [ ] `description` field updated with "pottery"
- [ ] TOML is valid

---

### Step 8: Verify P3 Changes (Package Metadata)

**Goal**: Ensure package configurations are valid

**Actions**:

1. **Validate frontend JSON**:
```bash
cd frontend
jq empty package.json
# Expected: No output (means valid JSON)
```

2. **Validate backend TOML**:
```bash
cd backend
python -c "import tomli; tomli.load(open('pyproject.toml', 'rb'))"
# Expected: No output (means valid TOML)
# Note: tomli may not be installed; if so, skip this check
```

3. **Verify package names unchanged**:
```bash
# From repository root
jq .name frontend/package.json
# Expected: "github-projects-chat-frontend"

grep "^name = " backend/pyproject.toml
# Expected: name = "github-projects-chat-backend"
```

**✅ Acceptance Criteria**:
- [ ] Both package names unchanged
- [ ] Both description fields include "pottery"
- [ ] JSON and TOML syntax valid

---

### Step 9: Final Verification & Testing

**Goal**: Comprehensive verification of all changes

**Full Test Suite**:

1. **Frontend tests**:
```bash
cd frontend

# TypeScript compilation
npm run type-check

# Unit tests (if any)
npm test

# E2E tests
npm run test:e2e
```

2. **Backend tests** (optional, not affected by title change):
```bash
cd backend
source .venv/bin/activate  # or create venv if needed
pytest tests/ -v
```

3. **Visual verification**:
```bash
cd frontend
npm run dev
# Open http://localhost:5173 in browser
# Verify tab shows "pottery"
```

4. **Git diff review**:
```bash
cd /home/runner/work/github-workflows/github-workflows
git --no-pager diff
# Review changes - should only show the 5 files modified as expected
```

**✅ Final Acceptance Criteria**:
- [ ] All tests pass
- [ ] Browser displays "pottery" in tab
- [ ] README shows "pottery" title
- [ ] Package configs updated correctly
- [ ] Only 5 files modified (html, test, README, 2 package configs)
- [ ] No unexpected changes in diff

---

### Step 10: Commit Changes

**Goal**: Commit all changes to the PR branch

**Actions**:

1. **Stage changes**:
```bash
cd /home/runner/work/github-workflows/github-workflows
git add frontend/index.html
git add frontend/e2e/ui.spec.ts
git add README.md
git add frontend/package.json
git add backend/pyproject.toml
```

2. **Review staged changes**:
```bash
git --no-pager diff --staged
# Verify only expected changes are staged
```

3. **Commit**:
```bash
git commit -m "Update project title to 'pottery' across HTML, docs, and package configs

- Update browser page title in frontend/index.html
- Update E2E test assertion to expect 'pottery'
- Update README title and subtitle
- Add description field to frontend/package.json
- Update description in backend/pyproject.toml
- Preserve package identifiers for backward compatibility

Closes #[ISSUE_NUMBER]"
```

4. **Push to PR branch**:
```bash
git push origin copilot/update-project-title-to-pottery-again
```

**✅ Acceptance Criteria**:
- [ ] Commit message descriptive
- [ ] Changes pushed to remote branch
- [ ] PR updated on GitHub

---

## Troubleshooting

### Issue: E2E Test Fails

**Symptoms**: Test reports browser title doesn't match

**Solutions**:
1. Verify frontend/index.html line 7 has `<title>pottery</title>` exactly
2. Ensure dev server restarted after HTML change
3. Check browser cache - try hard refresh (Ctrl+Shift+R)
4. Verify test file updated correctly (line 15)

---

### Issue: JSON Syntax Error in package.json

**Symptoms**: `jq` command fails or npm throws parse error

**Solutions**:
1. Check commas - description field needs comma after it
2. Verify quotes are straight quotes, not smart quotes
3. Use online JSON validator
4. Compare with original file structure

---

### Issue: Git Shows Unexpected Files Changed

**Symptoms**: `git status` shows more than 5 files

**Solutions**:
1. Review each file with `git diff <filename>`
2. Use `git checkout <filename>` to revert unintended changes
3. Check for editor temp files or node_modules changes
4. Ensure only intentional text changes made

---

### Issue: Package Names Changed Accidentally

**Symptoms**: Backend imports fail or npm package resolution errors

**Solutions**:
1. Verify package names:
   - `jq .name frontend/package.json` → should be `github-projects-chat-frontend`
   - `grep "^name = " backend/pyproject.toml` → should be `github-projects-chat-backend`
2. If changed, restore from git:
   ```bash
   git checkout frontend/package.json backend/pyproject.toml
   # Then redo Step 6 and Step 7 carefully
   ```

---

## Success Metrics

Upon completion, verify all success criteria from spec:

| Criterion | Verification | Status |
|-----------|--------------|--------|
| SC-001: Browser displays "pottery" in 100ms | Open app, check tab title | [ ] |
| SC-002: 100% documentation replacement | Search README for old title | [ ] |
| SC-003: Package metadata updated | Check descriptions in configs | [ ] |
| SC-004: No broken links | Test README links | [ ] |
| SC-005: Changes verifiable in 5 seconds | Quick visual + grep check | [ ] |

---

## Next Steps

After completing this quickstart:

1. ✅ Ensure all changes committed and pushed
2. ✅ Request code review from team
3. ✅ Wait for CI/CD pipeline to pass
4. ✅ Merge PR once approved
5. ✅ Verify changes in production/staging

---

## Reference Commands

Quick copy-paste commands for verification:

```bash
# Verify HTML title
grep -n "<title>" frontend/index.html

# Verify test assertion
grep "toHaveTitle" frontend/e2e/ui.spec.ts

# Verify README title
head -1 README.md

# Verify package names unchanged
jq .name frontend/package.json
grep "^name = " backend/pyproject.toml

# Verify descriptions updated
jq .description frontend/package.json
grep "^description = " backend/pyproject.toml

# Run full test suite
cd frontend && npm test && npm run test:e2e
cd ../backend && source .venv/bin/activate && pytest tests/

# Visual check
cd frontend && npm run dev
# Open http://localhost:5173
```

---

## Estimated Time

| Phase | Estimated Time |
|-------|---------------|
| Steps 1-2 (HTML & Test) | 5 minutes |
| Step 3 (Verify P1) | 10 minutes |
| Steps 4-5 (README) | 5 minutes |
| Steps 6-8 (Package configs) | 10 minutes |
| Step 9 (Final verification) | 15 minutes |
| Step 10 (Commit & push) | 5 minutes |
| **Total** | **50 minutes** |

---

## Rollback Plan

If issues arise after merge:

1. **Revert commit**:
```bash
git revert <commit-hash>
git push origin main
```

2. **Manual rollback** (if revert fails):
   - Restore frontend/index.html line 7 to `Welcome to Tech Connect 2026!`
   - Restore test assertion
   - Restore README title
   - Remove description from frontend/package.json
   - Restore backend/pyproject.toml description

All changes are text-only with no database or API impacts, making rollback safe and straightforward.
