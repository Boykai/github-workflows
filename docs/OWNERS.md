# Documentation Owners

Each doc file has a designated owner responsible for keeping it accurate. Owners must review relevant PRs and perform the weekly staleness sweep on their files.

| File | Owner | Key Things to Verify |
|------|-------|----------------------|
| `docs/setup.md` | Infra / DX lead | Prerequisites, Codespaces flow, env var list, Docker Compose steps |
| `docs/configuration.md` | Backend lead | All env vars, types, defaults, and validation rules |
| `docs/api-reference.md` | Backend lead | All routes, methods, params, auth requirements, and response shapes |
| `docs/architecture.md` | Tech lead | Service diagram, data flow, WebSocket flow, AI provider list |
| `docs/agent-pipeline.md` | Backend lead | Workflow orchestrator modules, Copilot polling, task/issue generation |
| `docs/custom-agents-best-practices.md` | Backend lead | Agent authoring patterns, extension points |
| `docs/signal-integration.md` | Backend lead | Signal sidecar setup, webhook flow, delivery logic |
| `docs/testing.md` | QA / full-stack lead | Test commands, coverage targets, Playwright setup, CI behavior |
| `docs/troubleshooting.md` | Rotating (whoever fixed the bug documents the fix) | Common errors and resolutions — remove fixed issues, add new ones |
| `docs/project-structure.md` | Full-stack lead | Directory layout — update after any structural refactor |
| `docs/checklists/weekly-sweep.md` | Rotating dev | Weekly staleness sweep checklist — API, config, setup accuracy |
| `docs/checklists/monthly-review.md` | Tech lead | Monthly full documentation review checklist |
| `docs/checklists/quarterly-audit.md` | Tech lead | Quarterly architecture audit checklist |
| `docs/decisions/` | Tech lead | ADRs — one per significant architectural decision |
| `frontend/docs/findings-log.md` | Frontend lead | Component findings and decisions log |

## Review Cadence

| Cadence | Scope | Owner |
|---------|-------|-------|
| Every PR | Files changed by the PR | PR author |
| Weekly (~30 min) | `api-reference.md`, `configuration.md`, `setup.md` | Rotating dev |
| Monthly (~2–3 hours) | All `docs/` files | Tech lead sign-off |
| Quarterly (~half day) | `architecture.md`, `docs/decisions/` | Tech lead |

## Definition of Good Documentation

A doc is considered current and complete when it meets all five criteria:

1. **Accurate** — Every step, command, variable, and path matches the current codebase
2. **Minimal** — No redundant content; each fact appears in exactly one place
3. **Actionable** — Readers can accomplish the documented task without needing to read source code
4. **Discoverable** — The correct doc is easy to find from the README or table of contents
5. **Maintained** — Last-reviewed date is within the current quarter

This definition serves as the acceptance bar for all review phases (weekly, monthly, quarterly). Reviewers should verify each criterion during their review cadence.
