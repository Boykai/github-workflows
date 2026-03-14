# Quickstart: Recurring Documentation Refresh Playbook

**Feature**: 040-doc-refresh-playbook
**Date**: 2026-03-14

## Prerequisites

- Git (with full history — not a shallow clone)
- Access to the repository with read permissions on all files
- Ability to run shell commands (`grep`, `find`, `git diff`, `git log`)
- Access to the running application (for UX spot-checks in Phase 6)

## Before Your First Refresh

If no `docs/.last-refresh` baseline file exists, create one:

```bash
# Record today's date and current commit as the starting baseline
SHA=$(git rev-parse HEAD)
DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)

cat > docs/.last-refresh << EOF
{
  "date": "$DATE",
  "sha": "$SHA",
  "documents_updated": [],
  "documents_skipped": [],
  "broken_links_found": 0,
  "manual_followups": []
}
EOF
```

## Refresh Cycle Walkthrough

### Phase 1: Detect Changes (30–45 min)

```bash
# Read the baseline
cat docs/.last-refresh
# Note the date and sha values

# Source 1: CHANGELOG delta
# Open CHANGELOG.md, find all entries after the baseline date
# Extract items under ### Added, ### Changed, ### Removed, ### Fixed

# Source 2: Spec scan
find specs/ -mindepth 1 -maxdepth 1 -type d -newer docs/.last-refresh

# Source 3: Code diff analysis
LAST_SHA=$(jq -r .sha docs/.last-refresh)
git diff --stat $LAST_SHA..HEAD
git diff --name-status $LAST_SHA..HEAD
git log --oneline --since="$(jq -r .date docs/.last-refresh)"
```

Compile findings into the Change Manifest with five categories:

- New features, Changed behavior, Removed functionality, Architectural shifts, UX shifts

### Phase 2: Prioritize (15–20 min)

Review the Change Manifest and assign priorities:

| Priority | Question to Ask | If Yes → Flag |
|---|---|---|
| **P0** | Has the app's pitch or primary workflow changed? | `README.md` |
| **P1** | Are specific features new or changed? | Relevant feature docs |
| **P2** | Were modules added/removed/reorganized? | `project-structure.md`, `architecture.md` |
| **P3** | Did config, errors, or tests change? | `configuration.md`, `troubleshooting.md`, `testing.md`, `setup.md` |

### Phase 3: Update README (30–60 min, if P0)

Only if README was flagged P0:

1. Update the feature list (add new capabilities, remove deprecated ones)
2. Update the architecture overview (if services changed)
3. Validate quickstart instructions:

   ```bash
   # Check current versions
   grep python_requires backend/pyproject.toml
   grep '"node"' frontend/package.json
   cat docker-compose.yml | head -20
   ```

4. Update workflow descriptions (page names, nav paths, terminology)

### Phase 4: Update Docs (1.5–2.5 hours)

For each flagged document, diff against its source of truth:

| Document | Quick Diff Command |
|---|---|
| `api-reference.md` | `grep -rn "@app\.\|@router\." backend/src/api/` |
| `architecture.md` | `grep "services:" docker-compose.yml -A 100` |
| `configuration.md` | `grep -n "os.environ\|getenv\|Field(" backend/src/config.py` |
| `project-structure.md` | `tree -I node_modules -I __pycache__ -I .git -L 3` |
| `testing.md` | `grep "\[tool.pytest\]" backend/pyproject.toml; grep "test" frontend/package.json` |
| `setup.md` | `cat docker-compose.yml; grep python_requires backend/pyproject.toml` |

For each document: correct inaccuracies, add new sections, remove stale content.

### Phase 5: Cross-References (15–20 min)

```bash
# Validate internal links
grep -rn '\[.*\](docs/' README.md docs/ | while read -r line; do
  FILE=$(echo "$line" | grep -oP '\(docs/[^)]+\)' | tr -d '()')
  if [ ! -f "$FILE" ]; then
    echo "BROKEN: $line → $FILE"
  fi
done

# Regenerate diagrams (if architecture changed)
scripts/generate-diagrams.sh

# Check for new ADRs
git diff --name-status $LAST_SHA..HEAD -- docs/decisions/
```

### Phase 6: Verify & Stamp (20–30 min)

1. Run the weekly sweep checklist: `docs/checklists/weekly-sweep.md`
2. Spot-check 3 user flows in the running application
3. Verify scope:

   ```bash
   git diff --stat
   # Should only show docs/, README.md, CHANGELOG.md
   ```

4. Add CHANGELOG entry and commit:

   ```bash
   # Add entry to CHANGELOG.md under current date
   git add docs/ README.md CHANGELOG.md
   git commit -m "docs: bi-weekly documentation refresh $(date +%Y-%m-%d)"
   ```

5. Update baseline:

   ```bash
   # Write new baseline with the refresh commit SHA
   SHA=$(git rev-parse HEAD)
   DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
   # Update docs/.last-refresh with new date, sha, and lists
   git add docs/.last-refresh
   git commit --amend --no-edit
   ```

## Total Estimated Time

| Phase | Time |
|---|---|
| Phase 1: Detect Changes | 30–45 min |
| Phase 2: Prioritize | 15–20 min |
| Phase 3: Update README | 0–60 min (skip if not P0) |
| Phase 4: Update Docs | 1.5–2.5 hours |
| Phase 5: Cross-References | 15–20 min |
| Phase 6: Verify & Stamp | 20–30 min |
| **Total** | **~3–4 hours** (within SC-001 target of 4 hours) |

## Key Files Reference

| File | Role |
|---|---|
| `docs/.last-refresh` | Baseline for next cycle (JSON) |
| `CHANGELOG.md` | Primary input for change detection |
| `docs/checklists/weekly-sweep.md` | Final validation checklist |
| `scripts/generate-diagrams.sh` | Mermaid diagram regeneration |
| `docs/architectures/*.mmd` | Architecture diagrams |
| `docs/decisions/README.md` | ADR index |
| `docs/OWNERS.md` | Documentation ownership |
