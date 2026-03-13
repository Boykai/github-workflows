/* eslint-disable */
/* This file is auto-generated from backend/src/constants.py */
/* Run: npm run generate:types */

export const StatusNames = {"BACKLOG": "Backlog", "READY": "Ready", "IN_PROGRESS": "In Progress", "IN_REVIEW": "In Review", "DONE": "Done"} as const;
export const DEFAULT_STATUS_COLUMNS = ["Backlog", "In Progress", "Done"] as const;
export const CACHE_PREFIX_PROJECTS = "projects:user" as const;
export const CACHE_PREFIX_PROJECT_ITEMS = "project:items" as const;
export const CACHE_PREFIX_SUB_ISSUES = "sub_issues" as const;
export const CACHE_PREFIX_REPO_AGENTS = "repo:agents" as const;
export const SESSION_COOKIE_NAME = "session_id" as const;
export const GITHUB_ISSUE_BODY_MAX_LENGTH = 65536 as const;
export const NOTIFICATION_EVENT_TYPES = ["task_status_change", "agent_completion", "new_recommendation", "chat_mention"] as const;
export const AGENT_OUTPUT_FILES = {"speckit.specify": ["spec.md"], "speckit.plan": ["plan.md"], "speckit.tasks": ["tasks.md"]} as const;
export const DEFAULT_AGENT_MAPPINGS = {"Backlog": ["speckit.specify"], "Ready": ["speckit.plan", "speckit.tasks"], "In Progress": ["speckit.implement"], "In Review": ["copilot-review"]} as const;
export const AGENT_DISPLAY_NAMES = {"speckit.specify": "Spec Kit - Specify", "speckit.plan": "Spec Kit - Plan", "speckit.tasks": "Spec Kit - Tasks", "speckit.implement": "Spec Kit - Implement", "copilot-review": "Copilot Review", "copilot": "GitHub Copilot", "human": "Human"} as const;
export const LABELS = ["feature", "bug", "enhancement", "refactor", "documentation", "testing", "infrastructure", "frontend", "backend", "database", "api", "ai-generated", "sub-issue", "good first issue", "help wanted", "security", "performance", "accessibility", "ux", "active", "stalled"] as const;
export const PIPELINE_LABEL_PREFIX = "pipeline:" as const;
export const AGENT_LABEL_PREFIX = "agent:" as const;
export const ACTIVE_LABEL = "active" as const;
export const STALLED_LABEL = "stalled" as const;
export const PIPELINE_LABEL_COLOR = "0052cc" as const;
export const AGENT_LABEL_COLOR = "7057ff" as const;
export const ACTIVE_LABEL_COLOR = "0e8a16" as const;
export const STALLED_LABEL_COLOR = "d73a4a" as const;
