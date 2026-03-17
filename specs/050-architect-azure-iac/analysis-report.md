# Specification Analysis Report: Architect Agent for Azure IaC

**Feature**: `050-architect-azure-iac` | **Date**: 2026-03-17 | **Analyzer**: speckit.analyze

**Artifacts Analyzed**:
- `spec.md` (170 lines) — 5 user stories, 21 functional requirements, 8 success criteria
- `plan.md` (107 lines) — Project structure, constitution check, complexity tracking
- `tasks.md` (217 lines) — 32 tasks across 8 phases
- `research.md` (346 lines) — 8 research topics resolved
- `data-model.md` (143 lines) — Entity extensions and relationships
- `contracts/agent-config.md` (174 lines) — 5 file-level contracts
- `contracts/backend-api.md` (157 lines) — 2 REST API contracts
- `quickstart.md` (242 lines) — Step-by-step implementation guide
- `constitution.md` (131 lines) — 5 core principles

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Coverage Gap | CRITICAL | spec.md:FR-017, plan.md:L49-101, tasks.md | FR-017 requires the Architect agent to be **automatically invoked** after every new app is scaffolded, but no task implements this auto-invocation mechanism. The plan's Project Structure lists no file for this wiring. The issue description (Phase 3, item 8) mentions it, but it never made it into plan.md or tasks.md. | Add a task to implement the agent auto-invocation in `create_app_with_new_repo()`. Define the mechanism (post-creation API call, background task, or GitHub Actions workflow trigger). Update plan.md project structure to include the target file. |
| C2 | Underspecification | CRITICAL | spec.md:FR-017, plan.md | The **mechanism** for auto-invoking the Architect agent is undefined across all artifacts. Is it: (a) a direct function call in `app_service.py`, (b) a background task/queue, (c) a GitHub Actions workflow dispatch, or (d) a webhook? The plan says "agent invocation is async and does not block app creation response" (L18) but no artifact specifies the async execution model. | Add a research topic or plan section defining the auto-invocation architecture. Add corresponding task(s) to tasks.md. |
| I1 | Inconsistency | HIGH | contracts/backend-api.md:L46, spec.md:FR-015, quickstart.md:Step 8 | The backend API contract specifies `azure_client_id` as "**UUID format**" but the implementation (quickstart.md Step 8) uses only `min_length=1` validation with no UUID enforcement. The spec (FR-015) says "optional input fields" with no format constraint. The data-model.md also says only "Minimum length: 1 character." | Align: either enforce UUID validation in the model (add `pattern` constraint) or remove "UUID format" from the backend API contract. Recommendation: Remove UUID constraint — Azure Client IDs are UUIDs but the model shouldn't enforce this since formats may vary. |
| I2 | Inconsistency | HIGH | plan.md:L18, tasks.md | Plan states "agent invocation is async and does not block app creation response" but tasks.md has no task implementing async execution (no background task, no queue, no fire-and-forget pattern). All credential storage tasks (T017-T018) are synchronous `await` calls within the create flow. | If agent invocation is truly async, add a task for implementing the async dispatch mechanism (e.g., `asyncio.create_task()` or a job queue). If credential storage is sync but agent invocation is async, clarify this distinction in the plan. |
| A1 | Ambiguity | HIGH | spec.md:FR-009, tasks.md:T011 | FR-009 requires the agent to "validate its output: Bicep compiles via `az bicep build`." However, the Architect is an AI agent generating code — it may not have Azure CLI installed in the execution environment. The validation phase (T011) describes this as an agent instruction, not a testable implementation task. How is this validated in CI/CD? | Clarify: (1) Is validation a best-effort agent self-check, or (2) must a CI/CD step run `az bicep build`? If (2), add a task for creating a GitHub Actions workflow that validates generated Bicep. If (1), note this in the spec as "agent-side validation when tooling is available." |
| A2 | Ambiguity | HIGH | spec.md:FR-011 | "Follow Azure Well-Architected Framework principles" lacks measurable criteria. The WAF has 5 pillars (Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency). Which pillars are mandatory? What constitutes "following" them? The agent instructions say "use Azure MCP WAF tool" but there's no testable acceptance criterion. | Add measurable criteria: e.g., "Generated Bicep MUST use managed identity (Security pillar), enable diagnostic settings (Operational Excellence), and tag all resources (Cost Optimization)." Or downgrade FR-011 to a SHOULD-level guideline in operating rules. |
| U1 | Underspecification | MEDIUM | spec.md:SC-002 | SC-002 states "at least 95% of app types supported by the Solune platform" but the spec never defines the set of app types. How many app types exist? What are they (Python/FastAPI, Node.js/Express, .NET, static sites)? Without this enumeration, the 95% threshold is unmeasurable. | Either enumerate the supported app types in the spec (e.g., "Python/FastAPI, Node.js/Express, static sites") or change SC-002 to "Generated Bicep modules compile successfully for the default app scaffold template." |
| U2 | Underspecification | MEDIUM | spec.md:SC-003 | SC-003 states "under 10 minutes" for app creation to first deployment, but this includes Azure provisioning time (outside the agent's control). The agent generates code; it doesn't provision. This success criterion conflates agent output quality with cloud provider performance. | Reframe SC-003 to measure agent output quality: e.g., "Generated `azd` scaffold requires zero manual configuration edits before running `azd up`." |
| U3 | Underspecification | MEDIUM | spec.md:SC-007, tasks.md | SC-007 requires "Generated CI/CD workflows pass security scanning" but no task implements or validates security scanning. What scanner? What rules? Is this the existing repo's security scanning or a new check? | Add a task for validating generated CI/CD workflows against a specific security standard (e.g., GitHub Advanced Security, or a manual review checklist). |
| U4 | Underspecification | MEDIUM | spec.md:edge cases, tasks.md | Edge case "agent detects existing infrastructure during Discovery phase and adapts — it does not overwrite existing files but may suggest enhancements or flag conflicts" has no corresponding task or acceptance test. How is this behavior validated? | Add a task to include this behavior in the agent's Phase 0 instructions (T005) with explicit guidance on conflict detection and non-overwrite behavior. |
| D1 | Duplication | MEDIUM | spec.md:FR-005, FR-010 | FR-005 mandates "Bicep infrastructure modules" and FR-010 mandates "Bicep over ARM JSON — always." FR-010 is a restatement of the Bicep-only constraint already implied by FR-005's exclusive use of Bicep. | Merge FR-010 into FR-005 as a note: "FR-005: ... using Bicep exclusively (never ARM JSON)." Or keep both for emphasis — low impact. |
| D2 | Duplication | LOW | spec.md:FR-012, FR-020 | FR-012 ("never hardcode secrets — Key Vault, managed identity, GitHub Secrets") and FR-020 ("use `azd` environment variables for parameterization") both address the same concern: no hardcoded values. FR-020 is a specific technique under FR-012's umbrella. | Consider consolidating into a single requirement covering both secret management and parameterization. Low priority — current separation adds clarity. |
| T1 | Terminology | MEDIUM | research.md:Topic 7, plan.md:L98 | Research Topic 7 references "lines 450-515 of `AppsPage.tsx`" — this is a fragile reference to specific line numbers that will break if the file is modified before implementation. The plan also references this pattern. | Replace line number references with stable anchors: e.g., "the 'New Repository Settings' section that renders when `repoType === 'new-repo'`." |
| T2 | Terminology | LOW | plan.md:L86-89, data-model.md:L103 | Plan refers to `RepositoryMixin` as the target for `set_repository_secret()`, while `_rest()` lives on the parent `GitHubProjectsService` in `service.py`. This is technically correct (mixin inherits access) but may confuse implementers unfamiliar with the inheritance chain. | Add a brief note in plan.md or quickstart.md: "`set_repository_secret()` is added to `RepositoryMixin` which accesses `self._rest()` from the parent `GitHubProjectsService`." |

---

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (agent-file-yaml) | ✅ | T004 | Agent file creation with YAML frontmatter |
| FR-002 (prompt-shortcut) | ✅ | T024 | Prompt file creation |
| FR-003 (discovery-phase) | ✅ | T005 | Agent Phase 0 instructions |
| FR-004 (mermaid-diagrams) | ✅ | T006, T021 | Agent Phase 1 + convention validation |
| FR-005 (bicep-modules) | ✅ | T007 | Agent Phase 2 instructions |
| FR-006 (azure-yaml) | ✅ | T008 | Agent Phase 3 instructions |
| FR-007 (deploy-button) | ✅ | T009 | Agent Phase 4 instructions |
| FR-008 (cicd-secrets-ref) | ✅ | T010 | Agent Phase 5 instructions |
| FR-009 (validation) | ✅ | T011 | Agent Phase 6 instructions (see A1 for ambiguity) |
| FR-010 (bicep-over-arm) | ✅ | T012 | Operating rules section |
| FR-011 (waf-principles) | ✅ | T012 | Operating rules section (see A2 for ambiguity) |
| FR-012 (no-hardcoded-secrets) | ✅ | T012 | Operating rules section |
| FR-013 (vscode-mcp) | ✅ | T001 | MCP config for local development |
| FR-014 (agents-mcp) | ✅ | T002 | MCP config for remote agents |
| FR-015 (frontend-fields) | ✅ | T020 | Frontend Azure credential input fields |
| FR-016 (backend-secrets-api) | ✅ | T017, T018 | Backend encryption + wiring |
| FR-017 (auto-invoke-agent) | ❌ | — | **CRITICAL: No task implements auto-invocation** |
| FR-018 (copilot-instructions-table) | ✅ | T025 | Utility agents table update |
| FR-019 (mcp-config-note) | ✅ | T026 | MCP Configuration section update |
| FR-020 (azd-env-vars) | ✅ | T012 | Operating rules section |
| FR-021 (naming-conventions) | ✅ | T012 | Operating rules section |

---

## Constitution Alignment

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | 5 prioritized user stories with Given-When-Then scenarios, clear scope boundaries |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates; plan includes Constitution Check |
| III. Agent-Orchestrated | ✅ PASS | Specify → Plan → Tasks → Implement chain is clean |
| IV. Test Optionality | ✅ PASS | Tests included for backend (secrets API, paired validation) and frontend (field rendering) per spec |
| V. Simplicity / DRY | ✅ PASS | 1 new dependency (pynacl) justified; extends existing models with 2 fields; no new abstractions |
| Branch/Dir Naming | ✅ PASS | `050-architect-azure-iac` follows `###-short-name` pattern |
| Phase-Based Execution | ✅ PASS | Specify → Plan → Tasks → Implement → Analyze sequence respected |
| Independent User Stories | ✅ PASS | All 5 stories have independent tests; MCP config can ship without agent, agent without credentials |

No constitution violations detected.

---

## Unmapped Tasks

All tasks map to at least one requirement. No orphan tasks found.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 21 |
| Total Tasks | 32 |
| Coverage (requirements with ≥1 task) | 95.2% (20/21) |
| Uncovered Requirements | 1 (FR-017) |
| Ambiguity Count | 2 (A1, A2) |
| Duplication Count | 2 (D1, D2) |
| Underspecification Count | 4 (U1–U4) |
| Inconsistency Count | 2 (I1, I2) |
| Terminology Issues | 2 (T1, T2) |
| Critical Issues | 2 (C1, C2) |
| High Issues | 4 (I1, I2, A1, A2) |
| Medium Issues | 5 (U1–U4, D1) |
| Low Issues | 2 (D2, T2) |
| Constitution Violations | 0 |
| Total Findings | 13 |

---

## Next Actions

### 🔴 CRITICAL — Resolve Before `/speckit.implement`

1. **C1 + C2: Add FR-017 coverage** — Define the auto-invocation mechanism for the Architect agent after app scaffolding. Options:
   - (a) Add `asyncio.create_task()` call in `create_app_with_new_repo()` that dispatches to a new `invoke_architect_agent()` function
   - (b) Add a GitHub Actions workflow that triggers on repository creation events
   - (c) Document that auto-invocation is deferred to a follow-up iteration (requires spec amendment)

   **Recommended**: Run `/speckit.specify` with refinement to define the auto-invocation mechanism, then `/speckit.tasks` to add the missing task(s).

2. **I1: Resolve UUID constraint mismatch** — Edit `contracts/backend-api.md` to remove "UUID format" from `azure_client_id` constraint, or add UUID validation to the model implementation.

### 🟡 HIGH — Address Before Implementation

3. **A1: Clarify Bicep validation** — Decide if `az bicep build` validation is agent-side (best effort) or CI/CD-enforced. If CI/CD, add a task for creating a validation workflow.

4. **A2: Define WAF measurable criteria** — Either add specific WAF pillar requirements to the agent instructions or downgrade FR-011 to SHOULD-level.

5. **I2: Clarify sync vs async credential storage** — The plan says "async" but implementation uses `await`. Clarify the execution model.

### 🟢 MEDIUM/LOW — Can Proceed, Improve Incrementally

6. **U1–U4**: Add app type enumeration, reframe SC-003, add security scanning task, validate existing-infra edge case.
7. **T1**: Replace fragile line number references with stable anchors.
8. **D1, D2**: Consider consolidating overlapping requirements (low priority).

---

## Remediation Summary

Would you like me to suggest concrete remediation edits for the top 5 issues (C1, C2, I1, I2, A1)? These would be specific text changes to spec.md, plan.md, contracts/backend-api.md, and tasks.md. *(Edits will NOT be applied automatically — this is a read-only analysis.)*
