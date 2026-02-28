# Data Model: Deep Security Review and Application Hardening

**Feature**: `012-deep-security-review`
**Date**: 2026-02-28
**Source**: [spec.md](spec.md), [research.md](research.md)

## Entities

### Vulnerability Finding

Represents a discovered security issue documented in the security findings report. This is a **documentation-only entity** — it is not stored in a database table but is captured in the security findings report artifact.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `finding_id` | String | Unique, format `SEC-###` | Sequential identifier for the finding |
| `severity` | Enum | `critical`, `high`, `medium`, `low`, `informational` | CVSS-based severity rating |
| `category` | String | NOT NULL | OWASP Top 10 or GitHub Actions security category |
| `affected_component` | String | NOT NULL | File path or system component affected |
| `description` | String | NOT NULL | Clear description of the vulnerability |
| `remediation_status` | Enum | `fixed`, `accepted_risk`, `deferred` | Current status of the finding |
| `fix_applied` | String | NULL | Description of the fix applied (if `fixed`) |
| `justification` | String | NULL | Reason for accepting risk (if `accepted_risk`) |
| `verification` | String | NULL | How the fix was verified |

**Lifecycle**: Created during security audit → status set based on remediation outcome → persisted in security findings report markdown file.

---

### Workflow Configuration

Represents the security posture of a GitHub Actions workflow file. Used as an audit checklist — not a database entity.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `file_path` | String | NOT NULL | Path to the workflow YAML file |
| `actions` | List | NOT NULL | All third-party action references in the workflow |
| `action_pinned` | Boolean | Per action | Whether the action is pinned to a full commit SHA |
| `permissions_explicit` | Boolean | Per job/workflow | Whether explicit permissions are declared |
| `permissions_least_privilege` | Boolean | Per job/workflow | Whether permissions follow least-privilege |
| `triggers` | List | NOT NULL | Workflow trigger events |
| `has_insecure_triggers` | Boolean | NOT NULL | Whether `pull_request_target` with code checkout is used |
| `secrets_used` | List | NOT NULL | Secrets referenced in the workflow |

---

### Dependency Advisory

Represents a known CVE or security advisory affecting a project dependency.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `advisory_id` | String | NOT NULL | CVE or advisory identifier (e.g., `CVE-2024-XXXXX`, `GHSA-XXXXX`) |
| `severity` | Enum | `critical`, `high`, `medium`, `low` | Advisory severity rating |
| `ecosystem` | Enum | `pip`, `npm` | Package ecosystem |
| `package_name` | String | NOT NULL | Affected package name |
| `affected_version` | String | NOT NULL | Version range affected |
| `fixed_version` | String | NULL | Version containing the fix (if available) |
| `remediation` | Enum | `updated`, `accepted_risk`, `not_applicable` | Action taken |

---

## Relationships

```text
Security Findings Report (document)
  └── contains N ──→ Vulnerability Findings
  └── contains N ──→ Dependency Advisories

Workflow Configuration (ci.yml)
  └── contains N ──→ Action References (to be SHA-pinned)
  └── contains N ──→ Job Permission Blocks (to be added)
```

## State Transitions

### Vulnerability Finding Lifecycle

```text
  ┌────────────┐
  │ Discovered │  Security audit identifies the issue
  └─────┬──────┘
        │
   ┌────┴─────┐
   │          │
   ▼          ▼
┌───────┐  ┌──────────────┐
│ Fixed │  │ Accepted Risk │  Cannot fix or low priority
└───────┘  └──────────────┘
```

### No Database Schema Changes

This feature does not introduce new database tables or modify existing schemas. All entities are documentation artifacts captured in the security findings report. The existing database schema (user_sessions, global_settings, signal_connections, signal_messages, signal_conflict_banners) is unaffected.

## Validation Rules

- **finding_id**: Must match pattern `SEC-\d{3}` (e.g., `SEC-001`).
- **severity**: Must be one of `critical`, `high`, `medium`, `low`, `informational`.
- **remediation_status**: Must be one of `fixed`, `accepted_risk`, `deferred`.
- **action references**: Must be a full 40-character hexadecimal SHA when pinned.
- **permissions blocks**: Must explicitly list only the scopes required by the job.
