# Quickstart: Optimistic Updates for Mutations

**Feature**: 001-optimistic-updates-mutations  
**Date**: 2026-03-21

## Prerequisites

- Node.js 18+
- Repository cloned with `solune/frontend` available

## Setup

```bash
cd solune/frontend
npm ci
```

## Development

```bash
npm run dev
```

## Key Files to Modify

| File | Changes |
|------|---------|
| `src/hooks/useAgents.ts` | Add `onMutate` to `useCreateAgent` (line ~64) and `useDeleteAgent` (line ~95) |
| `src/hooks/useTools.ts` | Add `onMutate` + `onError` toast to `uploadMutation` (line ~51) |
| `src/hooks/useProjects.ts` | Add `onMutate` to `useCreateProject` (line ~94) |
| `src/hooks/useChores.ts` | Extend all `onMutate` handlers for paginated cache |
| `src/hooks/useApps.ts` | Extend all `onMutate` handlers for paginated cache |

## Implementation Pattern

Every optimistic mutation follows this 4-step pattern (see `useCreateChore` at `src/hooks/useChores.ts:81` for reference):

### Step 1: onMutate — Apply optimistic update

```typescript
onMutate: async (data) => {
  if (!projectId) return;
  
  // Cancel in-flight queries
  const queryKey = entityKeys.list(projectId);
  const paginatedQueryKey = [...entityKeys.list(projectId), 'paginated'];
  await queryClient.cancelQueries({ queryKey });
  await queryClient.cancelQueries({ queryKey: paginatedQueryKey });
  
  // Snapshot current state
  const snapshot = queryClient.getQueryData(queryKey);
  const paginatedSnapshot = queryClient.getQueryData(paginatedQueryKey);
  
  // Apply optimistic update to flat cache
  // (create: prepend, delete: filter, update: map)
  
  // Apply same update to paginated cache
  // (map over pages[].items)
  
  return { snapshot, queryKey, paginatedSnapshot, paginatedQueryKey };
},
```

### Step 2: onError — Rollback

```typescript
onError: (error, _variables, context) => {
  if (context?.snapshot && context.queryKey) {
    queryClient.setQueryData(context.queryKey, context.snapshot);
  }
  if (context?.paginatedSnapshot && context.paginatedQueryKey) {
    queryClient.setQueryData(context.paginatedQueryKey, context.paginatedSnapshot);
  }
  toast.error(error.message || 'Failed to do thing', { duration: Infinity });
},
```

### Step 3: onSettled — Reconcile with server

```typescript
onSettled: () => {
  if (projectId) {
    queryClient.invalidateQueries({ queryKey: entityKeys.list(projectId) });
  }
},
```

### Step 4: onSuccess — User feedback

```typescript
onSuccess: () => {
  toast.success('Entity created');
},
```

## Testing

```bash
# Run all frontend tests
npm test

# Run specific hook tests
npx vitest run src/hooks/useAgents.test.tsx
npx vitest run src/hooks/useUndoableDelete.test.tsx
```

## Validation Checklist

1. ☐ Create agent → appears in list immediately
2. ☐ Create agent (server error) → agent removed, error toast shown
3. ☐ Delete agent → disappears from list immediately
4. ☐ Delete agent (server error) → agent reappears, error toast shown
5. ☐ Upload tool → appears in list immediately
6. ☐ Upload tool (server error) → tool removed, error toast shown
7. ☐ Create project → appears in list immediately
8. ☐ Create project (server error) → project removed, error toast shown
9. ☐ Create chore (paginated view) → appears on first page
10. ☐ Delete app (paginated view) → disappears from correct page
11. ☐ Rapid create 3 entities → all appear, errors revert individually

## Reference Implementations

- **Flat optimistic create**: `useCreateChore` in `src/hooks/useChores.ts:81–138`
- **Flat optimistic delete**: `useDeleteChore` in `src/hooks/useChores.ts:181–213`
- **Paginated-aware delete**: `removeEntityFromCache` in `src/hooks/useUndoableDelete.ts:74–125`
- **Undoable delete with InfiniteData**: `useUndoableDeleteAgent` in `src/hooks/useAgents.ts:115–136`
