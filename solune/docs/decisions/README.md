# Architecture Decision Records

Architecture Decision Records (ADRs) capture the key design decisions made during Solune's development — what was decided, why, and what alternatives were considered. We publish these to provide transparency into the project's technical direction and to help contributors understand the reasoning behind the codebase.

## Format

```markdown
## Context
What situation or problem drove this decision?

## Decision
What was decided, and what alternatives were considered?

## Consequences
What are the trade-offs, benefits, and known limitations?
```

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](001-githubkit-sdk.md) | Use `githubkit` as the GitHub API client | Accepted |
| [ADR-002](002-sqlite-wal-auto-migrations.md) | SQLite with WAL mode and numbered auto-migrations | Accepted |
| [ADR-003](003-copilot-default-ai-provider.md) | GitHub Copilot as default AI provider via OAuth token | Accepted |
| [ADR-004](004-pluggable-completion-provider.md) | Pluggable `CompletionProvider` abstraction for LLM backends | Accepted |
| [ADR-005](005-sub-issue-per-agent-pipeline.md) | Sub-issue-per-agent pipeline with durable tracking table | Accepted |
| [ADR-006](006-signal-sidecar.md) | Signal messaging via `signal-cli-rest-api` sidecar | Accepted |
