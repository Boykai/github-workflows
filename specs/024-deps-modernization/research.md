# Research: Full Dependency & Pattern Modernization

**Feature Branch**: `024-deps-modernization`
**Date**: 2026-03-06
**Status**: Complete — all NEEDS CLARIFICATION resolved

## Findings

### 1. Tenacity 8.x → 9.x Compatibility

- **Decision**: Direct upgrade — no code changes required
- **Rationale**: All APIs used by the codebase (`retry`, `retry_if_exception_type`, `stop_after_attempt`, `wait_exponential`, `before_sleep_log`) are preserved in v9. Verified by installing 9.1.4 and importing all symbols successfully.
- **Alternatives considered**: Pinning to 8.x — rejected because 9.x is fully backward compatible for our usage and provides bug fixes.
- **Impact**: Zero code changes in `src/services/signal_delivery.py`.

### 2. Websockets 12.x → 16.x Compatibility

- **Decision**: Direct upgrade — no code changes required
- **Rationale**: All APIs used (`websockets.connect()`, `websockets.ConnectionClosed`, async context manager pattern, `ping_interval` kwarg) are preserved in v16. Verified by installing 16.0 and confirming attribute availability.
- **Alternatives considered**: Pinning to 14.x — rejected because 16.0 is backward compatible and the spec references v14 which is outdated.
- **Impact**: Zero code changes in `src/services/signal_bridge.py`.

### 3. pytest-asyncio 0.23 → 1.3 Migration

- **Decision**: Upgrade with config addition
- **Rationale**: Major version jump (0.23→1.0→1.3) removes the deprecated `event_loop` fixture and renames `scope=` to `loop_scope=`. The codebase uses `asyncio_mode = "auto"` and does NOT use `event_loop` fixtures directly. One `pytest.fixture(scope="session")` exists in `conftest.py` but it's a synchronous fixture, not affected by pytest-asyncio changes.
- **Alternatives considered**: Staying on 0.25.x — rejected because 1.3.0 has better pytest 9 support.
- **Config change**: Add `asyncio_default_fixture_loop_scope = "function"` to `[tool.pytest.ini_options]`.

### 4. React 18 → 19 forwardRef Migration

- **Decision**: Remove `React.forwardRef` wrappers, accept `ref` as a regular prop
- **Rationale**: React 19 treats `ref` as a regular prop on function components. `forwardRef` still works but is deprecated. Removing it now follows best practices and reduces boilerplate.
- **Files affected** (8 forwardRef usages):
  - `frontend/src/components/ui/button.tsx` — 1 component
  - `frontend/src/components/ui/input.tsx` — 1 component
  - `frontend/src/components/ui/card.tsx` — 6 components (Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter)
- **Pattern**:
  ```tsx
  // Before (React 18)
  const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({ ...props }, ref) => { ... })
  Button.displayName = "Button"

  // After (React 19)
  function Button({ ref, ...props }: ButtonProps & { ref?: React.Ref<HTMLButtonElement> }) { ... }
  ```
- **Automation**: `npx codemod@latest react/19/migration-recipe` available but manual update preferred for 8 occurrences (more controlled).

### 5. Tailwind CSS 3 → 4 Migration

- **Decision**: Full CSS-first migration using `@tailwindcss/vite` plugin and `@theme` blocks
- **Rationale**: Tailwind v4 replaces JS config with CSS-first configuration. Using `@tailwindcss/vite` eliminates the need for PostCSS entirely. The `npx @tailwindcss/upgrade` tool automates most of the migration.
- **Alternatives considered**: Using `@config "./tailwind.config.js"` compat mode — rejected because it defers migration debt and doesn't benefit from v4 performance improvements.

#### Files to delete
- `frontend/postcss.config.js` (PostCSS no longer needed)
- `frontend/tailwind.config.js` (replaced by CSS-first config in index.css)

#### Dependencies to remove
- `autoprefixer` (built into Tailwind v4 via Lightning CSS)
- `tailwindcss-animate` (animation utilities built into v4)
- `postcss` (no longer needed with @tailwindcss/vite)

#### Dependencies to add
- `@tailwindcss/vite` (Vite plugin replaces PostCSS integration)

#### Config migration: tailwind.config.js → index.css @theme
Current JS config translates to CSS `@theme` blocks:
```css
@import "tailwindcss";

@theme {
  --font-display: 'Rye', 'Georgia', serif;
  --font-sans: 'Inter', 'system-ui', sans-serif;
  --shadow-warm-sm: 0 1px 2px 0 rgba(59,45,31,0.08);
  --shadow-warm: 0 1px 3px 0 rgba(59,45,31,0.12), 0 1px 2px -1px rgba(59,45,31,0.12);
  --shadow-warm-md: 0 4px 6px -1px rgba(59,45,31,0.12), 0 2px 4px -2px rgba(59,45,31,0.12);
  --shadow-warm-lg: 0 10px 15px -3px rgba(59,45,31,0.12), 0 4px 6px -4px rgba(59,45,31,0.12);
  --color-border: hsl(var(--border));
  --color-input: hsl(var(--input));
  --color-ring: hsl(var(--ring));
  --color-background: hsl(var(--background));
  --color-foreground: hsl(var(--foreground));
  --color-primary: hsl(var(--primary));
  --color-primary-foreground: hsl(var(--primary-foreground));
  --color-secondary: hsl(var(--secondary));
  --color-secondary-foreground: hsl(var(--secondary-foreground));
  --color-destructive: hsl(var(--destructive));
  --color-destructive-foreground: hsl(var(--destructive-foreground));
  --color-muted: hsl(var(--muted));
  --color-muted-foreground: hsl(var(--muted-foreground));
  --color-accent: hsl(var(--accent));
  --color-accent-foreground: hsl(var(--accent-foreground));
  --color-popover: hsl(var(--popover));
  --color-popover-foreground: hsl(var(--popover-foreground));
  --color-card: hsl(var(--card));
  --color-card-foreground: hsl(var(--card-foreground));
  --radius-lg: var(--radius);
  --radius-md: calc(var(--radius) - 2px);
  --radius-sm: calc(var(--radius) - 4px);
}
```

#### Utility class renames (handled by upgrade tool)
| Tailwind v3 | Tailwind v4 |
|-------------|-------------|
| `shadow-sm` | `shadow-xs` |
| `shadow` (bare) | `shadow-sm` |
| `rounded-sm` | `rounded-xs` |
| `rounded` (bare) | `rounded-sm` |
| `outline-none` | `outline-hidden` |
| `ring` (bare) | `ring-3` |

**Note**: `outline-none` is used in ~20+ component files. The upgrade tool handles this automatically.

#### Recommended approach
1. Run `npx @tailwindcss/upgrade` from `frontend/` to automate most changes
2. Manually verify CSS variable references and dark mode
3. Verify visual output matches pre-upgrade rendering

### 6. Vite 5 → 7 Migration

- **Decision**: Direct upgrade with plugin update
- **Rationale**: Vite 7 requires `@vitejs/plugin-react` v5 and Node.js ≥20.19. Current vite.config.ts uses no deprecated features (no `splitVendorChunkPlugin`, no Sass legacy API). Migration is straightforward.
- **Config changes**:
  - Update `@vitejs/plugin-react` from ^4.2.1 to ^5.1.0
  - Add `@tailwindcss/vite` plugin (from Tailwind v4 migration)
  - Remove `postcss` from devDependencies
- **Spec correction**: Spec says "Vite 6" (FR-008) but actual latest is Vite 7.3.1. Plan targets v7.

### 7. ESLint 9 → 10 Migration

- **Decision**: Direct upgrade — minimal config changes
- **Rationale**: Already on flat config format. Main impact is 3 new recommended rules (`no-unassigned-vars`, `no-useless-assignment`, `preserve-caught-error`) and improved JSX reference tracking.
- **Config changes**:
  - Update `@eslint/js` from ^9.0.0 to ^10.0.0
  - Update `eslint-plugin-react-hooks` from ^5.0.0 to ^7.0.0
  - v7 of react-hooks plugin provides `recommended` and `recommended-latest` configs. Current spread pattern (`...reactHooks.configs.recommended.rules`) should continue working.
- **Risk**: New recommended rules may flag existing code. Fix or configure as needed.

### 8. jsdom 27 → 28

- **Decision**: Direct upgrade — no code changes
- **Rationale**: Breaking change is about custom resource loaders (not used). Vitest uses `happy-dom` as the test environment, not jsdom. jsdom is listed as a devDependency but may be unused.
- **Impact**: Zero.

### 9. Unused Dependencies

- **python-jose[cryptography]**: Confirmed unused — `grep -rn 'python.jose\|jose\.' backend/src/` returns zero hits. Remove from pyproject.toml.
- **socket.io-client**: Confirmed unused — `grep -rn 'socket\.io\|io(' frontend/src/` returns zero hits. The app uses native WebSocket API. Remove from package.json.

### 10. Runtime Upgrades

- **Python 3.12 → 3.13**: Dockerfile base image change (`python:3.12-slim` → `python:3.13-slim`). Ruff target-version and pyright pythonVersion updated. No code changes needed — Python 3.13 is backward compatible and adds free-threaded mode (not used), improved error messages, and typing improvements.
- **Node 20 → 22**: Dockerfile base image change (`node:20-alpine` → `node:22-alpine`). Required by ESLint 10 (Node ≥20.19) and Vite 7 (Node ≥20.19). No code changes needed.

### 11. Ruff Lint Rule Expansion

- **Decision**: Add FURB, PTH, PERF, RUF rule sets; update target-version to py313
- **Rationale**: These rule sets enforce modern Python idioms:
  - FURB (refurb): Suggests more Pythonic alternatives
  - PTH (pathlib): Prefers pathlib over os.path
  - PERF (Perflint): Performance anti-patterns
  - RUF (Ruff-specific): Additional linting rules
- **Approach**: Run `ruff check --fix src/` to auto-fix safe violations first, then manually review remaining.

## Migration Order

The recommended execution order minimizes risk by establishing the build toolchain first:

1. **Backend deps** (pyproject.toml version bumps, remove python-jose) — lowest risk
2. **Backend config** (ruff rules, pyright version, pytest-asyncio config)
3. **Backend code** (ruff auto-fix, any manual fixes)
4. **Frontend Vite upgrade** (Vite 7, @vitejs/plugin-react 5) — establishes build
5. **Frontend React 19** (version bump, @types/react 19, forwardRef removal)
6. **Frontend Tailwind v4** (run upgrade tool, config migration, file deletions) — highest risk, do last
7. **Frontend ESLint 10** (version bumps, fix new rule violations)
8. **Frontend cleanup** (remove unused deps, verify build)
9. **Dockerfiles** (Python 3.13, Node 22)
10. **Docker Compose verification** (full stack build and health check)
