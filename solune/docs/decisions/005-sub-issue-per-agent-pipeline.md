# ADR-005: Sub-issue-per-agent pipeline with durable tracking table

**Status**: Accepted
**Date**: 2025-Q1

## Context

Agent Pipelines assign multiple custom GitHub agents to work on an issue in series or parallel. Without visibility into which agent is active or what state the pipeline is in, restarts and debugging are opaque. Options evaluated:

- **In-memory state only** — Simple, but lost on restart. Requires polling to reconstruct.
- **Database state table** — Durable, but adds a migration and coupling between the backend and GitHub.
- **Durable tracking table embedded in the issue body** — Visible on GitHub without the app, survives restarts, reconstructible by scanning issues.

## Decision

Embed a markdown tracking table directly in the GitHub Issue body (under `## 🤖 Agent Pipeline`). The table records each agent, its status column, and its state (Pending / Active / Done). Sub-issues are created upfront for every agent; each is titled `[agent-name] Parent Title`.

On restart, the system reconstructs pipeline state from:

- The tracking table in the issue body.
- `Done!` markers in issue comments.
- Sub-issue title prefixes and their open/closed state.

## Consequences

- **+** Pipeline state is visible directly on GitHub without the app running.
- **+** State survives server restarts with no external database dependency beyond what GitHub stores.
- **+** Sub-issues give per-agent visibility in the GitHub Projects board.
- **−** Issue body mutations happen frequently; GitHub rate limits and edit conflicts must be managed.
- **−** Reconstruction logic is non-trivial and must handle partial/corrupt states gracefully.
