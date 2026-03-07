# Research: Tools Page — Fix MCP Bugs, Broken Link, Repo Name Display, Discover Button & Auto-populate MCP Name

**Feature**: 028-mcp-tools-fixes | **Date**: 2026-03-07

## R1: Correct GitHub Copilot MCP Documentation URL

**Task**: Identify the correct, stable URL for the official GitHub Copilot MCP documentation to replace the currently broken link on the Tools page.

**Decision**: Update the MCP docs link to `https://docs.github.com/copilot/customizing-copilot/using-model-context-protocol`. This is the official GitHub Docs page for "Using Model Context Protocol" under the Copilot documentation section.

**Rationale**: The current link (`https://docs.github.com/en/copilot/customizing-copilot/extending-the-functionality-of-github-copilot-in-your-organization`) is broken/dead. The correct URL is the dedicated MCP page within GitHub's Copilot documentation. This page covers MCP server setup, configuration, and integration with GitHub Copilot — which is the exact guidance users need from the Tools page link. The URL is under the `docs.github.com/copilot/` path, confirming it is the official GitHub-maintained documentation.

**Alternatives Considered**:
- **`https://modelcontextprotocol.io/`**: Rejected — this is the general MCP protocol specification site, not GitHub Copilot-specific documentation.
- **`https://docs.github.com/en/copilot/concepts/context/mcp`**: Considered — this is a conceptual overview page ("About MCP"). However, the "Using Model Context Protocol" page is more actionable for users configuring MCP tools, making it the better default link.

---

## R2: MCP Type Inference Logic for Command/Args Definitions

**Task**: Determine the correct type inference behavior when an MCP server definition contains `command`/`args` fields but no explicit `type` field, and when it contains a `url` field but no explicit `type` field.

**Decision**: Implement type inference in the MCP validation logic with the following rules:
1. If `type` is explicitly set to `"http"` or `"stdio"` → use it as-is (existing behavior, unchanged).
2. If `type` is absent and `command` is present (non-empty string) → infer `type = "stdio"`.
3. If `type` is absent and `url` is present (non-empty string) → infer `type = "http"`.
4. If `type` is absent and neither `command` nor `url` is present → return a clear error: the definition is ambiguous/malformed.
5. If `command` is present but is an empty string → treat as malformed (don't infer stdio).

Apply this inference in both:
- **Frontend**: `validateMcpJson()` in `UploadMcpModal.tsx` (client-side UX validation)
- **Backend**: `validate_mcp_config()` in `backend/src/services/tools/service.py` (authoritative validation)

**Rationale**: The MCP specification defines two transport types: `stdio` (local command-based) and `http` (remote URL-based). The presence of `command` unambiguously identifies an stdio server, and `url` unambiguously identifies an http server. Many real-world MCP configurations (e.g., Docker-based servers, VS Code `mcp.json` files) omit the `type` field when `command` is present, relying on this implicit convention. The current validation strictly requires an explicit `type` field, causing valid configs to be rejected — as reported in the bug (markitdown Docker example). This fix aligns the validation with the MCP spec's implicit type convention.

**Alternatives Considered**:
- **Only fix frontend, not backend**: Rejected — the backend is the authoritative validator; a frontend-only fix would still cause server-side 400 errors.
- **Always require explicit `type`**: Rejected — this contradicts real-world MCP usage patterns and the reported bug behavior.
- **Only infer `stdio`, not `http`**: Rejected — the same principle applies to both transports; `url` without `type` is equally unambiguous and should be accepted.

---

## R3: MCP Name Auto-Population Strategy

**Task**: Determine the best approach for auto-populating the MCP Name field from an uploaded or pasted MCP definition JSON.

**Decision**: Add a `useEffect` hook in `UploadMcpModal` that watches the `configContent` state. When `configContent` changes:
1. Attempt to parse as JSON.
2. If parsing succeeds and `parsed.mcpServers` is a non-empty object:
   a. Extract the first key via `Object.keys(parsed.mcpServers)[0]`.
   b. If the `name` field is currently empty (empty string after trim), set it to the extracted key.
   c. If there are multiple keys under `mcpServers`, set an informational message (e.g., "Multiple servers detected; using first: '{name}'").
3. If parsing fails or `mcpServers` is missing/empty, do nothing (no error — validation handles this on submit).

The auto-populate only fires when the name field is empty — it never overwrites user-entered values.

**Rationale**: Using `useEffect` on `configContent` is the React-idiomatic approach for derived state. It fires for both paste mode (textarea `onChange`) and file upload mode (`FileReader.onload` sets `configContent`), so both paths are covered by a single reactive hook. Checking `name.trim() === ''` ensures user intent is respected — if they've typed anything, it won't be overwritten. Using the first key of `mcpServers` follows JavaScript's object key insertion order guarantee (ECMAScript 2015+), which JSON.parse preserves.

**Alternatives Considered**:
- **Parse inside `onChange` / `handleFileUpload` handlers**: Rejected — duplicates parsing logic in two places (paste and file upload paths). The `useEffect` approach handles both centrally.
- **Use a separate "Extract Name" button**: Rejected — adds friction; auto-population on config input is more intuitive and matches the spec requirement.
- **Parse every keystroke with debounce**: Considered — unnecessary because `configContent` is set as a complete string (not character-by-character) in both paste and file modes. Debouncing adds complexity without benefit.

---

## R4: Repository Bubble Display Fix

**Task**: Determine the correct fix for showing the repository name instead of the owner in the Repository display on the Tools page.

**Decision**: In `ToolsPage.tsx`, change the Repository stat value from `repo.owner` (or `${repo.owner}/${repo.name}`) to just `repo.name`. Specifically:
1. **Badge**: Change `badge={repo ? \`\${repo.owner}/\${repo.name}\` : 'Awaiting repository'}` to `badge={repo ? repo.name : 'Awaiting repository'}`.
2. **Stats**: Change `{ label: 'Repository', value: repo ? \`\${repo.owner}/\${repo.name}\` : 'Unlinked' }` to `{ label: 'Repository', value: repo ? repo.name : 'Unlinked' }`.

For dynamic bubble sizing: The `CelestialCatalogHero` component's stat values already use `truncate` CSS class (which applies `text-overflow: ellipsis; overflow: hidden; white-space: nowrap`), providing graceful handling for long names. The `moonwell` container already uses flexible sizing via padding-based layout. No additional CSS changes are needed — the existing Tailwind classes handle dynamic sizing.

**Rationale**: The spec requires showing the "repository name" (e.g., `github-workflows`) not the owner (e.g., `Boykai`) or the full path (`Boykai/github-workflows`). The `repo` object has separate `owner` and `name` properties; the current code concatenates them. The `CelestialCatalogHero` stat display already truncates long text with ellipsis, and the `moonwell` container adapts to content width via padding. The existing CSS handles names of any length without overflow.

**Alternatives Considered**:
- **Keep `owner/name` format but emphasize name**: Rejected — the spec explicitly says "should be the repo name, not the owner."
- **Add `width: fit-content` or `ResizeObserver`**: Rejected — the existing `truncate` class and flexible container already handle dynamic sizing. Adding JS-based resize logic would be over-engineering.
- **Add tooltip for long names**: Considered for future — the `truncate` class already signals overflow visually. A tooltip could be added later if users report issues with very long names.

---

## R5: Discover Button Placement and Styling

**Task**: Determine the optimal placement, styling, and accessibility attributes for the new "Discover" MCP Registry button.

**Decision**: Add a new `<Button>` element in the `actions` slot of `CelestialCatalogHero` on the Tools page, alongside the existing "Browse tools" and "MCP docs" buttons. Use the same `variant="outline"` and `size="lg"` as the "MCP docs" button for visual consistency. The button wraps an `<a>` tag with `href="https://github.com/mcp"`, `target="_blank"`, and `rel="noopener noreferrer"`. Add `aria-label="Discover MCP integrations on GitHub"` for screen reader accessibility.

**Rationale**: Placing the Discover button in the existing actions row maintains visual consistency and discoverability without cluttering the UI. Using `variant="outline"` makes it secondary to the primary "Browse tools" CTA, which is appropriate since discovery is an exploration action, not the primary page function. The `noopener noreferrer` attributes follow security best practices for external links. The `aria-label` provides a descriptive label for assistive technologies, satisfying FR-012.

**Alternatives Considered**:
- **Separate "Discover" section below the hero**: Rejected — adds visual weight and breaks the existing hero layout pattern.
- **Icon-only button**: Rejected — less discoverable; the text "Discover" provides clear affordance.
- **Button with external link icon (lucide `ExternalLink`)**: Considered — could be added as a visual indicator alongside text. Not strictly necessary since the button text and `target="_blank"` behavior communicate the external nature. Can be added later if user feedback suggests confusion.
