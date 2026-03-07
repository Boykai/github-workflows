# Contract: PR Template with Documentation Checklist

**Feature**: 027-doc-sweep | **Date**: 2026-03-07
**Requirement**: FR-001, FR-002

## File Location

```text
.github/pull_request_template.md
```

## Template Structure

The PR template MUST include the following sections in order:

### 1. Description Section

A free-text area for the PR author to describe the change.

```markdown
## Description

<!-- Describe the change and its motivation -->
```

### 2. Type of Change Section

Checkboxes to categorize the PR.

```markdown
## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] CI/CD or infrastructure change
```

### 3. Documentation Checklist Section

The documentation checklist required by FR-001. All items MUST be present.

```markdown
## Documentation

- [ ] Any new endpoint added to `api/` has a corresponding entry in `docs/api-reference.md`
- [ ] Any new environment variable added to `config.py` is documented in `docs/configuration.md`
- [ ] Any change to startup behavior, Docker setup, or prerequisites is reflected in `docs/setup.md`
- [ ] Any new agent, workflow module, or AI provider change is reflected in `docs/agent-pipeline.md`
- [ ] Any schema or data model change is reflected in relevant API or architecture docs
- [ ] Documentation updated (or confirmed not needed — explain below)

**Doc files updated**: <!-- List files or write "None — no doc changes needed" with rationale -->
```

### 4. Testing Section

A section for test verification.

```markdown
## Testing

- [ ] Existing tests pass
- [ ] New tests added (if applicable)
```

## Validation Rules

- The documentation checklist section MUST contain exactly 6 checkbox items matching FR-001 requirements
- The "Doc files updated" field MUST be visible to reviewers for FR-002 compliance
- The template MUST be a single file (not a multi-template directory) per R1 research decision
- All checkbox items MUST use GitHub-flavored markdown checkbox syntax (`- [ ]`)

## Acceptance Criteria Mapping

| Scenario | Checklist Item |
|----------|---------------|
| New endpoint added | `docs/api-reference.md` item |
| New env var added | `docs/configuration.md` item |
| Startup/Docker/prereq change | `docs/setup.md` item |
| Agent/workflow/AI change | `docs/agent-pipeline.md` item |
| Schema/data model change | Relevant API/architecture docs item |
| No doc changes needed | "Documentation updated" item + rationale |
