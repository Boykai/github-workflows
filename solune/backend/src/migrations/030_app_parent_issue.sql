-- 030: Add parent issue tracking columns to apps table
-- Stores the parent issue number and URL when a pipeline is launched during app creation.

ALTER TABLE apps ADD COLUMN parent_issue_number INTEGER DEFAULT NULL;
ALTER TABLE apps ADD COLUMN parent_issue_url TEXT DEFAULT NULL;
