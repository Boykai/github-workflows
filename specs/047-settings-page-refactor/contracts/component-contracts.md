# Component Contracts

**Feature**: 047-settings-page-refactor | **Date**: 2026-03-16

## Contract: Settings Page Tab Layout

The Settings page MUST present a tabbed interface using Shadcn Tabs (Radix UI primitives).

### Tab Structure

```
SettingsPage
  └── Tabs (controlled, value synced with URL hash)
        ├── TabsList
        │     ├── TabsTrigger value="essential"    — always visible
        │     ├── TabsTrigger value="secrets"       — always visible
        │     ├── TabsTrigger value="preferences"   — always visible
        │     └── TabsTrigger value="admin"         — visible only if isAdmin
        ├── TabsContent value="essential"
        │     └── EssentialSettings
        ├── TabsContent value="secrets"
        │     └── SecretsManager
        ├── TabsContent value="preferences"
        │     └── PreferencesTab
        └── TabsContent value="admin" (rendered only if isAdmin)
              └── AdminTab
```

### URL Hash Synchronization

```
[Page Mount]
  → Read window.location.hash
  → If #essential → set tab "essential"
  → If #secrets → set tab "secrets"
  → If #preferences → set tab "preferences"
  → If #admin AND isAdmin → set tab "admin"
  → If #admin AND NOT isAdmin → set tab "essential" (fallback)
  → If no hash or unknown hash → set tab "essential" (default)

[Tab Change]
  → User clicks tab trigger
  → onValueChange fires with new tab value
  → window.location.hash = `#${value}`
  → URL updates without page reload (replaceState)
```

**Constraints**:
- Tab value MUST be one of: `"essential"`, `"secrets"`, `"preferences"`, `"admin"`
- Default tab MUST be `"essential"` when no valid hash is present
- Admin tab MUST NOT be rendered (not just hidden) for non-admin users
- Hash update MUST use `history.replaceState` to avoid polluting browser history
- Unsaved changes warning MUST work across all tabs

---

## Contract: EssentialSettings Component

Displays the core AI configuration that 90% of users need.

### Props

```typescript
interface EssentialSettingsProps {
  settings: EffectiveUserSettings;
  onSettingsChange: (update: UserPreferencesUpdate) => Promise<void>;
  isPending: boolean;
}
```

### Composition

```
EssentialSettings
  └── SettingsSection title="AI Configuration"
        ├── DynamicDropdown (AI Provider)
        ├── DynamicDropdown (Model — loads based on selected provider)
        └── Temperature Slider
```

**Constraints**:
- MUST NOT include SignalConnection (moved to PreferencesTab)
- MUST NOT include display, workflow, or notification settings
- Model dropdown MUST update when provider changes (existing `useModelOptions` hook)
- Save button per section via SettingsSection wrapper

---

## Contract: PreferencesTab Component

Consolidates secondary user preferences into card-grouped sections.

### Composition

```
PreferencesTab
  ├── DisplayPreferences    (SettingsSection wrapper)
  ├── WorkflowDefaults      (SettingsSection wrapper)
  ├── NotificationPreferences (SettingsSection wrapper)
  └── SignalConnection       (SettingsSection wrapper)
```

**Constraints**:
- Each section MUST have its own independent save button
- Saving one section MUST NOT affect unsaved changes in other sections
- All leaf components are reused unchanged from existing codebase
- Component is a pure composition — no new state management logic

---

## Contract: AdminTab Component

Provides admin-only settings for instance-wide defaults and project configuration.

### Composition

```
AdminTab
  ├── GlobalSettings        (global AI/display/workflow/notification defaults + allowed models)
  └── ProjectSettings       (per-project board config + agent pipeline mappings)
```

**Constraints**:
- MUST only be rendered when user is admin (parent checks `isAdmin` before mounting)
- Reuses existing `globalSettingsSchema.ts` Zod validation
- Reuses existing `flatten()`/`toUpdate()` converters for global settings
- Backend enforces admin-only on PUT `/settings/global` (no new backend changes needed)

---

## Contract: SecretsManager Component

Full CRUD interface for GitHub environment secrets.

### Props

```typescript
interface SecretsManagerProps {
  // No required props — uses hooks internally for data fetching
}
```

### Internal State

```typescript
// Repository selection
selectedOwner: string | null
selectedRepo: string | null
environment: string  // defaults to "copilot"

// Custom secret form
customSecretName: string
customSecretValue: string
showCustomForm: boolean

// Secret value input (for known secrets)
activeSecretName: string | null  // which secret is being set/updated
secretValueInput: string
showPassword: boolean
```

### Composition

```
SecretsManager
  ├── Repository Selector (dropdown from user's repos)
  ├── Environment Input (default "copilot", advanced toggle for custom)
  ├── Known Secrets Section
  │     └── For each KNOWN_SECRETS entry:
  │           ├── Label + Description
  │           ├── Status Badge ("Set ✓" / "Not Set")
  │           └── Action Buttons (Set / Update / Remove)
  ├── Custom Secrets Section
  │     ├── Existing Custom Secrets List (name + status + remove button)
  │     └── "Add Custom Secret" Form
  │           ├── Name Input (validated: ^[A-Z][A-Z0-9_]*$)
  │           ├── Value Input (password type, show/hide toggle)
  │           └── Add Button
  └── Secret Value Dialog/Inline
        ├── Password Input (autocomplete="off", aria-label)
        ├── Show/Hide Toggle
        └── Confirm / Cancel Buttons
```

**Constraints**:
- Secret values MUST use `<input type="password">` with show/hide toggle
- Secret values MUST NEVER be pre-filled (inputs always start empty)
- `autocomplete="off"` MUST be set on all secret value inputs
- Secret name validation MUST happen client-side before submission
- Custom secret names without `COPILOT_MPC_` prefix MUST show a warning (not block)
- Repository selector MUST be populated from user's available repos
- Environment defaults to `"copilot"` but MUST be editable for power users

---

## Contract: useSecrets Hook

TanStack Query hooks for secrets API operations.

### Query Key Factory

```typescript
export const secretsKeys = {
  all: ['secrets'] as const,
  list: (owner: string, repo: string, env: string) =>
    [...secretsKeys.all, 'list', owner, repo, env] as const,
  check: (owner: string, repo: string, env: string, names: string[]) =>
    [...secretsKeys.all, 'check', owner, repo, env, ...names] as const,
};
```

### Hooks

```typescript
// Query: List secrets for a repository environment
useSecrets(owner: string | null, repo: string | null, env: string)
  → enabled: owner != null && repo != null
  → queryKey: secretsKeys.list(owner!, repo!, env)
  → queryFn: () => secretsApi.listSecrets(owner!, repo!, env)
  → returns: { data: SecretsListResponse, isLoading, error }

// Mutation: Set (create/update) a secret
useSetSecret()
  → mutationFn: ({ owner, repo, env, name, value }) => secretsApi.setSecret(...)
  → onSuccess: invalidateQueries({ queryKey: secretsKeys.all })
  → returns: { mutateAsync, isPending }

// Mutation: Delete a secret
useDeleteSecret()
  → mutationFn: ({ owner, repo, env, name }) => secretsApi.deleteSecret(...)
  → onSuccess: invalidateQueries({ queryKey: secretsKeys.all })
  → returns: { mutateAsync, isPending }

// Query: Bulk check secret existence
useCheckSecrets(owner: string | null, repo: string | null, env: string, names: string[])
  → enabled: owner != null && repo != null && names.length > 0
  → queryKey: secretsKeys.check(owner!, repo!, env, names)
  → queryFn: () => secretsApi.checkSecrets(owner!, repo!, env, names)
  → returns: { data: SecretCheckResponse, isLoading, error }
```

**Constraints**:
- Mutations MUST invalidate `secretsKeys.all` to refresh both list and check queries
- Queries MUST be disabled when required parameters are null/empty
- No optimistic updates for secrets (operations are remote to GitHub, not local)

---

## Contract: secretsApi Service

Frontend API service group for secrets operations.

### Methods

```typescript
export const secretsApi = {
  listSecrets(owner: string, repo: string, env: string): Promise<SecretsListResponse>
    // GET /api/v1/secrets/{owner}/{repo}/{env}

  setSecret(owner: string, repo: string, env: string, name: string, value: string): Promise<void>
    // PUT /api/v1/secrets/{owner}/{repo}/{env}/{name}
    // Body: { value }

  deleteSecret(owner: string, repo: string, env: string, name: string): Promise<void>
    // DELETE /api/v1/secrets/{owner}/{repo}/{env}/{name}

  checkSecrets(owner: string, repo: string, env: string, names: string[]): Promise<SecretCheckResponse>
    // GET /api/v1/secrets/{owner}/{repo}/{env}/check?names={names.join(",")}
};
```

**Constraints**:
- Follow existing `settingsApi` / `signalApi` HTTP wrapper pattern
- Use the shared request utility from `api.ts`
- No `RequestInit` needed (no AbortSignal use cases for secrets)
