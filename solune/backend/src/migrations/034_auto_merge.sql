-- Add auto_merge column to project_settings for per-project auto merge toggle.
-- When auto_merge = 1, pipelines automatically squash-merge parent PRs on completion.
-- TODO(bug-bash): This file shares migration prefix 034 with 034_phase8_pipeline_states_ext.sql.
-- Both are applied (in filename order) and the code logs a warning, but consider renumbering
-- one to avoid ambiguity. Renaming requires coordination with existing deployments.
ALTER TABLE project_settings ADD COLUMN auto_merge INTEGER NOT NULL DEFAULT 0;
