-- 016_chores_enhancements.sql
-- Extends chores table with execution tracking, AI enhance preference, and pipeline assignment.

-- Add execution count for "Most Run" ranking
ALTER TABLE chores ADD COLUMN execution_count INTEGER NOT NULL DEFAULT 0;

-- Add AI enhance toggle (1 = ON/default, 0 = OFF)
ALTER TABLE chores ADD COLUMN ai_enhance_enabled INTEGER NOT NULL DEFAULT 1;

-- Add agent pipeline reference ("" = Auto, UUID = specific pipeline)
ALTER TABLE chores ADD COLUMN agent_pipeline_id TEXT NOT NULL DEFAULT '';

-- Index for Featured Rituals queries (Most Run ranking, Most Recently Run)
CREATE INDEX IF NOT EXISTS idx_chores_execution_count ON chores(execution_count DESC);
CREATE INDEX IF NOT EXISTS idx_chores_last_triggered_at ON chores(last_triggered_at DESC);
