-- Migration 002: Add workflow_config column to project_settings
-- Stores the full serialized WorkflowConfiguration JSON so that
-- agent_mappings (and other workflow fields) survive server restarts.

ALTER TABLE project_settings ADD COLUMN workflow_config TEXT;
