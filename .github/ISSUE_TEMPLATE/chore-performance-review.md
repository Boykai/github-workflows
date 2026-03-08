---
name: Performance Review
about: Recurring chore for a custom GitHub agent to analyze and optimize the codebase
title: '[CHORE] Performance Review'
labels: chore
assignees: ''
---

## Performance Review

Use a custom GitHub coding agent to perform a deep performance, responsiveness, refresh-path, and maintainability review across the live #codebase, then apply the highest-value safe optimizations directly in code.

This repository is actively evolving. Do not assume the stack, frameworks, languages, package managers, or dependency set are static. Start by discovering what exists today, then adapt the optimization plan to the actual implementation.

## Agent Objective

Produce a practical optimization pass that:

1. Discovers the current stack, hot paths, refresh flows, and runtime surfaces.
2. Measures or approximates current bottlenecks before changing behavior.
3. Improves backend, frontend, data-fetching, refresh, rendering, and automation performance where the gains are real and safe.
4. Looks for opportunities to simplify and DRY the codebase when duplication, branching, or fragmented logic is causing unnecessary work, stale behavior, or refresh churn.
5. Adds or updates validation, regression coverage, instrumentation, or documentation where needed to preserve the gains.
6. Leaves a concise summary describing what was measured, what was changed, what improved, what was deferred, and what should be reviewed by a human.

## Required Review Scope

The agent must inspect the current repository rather than relying on assumptions. Review at least these areas when they exist:

- Request-heavy backend paths, polling loops, websocket update flows, scheduled/background work, and API endpoints with repeated or redundant upstream calls.
- Frontend data-fetching, cache invalidation, refresh policies, state synchronization, render loops, repeated derived computations, and expensive list/card rendering.
- Duplicate logic across services, hooks, pages, utilities, or API layers that increases maintenance cost or causes inconsistent refresh behavior.
- Opportunities to consolidate shared code paths, centralize refresh contracts, reuse caching, or eliminate redundant transforms.
- Database queries, cache usage, serialization cost, payload size, and expensive recomputation in read-heavy paths.
- Container/runtime configuration, build steps, startup behavior, and asset delivery choices that affect developer or runtime performance.
- CI or automation paths that are unnecessarily slow, duplicated, or doing avoidable work.

## Execution Rules

The agent should follow this workflow:

1. Discover the current stack first.
   Identify the active languages, frameworks, package managers, entrypoints, refresh flows, polling mechanisms, and high-traffic paths before proposing changes.
2. Measure before optimizing.
   Capture baselines where practical: API activity, request counts, refresh frequency, rerender hot spots, payload size, build time, or other relevant signals for the discovered stack.
3. Prioritize by impact, safety, and repeat cost.
   Focus first on optimizations that reduce redundant work, repeated refreshes, unnecessary queries, excess rerenders, duplicated logic, and maintainability drag.
4. Prefer simplification over cleverness.
   If the same performance gain can be achieved by removing duplication, unifying a code path, centralizing logic, or simplifying refresh orchestration, prefer that over adding complexity.
5. Apply changes when the benefit is clear.
   Do not stop at reporting bottlenecks if the fix is safe and belongs in this repository.
6. Stay conservative with risky rewrites.
   Avoid broad architectural churn unless measurement shows the existing design cannot meet reasonable performance targets without it.
7. Validate the work.
   Run the relevant tests, type checks, lint checks, builds, or targeted profiling/verification commands for the languages and tooling discovered in the repo.

## Expected Deliverables

The agent should leave behind:

- Code changes for safe performance improvements that belong in this pass.
- Simplification or DRY refactors where they directly improve performance, refresh correctness, or maintainability.
- Regression coverage or focused checks for the optimized paths where practical.
- Documentation or comments only when needed to explain a non-obvious performance contract.
- A summary grouped by outcome: improved now; deferred and why; human follow-up needed.

## Minimum Reporting Format

In the final summary, include:

1. Stack discovered
2. Performance surfaces reviewed
3. Baselines or observations captured
4. Improvements implemented
5. DRY or simplification changes made
6. Validation performed
7. Deferred opportunities and follow-up actions

## Preferred Optimization Patterns

When applicable, prefer changes like:

- Removing duplicate or competing refresh logic.
- Narrowing query invalidation and refetch scope.
- Reusing shared derived data instead of recomputing it in multiple places.
- Consolidating duplicated backend/service logic that causes repeated I/O or divergent behavior.
- Reducing unnecessary network requests, polling, serialization, and payload size.
- Stabilizing hot props/state only where it measurably reduces rerenders.
- Using caching or memoization only when it simplifies or clearly outperforms the current path.
- Moving from scattered one-off logic to a single coherent refresh/update contract.
- Simplifying large conditional flows that obscure performance behavior.

## Out of Scope

Do not spend this pass on speculative micro-optimizations or broad rewrites unless measurement shows they are necessary. Prefer practical, explainable improvements that can be merged safely in an active codebase.

## Success Criteria

This issue is complete when:

- The custom GitHub agent has reviewed the live #codebase rather than a stale assumed stack.
- Meaningful performance and refresh-path improvements have been applied, not just reported.
- The agent has considered simplification and DRY opportunities as part of the optimization pass.
- Relevant validation has been run for the discovered stack.
- Remaining bottlenecks are documented with rationale and next actions.
