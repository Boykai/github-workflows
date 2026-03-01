# Research: Preserve Full User-Provided GitHub Issue Description Without Truncation

**Feature**: 014-preserve-issue-description
**Date**: 2026-02-28

## Research Task 1: Audit the Chat-to-Issue Pipeline for Truncation Points

### Decision

The pipeline has **no additional truncation on the GitHub API body path beyond model-level limits** — all explicit truncation we add is display-only (preview text in chat messages). However, `ChatMessageRequest.content` enforces `max_length=100000` and is normalized by `sanitize_content()` (strips leading/trailing whitespace, removes `\x00` null bytes, collapses runs of 4+ consecutive newlines), and there are other Pydantic `max_length` constraints on downstream model fields that could reject long descriptions before they reach the API.

### Rationale

A line-by-line audit of the data flow reveals:

1. **User input** → `ChatMessageRequest.content` (`max_length=100000`; content is stripped, null bytes removed, and runs of 4+ newlines collapsed by `sanitize_content()` — content is not preserved byte-for-byte at this boundary)
2. **AI processing** → `ai_agent.py:generate_issue_recommendation()` sends full normalized input to LLM; title is truncated to 256 chars (line 233–234) but description fields are not truncated
3. **Storage** → `IssueRecommendation` stored in `_recommendations` dict (in-memory, no serialization limits)
4. **Preview messages** → `chat.py:209` truncates `technical_notes[:300]` and `chat.py:359` truncates `description[:200]` — but these are **display-only** in the chat bubble, not the API payload
5. **Confirmation** → `workflow.py:confirm_recommendation()` calls `orchestrator.format_issue_body()` which assembles full text, then calls `github.create_issue(body=body)`
6. **GitHub API call** → `service.py:create_issue()` passes `body` directly in JSON payload — no truncation

**Potential issues found:**
- `AITaskProposal.proposed_description` has `max_length=65535` (line 37–38 of recommendation.py) — this is 65,535 not 65,536. Off-by-one: GitHub API allows 65,536.
- `ProposalConfirmRequest.edited_description` has `max_length=65535` — same off-by-one.
- `IssueRecommendation` fields (`user_story`, `ui_ux_description`, `technical_notes`) have **no** max_length, which is correct.
- The `format_issue_body()` method in `orchestrator.py` assembles a body from multiple fields (user_story, ui_ux_description, requirements, technical_notes, metadata, original_context) plus a tracking table — the combined body could exceed 65,536 characters even if individual fields don't.
- **No validation exists** to check the assembled body length before sending to GitHub API.

### Alternatives Considered

- **Add max_length to all IssueRecommendation fields**: Rejected — would introduce artificial limits and complicate the user experience.
- **Truncate at the API call layer**: Rejected — violates FR-002 (no silent truncation).
- **Validate combined body length and notify user**: Chosen — matches FR-006 (explicit user notification).

---

## Research Task 2: GitHub REST API Body Limits and Behavior

### Decision

The GitHub REST API accepts up to **65,536 characters** (64 KiB) in the `body` field for issue creation. Exceeding this returns a `422 Unprocessable Entity` error.

### Rationale

The GitHub REST API documentation for [Create an issue](https://docs.github.com/en/rest/issues/issues#create-an-issue) specifies:
- The `body` parameter is a string
- Maximum length is 65,536 characters
- Exceeding the limit returns HTTP 422 with an error message about the body being too long
- All markdown is preserved as-is — GitHub does not modify the body content

The system should:
1. Check the assembled body length before calling the API
2. If it exceeds 65,536 characters, return an explicit error to the user
3. If it's within the limit, pass it through unchanged

### Alternatives Considered

- **Silently truncate to 65,536 characters**: Rejected — violates FR-002 and FR-006.
- **Let the API return a 422 and surface the raw error**: Partially acceptable, but a better UX is to pre-validate and give a clear message.
- **Pre-validate and provide clear user notification**: Chosen — best UX, matches FR-006.

---

## Research Task 3: Pydantic max_length Constraints in Recommendation Models

### Decision

Increase `max_length` from `65535` to `65536` on `AITaskProposal.proposed_description` and `ProposalConfirmRequest.edited_description` to match the actual GitHub API limit. Do not add max_length to `IssueRecommendation` fields.

### Rationale

The current `max_length=65535` is an off-by-one error (65,535 vs GitHub's 65,536 limit). This could cause Pydantic validation to reject a description at exactly 65,536 characters, even though the GitHub API would accept it.

The `IssueRecommendation` model does not have `max_length` on its text fields (user_story, technical_notes, etc.), which is correct — these fields are assembled into a combined body by `format_issue_body()`, and the combined length check should happen at the assembled body level, not on individual fields.

### Alternatives Considered

- **Remove max_length entirely from AITaskProposal**: Rejected — having a reasonable max_length provides defense-in-depth against accidentally sending enormous payloads.
- **Keep max_length=65535**: Rejected — off-by-one would reject valid descriptions at the 65,536-character boundary.
- **Set max_length=65536**: Chosen — matches the GitHub API limit exactly.

---

## Research Task 4: LLM Prompt Construction and Description Passthrough

### Decision

The current LLM prompt construction already preserves user input verbatim. No changes needed to the prompt construction path.

### Rationale

The `issue_generation.py` prompt system:
1. Embeds the user's full input in the prompt with explicit instructions: "PRESERVE ALL DETAILS BELOW — every word matters"
2. The system prompt includes: "NEVER drop, omit, or summarize away any detail the user provided"
3. The AI generates structured output (title, user_story, requirements, etc.) — but the `original_input` is stored separately and used as `original_context` in the issue body
4. The `format_issue_body()` method in the orchestrator includes an "Original Request" section that preserves the user's verbatim input as a blockquote

The LLM processing path and the verbatim passthrough path are already separated — `original_input`/`original_context` is never modified by AI reasoning.

### Alternatives Considered

- **Add a separate "raw description" field**: Rejected — `original_input` and `original_context` already serve this purpose.
- **Skip LLM processing for long descriptions**: Rejected — the LLM adds value (structured analysis) without modifying the original text.

---

## Research Task 5: Signal Chat Pipeline Audit

### Decision

The Signal chat pipeline (`signal_chat.py`) constructs issue bodies from structured recommendation fields, not from a raw user description. The display-only truncation in Signal replies (e.g., `user_story[:300]`, `description[:500]`) does not affect the API body.

### Rationale

Signal chat flow:
1. Signal message → parsed by Signal bridge
2. Feature request detected → AI recommendation generated (same `ai_agent.py` path)
3. Recommendation confirmed → `create_issue()` called with structured body built from `body_parts` list
4. Signal reply previews use truncation for readability, but the actual issue body is constructed from full fields

No changes needed for the Signal pipeline — the same `create_issue()` service method is used, and the body is built from full-length fields.

### Alternatives Considered

- **Apply same length validation to Signal path**: Chosen — the validation at the `create_issue()` or `format_issue_body()` level will automatically cover both web and Signal paths.

---

## Research Task 6: Frontend Description Handling

### Decision

The frontend passes the description through without modification. The `IssueRecommendationPreview` component displays the full description in the UI, and the confirmation API call sends the recommendation ID (not the description text) to the backend.

### Rationale

Frontend flow:
1. User types feature request → `chatApi.sendMessage(content)` sends full text
2. Backend returns `action_data` with recommendation fields for preview
3. User clicks "Confirm" → `workflowApi.confirmRecommendation(recommendationId)` sends only the ID
4. Backend looks up the stored recommendation and creates the issue

The frontend never truncates or modifies the description — it only displays it in the preview component and passes the recommendation ID for confirmation. No frontend changes are needed for the core passthrough requirement.

For the user notification requirement (FR-006), the frontend will need to display an error message if the backend returns a body-too-long validation error.

### Alternatives Considered

- **Add client-side length validation**: Nice-to-have but not strictly necessary — the backend validation is authoritative. Could be added as a future enhancement.
- **Show character count in preview**: Useful UX improvement but out of scope for MVP.
