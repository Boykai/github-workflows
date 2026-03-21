# Optimistic Cache Contract

**Feature**: 001-optimistic-updates-mutations  
**Date**: 2026-03-21

This document defines the contract for optimistic cache updates — how the client-side cache is manipulated during mutations before server confirmation.

## Contract: Optimistic Create (Prepend)

**Applies to**: `useCreateAgent`, `uploadTool` (in `useToolsList`), `useCreateProject`

### Flat Array Cache

```typescript
// For raw arrays (agents, chores, apps):
queryClient.setQueryData<Entity[]>(queryKey, [placeholder, ...snapshot]);

// For wrapper objects (tools, projects):
queryClient.setQueryData<{ entities: Entity[] }>(queryKey, (old) => ({
  ...old,
  entities: [placeholder, ...old.entities],
}));
```

### Paginated Cache (InfiniteData)

```typescript
queryClient.setQueryData(paginatedQueryKey, (old: InfiniteData<PaginatedResponse<Entity>>) => {
  if (!old?.pages?.length) return old;
  return {
    ...old,
    pages: old.pages.map((page, index) =>
      index === 0
        ? { ...page, items: [placeholder, ...page.items] }
        : page
    ),
  };
});
```

**Invariants**:
- Placeholder is prepended to the first page only
- `pageParams` is not modified
- `next_cursor`, `has_more`, and `total_count` are not modified (reconciled on `onSettled` invalidation)

## Contract: Optimistic Delete (Filter)

**Applies to**: `useDeleteAgent` (and existing hooks needing paginated fix)

### Flat Array Cache

```typescript
queryClient.setQueryData<Entity[]>(queryKey, (old) =>
  old?.filter((entity) => entity.id !== entityId)
);
```

### Paginated Cache (InfiniteData)

```typescript
queryClient.setQueryData(paginatedQueryKey, (old: InfiniteData<PaginatedResponse<Entity>>) => {
  if (!old?.pages) return old;
  return {
    ...old,
    pages: old.pages.map((page) => ({
      ...page,
      items: page.items.filter((item) => item.id !== entityId),
    })),
  };
});
```

**Invariants**:
- Entity is removed from all pages (not just the visible one)
- `pageParams` is not modified
- `total_count` is not decremented (reconciled on server response)

## Contract: Optimistic Update (Map)

**Applies to**: Existing hooks (`useUpdateChore`, `useInlineUpdateChore`, `useUpdateApp`, `useStartApp`, `useStopApp`) — paginated fix only

### Flat Array Cache

```typescript
queryClient.setQueryData<Entity[]>(queryKey, (old) =>
  old?.map((entity) =>
    entity.id === entityId ? { ...entity, ...updates } : entity
  )
);
```

### Paginated Cache (InfiniteData)

```typescript
queryClient.setQueryData(paginatedQueryKey, (old: InfiniteData<PaginatedResponse<Entity>>) => {
  if (!old?.pages) return old;
  return {
    ...old,
    pages: old.pages.map((page) => ({
      ...page,
      items: page.items.map((item) =>
        item.id === entityId ? { ...item, ...updates } : item
      ),
    })),
  };
});
```

## Contract: Snapshot & Rollback

**All optimistic mutations** follow this lifecycle contract:

### onMutate (Setup)

```typescript
async onMutate(variables) {
  if (!projectId) return;
  
  // 1. Cancel in-flight queries for both cache keys
  const queryKey = entityKeys.list(projectId);
  const paginatedQueryKey = [...entityKeys.list(projectId), 'paginated'];
  await queryClient.cancelQueries({ queryKey });
  await queryClient.cancelQueries({ queryKey: paginatedQueryKey });
  
  // 2. Snapshot both caches
  const snapshot = queryClient.getQueryData(queryKey);
  const paginatedSnapshot = queryClient.getQueryData(paginatedQueryKey);
  
  // 3. Apply optimistic update (create/delete/update per above contracts)
  // ...
  
  // 4. Return context for rollback
  return { snapshot, queryKey, paginatedSnapshot, paginatedQueryKey };
}
```

### onError (Rollback)

```typescript
onError(error, variables, context) {
  // Restore flat cache
  if (context?.snapshot && context.queryKey) {
    queryClient.setQueryData(context.queryKey, context.snapshot);
  }
  // Restore paginated cache
  if (context?.paginatedSnapshot && context.paginatedQueryKey) {
    queryClient.setQueryData(context.paginatedQueryKey, context.paginatedSnapshot);
  }
  toast.error(error.message || 'Fallback error message', { duration: Infinity });
}
```

### onSettled (Reconcile)

```typescript
onSettled() {
  if (projectId) {
    queryClient.invalidateQueries({ queryKey: entityKeys.list(projectId) });
    // Paginated key is a child of list key, so invalidation cascades automatically
  }
}
```

## Type Safety

All optimistic placeholders use the `satisfies Entity & { _optimistic: boolean }` pattern established by `useCreateChore` and `useCreateApp`. The `_optimistic` flag is a compile-time marker that does not affect runtime behavior but ensures the placeholder object has all required fields.

## Edge Cases Handled by Contract

1. **No existing cache data**: `onMutate` short-circuits (`if (!snapshot) return`) — no optimistic update applied, mutation still proceeds normally.
2. **Rapid sequential mutations**: Each `onMutate` snapshots the current cache state (which may include previous optimistic entries), so rollback restores to the state just before that specific mutation.
3. **Component unmount**: `onSettled` invalidation still fires (TanStack Query guarantees lifecycle callbacks), ensuring cache is eventually consistent.
4. **Paginated cache not yet loaded**: `getQueryData` returns `undefined`, so paginated update is skipped. The `onSettled` invalidation will populate it when the user navigates to the paginated view.
