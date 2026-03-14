# ADR-003: GitHub Copilot as default AI provider via OAuth token

**Status**: Accepted
**Date**: 2025-Q1

## Context

The system generates GitHub Issues from natural language descriptions and orchestrates Copilot agents. The AI provider must:

1. Be available to all users without a separate API key or billing account.
2. Operate within GitHub's security model (no third-party token leakage).
3. Support the chat-completion interface needed for structured JSON output.

Options evaluated:

- **OpenAI (direct)** — Requires each user to supply a personal API key; adds friction and cost.
- **Azure OpenAI** — Requires an Azure subscription; good for enterprise but excludes individual contributors.
- **GitHub Copilot SDK** — Uses the user's existing GitHub OAuth token; no extra credentials needed for users with a Copilot subscription.

## Decision

Default to the GitHub Copilot SDK (`github-copilot-sdk`) as `AI_PROVIDER=copilot`. The user's GitHub OAuth token (obtained during login) is passed per-request.

Azure OpenAI is supported as an opt-in fallback via `AI_PROVIDER=azure_openai` with `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_KEY`.

## Consequences

- **+** Zero friction for users who already have GitHub Copilot — no additional credentials.
- **+** Token scoping is reused from the OAuth flow; no separate secret management.
- **+** Both providers share the same `CompletionProvider` interface (see ADR-004).
- **−** Requires an active GitHub Copilot subscription; free accounts cannot use the default provider.
- **−** Copilot SDK rate limits and model availability are governed by GitHub, not the application.
