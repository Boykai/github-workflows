# ADR-001: Use `githubkit` as the GitHub API client

**Status**: Accepted
**Date**: 2025-Q1

## Context

The backend needs to call both the GitHub REST API and the GitHub GraphQL API (Projects V2 requires GraphQL). Options evaluated:

- **PyGitHub** — REST only, no GraphQL support, limited async.
- **gidgethub** — Lightweight async REST, no built-in GraphQL or type safety.
- **httpx + raw requests** — Maximum flexibility but requires manually maintaining request/response models for every endpoint.
- **githubkit** — Typed async client with first-class support for both REST and GraphQL, auto-generated from the GitHub OpenAPI spec, supports OAuth token injection per-request.

## Decision

Use `githubkit` (`>=0.14.0`) as the sole GitHub API client.

A `GitHubClientFactory` in `services/github_projects/__init__.py` pools `githubkit` instances keyed by OAuth token, avoiding repeated client construction on hot paths.

## Consequences

- **+** Type-safe API calls reduce runtime errors from typos in field names.
- **+** Per-request token injection means impersonated calls work correctly without shared state.
- **+** GraphQL support covers Projects V2 mutations not available in the REST API.
- **−** `githubkit` is less mainstream than PyGitHub; API changes in the library require version pinning.
- **−** The auto-generated models are verbose; callers must navigate nested response types.
