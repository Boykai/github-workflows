-- 029: Add parent issue tracking columns to the apps table
-- Stores the GitHub parent issue number and URL created during pipeline setup.

ALTER TABLE apps ADD COLUMN parent_issue_number INTEGER;
ALTER TABLE apps ADD COLUMN parent_issue_url TEXT;
