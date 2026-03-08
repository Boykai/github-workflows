---
name: Security Review
about: Recurring chore for a custom GitHub agent to analyze and harden the codebase
title: '[CHORE] Security Review'
labels: chore
assignees: ''
---

## Security Review

Use a custom GitHub coding agent to perform a deep security, privacy, secrets-handling, dependency, and operational best-practices review across the live #codebase, then apply the highest-value safe fixes directly in code.

This repository is actively evolving. Do not assume the stack, frameworks, languages, package managers, or dependency set are static. Start by discovering the current implementation and threat surface from the repository as it exists today, then adapt the review plan to what is actually present.

## Agent Objective

Produce a practical hardening pass that:

1. Inventories the current codebase, runtime surfaces, dependencies, and trust boundaries.
2. Identifies real security, privacy, secrets-management, authn/authz, supply-chain, and unsafe-default risks.
3. Applies low-risk and medium-risk fixes directly where the correct remediation is clear.
4. Adds or updates tests, guards, validation, and documentation where needed to prevent regressions.
5. Leaves a concise audit summary in the issue or PR describing what was found, what was changed, what was intentionally deferred, and what still needs manual follow-up.

## Required Review Scope

The agent must inspect the current repository rather than relying on assumptions. Review at least these areas when they exist:

- Authentication, authorization, session handling, and access control boundaries.
- Secret handling, token storage, encryption, cookies, headers, CORS, CSRF, SSRF, XSS, injection, unsafe deserialization, file handling, and webhook verification.
- API endpoints, websocket/event channels, background jobs, schedulers, automations, chat flows, tool integrations, and any user-controlled prompts or model inputs.
- Database access, migration safety, data retention, auditability, logging hygiene, and privacy-sensitive persistence.
- Frontend storage, browser-visible secrets, unsafe URL/query-param usage, and sensitive data exposure in UI or logs.
- Docker, container runtime, compose files, reverse proxy or web-server config, filesystem permissions, network exposure, and insecure defaults.
- CI/CD, GitHub Actions, issue/PR automation, workflow permissions, dependency update rules, and supply-chain attack surface.
- Third-party libraries, SDKs, package manifests, and lockfiles for known risky patterns, stale packages, or dangerous configuration.

## Execution Rules

The agent should follow this workflow:

1. Discover the current stack first.
   Identify the active languages, frameworks, package managers, entrypoints, deployment surfaces, and security-sensitive integrations before proposing fixes.
2. Prioritize by impact and exploitability.
   Fix clear critical, high, and medium risks first. Avoid wasting time on cosmetic lint-only work unless it directly supports a security fix.
3. Apply changes when the correct remediation is clear.
   Do not stop at reporting problems if the issue can be safely fixed in this repository.
4. Prefer root-cause fixes.
   Favor safer defaults, centralized validation, shared auth checks, stricter config validation, and regression tests over one-off patches.
5. Stay conservative with breaking changes.
   If a hardening change would require operator migration, credential rotation, infrastructure coordination, or user re-authorization, implement it only when it can be done safely and document the operational impact clearly.
6. Validate the work.
   Run the relevant tests, type checks, lint checks, builds, or targeted verification commands for the languages and tooling discovered in the repo.

## Expected Deliverables

The agent should leave behind:

- Code changes for the remediations that are safe to apply now.
- Regression coverage for security-sensitive behavior where practical.
- Documentation or config updates when operational behavior changes.
- A summary grouped by severity: Fixed in this pass; Still open and why; Needs human/operator follow-up.

## Minimum Reporting Format

In the final summary, include:

1. Stack discovered
2. Threat areas reviewed
3. Findings fixed
4. Findings deferred
5. Validation performed
6. Follow-up actions required

## Preferred Fix Patterns

When applicable, prefer changes like:

- Enforcing secure-by-default configuration at startup.
- Centralizing authorization and ownership checks.
- Removing secrets from URLs, client storage, logs, and browser-visible surfaces.
- Using constant-time comparison for secrets and signatures.
- Tightening cookie and header settings.
- Reducing default permissions and network exposure.
- Narrowing overly broad tokens, scopes, workflow permissions, or package capabilities.
- Sanitizing externally sourced error messages and user-controlled content.
- Adding bounded retries, rate limits, and abuse protections on sensitive or expensive paths.
- Running containers and services with least privilege.

## Out of Scope

Do not spend this pass on broad architectural rewrites unless they are required to remove a concrete security risk. Prefer targeted hardening that can be merged safely in an active codebase.

## Success Criteria

This issue is complete when:

- The custom GitHub agent has reviewed the live #codebase rather than a stale assumed stack.
- Meaningful security/privacy hardening changes have been applied, not just reported.
- Relevant validation has been run for the discovered stack.
- Remaining gaps are documented with clear rationale and next actions.
