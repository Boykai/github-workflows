<!--
Sync Impact Report: v1.0.0 Initial Constitution Ratification

Version Change: Initial → 1.0.0
Modified Principles: All principles newly defined
Added Sections: Complete constitution created
Removed Sections: N/A

Template Updates Status:
✅ plan-template.md - Aligned (Constitution Check section references this document)
✅ spec-template.md - Aligned (User story prioritization and independence requirements)
✅ tasks-template.md - Aligned (Phase-based execution and test optionality)
✅ Agent commands - Aligned (All reference constitution for governance)

Follow-up TODOs: None - All placeholders resolved
-->

# Speckit Constitution

## Core Principles

### I. Specification-First Development

All feature work begins with explicit specification. Requirements must be captured in structured markdown documents (`spec.md`) using the canonical template. Specifications MUST include:

- Prioritized user stories (P1, P2, P3...) with independent testing criteria
- Given-When-Then acceptance scenarios for each story
- Clear scope boundaries and out-of-scope declarations

**Rationale**: Explicit specifications prevent scope creep, enable parallel development of independent user stories, and provide a contract between stakeholders and implementers. The prioritization ensures MVP-viable increments.

### II. Template-Driven Workflow

All workflow artifacts (specifications, plans, tasks, checklists) MUST follow the canonical templates in `.specify/templates/`. Templates are prescriptive and non-negotiable. Custom sections may be added only when documented in the specific artifact with clear justification.

**Rationale**: Templates ensure consistency across features, enable tooling automation, and reduce cognitive load. Standardization allows AI agents and developers to work predictably across different features.

### III. Agent-Orchestrated Execution

Complex workflows are decomposed into single-responsibility AI agents (specify, plan, tasks, implement, etc.). Each agent:

- Has ONE clear purpose defined in its agent file
- Operates on well-defined inputs (previous phase artifacts)
- Produces specific outputs (markdown documents, code)
- Hands off to subsequent agents via explicit transitions

**Rationale**: Single-responsibility agents are easier to debug, test, and improve. Clear handoffs prevent agent confusion and ensure workflow traceability.

### IV. Test Optionality with Clarity

Tests (unit, integration, contract) are OPTIONAL by default. They MUST be included only when:

- Explicitly requested in the feature specification
- Mandated by the constitution check in `plan.md`
- Required for TDD approach chosen by the user

When tests are included, they follow strict phase ordering: test tasks precede implementation tasks (Red-Green-Refactor).

**Rationale**: Not all workflows require tests (e.g., documentation updates, configuration changes). Making tests opt-in reduces overhead while maintaining rigor when needed. Explicit TDD support ensures proper test-first discipline when chosen.

### V. Simplicity and DRY

Code and specifications MUST favor simplicity over cleverness. Follow YAGNI (You Aren't Gonna Need It) principles. Avoid premature abstraction. Duplication is preferable to wrong abstraction. When complexity is unavoidable, it MUST be justified in the `Complexity Tracking` section of `plan.md`.

**Rationale**: Simple systems are easier to understand, maintain, and extend. Complexity compounds over time; explicit justification creates accountability and enables future refactoring decisions.

## Workflow Standards

### Branch and Directory Naming

All features follow the pattern `###-short-name` where:

- `###` is a zero-padded sequential number (001, 002, etc.)
- `short-name` is a 2-4 word kebab-case identifier derived from the feature description
- The same identifier is used for git branches and `specs/` directories

Branch creation MUST check for existing branches/specs with the same `short-name` and increment the number if conflicts exist.

### Phase-Based Execution

Feature implementation follows strict phases:

1. **Specify** → Create `spec.md` with user stories and acceptance criteria
2. **Plan** → Generate `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
3. **Tasks** → Generate `tasks.md` decomposing user stories into executable tasks
4. **Implement** → Execute tasks in dependency order, optionally with tests-first
5. **Analyze** → Validate consistency across artifacts

Each phase MUST complete before the next begins. Phase outputs are immutable once handed off (amendments require explicit clarification cycles).

### Independent User Stories

User stories in `spec.md` MUST be independently implementable and testable. Each story should:

- Deliver standalone value (viable for MVP if implemented alone)
- Have no hidden dependencies on other stories (shared infrastructure goes in foundational phase)
- Include explicit "Independent Test" criteria showing how to verify the story in isolation

Tasks in `tasks.md` are organized by user story to enable parallel implementation.

## Artifact Consistency

### Constitution Supremacy

This constitution supersedes all other guidance. When conflicts arise between constitution and templates, the constitution wins. When conflicts arise between templates and agent instructions, templates win.

### Amendment Process

Constitution amendments require:

1. **Version bump** following semantic versioning (MAJOR.MINOR.PATCH)
2. **Sync Impact Report** documenting all affected templates and commands
3. **Propagation** of changes to all dependent artifacts before merge
4. **Last Amended Date** update to current date (ISO 8601 format)

MAJOR version: Backward-incompatible principle changes or removals  
MINOR version: New principles, sections, or material expansions  
PATCH version: Clarifications, wording improvements, typo fixes

### Compliance Review

All feature `plan.md` files MUST include a "Constitution Check" section evaluating compliance with each principle. Violations MUST be justified in the "Complexity Tracking" section or corrected before proceeding to implementation.

## Governance

The constitution is maintained in `.specify/memory/constitution.md`. All agents reference this file for governance rules. The `/speckit.constitution` command is the authoritative tool for amendments.

All artifact generation (specs, plans, tasks) MUST verify constitution compliance before output. Unjustified complexity or template violations cause workflow halts.

**Version**: 1.0.0 | **Ratified**: 2026-01-30 | **Last Amended**: 2026-01-30
