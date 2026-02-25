-- Migration 003: Add admin_github_user_id to global_settings
-- The first authenticated user auto-promotes to admin (session owner).
-- Used by FR-005 to gate settings modification endpoints.

ALTER TABLE global_settings ADD COLUMN admin_github_user_id TEXT DEFAULT NULL;
