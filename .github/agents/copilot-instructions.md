# codeagentworkflows Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-30

## Active Technologies
- In-memory session storage (MVP), Redis for token caching (future) (001-github-project-chat)
- Python 3.11 + FastAPI, httpx, azure-ai-inference, pydantic (001-github-project-workflow)
- In-memory (MVP) with session-based caching (001-github-project-workflow)
- Azure Bicep (latest), Shell scripting (bash), Azure CLI 2.x + Azure CLI, Bicep CLI, Azure Resource Manager (001-azure-iac)
- N/A (application uses GitHub API, no persistent database required) (001-azure-iac)

- Python 3.11+ (backend), TypeScript 5.x (frontend) (001-github-project-chat)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+ (backend), TypeScript 5.x (frontend): Follow standard conventions

## Recent Changes
- 001-azure-iac: Added Azure Bicep (latest), Shell scripting (bash), Azure CLI 2.x + Azure CLI, Bicep CLI, Azure Resource Manager
- 001-github-project-workflow: Added Python 3.11 + FastAPI, httpx, azure-ai-inference, pydantic
- 001-github-project-chat: Added Python 3.11+ (backend), TypeScript 5.x (frontend)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
