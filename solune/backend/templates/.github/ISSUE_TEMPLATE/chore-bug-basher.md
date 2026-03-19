---
name: Bug Basher
about: Recurring chore for a custom GitHub agent to inspect and fix bugs across the codebase
title: '[CHORE] Bug Basher'
labels: chore
assignees: ''
---

## Bug Basher

Use a custom GitHub coding agent to perform a deep correctness, reliability, bug-risk, and coding-error review across the live #codebase, then apply the highest-value safe fixes directly in code.

This repository is actively evolving. Do not assume the stack, frameworks, languages, package managers, or dependency set are static. Start by discovering what exists today, then adapt the bug-bash plan to the actual implementation.

## Agent Objective

Produce a practical bug-fix pass that:

1. Discovers the current stack, runtime surfaces, critical workflows, and error-prone code paths.
2. Identifies real bugs, coding errors, reliability risks, edge-case failures, broken assumptions, and likely regressions.
3. Applies safe fixes directly where the correct remediation is clear.
4. Looks for opportunities to simplify and DRY the codebase when duplication, fragmented logic, or inconsistent implementations are contributing to bugs or unnecessary performance cost.
5. Adds or updates tests, validation, guards, and documentation where needed to prevent the bugs from returning.
6. Leaves a concise summary describing what was found, what was fixed, what was deferred, and what requires human judgment.

## Required Review Scope

The agent must inspect the current repository rather than relying on assumptions. Review at least these areas when they exist:

- Runtime errors, unhandled exceptions, invalid state transitions, race conditions, null/None or undefined access, incorrect async behavior, resource leaks, and broken control flow.
- Logic bugs in APIs, UI state, workflows, orchestration, polling, scheduling, caching, data transforms, and persistence.
- Mismatches between frontend and backend contracts, stale assumptions, shape drift, schema drift, and missing validation.
- Test gaps, fragile tests, false-positive assertions, mock leakage into production paths, and missing regression coverage for known-risk behavior.
- Duplicate logic across services, hooks, pages, or utilities that can drift apart and create inconsistent behavior.
- Opportunities to simplify or centralize code paths where that reduces bug surface area and produces performance gains through less redundant work.
- Dead code, unreachable branches, silent failures, misleading fallbacks, and swallowed errors that hide defects.

## Execution Rules

The agent should follow this workflow:

1. Discover the current stack first.
   Identify the active languages, frameworks, package managers, entrypoints, runtime flows, and validation tools before proposing changes.
2. Prioritize by correctness risk and user impact.
   Fix bugs that can cause data loss, broken workflows, stale state, crashes, silent corruption, or recurring operator pain before lower-value cleanup.
3. Apply changes when the correct remediation is clear.
   Do not stop at reporting problems if the issue can be safely fixed in this repository.
4. Prefer root-cause fixes.
   Favor shared validation, centralized logic, simpler control flow, and removal of duplicate behavior over scattered point fixes.
5. Use DRY and simplification deliberately.
   If duplication or over-complex branching is creating bugs or wasting work, simplify it when the result is easier to reason about and safer to maintain.
6. Stay conservative with ambiguous changes.
   If a possible fix would alter intended product behavior, create migration risk, or depends on unclear business rules, document it clearly and defer rather than guessing.
7. Validate the work.
   Run the relevant tests, type checks, lint checks, builds, or targeted verification commands for the languages and tooling discovered in the repo.

## Expected Deliverables

The agent should leave behind:

- Code changes for the bugs and coding errors that are safe to fix now.
- Regression coverage or focused validation for corrected behavior where practical.
- Simplification or DRY refactors where they directly reduce bug surface area, inconsistent logic, or unnecessary performance cost.
- Documentation or comments only when needed to clarify a non-obvious behavior contract.
- A summary grouped by outcome: fixed in this pass; deferred and why; human follow-up needed.

## Minimum Reporting Format

In the final summary, include:

1. Stack discovered
2. Critical flows reviewed
3. Bugs and coding errors fixed
4. DRY or simplification changes made
5. Validation performed
6. Deferred findings and why
7. Follow-up actions required

## Preferred Fix Patterns

When applicable, prefer changes like:

- Centralizing duplicated logic that has drifted across files or layers.
- Replacing silent fallbacks with explicit validation or error handling.
- Tightening type or schema checks at boundaries.
- Removing dead branches and unreachable code that obscure real behavior.
- Narrowing refresh or recomputation paths when they cause stale state or repeated work.
- Consolidating shared transforms or decision logic instead of maintaining multiple versions.
- Adding regression tests around previously broken edge cases.
- Simplifying conditionals and state transitions so failures are easier to reason about.

## Out of Scope

Do not spend this pass on broad speculative rewrites unless they are required to fix a concrete bug pattern. Prefer targeted, explainable fixes that can be merged safely in an active codebase.

## Success Criteria

This issue is complete when:

- The custom GitHub agent has reviewed the live #codebase rather than a stale assumed stack.
- Meaningful bug fixes or coding-error corrections have been applied, not just reported.
- The agent has considered simplification and DRY opportunities where they reduce bugs or unnecessary performance cost.
- Relevant validation has been run for the discovered stack.
- Remaining ambiguous defects are documented with rationale and next actions.
