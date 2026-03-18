# Documentation Owners

> **Internal document** — This file is for project maintainers. It defines documentation ownership and review cadences. If you're looking for user-facing documentation, see the [main README](../README.md).

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
| `docs/.last-refresh` | Rotating dev | Bi-weekly refresh baseline (date, SHA, updated docs) |
| `docs/.change-manifest.md` | Rotating dev | Change manifest compiled during each refresh cycle |

## Review Cadence

| Cadence | Scope | Owner |
|---------|-------|-------|
| Every PR | Files changed by the PR | PR author |
| Weekly (~30 min) | `api-reference.md`, `configuration.md`, `setup.md` | Rotating dev |
| Bi-weekly (~3–4 hours) | Full documentation refresh cycle (detect changes, prioritize, rewrite) | Rotating dev |
| Monthly (~2–3 hours) | All `docs/` files | Tech lead sign-off |
| Quarterly (~half day) | `architecture.md`, `docs/decisions/` | Tech lead |
