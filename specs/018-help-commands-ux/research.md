# Research: Enhance #help and General # Commands UX

**Feature**: 018-help-commands-ux | **Date**: 2026-03-04

## R1: Command Categorization Strategy

**Decision**: Add an optional `category` field to `CommandDefinition` with a default of `"General"`. Categories are display-only groupings used in #help output.

**Rationale**: The spec requires commands to be grouped by category in the #help listing (FR-001, FR-010). Adding an optional field to the existing type is the minimal change that enables categorization without breaking any existing code. Commands that omit the field automatically fall into "General."

**Alternatives considered**:
- Separate category registry with category→command mappings — rejected because it introduces a second source of truth and requires synchronization. Violates DRY (Constitution V).
- Category as a required field — rejected because it would break all existing `registerCommand()` call sites and test factories. Optional with default is safer.

## R2: Fuzzy Matching Algorithm for "Did you mean?"

**Decision**: Use a simple Levenshtein distance implementation (edit distance) with a threshold of 2 edits. No external library needed — the algorithm is ~20 lines of TypeScript.

**Rationale**: The spec requires suggesting closest matching commands when a user types an unrecognized command (FR-006, SC-004). Levenshtein distance is the standard approach for this problem. A threshold of 2 edits catches common typos (missing letter, swapped letters, extra letter) while avoiding false positives. With only 6–20 commands, performance is trivially fast (no optimization needed).

**Alternatives considered**:
- `fastest-levenshtein` npm package — rejected because the command set is tiny (<20 entries) and adding a dependency for 20 lines of logic violates simplicity (Constitution V).
- Jaro-Winkler distance — rejected because Levenshtein is simpler, more predictable, and sufficient for short command names.
- Substring/prefix matching only — rejected because it wouldn't catch transposition errors like `#hep` → `#help`.

## R3: Plain-Text Formatting Strategy

**Decision**: Use whitespace-based formatting with consistent indentation, line-based structure, and the em dash (—) separator already established in the current help output. No Markdown, no emoji for status indication.

**Rationale**: The spec assumption explicitly states "chat messages are rendered without a Markdown parser" and FR-009 prohibits relying solely on color or emoji. The existing help handler already uses `  syntax  —  description` format. We extend this pattern with section headers and blank-line separators for category grouping.

**Alternatives considered**:
- Markdown formatting (bold, code blocks) — rejected because the chat renderer doesn't parse Markdown; literal `**` markers would appear.
- Emoji-prefixed categories — rejected by FR-009. While emoji can supplement text, the spec requires text-only conveyance of meaning. We include the emoji-as-supplement option only as a future enhancement note.

## R4: Single-Command Help (`#help <command>`)

**Decision**: Reuse the `_args` parameter (currently ignored) in the help handler. When args is non-empty, look up the specific command and display its detailed info. Strip a leading `#` from the argument to handle `#help #theme`.

**Rationale**: FR-003 requires `#help <command>` to show detailed info for one command. The handler signature already receives `args` — it's just unused. Parsing the arg and looking up the command in the registry is a straightforward extension. The edge case of `#help #theme` (spec Edge Cases) is handled by stripping the `#` prefix from the argument.

**Alternatives considered**:
- Separate `#helpfor` command — rejected because it introduces an unnecessary new command. The existing `#help` with optional argument is cleaner and matches user expectations (FR-003).
- Subcommand pattern (`#help:theme`) — rejected because it deviates from the established `#command args` pattern.

## R5: Consistent Error Message Format

**Decision**: All error responses follow a three-part structure:
1. **What went wrong** — e.g., "Unknown command 'hep'."
2. **How to fix it** — e.g., "Did you mean #help?"
3. **Where to get more help** — e.g., "Type #help to see all available commands."

**Rationale**: FR-007 requires consistent structural formatting across all command responses. The three-part pattern (problem → solution → reference) is a well-established UX best practice for error messages. It reduces user cognitive load by placing information in a predictable location.

**Alternatives considered**:
- Single-line errors (current approach) — rejected because the spec explicitly requires structured, consistent formatting that helps users self-correct.
- JSON-structured errors with field labels — rejected as over-engineering for plain-text chat output.

## R6: Category Assignment for Existing Commands

**Decision**: Assign categories to the 6 existing commands as follows:

| Command | Category |
|---------|----------|
| help | General |
| theme | Settings |
| language | Settings |
| notifications | Settings |
| view | Settings |
| agent | Workflow |

Category display order in #help: General → Settings → Workflow (alphabetical within each category).

**Rationale**: These groupings match the natural function of each command and align with the spec's example categories (FR-001). The `help` command belongs in General as the meta-command for discovery. Settings commands (`theme`, `language`, `notifications`, `view`) all modify user preferences. The `agent` command creates workflow automation and belongs in Workflow.

**Alternatives considered**:
- All commands in "General" — rejected because categorization is a core requirement (FR-001) and provides the scanning benefit described in SC-001.
- More granular categories (e.g., "Appearance" for theme, "Communication" for notifications) — rejected because with only 6 commands, 3 categories already provide meaningful grouping without fragmentation.

## R7: Input Sanitization in Error Messages

**Decision**: Truncate displayed user input in error messages to a maximum of 50 characters. This prevents layout breakage from very long or unusual input strings.

**Rationale**: The spec edge case explicitly asks "How does the system handle very long or unusual command arguments in error messages?" Truncating at 50 characters is sufficient to show the user what they typed while preventing horizontal scrolling on narrow viewports (FR-008).

**Alternatives considered**:
- No truncation — rejected because it could break layout on 320px viewports with very long input.
- HTML encoding/escaping — not needed because output is plain text, not HTML.
