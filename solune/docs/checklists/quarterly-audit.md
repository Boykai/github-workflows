# Quarterly Architecture Audit

**Estimated time**: ~half day
**Frequency**: Quarterly (after major feature milestones)
**Purpose**: Deep structural documentation review covering architecture, decision records, developer experience, and documentation gaps.

## Architecture Document Review

Review `docs/architecture.md` against the current system:

- [ ] Service diagram reflects current Docker Compose topology
- [ ] All backend service modules are represented (Workflow Orchestrator, Copilot Polling, GitHub Projects Service, Signal Bridge, AI providers)
- [ ] Data flow arrows are accurate — especially WebSocket paths and GitHub API interactions
- [ ] AI provider list is current (Copilot SDK, OpenAI, Anthropic, etc.)

## Architecture Decision Records

Review `docs/decisions/` directory and its `README.md` index:

- [ ] Any significant architectural decision made this quarter has a corresponding ADR in `docs/decisions/`
- [ ] Each ADR follows the **Context → Decision → Consequences** format
- [ ] ADR index in `docs/decisions/README.md` is up to date with all current records

## Developer Experience Audit

- [ ] Have a team member (or new contributor) follow `docs/setup.md` from scratch — note any friction
- [ ] Time the full local setup end-to-end; document in setup guide
- [ ] Review `docs/troubleshooting.md` — add any issues encountered during the audit

## Documentation Gaps Analysis

- [ ] List all features shipped in the last quarter — confirm each has adequate documentation
- [ ] Identify docs that exist but no one references — consider consolidating or removing
- [ ] Check if a public-facing changelog or `CHANGELOG.md` should be started or updated

## Completion

- **Date**: YYYY-MM-DD
- **Reviewer**: @username
- **Issues found**: [count] (link to issues if filed)

## See Also

- [Weekly Sweep](weekly-sweep.md) — lightweight weekly validation pass
- [Monthly Review](monthly-review.md) — monthly quality gate
