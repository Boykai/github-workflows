# ADR-004: Pluggable `CompletionProvider` abstraction for LLM backends

**Status**: Accepted
**Date**: 2025-Q1

## Context

The backend uses LLM completions in multiple places: issue generation, task generation, agent chat, chore template refinement. The initial implementation hardcoded the Copilot SDK. When Azure OpenAI was added as an enterprise option, the integration points needed to stay clean.

## Decision

Define a `CompletionProvider` protocol/abstract interface in `services/completion_providers.py`. Both `CopilotCompletionProvider` and `AzureOpenAICompletionProvider` implement this interface.

The active provider is selected at startup based on `AI_PROVIDER` and injected via `app.state`. All callers depend on the interface, not a concrete class.

## Consequences

- **+** Adding a new LLM backend (e.g., Anthropic, local Ollama) requires only implementing the interface and registering it — no changes to callers.
- **+** Tests can inject a mock provider without monkey-patching.
- **−** The interface must remain stable across providers; any provider-specific capability (e.g., streaming, tool-calling) must be added to the shared interface or handled with optional overrides.
