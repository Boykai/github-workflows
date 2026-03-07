-- 015_pipeline_mcp_presets.sql
-- Extends pipeline_configs with preset identification and project pipeline assignment.

-- Add preset columns to pipeline_configs
ALTER TABLE pipeline_configs ADD COLUMN is_preset INTEGER NOT NULL DEFAULT 0;
ALTER TABLE pipeline_configs ADD COLUMN preset_id TEXT NOT NULL DEFAULT '';

-- Unique constraint for preset seeding (one preset per project)
CREATE UNIQUE INDEX IF NOT EXISTS idx_pipeline_configs_preset
    ON pipeline_configs(preset_id, project_id)
    WHERE preset_id != '';

-- Add assigned pipeline column to project_settings
ALTER TABLE project_settings ADD COLUMN assigned_pipeline_id TEXT NOT NULL DEFAULT '';
