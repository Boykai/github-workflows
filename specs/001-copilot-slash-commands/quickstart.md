# Quickstart: Add 9 GitHub Copilot Slash Commands to Solune Chat

**Feature**: 001-copilot-slash-commands | **Date**: 2026-03-27

## Prerequisites

- Python ≥3.12 with `pip` (backend)
- Node.js ≥20 with `npm` (frontend)
- GitHub OAuth token (for Copilot completion provider)
- Repository cloned: `github-workflows`

## Development Setup

### 1. Backend

```bash
cd solune/backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

### 2. Frontend

```bash
cd solune/frontend
npm ci
```

## Files to Create

### Backend: `solune/backend/src/services/copilot_commands.py`

New service file containing:
- `COPILOT_COMMANDS` — `set[str]` of the 9 command names
- `COPILOT_COMMAND_PROMPTS` — `dict[str, str]` mapping each command to its system prompt
- `is_copilot_command(content: str) → tuple[str, str] | None` — detects and extracts command + args
- `execute_copilot_command(command: str, args: str, github_token: str) → str` — builds messages and calls `CopilotCompletionProvider.complete()`

### Frontend: `solune/frontend/src/lib/commands/handlers/copilot.ts`

New handler file containing:
- `copilotPassthroughHandler()` — returns `{ success: true, message: '', clearInput: true, passthrough: true }`

## Files to Modify

| File | Change |
|------|--------|
| `solune/frontend/src/lib/commands/types.ts` | Add `category?: 'solune' \| 'copilot'` to `CommandDefinition` |
| `solune/frontend/src/lib/commands/registry.ts` | Import `copilotPassthroughHandler`, register 9 commands with `category: 'copilot'`, add `category: 'solune'` to existing commands |
| `solune/frontend/src/components/chat/CommandAutocomplete.tsx` | Group commands by category, render "Solune" and "GitHub Copilot" section headers |
| `solune/backend/src/api/chat.py` | Add `_handle_copilot_command()` at priority 0.1 in `send_message()` dispatch chain |

## Files to Create (Tests)

| File | Coverage |
|------|----------|
| `solune/frontend/src/lib/commands/registry.test.ts` | Extend existing — verify 9 Copilot commands in registry, parseCommand behavior, handler shape |
| `solune/backend/tests/unit/test_copilot_commands.py` | New — verify `is_copilot_command()` parsing, rejection of non-Copilot input, `execute_copilot_command()` calls provider with correct prompt |

## Verification Commands

### 1. Frontend tests

```bash
cd solune/frontend && npm run test
```

### 2. Backend Copilot command tests

```bash
cd solune/backend && python -m pytest tests/unit/test_copilot_commands.py -v
```

### 3. Full backend suite (regression check)

```bash
cd solune/backend && python -m pytest
```

### 4. Frontend lint

```bash
cd solune/frontend && npx eslint src/lib/commands/
```

### 5. Frontend type-check

```bash
cd solune/frontend && npm run type-check
```

### 6. Frontend build

```bash
cd solune/frontend && npm run build
```

## Manual Smoke Tests

1. **Autocomplete visibility**: Type `/` in chat input → confirm "Solune" and "GitHub Copilot" section headers appear, with all 9 Copilot commands listed under "GitHub Copilot"
2. **Command execution**: Type `/explain What is a closure?` → submit → confirm a Copilot-generated explanation appears as an assistant message
3. **Input clearing**: After submitting a Copilot command → confirm the chat input field is cleared
4. **Existing commands**: Type `/help`, `/agent test`, `/plan test`, `/clear` → confirm each works exactly as before
5. **Non-Copilot input**: Type `Hello world` → confirm it routes to the default handler (not intercepted by Copilot handler)

## Architecture Reference

```
User → Chat Input → parseCommand() → getCommand()
                                        │
                              passthrough: true?
                                   │         │
                                  yes        no
                                   │         │
                                   ▼         ▼
                          POST /chat/messages  Execute handler locally
                                   │
                          send_message() dispatch:
                            Priority 0.0: _handle_agent_command()
                            Priority 0.1: _handle_copilot_command()  ← NEW
                            Priority 0.5: _handle_transcript_upload()
                            Priority 1.0: _handle_feature_request()
                            Priority 2.0: _handle_status_change()
                            Priority 3.0: _handle_task_generation()
```
