# Monthly Full Documentation Review

**Estimated time**: 2–3 hours
**Frequency**: Monthly (sprint planning item)
**Purpose**: Comprehensive quality gate ensuring accuracy, completeness, and consistency across all documentation.

## Coverage Audit

Walk every file in `docs/` and verify it is accurate, complete, and consistent.

| File | Ownership | Key Things to Verify |
|------|-----------|----------------------|
| `docs/setup.md` | Infra/DX lead | Prerequisites, Codespaces flow, env var list, Docker Compose steps |
| `docs/configuration.md` | Backend lead | All env vars, types, defaults, and validation rules |
| `docs/api-reference.md` | Backend lead | All routes, methods, params, auth requirements, and response shapes |
| `docs/architecture.md` | Tech lead | Service diagram, data flow, WebSocket flow, AI provider list |
| `docs/agent-pipeline.md` | Backend lead | Workflow orchestrator modules, Copilot polling, task/issue generation |
| `docs/custom-agents-best-practices.md` | Backend lead | Agent authoring patterns, extension points |
| `docs/signal-integration.md` | Backend lead | Signal sidecar setup, webhook flow, delivery logic |
| `docs/testing.md` | QA / full-stack lead | Test commands, coverage targets, Playwright setup, CI behavior |
| `docs/troubleshooting.md` | Rotating | Common errors and resolutions — remove fixed issues, add new ones |
| `docs/project-structure.md` | Full-stack lead | Directory layout — update after any structural refactor |
| `frontend/docs/` | Frontend lead | Component patterns, findings log, any frontend-specific guides |
| `docs/checklists/` | Rotating dev / Tech lead | Checklist item accuracy — update if codebase paths change |

For each file, verify:

- [ ] **Accurate** — reflects current code behavior, not aspirational or outdated state
- [ ] **Complete** — no major features or workflows are undocumented
- [ ] **Consistent** — terminology, naming, and formatting are uniform across files

## Cross-Reference Check

- [ ] All internal `docs/` links are valid and resolve to existing headings
- [ ] Code snippets in docs compile or run without error against current codebase
- [ ] `README.md` top-level links point to correct doc files
- [ ] Any external links (GitHub docs, library docs) still resolve to relevant pages

## Readability Assessment

- [ ] Each page has a clear purpose statement at the top
- [ ] Step-by-step guides use numbered lists and include expected outcomes
- [ ] Configuration tables include: variable name, type, required/optional, default, description
- [ ] API tables include: method, path, auth required, brief description
- [ ] Troubleshooting entries follow the format: **Symptom → Cause → Fix**

## Completion

- **Date**: YYYY-MM-DD
- **Reviewer**: @username
- **Issues found**: [count] (link to issues if filed)

## See Also

- [Weekly Sweep](weekly-sweep.md) — lightweight weekly validation pass
- [Quarterly Audit](quarterly-audit.md) — comprehensive structural review
