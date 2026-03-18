#!/usr/bin/env bash
# Generate Mermaid architecture diagrams from the codebase.
# Outputs .mmd files to docs/architectures/. Only overwrites a file when its
# content has actually changed, so downstream git operations see no noise.
#
# Usage:
#   ./scripts/generate-diagrams.sh          # generate all diagrams
#   ./scripts/generate-diagrams.sh --check  # exit 1 if any diagram is out of date

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="$REPO_ROOT/solune/docs/architectures"
CHECK_MODE=false
CHANGED=0

if [[ "${1:-}" == "--check" ]]; then
    CHECK_MODE=true
fi

mkdir -p "$OUT_DIR"

# ---------------------------------------------------------------------------
# Helper: write a file only when content differs
# ---------------------------------------------------------------------------
write_if_changed() {
    local target="$1"
    local content="$2"
    local tmpfile

    tmpfile=$(mktemp)
    printf '%s\n' "$content" > "$tmpfile"

    if [[ -f "$target" ]] && cmp -s "$target" "$tmpfile"; then
        echo "  ✓ $(basename "$target") — unchanged"
        rm -f "$tmpfile"
        return
    fi

    if $CHECK_MODE; then
        echo "  ✗ $(basename "$target") — out of date"
        rm -f "$tmpfile"
        CHANGED=1
        return
    fi

    mv "$tmpfile" "$target"
    echo "  ↻ $(basename "$target") — updated"
}

# ---------------------------------------------------------------------------
# 1. High-Level Architecture Diagram
# ---------------------------------------------------------------------------
generate_high_level() {
    local diagram
    diagram=$(cat <<'MERMAID'
graph TB
    subgraph Client["Client Browser"]
        FE["Frontend<br/>React 19 · Vite 8<br/>TypeScript 5.9"]
    end

    subgraph DockerCompose["Docker Compose Network"]
        NGINX["nginx reverse proxy<br/>Static assets · SPA fallback"]
        BE["Backend<br/>FastAPI · Python 3.12+"]
        DB[("SQLite<br/>WAL mode<br/>aiosqlite")]
        SIG["Signal Sidecar<br/>signal-cli-rest-api"]
    end

    subgraph External["External Services"]
        GH["GitHub API<br/>GraphQL + REST"]
        AI["AI Providers<br/>Copilot SDK · Azure OpenAI"]
    end

    FE -- "HTTP / WebSocket" --> NGINX
    NGINX -- "/api/* proxy" --> BE
    BE -- "aiosqlite" --> DB
    BE -- "HTTP + WS" --> SIG
    BE -- "githubkit SDK" --> GH
    BE -- "Completion API" --> AI
MERMAID
)
    write_if_changed "$OUT_DIR/high-level.mmd" "$diagram"
}

# ---------------------------------------------------------------------------
# 2. Backend Component Diagram — derived from backend/src/services/
# ---------------------------------------------------------------------------
generate_backend_components() {
    local services_dir="$REPO_ROOT/solune/backend/src/services"
    local api_dir="$REPO_ROOT/solune/backend/src/api"

    # Discover service modules (directories and top-level .py files)
    local service_defs=""
    local idx=0

    if [[ -d "$services_dir" ]]; then
        for entry in "$services_dir"/*; do
            local name
            name=$(basename "$entry")
            # Skip __pycache__ and __init__
            [[ "$name" == "__pycache__" || "$name" == "__init__.py" ]] && continue

            local label
            label=$(echo "$name" | sed 's/\.py$//' | sed 's/_/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1')
            local node_id="SVC_${idx}"

            if [[ -d "$entry" ]]; then
                local count
                count=$(find "$entry" -maxdepth 1 -name '*.py' ! -name '__init__.py' | wc -l | tr -d ' ')
                service_defs="${service_defs}        ${node_id}[\"${label}<br/>(${count} modules)\"]"$'\n'
            else
                service_defs="${service_defs}        ${node_id}[\"${label}\"]"$'\n'
            fi
            idx=$((idx + 1))
        done
    fi

    # Discover API route modules
    local api_defs=""
    local aidx=0

    if [[ -d "$api_dir" ]]; then
        for entry in "$api_dir"/*.py; do
            local name
            name=$(basename "$entry" .py)
            [[ "$name" == "__init__" ]] && continue
            local label
            label=$(echo "$name" | sed 's/_/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1')
            local node_id="API_${aidx}"
            api_defs="${api_defs}        ${node_id}[\"${label}\"]"$'\n'
            aidx=$((aidx + 1))
        done
    fi

    local diagram
    diagram=$(cat <<MERMAID
graph TB
    subgraph API["API Routes"]
${api_defs}    end

    subgraph Services["Business Logic Services"]
${service_defs}    end

    subgraph Infra["Infrastructure"]
        DB[("SQLite · aiosqlite")]
        DI["FastAPI DI<br/>app.state singletons"]
        MW["Middleware<br/>RequestID · CORS"]
    end

    API --> Services
    Services --> DB
    Services --> DI
    API --> MW
MERMAID
)
    write_if_changed "$OUT_DIR/backend-components.mmd" "$diagram"
}

# ---------------------------------------------------------------------------
# 3. Frontend Component Diagram — derived from frontend/src/
# ---------------------------------------------------------------------------
generate_frontend_components() {
    local src_dir="$REPO_ROOT/solune/frontend/src"

    # Discover component groups
    local comp_dir="$src_dir/components"
    local comp_defs=""
    local cidx=0

    if [[ -d "$comp_dir" ]]; then
        for entry in "$comp_dir"/*/; do
            [[ ! -d "$entry" ]] && continue
            local name
            name=$(basename "$entry")
            local label
            label=$(echo "$name" | sed 's/_/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1')
            local count
            count=$(find "$entry" -maxdepth 1 \( -name '*.tsx' -o -name '*.ts' \) ! -name '*.test.*' ! -name '*.spec.*' | wc -l | tr -d ' ')
            comp_defs="${comp_defs}        C_${cidx}[\"${label}<br/>(${count} files)\"]"$'\n'
            cidx=$((cidx + 1))
        done
    fi

    # Discover pages
    local pages_dir="$src_dir/pages"
    local page_defs=""
    local pidx=0

    if [[ -d "$pages_dir" ]]; then
        for entry in "$pages_dir"/*.tsx; do
            [[ ! -f "$entry" ]] && continue
            local name
            name=$(basename "$entry" .tsx)
            # Skip test files
            [[ "$name" == *.test ]] && continue
            page_defs="${page_defs}        P_${pidx}[\"${name}\"]"$'\n'
            pidx=$((pidx + 1))
        done
    fi

    # Discover hooks
    local hooks_dir="$src_dir/hooks"
    local hook_count=0
    if [[ -d "$hooks_dir" ]]; then
        hook_count=$(find "$hooks_dir" -maxdepth 1 \( -name '*.ts' -o -name '*.tsx' \) ! -name '*.test.*' ! -name '*.spec.*' | wc -l | tr -d ' ')
    fi

    local diagram
    diagram=$(cat <<MERMAID
graph TB
    subgraph Pages["Pages"]
${page_defs}    end

    subgraph Components["Component Groups"]
${comp_defs}    end

    subgraph State["State & Services"]
        Hooks["Custom Hooks<br/>(${hook_count} hooks)"]
        API["api.ts<br/>HTTP + WS Client"]
        TQ["TanStack Query v5<br/>Server State"]
    end

    subgraph Styling["Styling & Theming"]
        TW["Tailwind CSS 4"]
        Theme["ThemeProvider<br/>dark / light / system"]
    end

    Pages --> Components
    Pages --> Hooks
    Components --> Hooks
    Hooks --> API
    Hooks --> TQ
    Components --> TW
    Components --> Theme
MERMAID
)
    write_if_changed "$OUT_DIR/frontend-components.mmd" "$diagram"
}

# ---------------------------------------------------------------------------
# 4. Data Flow Diagram
# ---------------------------------------------------------------------------
generate_data_flow() {
    local diagram
    diagram=$(cat <<'MERMAID'
graph LR
    User(("User"))

    subgraph Frontend
        UI["React UI"]
        WS_C["WebSocket Client"]
        TQ["TanStack Query"]
    end

    subgraph Backend
        Router["FastAPI Router"]
        WS_S["WebSocket Server"]
        Orch["Workflow Orchestrator"]
        Poll["Copilot Polling"]
        GHSvc["GitHub Projects Service"]
        Cache["In-Memory Cache"]
    end

    DB[("SQLite")]
    GitHub["GitHub API"]
    Signal["Signal Sidecar"]
    AI["AI Provider"]

    User --> UI
    UI -- "REST requests" --> TQ
    TQ -- "HTTP" --> Router
    UI -- "WS connect" --> WS_C
    WS_C <--> |"real-time updates"| WS_S
    Router --> GHSvc
    Router --> Orch
    Orch --> Poll
    Poll --> AI
    GHSvc --> GitHub
    GHSvc --> Cache
    Router --> DB
    Orch --> DB
    Router --> Signal
MERMAID
)
    write_if_changed "$OUT_DIR/data-flow.mmd" "$diagram"
}

# ---------------------------------------------------------------------------
# 5. Deployment Diagram — derived from docker-compose.yml
# ---------------------------------------------------------------------------
generate_deployment() {
    local diagram
    diagram=$(cat <<'MERMAID'
graph TB
    subgraph Host["Docker Host"]
        subgraph Net["solune-network (bridge)"]
            FE["solune-frontend<br/>nginx :8080<br/>→ host :5173"]
            BE["solune-backend<br/>uvicorn :8000"]
            SIG["solune-signal-api<br/>signal-cli :8080 (internal)"]
        end
        VOL_DATA[("solune-data volume<br/>SQLite DB")]
        VOL_SIG[("signal-cli-config volume")]
    end

    FE -- "/api/* reverse proxy" --> BE
    BE -- "HTTP + WS" --> SIG
    BE --- VOL_DATA
    SIG --- VOL_SIG
MERMAID
)
    write_if_changed "$OUT_DIR/deployment.mmd" "$diagram"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
echo "📊 Generating Mermaid architecture diagrams…"
generate_high_level
generate_backend_components
generate_frontend_components
generate_data_flow
generate_deployment

if $CHECK_MODE && [[ $CHANGED -ne 0 ]]; then
    echo ""
    echo "❌ Diagrams are out of date. Run ./scripts/generate-diagrams.sh to regenerate."
    exit 1
fi

echo ""
echo "✅ Diagram generation complete — output in docs/architectures/"
