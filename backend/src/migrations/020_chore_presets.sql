-- 020_chore_presets.sql
-- Extends chores table with preset identification for built-in chore templates.

-- Add preset columns to chores
ALTER TABLE chores ADD COLUMN is_preset INTEGER NOT NULL DEFAULT 0;
ALTER TABLE chores ADD COLUMN preset_id TEXT NOT NULL DEFAULT '';

-- Unique constraint for preset seeding (one preset per project)
CREATE UNIQUE INDEX IF NOT EXISTS idx_chores_preset
    ON chores(preset_id, project_id)
    WHERE preset_id != '';
