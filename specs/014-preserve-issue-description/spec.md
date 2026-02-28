# Feature Specification: Preserve Full User-Provided GitHub Issue Description Without Truncation

**Feature Branch**: `014-preserve-issue-description`  
**Created**: 2026-02-28  
**Status**: Draft  
**Input**: User description: "As a user composing a GitHub Issue via chat, I want my full issue description preserved and used verbatim — regardless of length — so that long, detailed descriptions are not silently truncated, ensuring the created GitHub Issue accurately reflects everything I wrote."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Full Description Preserved on Issue Creation (Priority: P1)

A user composes a detailed, multi-paragraph GitHub Issue description through the chat interface. The description includes markdown formatting such as headers, bullet points, code blocks, and newlines. When the issue is created, the user navigates to the GitHub Issue and sees that the entire description — every character, every line break, every formatting element — is present exactly as they wrote it.

**Why this priority**: This is the core value proposition. If the full description is not preserved verbatim, the feature has failed its primary purpose. Users lose trust in the system when their content is silently modified or truncated.

**Independent Test**: Can be fully tested by submitting a multi-thousand-character description through the chat-to-issue flow and verifying the created GitHub Issue body matches the input character-for-character.

**Acceptance Scenarios**:

1. **Given** a user has composed a 5,000-character issue description with markdown formatting (headers, bullets, code blocks), **When** the issue is created via the chat interface, **Then** the resulting GitHub Issue body contains the exact same 5,000 characters with all formatting intact.
2. **Given** a user has composed a single-line, 20-character issue description, **When** the issue is created via the chat interface, **Then** the resulting GitHub Issue body matches the input exactly.
3. **Given** a user has composed a description at the maximum length supported by the GitHub API (65,536 characters), **When** the issue is created via the chat interface, **Then** the resulting GitHub Issue body matches the full 65,536-character input exactly.

---

### User Story 2 - No Silent Truncation at Any Processing Stage (Priority: P1)

A user submits a long issue description through the chat interface. At no point during the processing pipeline — chat handling, state storage, prompt construction, or API call building — is the description silently shortened, summarized, or truncated. If the description passes through an AI/LLM processing stage, the verbatim user text is kept separate from any AI reasoning and is never modified by summarization.

**Why this priority**: Silent truncation is the specific problem being solved. Even if the final output is correct, intermediate truncation could introduce subtle data loss depending on future pipeline changes. Ensuring no stage truncates is essential for long-term reliability.

**Independent Test**: Can be tested by submitting descriptions at known truncation boundaries (256, 1,024, 4,096, 65,536 characters) and asserting that the full text is preserved at each stage of the processing pipeline.

**Acceptance Scenarios**:

1. **Given** a user has composed a 4,096-character description, **When** the description passes through all intermediate processing steps (chat handling, state storage, prompt construction, API payload building), **Then** the text at each stage is identical to the original input with no data loss.
2. **Given** a user has composed a description that is used as context in an LLM prompt, **When** the issue is created, **Then** the verbatim user description is passed to the GitHub API independently of any AI-generated content, and the AI summarization does not alter the user's original text.

---

### User Story 3 - User Notification on API Length Limit Exceeded (Priority: P2)

A user composes a description that exceeds the GitHub API's hard limit of 65,536 characters. Instead of silently cutting the content, the system notifies the user that their description exceeds the API limit and cannot be submitted in full, giving them the opportunity to revise.

**Why this priority**: While most descriptions will be well under the limit, handling this edge case gracefully prevents a confusing user experience. Explicit notification is preferable to silent data loss.

**Independent Test**: Can be tested by submitting a description of 65,537+ characters and verifying the user receives a clear notification about the length limit, and no truncated issue is created without consent.

**Acceptance Scenarios**:

1. **Given** a user has composed a description exceeding 65,536 characters, **When** the system attempts to create the issue, **Then** the user receives an explicit notification stating the description exceeds the GitHub API body limit and the issue is not created with truncated content.
2. **Given** a user has composed a description of exactly 65,536 characters, **When** the system creates the issue, **Then** the issue is created successfully with the full description preserved.

---

### User Story 4 - Formatting Preservation Across All Markdown Elements (Priority: P2)

A user composes an issue description containing a variety of markdown elements: headers (h1–h6), ordered and unordered lists, nested lists, code blocks (inline and fenced), blockquotes, tables, links, images, bold, italic, strikethrough, and horizontal rules. All formatting is preserved exactly as written in the created GitHub Issue.

**Why this priority**: Formatting fidelity is a key part of "preserving the full description." Users who write structured descriptions rely on markdown formatting to convey meaning, and broken formatting undermines the usefulness of the created issue.

**Independent Test**: Can be tested by submitting a description with every supported markdown element and verifying each renders correctly on the created GitHub Issue.

**Acceptance Scenarios**:

1. **Given** a user has composed a description containing headers, lists, code blocks, blockquotes, tables, links, bold, italic, and horizontal rules, **When** the issue is created, **Then** every markdown element is present and correctly formatted in the GitHub Issue body.
2. **Given** a user has composed a description with multi-line fenced code blocks including special characters and indentation, **When** the issue is created, **Then** the code blocks are preserved exactly, including all whitespace and special characters.

---

### Edge Cases

- What happens when the description is empty (zero characters)? The system should handle this gracefully, either by creating an issue with an empty body or prompting the user to provide a description, consistent with existing behavior.
- What happens when the description contains only whitespace or newlines? The system should preserve the whitespace exactly as provided.
- What happens when the description contains Unicode characters, emoji, or non-ASCII text? All characters should be preserved verbatim without encoding issues.
- What happens when the description contains special characters that might be interpreted as control sequences (e.g., backslashes, null bytes, HTML entities)? The system should pass these through to the GitHub API without modification.
- What happens when the description is exactly at the 65,536-character boundary? The issue should be created successfully with the full content.
- What happens when the description is 1 character over the 65,536-character limit? The user should be notified explicitly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST pass the complete, unmodified user-provided issue description text to the GitHub Issues API as the issue body, regardless of character count or line count.
- **FR-002**: System MUST NOT silently truncate, summarize, or shorten any user-provided issue description at any stage of processing — including chat handling, state storage, prompt construction, or API call construction.
- **FR-003**: System MUST preserve all formatting in the full description, including newlines, markdown syntax, bullet points, headers, code blocks, tables, links, and all other markdown elements.
- **FR-004**: System MUST preserve all character types in the description, including Unicode characters, emoji, special characters, and whitespace.
- **FR-005**: System MUST correctly handle descriptions of varying lengths — from empty/single-character to the maximum supported by the GitHub API (65,536 characters) — without behavioral differences in content fidelity.
- **FR-006**: System SHOULD notify the user explicitly if the description exceeds the GitHub API's hard content length limit (65,536 characters), rather than silently cutting the content.
- **FR-007**: System MUST store and forward the full description text through all intermediate processing steps (e.g., chat message handling, state serialization, prompt construction, API payload building) without data loss.
- **FR-008**: If the user-provided description is used as context within an LLM prompt, the system MUST separate the verbatim user description passthrough path from any AI reasoning or summarization path, ensuring AI processing never alters the original text destined for the issue body.
- **FR-009**: System MUST detect and remove any currently applied truncation thresholds, substring operations, or length caps on the user-provided issue description within the chat-to-issue pipeline.

### Key Entities

- **Issue Description**: The user-provided text intended to become the body of a GitHub Issue. Key attributes: raw text content, character length, markdown formatting. Must be treated as immutable from the point of user submission through to API delivery.
- **Processing Pipeline**: The sequence of stages the issue description passes through — from chat input capture, through any intermediate state storage or LLM context usage, to the final GitHub API call. Each stage must forward the description without modification.
- **GitHub API Body Field**: The destination field in the GitHub REST API that receives the issue description. Hard limit of 65,536 characters imposed by GitHub.

## Assumptions

- The GitHub REST API's `body` field for issue creation accepts up to 65,536 characters. This is the authoritative hard limit.
- The existing chat-to-GitHub-issue pipeline may have one or more points where truncation occurs (e.g., LLM prompt construction, intermediate state serialization, or explicit substring operations). These must be identified and removed or bypassed.
- Empty descriptions are handled by existing behavior and do not require special treatment beyond ensuring no new restrictions are introduced.
- The system already has a mechanism for creating GitHub Issues from chat; this feature modifies the data flow, not the overall architecture.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of user-provided issue descriptions up to 65,536 characters are preserved character-for-character in the created GitHub Issue body, with zero data loss.
- **SC-002**: Descriptions at common truncation boundaries (256, 1,024, 4,096, 32,768, and 65,536 characters) pass through the system with identical input and output.
- **SC-003**: All markdown formatting elements (headers, lists, code blocks, tables, links, bold, italic, blockquotes, horizontal rules) are rendered correctly on the created GitHub Issue when included in the description.
- **SC-004**: Users receive an explicit notification within 5 seconds when a description exceeds the 65,536-character API limit, preventing silent data loss.
- **SC-005**: Zero instances of silent truncation, summarization, or content modification occur across the entire processing pipeline, as verified by end-to-end tests comparing input to output at each pipeline stage.
- **SC-006**: Edge case inputs (Unicode, emoji, special characters, whitespace-only, maximum length) are handled without errors or data corruption.
