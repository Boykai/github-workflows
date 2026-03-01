# Quickstart: Attach Parent Branch to GitHub Issue Upon Branch Creation

**Feature**: 014-attach-parent-branch-issue | **Date**: 2026-02-28

## Prerequisites

- GitHub repository with GitHub Actions enabled
- Repository must have Issues enabled
- Branches must follow a naming convention with a leading issue number (e.g., `042-fix-navigation`)

## Overview

This feature adds a GitHub Actions workflow (`.github/workflows/branch-issue-link.yml`) that automatically posts a comment on a GitHub Issue when a new branch is created with that issue's number in the branch name.

## How It Works

1. A developer creates a branch (e.g., `042-fix-navigation`)
2. GitHub fires a `create` event
3. The workflow parses the branch name and extracts `42` as the issue number
4. The workflow checks Issue #42 exists and hasn't already been linked
5. The workflow posts a comment on Issue #42 with the branch reference

## Supported Branch Naming Conventions

| Pattern | Example | Extracted Issue # |
|---------|---------|-------------------|
| `NNN-description` | `042-fix-navigation` | #42 |
| `prefix/issue-NNN-description` | `feature/issue-15-add-search` | #15 |
| `NNN-any-text` | `100-implement-dashboard` | #100 |
| Leading zeros | `007-feature` | #7 |

## Testing Locally

### Verify Workflow Syntax

```bash
# Check YAML syntax (requires yamllint)
yamllint .github/workflows/branch-issue-link.yml

# Or use actionlint for GitHub Actions-specific validation
actionlint .github/workflows/branch-issue-link.yml
```

### Manual Testing

```bash
# 1. Ensure you have an open issue (e.g., Issue #42)

# 2. Create a branch with the issue number
git checkout -b 042-test-branch-link

# 3. Push the branch to trigger the workflow
git push origin 042-test-branch-link

# 4. Check the workflow run in GitHub Actions tab

# 5. Verify Issue #42 has a new comment with the branch link

# 6. Clean up
git checkout main
git branch -d 042-test-branch-link
git push origin --delete 042-test-branch-link
```

### Testing Edge Cases

```bash
# No issue number (should log warning, no error)
git checkout -b hotfix-urgent
git push origin hotfix-urgent

# Non-existent issue number (should warn)
git checkout -b 99999-nonexistent
git push origin 99999-nonexistent

# Re-push same branch (idempotency — no duplicate comment)
git checkout -b 042-test-branch-link
git push origin 042-test-branch-link
# Delete and recreate
git push origin --delete 042-test-branch-link
git push origin 042-test-branch-link
# Verify only one comment exists on Issue #42
```

## Viewing Workflow Logs

```bash
# List recent workflow runs for branch-issue-link
gh run list --workflow=branch-issue-link.yml

# View logs for a specific run
gh run view <run-id> --log
```

## Key Files

| Path | Description |
|------|-------------|
| `.github/workflows/branch-issue-link.yml` | The GitHub Actions workflow |
| `specs/014-attach-parent-branch-issue/spec.md` | Feature specification |
| `specs/014-attach-parent-branch-issue/plan.md` | Implementation plan |
| `specs/014-attach-parent-branch-issue/contracts/branch-issue-link-workflow.md` | Workflow contract |

## Troubleshooting

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Workflow doesn't trigger | Branch created in a fork | Workflow only runs on the main repository |
| No comment posted | Branch name doesn't contain an issue number | Use a naming convention like `NNN-description` |
| Duplicate comments | Idempotency marker was removed from a previous comment | Do not edit or delete the HTML marker in workflow-generated comments |
| Warning: issue not found | Issue number in branch name doesn't match any issue | Verify the issue number exists in the repository |
| Warning: issue is closed | The referenced issue was previously closed | Reopen the issue or ignore the warning — the comment is still posted |
