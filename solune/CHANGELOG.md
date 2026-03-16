# Changelog

All notable changes to this project will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions.

---

## [Unreleased]

### Added

- **Monorepo restructure**: Repository reorganized with `solune/` (platform core) and `apps/` (generated applications) at the root
- **Full product rebrand**: All references renamed from "Agent Projects" / "ghchat" to "Solune" across ~70+ files
- **App management backend**: New `apps` table, Pydantic models (`App`, `AppCreate`, `AppUpdate`, `AppStatus`), app service with full CRUD lifecycle (create, list, get, update, start, stop, delete), directory scaffolding, and name validation
- **App management API**: RESTful endpoints at `/api/v1/apps` for all app operations including lifecycle controls (start/stop) and status checks
- **Apps page**: New frontend page at `/apps` with card grid view, create dialog, detail view with live iframe preview and start/stop controls
- **Slash command context switching**: `active_app_name` session attribute for `/<app-name>` command support and working directory resolution
- **Admin guard system**: `guard-config.yml` with `@admin` / `@adminlock` protection levels, guard service with most-specific-match-wins evaluation, and middleware for file operation interception
- Pipeline Analytics dashboard replacing the Recent Activity section on the Agents Pipelines page — displays agent frequency, model distribution, execution mode breakdown, and complexity spotlight
- Expand button visible in collapsed sidebar so users can re-open it
- Rich gold primary color for the "+ Add Agent" button on the Agents page

### Changed

- Agent pills in the Agents page "Column assignments" sidebar now show only the `model_name` on hover instead of full config dump
- Removed project selection button from the Projects page (project selection handled via sidebar)
- Cleaned up shared Copilot custom instructions by removing stale stack history, correcting repo paths and migration references, and simplifying repeated agent routing guidance
- Documentation refresh: updated agent-pipeline.md (pipeline analytics, group-aware execution), architecture.md (CSP/rate-limit middleware, logging_utils), configuration.md (ADMIN_GITHUB_USER_ID), setup.md (Python 3.13+), troubleshooting.md (pipeline recovery details) to match current codebase state

---

## 2026-03-11

### Added

- Dead code and technical debt cleanup specification (039-dead-code-cleanup)
- Group-aware pipeline execution and tracking table (039-group-pipeline-execution)
- Automated Mermaid architecture diagram generation via CI and commit hooks
- Bug Basher specification (037-bug-basher)
- Theme contrast audit specification (037-theme-contrast-audit)
- Chat attachment to GitHub parent issue specification (037-chat-attachment-github-issue)
- Security, privacy & vulnerability audit specification (037-security-review)
- Performance review specification (037-performance-review)
- Pipeline builder UX reinvention specification (037-pipeline-builder-ux)

### Fixed

- Chore issue run count now excludes chore-type issues via GitHub Issue Types
- Documentation drift fixes found during documentation sweep

### Changed

- Removed "Current Pipeline" section from Pipelines page
- Made Parent Issue Intake module collapsible (collapsed by default)
- Require `ADMIN_GITHUB_USER_ID` in production mode; removed tools from agent definitions

### Security

- Enforced `tools: ['*']` on all agent definitions via MCP server sync

---

## 2026-03-04

### Added

- GitHub label-based agent pipeline state tracking (034-label-pipeline-state)
- Projects page audit specification for visual cohesion and UX quality (034-projects-page-audit)
- `.cgcignore` file for CodeGraph context filtering
- Performance review specification (first pass)

---

## 2026-02-25

### Added

- Code quality overhaul — 9-phase refactor (spec 033)
- Replace GitHub toolset with MCP configuration generator on Tools page
- Parallel agent layout in pipelines specification (033-parallel-agent-layout)
- Projects page audit specification (033-projects-page-audit)
- Pipelines page UI consistency and quality audit specification
- Feature specification for issue upload pipeline config (032)
- Context7 and Code Graph Context as built-in MCP presets

### Fixed

- Throttled popover scroll handlers and scoped ChatPopup resize listeners
- Pipeline recovery reliability — 6 bug fixes for agent error detection, stale tracking, and UI

---

## 2026-02-18

### Added

- Built-in preset configs for pipelines, chores, and simplified model resolution
- Issue template for Code Quality Check

### Fixed

- Minor UI improvements across Pipeline, Board, Chores, and Agents pages
- Documentation drift — missing endpoints, stale versions, env var gaps

---
