# Verification and Baseline Contract

**Feature**: 040-doc-refresh-playbook
**Date**: 2026-03-14
**Version**: 1.0

## Purpose

Defines the verification steps and baseline recording process that close each refresh cycle. This contract governs Phase 5 (Cross-References & Diagrams) and Phase 6 (Verify & Stamp) of the refresh playbook.

## Cross-Reference Validation (Phase 5)

### Internal Link Check

**Command**:
```bash
grep -rn '\[.*\](docs/' README.md docs/
```

**Processing**:
1. For each match, extract the target path from the markdown link
2. Resolve the path relative to the repository root
3. Check if the target file exists
4. If the link includes an anchor (`#section-name`), check if the target file contains a heading that generates that anchor

**Output**: List of broken links with source file, line number, and target path.

**Acceptance criteria** (SC-003): Zero broken internal links after the refresh cycle.

### Mermaid Diagram Regeneration

**Trigger**: Change Manifest contains items in the "Architectural shifts" category.

**Command**:
```bash
scripts/generate-diagrams.sh
```

**Verification**: After regeneration, verify that all `.mmd` files in `docs/architectures/` are valid Mermaid syntax. The CI pipeline includes automated diagram generation, but the refresh cycle may need to invoke the script explicitly for changes not captured by CI.

**Files affected**:
- `docs/architectures/high-level.mmd`
- `docs/architectures/deployment.mmd`
- `docs/architectures/frontend-components.mmd`
- `docs/architectures/backend-components.mmd`
- `docs/architectures/data-flow.mmd`

### ADR Index Update

**Trigger**: New files in `docs/decisions/` since the last refresh.

**Command**:
```bash
git diff --name-status <baseline-sha>..HEAD -- docs/decisions/
```

**Processing**: For each new ADR file, add an entry to `docs/decisions/README.md` with the ADR number, title, date, and status.

### Ownership Update

**Trigger**: New documentation files created during the refresh.

**Processing**: If new files were added to `docs/`, update `docs/OWNERS.md` with ownership for the new files.

## Final Verification (Phase 6)

### Weekly Sweep Checklist

Run the checklist at `docs/checklists/weekly-sweep.md` as a validation pass:
- API Reference Check (against `backend/src/api/`)
- Configuration Check (against `backend/src/config.py`)
- Setup Guide Check (against current project state)
- All other sections as defined in the checklist

**Acceptance criteria**: All checklist items should pass after a complete refresh cycle.

### UX Spot-Check

Manually verify 3 key user flows in the running application:
1. Select a representative P0/P1 user flow
2. Walk through the flow in the application
3. Compare page names, navigation, and terminology against the documentation
4. Flag any discrepancies for correction

**Acceptance criteria** (SC-006): All three spot-checked flows match documentation.

### Scope Verification

**Command**:
```bash
git diff --stat
```

**Acceptance criteria** (SC-005): Changes are limited to:
- `docs/**` (documentation files)
- `README.md` (project readme)
- `CHANGELOG.md` (refresh record)
- `docs/.last-refresh` (baseline file)

Any changes outside these paths indicate accidental code edits and must be reverted before committing.

## Baseline Recording

### CHANGELOG Entry

Add a dated entry to `CHANGELOG.md` under the appropriate section:

```markdown
## YYYY-MM-DD

### Changed
- Documentation refresh: updated [list of documents] to match current codebase state
```

The entry lists which documents were updated and any notable changes (e.g., "added new /videos API documentation", "removed deprecated Signal integration section").

### Baseline File Update

Write `docs/.last-refresh` with the current cycle's data:

```json
{
  "date": "2026-03-14T18:00:00Z",
  "sha": "<commit-sha-of-refresh-commit>",
  "documents_updated": ["docs/api-reference.md", "docs/architecture.md", "README.md"],
  "documents_skipped": ["docs/signal-integration.md", "docs/testing.md"],
  "broken_links_found": 0,
  "manual_followups": []
}
```

**Timing**: The baseline is written AFTER the CHANGELOG entry is committed, so the SHA reflects the complete refresh commit. This ensures the next cycle's diff window starts from the fully-committed state.

**Commit message format**:
```
docs: bi-weekly documentation refresh YYYY-MM-DD

Updated: <list of files>
Skipped: <list of files>
Broken links: <count>
```

## Error Handling

| Condition | Behavior |
|---|---|
| Link validation finds broken links | Report all broken links; do NOT block the refresh. Broken links are recorded in the baseline for the next cycle. |
| Diagram generation fails | Report the failure; continue with remaining tasks. Record as a manual followup. |
| Weekly sweep checklist has failures | Investigate each failure. If caused by the refresh itself, fix immediately. If pre-existing, record as a manual followup. |
| UX spot-check reveals discrepancies | Fix documentation to match the application. If the application behavior is wrong, file a bug instead. |
| Scope verification shows code changes | Revert code changes before committing. Documentation refresh must not modify code. |
