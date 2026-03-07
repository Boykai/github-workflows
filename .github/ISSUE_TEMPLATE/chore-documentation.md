---
name: Documentation Sweep
about: Recurring chore — Documentation Staleness Sweep
title: '[CHORE] Documentation Sweep'
labels: chore
assignees: ''
---

## Recurring Documentation Update Process

## Overview

A structured cadence for keeping all project documentation accurate, complete, and helpful across the full stack — backend API, frontend components, architecture, configuration, and developer guides.

---

## Cadence

| Review Type            | Frequency     | Trigger                                              |
|------------------------|---------------|------------------------------------------------------|
| Inline doc check       | Every PR      | Author + reviewer responsibility                     |
| Staleness sweep        | Weekly        | Dev rotation (same person as security spot check)    |
| Full doc review        | Monthly       | Sprint planning item                                 |
| Architecture audit     | Quarterly     | After major feature milestones                       |
| New contributor review | On demand     | Before onboarding a new team member                  |

---

## Phase 1 — PR-Level Checks (Every Pull Request)

The PR author is responsible. Reviewers must not approve if these are unmet.

- [ ] Any new endpoint added to `api/` has a corresponding entry in `docs/api-reference.md`
- [ ] Any new environment variable added to `config.py` is documented in `docs/configuration.md`
- [ ] Any change to startup behavior, Docker setup, or prerequisites is reflected in `docs/setup.md`
- [ ] Any new agent, workflow module, or AI provider change is reflected in `docs/agent-pipeline.md`
- [ ] Any schema or data model change is reflected in relevant API or architecture docs
- [ ] PR description references which doc files were updated (or explicitly states "no doc changes needed")

**Add to PR template checklist:**

```markdown
- [ ] Documentation updated (or confirmed not needed)
```

---

## Phase 2 — Weekly Staleness Sweep (~30 minutes, dev rotation)

A quick pass to catch docs that have drifted from the codebase.

### API Reference (`docs/api-reference.md`)

- [ ] Scan `backend/src/api/` — confirm every route file has matching API table entries
- [ ] Confirm all path prefixes, methods, and path params are still accurate
- [ ] Flag any endpoints removed or deprecated but still listed

### Configuration (`docs/configuration.md`)

- [ ] Compare documented env vars against `backend/src/config.py` — add any missing, remove any deleted
- [ ] Confirm default values and required/optional status are still correct

### Setup Guide (`docs/setup.md`)

- [ ] Confirm Docker Compose and manual setup steps still match project state
- [ ] Confirm prerequisite versions (Python, Node, Docker) still match `pyproject.toml` and `package.json`
- [ ] Confirm Codespaces badge and quick start flow still work end-to-end

---

## Phase 3 — Monthly Full Documentation Review (~2–3 hours)

### Coverage Audit

Walk every file in `docs/` and verify it is:

- [ ] **Accurate** — reflects current code behavior, not aspirational or outdated state
- [ ] **Complete** — no major features or workflows are undocumented
- [ ] **Consistent** — terminology, naming, and formatting are uniform across files

| File | Ownership | Key Things to Verify |
|------|-----------|----------------------|
| `docs/setup.md` | Infra/DX | Prerequisites, Codespaces flow, env var list, Docker Compose steps |
| `docs/configuration.md` | Backend | All env vars, types, defaults, and validation rules |
| `docs/api-reference.md` | Backend | All routes, methods, params, auth requirements, and response shapes |
| `docs/architecture.md` | Full stack | Service diagram, data flow, WebSocket flow, AI provider list |
| `docs/agent-pipeline.md` | Backend | Workflow orchestrator modules, Copilot polling, task/issue generation |
| `docs/custom-agents-best-practices.md` | Backend | Agent authoring patterns, extension points |
| `docs/signal-integration.md` | Backend | Signal sidecar setup, webhook flow, delivery logic |
| `docs/testing.md` | Full stack | Test commands, coverage targets, Playwright setup, CI behavior |
| `docs/troubleshooting.md` | Full stack | Common errors and resolutions — remove fixed issues, add new ones |
| `docs/project-structure.md` | Full stack | Directory layout — update after any structural refactor |
| `frontend/docs/` | Frontend | Component patterns, findings log, any frontend-specific guides |

### Cross-Reference Check

- [ ] All internal `docs/` links are valid and resolve to existing headings
- [ ] Code snippets in docs compile or run without error against current codebase
- [ ] README.md top-level links to correct doc files
- [ ] Any external links (GitHub docs, library docs) still resolve to relevant pages

### Readability & Usability

- [ ] Each page has a clear purpose statement at the top
- [ ] Step-by-step guides use numbered lists and include expected outcomes
- [ ] Configuration tables include: variable name, type, required/optional, default, description
- [ ] API tables include: method, path, auth required, brief description
- [ ] Troubleshooting entries follow the format: **Symptom → Cause → Fix**

---

## Phase 4 — Quarterly Architecture Audit (~half day)

Run after major feature milestones (new integrations, significant refactors, new agent types).

### Architecture Document (`docs/architecture.md`)

- [ ] Service diagram reflects current Docker Compose topology
- [ ] All backend service modules are represented (Workflow Orchestrator, Copilot Polling, GitHub Projects Service, Signal Bridge, AI providers)
- [ ] Data flow arrows are accurate — especially WebSocket paths and GitHub API interactions
- [ ] AI provider list is current (Copilot SDK, OpenAI, Anthropic, etc.)

### Decision Records

- [ ] Any significant architectural decision made this quarter is captured as an ADR (Architecture Decision Record) in `docs/decisions/` (create if it doesn't exist)
- [ ] ADR format: **Context → Decision → Consequences**

### Developer Experience Audit

- [ ] Have a team member (or new contributor) follow `docs/setup.md` from scratch — note any friction
- [ ] Time the full local setup end-to-end; document in setup guide
- [ ] Review `docs/troubleshooting.md` — add any issues encountered during the audit

### Docs Gaps Analysis

- [ ] List all features shipped in the last quarter — confirm each has adequate documentation
- [ ] Identify docs that exist but no one references — consider consolidating or removing
- [ ] Check if a public-facing changelog or `CHANGELOG.md` should be started or updated

---

## Phase 5 — Standards & Tooling

### Formatting Standards

- All docs use ATX-style headings (`#`, `##`, `###`)
- Code blocks specify language for syntax highlighting (` ```python `, ` ```bash `, ` ```typescript `)
- Tables used for: env vars, API endpoints, config options
- Numbered lists for sequential steps; bullet lists for non-ordered items
- Filenames referenced in docs use inline code formatting (e.g., `config.py`)

### Linting & Automation

- [ ] Add `markdownlint` to CI — enforce consistent formatting on all `docs/` and `*.md` files
- [ ] Add `markdown-link-check` to CI — catch broken internal and external links automatically
- [ ] Consider `vale` for prose style linting (consistent tone, no passive voice, etc.)

### Doc Ownership

Each doc file should have a designated owner listed in a `docs/OWNERS.md` file:

```text
docs/setup.md                   → infra/DX lead
docs/api-reference.md           → backend lead
docs/architecture.md            → tech lead
docs/agent-pipeline.md          → backend lead
docs/configuration.md           → backend lead
docs/signal-integration.md      → backend lead
docs/testing.md                 → QA / full stack lead
docs/troubleshooting.md         → rotating (whoever fixes the bug documents the fix)
docs/custom-agents-best-practices.md → backend lead
```

---

## Roles & Responsibilities

| Role | Responsibility |
|------|---------------|
| PR author | Update docs for any code change that affects behavior, config, or APIs |
| PR reviewer | Reject PRs that change behavior without updating relevant docs |
| Dev (rotation) | Weekly staleness sweep |
| Tech lead | Monthly review sign-off; quarterly architecture audit |
| All contributors | Follow formatting standards; flag stale docs when encountered |

---

## Definition of "Good Documentation"

A doc is considered current and complete when:

1. **Accurate** — Every step, command, variable, and path matches the current codebase
2. **Minimal** — No redundant content; each fact appears in exactly one place
3. **Actionable** — Readers can accomplish the documented task without needing to read source code
4. **Discoverable** — The correct doc is easy to find from the README or table of contents
5. **Maintained** — Last-reviewed date is within the current quarter
