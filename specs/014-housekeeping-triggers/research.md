# Research: Housekeeping Issue Templates with Configurable Triggers

**Feature**: 014-housekeeping-triggers | **Date**: 2026-02-28

## Research Task 1: Persisting Housekeeping Task Definitions in SQLite

### Decision
Add three new tables to the existing SQLite database (`settings.db`): `housekeeping_templates` (reusable issue templates), `housekeeping_tasks` (task definitions with trigger config), and `housekeeping_trigger_history` (execution log). Use a new migration file `006_housekeeping.sql` following the existing migration pattern.

### Rationale
The project already uses SQLite via aiosqlite with WAL mode and a sequential migration system (`backend/src/services/database.py` with files in `backend/src/migrations/`). Extending this with new tables is the simplest path — no new dependencies, no new storage technology. The schema aligns with the spec's technical notes: id, name, description, templateRef, subIssueConfig, triggerType, triggerValue, lastTriggeredAt, lastTriggeredIssueCount, enabled.

### Alternatives Considered
- JSON/YAML config file in the repository — rejected because it would require file I/O, merge conflicts in multi-user scenarios, and lacks transactional integrity for atomic counter updates
- New SQLite database file — rejected because the project already has a single `settings.db` with migration infrastructure; adding a second database adds unnecessary complexity

---

## Research Task 2: Time-Based Trigger Integration with GitHub Actions

### Decision
Create a new GitHub Actions workflow (`housekeeping-cron.yml`) that runs on a `schedule` trigger with a configurable cron expression. The workflow calls the backend API to evaluate and execute due time-based housekeeping tasks. Each task's individual cron expression is evaluated server-side against `lastTriggeredAt`.

### Rationale
The project already uses GitHub Actions for CI (`ci.yml`) and webhook-driven workflows (`branch-issue-link.yml`). Adding a scheduled workflow is the canonical GitHub approach for recurring tasks. A single workflow with a frequent schedule (e.g., every 15 minutes) can evaluate all time-based tasks server-side, rather than creating one workflow per task (which would be unmanageable). The backend evaluates each task's cron expression against its `lastTriggeredAt` timestamp to determine if it's due.

### Alternatives Considered
- Internal cron scheduler running inside the backend process — rejected because the backend runs as a web server and doesn't have a built-in job scheduler; adding one (e.g., APScheduler) would introduce a new dependency and complicate deployment
- GitHub Apps scheduled events — rejected because the project doesn't use GitHub Apps for scheduling; GitHub Actions `schedule` is simpler and already proven in this repo
- One GitHub Actions workflow per task — rejected because it would require dynamically creating/deleting workflow files, which is fragile and doesn't scale

---

## Research Task 3: Count-Based Trigger Integration with Issue Creation Events

### Decision
Hook into the existing webhook pipeline (`backend/src/api/webhooks.py`) to detect new parent issue creation events. When a new parent issue is created, the system increments the internal counter and evaluates all count-based housekeeping tasks against their thresholds. The counter uses the `WorkflowTransition` audit log (or a dedicated counter in the housekeeping_tasks table) to track issues created since the last trigger.

### Rationale
The project already receives GitHub webhook events for pull requests (`webhooks.py`). Extending this to listen for `issues` events (action: `opened`) follows the same pattern. The count is tracked per-task in the `housekeeping_tasks` table as `last_triggered_issue_count` — when a new parent issue is created, the system compares the current total issue count against each task's baseline to determine if the threshold is met.

### Alternatives Considered
- Polling the GitHub API for issue counts on a timer — rejected because it's wasteful, introduces latency, and the webhook approach is already established
- Using GitHub Actions `issues` event trigger — possible but adds workflow complexity; the webhook approach is more direct since the backend already processes webhooks
- Separate counter table — rejected for simplicity; the baseline count in the task record is sufficient

---

## Research Task 4: Idempotency and Cooldown Guards

### Decision
Implement a minimum cooldown window (configurable, default 5 minutes) per housekeeping task. Before executing a trigger, acquire a row-level lock (SQLite's serialized writes) and check if `lastTriggeredAt` is within the cooldown window. If so, skip execution. For concurrent "Run Now" requests, use an atomic compare-and-swap pattern on the `lastTriggeredAt` field.

### Rationale
The spec explicitly requires idempotency guards (FR-010). SQLite's serialized write model (WAL mode with `busy_timeout=5000`) provides natural serialization for concurrent access within a single process. For the edge case of two simultaneous "Run Now" requests, the first writer updates `lastTriggeredAt` and the second sees the updated value and aborts. This is simpler and more reliable than external locking mechanisms.

### Alternatives Considered
- Redis-based distributed lock — rejected because the project doesn't use Redis and the single-process SQLite model doesn't require distributed locking
- Application-level mutex — rejected because SQLite transactions already provide the necessary serialization
- No cooldown (rely on user discipline) — rejected because the spec explicitly requires automatic idempotency guards

---

## Research Task 5: Sub-Issue Generation via Agent Pipeline

### Decision
Reuse the existing `WorkflowOrchestrator` and `DEFAULT_AGENT_MAPPINGS` from `backend/src/constants.py` to generate sub issues. When a housekeeping task fires, the system creates the parent issue via the GitHub Issues API, then calls the orchestrator to create sub issues based on either the task's custom `subIssueConfig` or the default Spec Kit agent pipeline configuration.

### Rationale
The workflow orchestrator already handles issue creation and sub-issue generation through the agent pipeline. The `DEFAULT_AGENT_MAPPINGS` in `constants.py` defines the standard Spec Kit pipeline (Specify → Plan/Tasks → Implement → Copilot Review). Reusing this avoids duplicating issue creation logic and ensures consistency with the existing workflow system.

### Alternatives Considered
- Direct GitHub API calls for sub-issue creation (bypassing the orchestrator) — rejected because it would duplicate the sub-issue linking and pipeline state tracking logic
- Creating a separate orchestrator for housekeeping — rejected per DRY principle; the existing orchestrator handles the same pattern

---

## Research Task 6: Built-in Seed Templates Design

### Decision
Ship three built-in seed templates as Python data structures in a `seed.py` module within the housekeeping service package. Templates are inserted into the `housekeeping_templates` table during database migration or first-run initialization, marked with a `category = 'built-in'` flag to distinguish them from user-created templates.

### Rationale
The three required templates (Security and Privacy Review, Test Coverage Refresh, Bug Bash) are static content that should be available immediately on fresh installations. Storing them as seed data in the migration ensures they exist without requiring user action. The `built-in` category flag prevents accidental deletion and allows the UI to show them distinctly.

### Alternatives Considered
- Storing seed templates as markdown files in the repository — rejected because it would require file I/O to load templates and complicates the storage model
- Loading seed templates from a remote API — rejected because it adds an external dependency and network requirement
- Hardcoding templates in the service layer — close to the chosen approach, but the migration-based seeding is cleaner and ensures templates exist even if the service isn't invoked

---

## Research Task 7: Frontend Component Architecture for Housekeeping UI

### Decision
Create a new `housekeeping/` component directory under `frontend/src/components/` with five components: `HousekeepingTaskList` (main view), `HousekeepingTaskForm` (create/edit dialog), `TemplateLibrary` (template management), `TriggerHistoryLog` (per-task history), and `RunNowButton` (manual trigger action). Use a `useHousekeeping` custom hook for API calls via TanStack Query, following the existing hook patterns (e.g., `useWorkflow`, `useSettings`).

### Rationale
The frontend follows a consistent pattern: feature-specific component directories (`board/`, `chat/`, `settings/`), custom hooks for API interaction, and Shadcn/ui for UI primitives. The housekeeping UI should follow the same structure. TanStack Query provides caching, refetching, and optimistic updates that match the existing data-fetching patterns.

### Alternatives Considered
- Adding housekeeping UI inline to existing settings page — rejected because housekeeping is a distinct feature with its own navigation, not a settings sub-page
- Using a separate SPA or micro-frontend — rejected for simplicity; the existing single-SPA architecture is sufficient

---

## Research Task 8: GitHub Actions Workflow for Scheduled Triggers

### Decision
Create a `housekeeping-cron.yml` workflow that runs on `schedule: cron: '*/15 * * * *'` (every 15 minutes). The workflow uses `gh api` or `curl` to call the backend's housekeeping evaluation endpoint, which checks all enabled time-based tasks and executes those that are due. The workflow uses the existing `GH_TOKEN` pattern for authentication.

### Rationale
A 15-minute polling interval balances between responsiveness (spec requires "within 5 minutes of schedule") and GitHub Actions resource consumption. The backend performs the actual cron expression evaluation so the workflow itself is simple and stateless. This follows the existing pattern where GitHub Actions workflows call backend APIs (similar to webhook handling).

### Alternatives Considered
- Per-task dynamic cron expressions in GitHub Actions — GitHub Actions doesn't support dynamic `schedule` values; the schedule must be static in the YAML
- Longer polling interval (hourly) — rejected because it would violate the "within 5 minutes" performance requirement for daily/weekly schedules
- Shorter polling interval (every minute) — rejected because it wastes GitHub Actions minutes; 15-minute granularity is sufficient for most housekeeping schedules
