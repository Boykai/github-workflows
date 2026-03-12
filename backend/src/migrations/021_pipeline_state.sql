-- Migration: 021_pipeline_state.sql
-- Description: Create tables for persistent pipeline state, branch tracking,
-- sub-issue mapping, and agent trigger guard storage.
-- Previously these were stored in module-level BoundedDict instances and lost on restart.

CREATE TABLE IF NOT EXISTS pipeline_states (
    issue_number INTEGER PRIMARY KEY,
    project_id TEXT NOT NULL,
    status TEXT NOT NULL,
    agent_name TEXT,
    agent_instance_id TEXT,
    pr_number INTEGER,
    pr_url TEXT,
    sub_issues TEXT,
    metadata TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS issue_main_branches (
    issue_number INTEGER PRIMARY KEY,
    branch TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    head_sha TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS issue_sub_issue_map (
    issue_number INTEGER NOT NULL,
    agent_name TEXT NOT NULL,
    sub_issue_number INTEGER NOT NULL,
    sub_issue_node_id TEXT NOT NULL,
    sub_issue_url TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    PRIMARY KEY (issue_number, agent_name)
);

CREATE TABLE IF NOT EXISTS agent_trigger_inflight (
    trigger_key TEXT PRIMARY KEY,
    started_at TEXT NOT NULL
);
