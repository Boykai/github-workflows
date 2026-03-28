# Data Model: Fix Playwright Auth Setup, Mutation-Testing CI Noise, and Deprecated Chores Hook Usage

**Feature Branch**: `001-fix-ci-auth-chores`  
**Date**: 2026-03-28  
**Status**: N/A

## Overview

This feature involves configuration edits, workflow consolidation, and a mechanical hook migration. **No data model changes are required.**

- No new entities, fields, or relationships
- No database migrations
- No API schema changes
- No state transitions

The `Chore` entity and `PaginatedResponse<T>` types are pre-existing and unchanged. The migration from `useChoresList` to `useChoresListPaginated` changes only the frontend hook call pattern — the backend API endpoints (`/chores` and `/chores/paginated`) are unmodified.

## Existing Types Referenced

### Chore (unchanged)

Defined in `solune/frontend/src/types/index.ts`. Fields include `id`, `project_id`, `name`, `template_path`, `template_content`, `schedule_type`, `schedule_value`, `status`, `last_triggered_at`, `execution_count`, and timestamps.

### PaginatedResponse<T> (unchanged)

Defined in `solune/frontend/src/types/index.ts`. Shape: `{ items: T[], has_more: boolean, next_cursor?: string, total_count: number }`.

### useInfiniteList<T> return (unchanged)

Defined in `solune/frontend/src/hooks/useInfiniteList.ts`. Returns: `{ ...useInfiniteQuery result, allItems: T[], totalCount: number | null, resetPagination: () => void }`.
