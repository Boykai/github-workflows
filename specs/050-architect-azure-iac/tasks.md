# Tasks: Architect Agent for Azure IaC

**Input**: Design documents from `/specs/050-architect-azure-iac/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — tests are explicitly requested in the feature specification for backend Azure credential storage and frontend credential field rendering.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/` (Python/FastAPI), `solune/frontend/src/` (TypeScript/React)
- **Backend tests**: `solune/backend/tests/`
- **Frontend tests**: colocated `*.test.tsx` files
- **Agent files**: `.github/agents/`, `.github/prompts/`
- **MCP config**: `.vscode/mcp.json`, `.github/agents/mcp.json`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: MCP configuration for both local and remote environments — enables agent tooling

- [ ] T001 [P] Add `microsoft/azure-mcp` entry to `.vscode/mcp.json` `servers` object with `type: "stdio"`, `command: "npx"`, `args: ["@azure/mcp@latest", "server", "start"]` — per contract in `contracts/agent-config.md` Contract 3
- [ ] T002 [P] Add `azure-mcp` entry to `.github/agents/mcp.json` `mcpServers` object with `type: "local"`, `command: "npx"`, `args: ["@azure/mcp@latest", "server", "start"]`, `tools: ["*"]` — per contract in `contracts/agent-config.md` Contract 4

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add `pynacl` dependency for GitHub Secrets encryption — required before any credential storage tasks

**⚠️ CRITICAL**: No backend credential storage work can begin until this phase is complete

- [ ] T003 Add `pynacl` to `dependencies` list in `solune/backend/pyproject.toml` and run `pip install -e ".[dev]"` to verify installation

**Checkpoint**: Foundation ready — `pynacl` available for `libsodium` sealed-box encryption. User story implementation can now begin.

---

## Phase 3: User Story 1 — New App Ships with Azure-Ready Infrastructure (Priority: P1) 🎯 MVP

**Goal**: The Architect agent generates a complete Azure infrastructure package (Bicep modules, `azure.yaml`, architecture diagrams, deploy button) for every new app.

**Independent Test**: Invoke the Architect agent on a scaffolded app repo → verify `infra/` directory, `azure.yaml`, architecture diagrams in `docs/architectures/`, and README deploy button are generated and structurally valid.

### Implementation for User Story 1

- [ ] T004 [US1] Create `.github/agents/architect.agent.md` with YAML frontmatter (`name: Architect`, `description`, `mcp-servers` for Context7, CodeGraphContext, and azure-mcp) per contract in `contracts/agent-config.md` Contract 1
- [ ] T005 [US1] Write Phase 0 — Discovery instructions in `.github/agents/architect.agent.md`: analyze project structure (docker-compose, services, existing infra), use CodeGraphContext for dependency mapping, check for existing `azure.yaml`/Bicep/Terraform
- [ ] T006 [US1] Write Phase 1 — Architecture Diagram instructions in `.github/agents/architect.agent.md`: generate Mermaid `.mmd` diagrams (high-level, deployment) in `docs/architectures/`, following conventions from `solune/docs/architectures/`
- [ ] T007 [US1] Write Phase 2 — IaC Generation instructions in `.github/agents/architect.agent.md`: generate Bicep modules in `infra/` with `main.bicep`, per-resource modules, `main.bicepparam`, using Azure Verified Modules (AVM)
- [ ] T008 [US1] Write Phase 3 — Azure Developer CLI Scaffold instructions in `.github/agents/architect.agent.md`: generate `azure.yaml` manifest with services, hooks, env config supporting `azd init`/`azd up`/`azd deploy`
- [ ] T009 [US1] Write Phase 4 — 1-Click Deploy Button instructions in `.github/agents/architect.agent.md`: add "Deploy to Azure" badge and `azd init` one-liner to app README
- [ ] T010 [US1] Write Phase 5 — GitHub Secrets Setup instructions in `.github/agents/architect.agent.md`: document CI/CD workflow referencing `${{ secrets.AZURE_CLIENT_ID }}` and `${{ secrets.AZURE_CLIENT_SECRET }}`
- [ ] T011 [US1] Write Phase 6 — Validation instructions in `.github/agents/architect.agent.md`: verify Bicep compiles (`az bicep build`), `azure.yaml` valid, diagrams render
- [ ] T012 [US1] Write Operating Rules section in `.github/agents/architect.agent.md`: Bicep over ARM JSON, use AVM, follow WAF, never hardcode secrets, use `azd` env vars, follow project naming conventions via CodeGraphContext

**Checkpoint**: Architect agent definition is complete and can be invoked via `@architect` prompt.

---

## Phase 4: User Story 2 — Azure Credentials Securely Stored During App Creation (Priority: P1)

**Goal**: Azure Client ID and Client Secret are optionally collected during app creation, encrypted, and stored as GitHub repository secrets.

**Independent Test**: Create a new app via Solune UI with Azure credentials → verify `AZURE_CLIENT_ID` and `AZURE_CLIENT_SECRET` appear in the new repo's GitHub Secrets and no plaintext credentials exist in any generated files.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US2] Add test cases in `solune/backend/tests/unit/test_github_repository.py` for `set_repository_secret()`: mock `_rest()` → verify GET public-key call, sealed-box encryption with PyNaCl, PUT encrypted secret call; test error handling for API failures
- [ ] T014 [P] [US2] Add test cases in `solune/backend/tests/unit/test_app_service_new_repo.py` for credential storage in create flow: mock `set_repository_secret()` → verify called twice (once per secret) when credentials provided; verify NOT called when credentials absent; verify app creation succeeds even when secret storage fails

### Implementation for User Story 2

- [ ] T015 [US2] Add `azure_client_id: str | None = Field(default=None, min_length=1)` and `azure_client_secret: str | None = Field(default=None, min_length=1, json_schema_extra={"writeOnly": True})` fields to `AppCreate` model in `solune/backend/src/models/app.py`
- [ ] T016 [US2] Add `@model_validator(mode="after")` for paired Azure credential validation (both or neither) to `AppCreate` model in `solune/backend/src/models/app.py`
- [ ] T017 [US2] Implement `set_repository_secret()` async method on `RepositoryMixin` in `solune/backend/src/services/github_projects/repository.py`: GET public key → encrypt with `nacl.public.SealedBox` → PUT encrypted value — per contract in `contracts/backend-api.md` Contract 2
- [ ] T018 [US2] Wire credential storage into `create_app_with_new_repo()` in `solune/backend/src/services/app_service.py`: after repo creation, call `set_repository_secret()` for both `AZURE_CLIENT_ID` and `AZURE_CLIENT_SECRET` if provided; wrap in try/except with warning log on failure
- [ ] T019 [P] [US2] Add `azure_client_id?: string` and `azure_client_secret?: string` fields to `AppCreate` interface in `solune/frontend/src/types/apps.ts`
- [ ] T020 [US2] Add `azureClientId` and `azureClientSecret` state variables to `AppsPage.tsx`, add two input fields (Client ID as `type="text"`, Client Secret as `type="password"`) in the "New Repository Settings" section, add paired validation in submit handler, include in `createMutation.mutate()` payload when `repo_type === 'new-repo'` in `solune/frontend/src/pages/AppsPage.tsx`

**Checkpoint**: Azure credential storage is fully functional — backend stores encrypted secrets, frontend collects credentials, paired validation works.

---

## Phase 5: User Story 3 — Architecture Diagrams Generated for Every New App (Priority: P2)

**Goal**: Mermaid-format architecture diagrams are generated following the established pattern in `solune/docs/architectures/`.

**Independent Test**: Invoke the Architect agent → verify `.mmd` files are created in `docs/architectures/`, follow Mermaid syntax, and render correctly.

### Implementation for User Story 3

Note: The diagram generation capability is defined within the Architect agent instructions (T006 above). This phase ensures the conventions and patterns are fully specified in the agent.

- [ ] T021 [US3] Verify that the Phase 1 — Architecture Diagram instructions in `.github/agents/architect.agent.md` reference all four diagram types from `solune/docs/architectures/`: high-level, deployment, components, data-flow — and specify `graph TB` orientation, `subgraph` groupings, `-->` arrows with labels

**Checkpoint**: Architecture diagram generation follows established Mermaid conventions.

---

## Phase 6: User Story 4 — MCP Configuration Enables Agent Tooling (Priority: P2)

**Goal**: Azure MCP tools are accessible in both local VS Code and remote GitHub Custom Agent environments.

**Independent Test**: Open VS Code Agent mode → verify Azure MCP tools listed; confirm `.github/agents/mcp.json` entry follows CodeGraphContext pattern.

### Implementation for User Story 4

Note: MCP configuration tasks are in Phase 1 (T001, T002). This phase validates the configuration works end-to-end.

- [ ] T022 [US4] Validate `.vscode/mcp.json` remains valid JSON after Azure MCP entry addition — run `python -m json.tool .vscode/mcp.json`
- [ ] T023 [P] [US4] Validate `.github/agents/mcp.json` remains valid JSON after Azure MCP entry addition — run `python -m json.tool .github/agents/mcp.json`

**Checkpoint**: MCP configuration validated — both local and remote environments have Azure MCP tools available.

---

## Phase 7: User Story 5 — Agent and Prompt Files Registered in Copilot (Priority: P3)

**Goal**: The Architect agent appears in the VS Code Copilot agent picker and is documented in `copilot-instructions.md`.

**Independent Test**: Open agent file in VS Code → confirm it appears in agent picker; verify `/architect` prompt routes correctly; check `copilot-instructions.md` utility agents table.

### Implementation for User Story 5

- [ ] T024 [P] [US5] Create `.github/prompts/architect.prompt.md` with `---\nagent: architect\n---` matching the 15 existing prompt files — per contract in `contracts/agent-config.md` Contract 2
- [ ] T025 [US5] Update `.github/agents/copilot-instructions.md` utility agents table: add `architect` row with description "Generates Azure IaC (Bicep), `azd` scaffolds, architecture diagrams, and deploy buttons. Always runs for new apps." in alphabetical position (before `archivist`) — per contract in `contracts/agent-config.md` Contract 5
- [ ] T026 [US5] Update MCP Configuration section in `.github/agents/copilot-instructions.md` to note Azure MCP availability in `.github/agents/mcp.json` — per contract in `contracts/agent-config.md` Contract 5

**Checkpoint**: Architect agent is fully registered, discoverable, and documented.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup across all user stories

- [ ] T027 [P] Run `ruff check src/ && ruff format --check src/` in `solune/backend/` — verify no lint errors
- [ ] T028 [P] Run `pyright src` in `solune/backend/` — verify no type errors
- [ ] T029 [P] Run `npx tsc --noEmit` in `solune/frontend/` — verify no TypeScript errors
- [ ] T030 [P] Run `pytest tests/ -x -q` in `solune/backend/` — verify all tests pass including new credential storage tests
- [ ] T031 [P] Run `npx vitest run` in `solune/frontend/` — verify all frontend tests pass
- [ ] T032 Run `quickstart.md` validation — walk through each step and verify commands work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately (MCP config edits)
- **Foundational (Phase 2)**: No dependencies on Phase 1 — can run in parallel (pynacl installation)
- **User Story 1 (Phase 3)**: Depends on Phase 1 completion (MCP config needed for agent definition)
- **User Story 2 (Phase 4)**: Depends on Phase 2 completion (pynacl needed for encryption)
- **User Story 3 (Phase 5)**: Depends on Phase 3 (agent definition must exist for diagram instructions)
- **User Story 4 (Phase 6)**: Depends on Phase 1 (MCP config must exist for validation)
- **User Story 5 (Phase 7)**: Depends on Phase 3 (agent file must exist before registration)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Agent definition — no dependency on other stories
- **User Story 2 (P1)**: Credential storage — no dependency on other stories (independent of agent)
- **User Story 3 (P2)**: Diagram conventions — depends on US1 (agent file must exist)
- **User Story 4 (P2)**: MCP validation — depends on Phase 1 (config entries)
- **User Story 5 (P3)**: Registration — depends on US1 (agent file must exist)

### Parallel Opportunities

- Phase 1 tasks (T001, T002) can run in parallel
- Phase 1 and Phase 2 can run in parallel (different files)
- User Story 1 (Phase 3) and User Story 2 (Phase 4) can run in parallel after their prerequisites
- Tests within User Story 2 (T013, T014) can run in parallel
- Frontend type change (T019) can run in parallel with backend implementation (T015-T018)
- All polish tasks (T027-T031) can run in parallel

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: MCP Configuration (T001-T002)
2. Complete Phase 2: Foundational (T003)
3. Complete Phase 3: User Story 1 — Agent Definition (T004-T012)
4. Complete Phase 4: User Story 2 — Credential Storage (T013-T020)
5. **STOP and VALIDATE**: Agent generates valid output; credentials are stored securely

### Incremental Delivery

1. MCP Config + Foundation → Tooling ready
2. Agent Definition → Agent invokable for IaC generation (MVP!)
3. Credential Storage → Full Create New App flow with Azure credentials
4. Diagram Conventions + MCP Validation → Quality assurance
5. Registration + Documentation → Discoverability and polish

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Agent file tasks (T004-T012) are intentionally NOT parallel — they build the agent file sequentially
- Backend credential tasks depend on `pynacl` (Phase 2) — cannot start before T003
- Frontend tasks (T019-T020) can start as soon as the TypeScript type is defined
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
