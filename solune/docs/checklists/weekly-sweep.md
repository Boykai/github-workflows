# Weekly Documentation Staleness Sweep

**Estimated time**: ~30 minutes
**Frequency**: Weekly (dev rotation)
**Purpose**: Catch documentation that has drifted from the codebase since the last review.

## API Reference Check

Compare `docs/api-reference.md` against `backend/src/api/`:

- [ ] Every route file in `backend/src/api/` has matching API table entries in `docs/api-reference.md`
- [ ] All path prefixes, methods, and path parameters are still accurate
- [ ] No endpoints removed or deprecated in code are still listed in the docs

## Configuration Check

Compare `docs/configuration.md` against `backend/src/config.py`:

- [ ] All environment variables in `backend/src/config.py` are documented in `docs/configuration.md`
- [ ] No deleted environment variables are still listed in the docs
- [ ] Default values and required/optional status are still correct

## Setup Guide Check

Compare `docs/setup.md` against the current project state:

- [ ] Docker Compose and manual setup steps still match project state
- [ ] Prerequisite versions (Python, Node, Docker) still match `pyproject.toml` and `package.json`
- [ ] Codespaces badge and quick start flow still work end-to-end

## Completion

- **Date**: YYYY-MM-DD
- **Reviewer**: @username
- **Issues found**: [count] (link to issues if filed)

## See Also

- [Weekly Sweep Checklist](../checklists/weekly-sweep.md) — this checklist
- [Monthly Review](monthly-review.md) — deeper monthly quality gate
- [Quarterly Audit](quarterly-audit.md) — comprehensive structural review
