# Documentation Update Contract

**Feature**: 040-doc-refresh-playbook
**Date**: 2026-03-14
**Version**: 1.0

## Purpose

Defines the process for updating individual documentation files against their source-of-truth files. This contract governs Phase 3 (README update) and Phase 4 (docs/ update) of the refresh playbook.

## Documentation-to-Source Mapping

Each documentation file has a designated source-of-truth. Updates are performed by diffing the document's claims against the source's actual state.

| Document | Source of Truth | Diff Method |
|---|---|---|
| `README.md` (feature list) | Change Manifest "New features" + "Removed functionality" | Compare listed features against manifest |
| `README.md` (architecture) | `docker-compose.yml`, `backend/src/services/` | Compare described services against running services |
| `README.md` (quickstart) | `pyproject.toml`, `package.json`, `docker-compose.yml` | Compare documented versions/commands against files |
| `docs/api-reference.md` | `backend/src/api/*.py` route decorators | Compare documented endpoints against code routes |
| `docs/architecture.md` | `backend/src/services/` + `docker-compose.yml` | Compare documented services against code/compose |
| `docs/agent-pipeline.md` | Pipeline/orchestrator service files | Compare documented stages/flow against code logic |
| `docs/configuration.md` | `backend/src/config.py` | Compare documented env vars against config class |
| `docs/custom-agents-best-practices.md` | Agent MCP sync code + `.agent.md` files | Compare documented properties against code |
| `docs/project-structure.md` | `tree` or `find` output | Compare documented tree against filesystem |
| `docs/testing.md` | Test dirs + `pyproject.toml` / `vitest.config.ts` | Compare documented commands against config |
| `docs/troubleshooting.md` | Change Manifest "Fixed" items | Add new error patterns, remove fixed issues |
| `docs/setup.md` | `pyproject.toml`, `package.json`, `docker-compose.yml` | Compare documented steps against current files |
| `docs/signal-integration.md` | Signal-related backend code | Compare documented behavior against code |

## Update Process (Per Document)

For each document flagged by the PriorityAssignment:

### Step 1: Extract Current Claims

Read the document and list all factual claims:
- Endpoint paths, methods, and parameters (for API docs)
- Environment variable names, types, and defaults (for config docs)
- Service names and relationships (for architecture docs)
- Version numbers and commands (for setup/quickstart docs)
- File paths and directory structures (for project-structure docs)

### Step 2: Extract Source Truth

Read the source-of-truth file(s) and extract the current state:
- Parse route decorators for API endpoints
- Parse config class for environment variables
- Parse docker-compose.yml for services
- Run `tree` for filesystem structure
- Parse pyproject.toml/package.json for versions

### Step 3: Diff and Classify Changes

Compare claims against truth and classify each discrepancy:

| Discrepancy Type | Action |
|---|---|
| **Stale claim** (doc says X, source says Y) | Update doc to match source |
| **Missing coverage** (source has X, doc doesn't mention it) | Add new section/entry to doc |
| **Orphaned content** (doc says X, source no longer has X) | Remove from doc |
| **Accurate claim** (doc matches source) | No action needed |

### Step 4: Apply Updates

For each discrepancy:
1. Make the minimum change to correct the document
2. Preserve existing formatting and style
3. Do not rewrite sections that are already accurate
4. Add new content in the appropriate location (following existing structure)

### Step 5: Verify Update

After applying all changes to a document:
1. Re-run the diff between updated doc and source — zero discrepancies expected
2. Check that all internal links within the document still resolve
3. Check that markdown formatting is valid

## README-Specific Rules (Phase 3)

README updates follow additional rules beyond the standard process:

1. **Feature list ordering**: Features are ordered by current prominence (most-used/most-promoted first)
2. **Architecture overview**: Must match the current `docker-compose.yml` service topology
3. **Quickstart instructions**: Must be executable — every command must work on a fresh clone
4. **Workflow descriptions**: Page names, navigation paths, and terminology must match the live application

## Scope Boundaries

- **In scope**: Factual accuracy of documentation content (endpoints, configs, services, versions, commands, structure)
- **Out of scope**: Prose quality, writing style, tutorial completeness (these are addressed by separate editorial review)
- **Out of scope**: Code comments and inline documentation (per spec scope boundary)
- **Out of scope**: Frontend `docs/` files are included but secondary — updated only when the Change Manifest includes frontend-specific changes
